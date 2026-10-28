"""Render hash-locked, source-text font specimens without modifying game resources.

Uses the project's shared-baseline glyph rasterizer and BC3 round-trip. The
output is an offline typography specimen, not an emulated game screenshot.
All locale text, font identities, roles and source references live in a profile.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import math
from pathlib import Path
import re
import unicodedata
import urllib.request
import zipfile

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version
from fontTools import __version__ as fonttools_version
from fontTools.ttLib import TTFont
from .supplement_font import rasterize_plan
from .font_shadow import shadow_pixels
from .font_outline import embolden_glyph  # Retained public import for specimen callers.
from .texture_overlay import encode_rgba_block
from .ue3_textures import decode_dxt5, encode_white_bc3_block

MAX_FONT_BYTES = 40 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return sha(json.dumps(data, sort_keys=True, separators=(',', ':')).encode())


def local(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('Expected a project-relative path')
    root = Path(root).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Path escapes project')
    return path


def locked(root, item):
    path = local(root, item['path'])
    data = path.read_bytes()
    identity = data
    mode = item.get('identity_mode', 'raw')
    if mode == 'utf8-lf':
        text = data.decode('utf-8').replace('\r\n', '\n')
        if '\r' in text:
            raise ValueError('Unsupported bare CR in text input')
        identity = text.encode('utf-8')
    elif mode != 'raw':
        raise ValueError('Unknown input identity mode')
    if sha(identity) != item['sha256']:
        raise ValueError('Input SHA256 mismatch: ' + item['path'])
    return path, data


def fetch_fonts(profile, root):
    """Optional bounded release-file acquisition; no font installation."""
    def get(url):
        if not isinstance(url, str) or not url.startswith('https://'):
            raise ValueError('HTTPS font source required')
        request = urllib.request.Request(url, headers={'User-Agent': 'localization-font-preview'})
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read(MAX_FONT_BYTES + 1)
        if len(data) > MAX_FONT_BYTES:
            raise ValueError('Font download exceeds size limit')
        return data

    items = list(profile['fonts'])
    if profile.get('label_font', {}).get('download_url'):
        items.append(profile['label_font'])
    for item in items:
        target = local(root, item['path'])
        license_path = local(root, item['license_path'])
        if not target.is_relative_to(Path(root).resolve() / 'build') or not license_path.is_relative_to(Path(root).resolve() / 'build'):
            raise ValueError('Downloaded fonts/licenses must stay under build')
        if target.exists():
            locked(root, item)
        else:
            data = get(item['download_url'])
            if item.get('archive_sha256'):
                if sha(data) != item['archive_sha256']:
                    raise ValueError('Font archive SHA256 mismatch')
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    matches = [n for n in archive.infolist() if Path(n.filename).name == target.name]
                    if len(matches) != 1 or matches[0].file_size > MAX_FONT_BYTES:
                        raise ValueError('Ambiguous or oversized font member')
                    data = archive.read(matches[0])
            if sha(data) != item['sha256']:
                raise ValueError('Downloaded font SHA256 mismatch')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
        if license_path.exists():
            if sha(license_path.read_bytes()) != item['license_sha256']:
                raise ValueError('Existing license SHA256 mismatch')
        else:
            data = get(item['license_url'])
            if sha(data) != item['license_sha256']:
                raise ValueError('Downloaded license SHA256 mismatch')
            license_path.parent.mkdir(parents=True, exist_ok=True)
            with license_path.open('xb') as stream:
                stream.write(data)


def source_text(root, reference):
    _, raw = locked(root, reference)
    data = json.loads(raw)
    matches = [entry for entry in data['entries'] if entry['id'] == reference['entry_id']]
    if len(matches) != 1:
        raise ValueError('Text source ID missing or ambiguous')
    text = matches[0]['translation'].replace('\\n', '\n')
    if not text.strip() or len(text) > 1000 or any(ord(c) < 32 and c != '\n' for c in text):
        raise ValueError('Unsupported text specimen')
    return text


def role_specs(root, profiles):
    specs = []
    for item in profiles:
        _, raw = locked(root, item['glyph_source'])
        source = json.loads(raw)
        if canonical(source) != item['canonical_sha256']:
            raise ValueError('Glyph source canonical identity differs')
        spec = {key: source[key] for key in ('font_size', 'metric_height', 'ink_padding', 'wide_letter_advance')}
        if not 8 <= spec['font_size'] <= 64 or not 8 <= spec['metric_height'] <= 96:
            raise ValueError('Unsupported specimen raster size')
        specs.append(dict(item, **spec))
    if len(specs) != 3 or len({s['font_size'] for s in specs}) != 3:
        raise ValueError('Three distinct locked raster roles required')
    return specs


def round4(n):
    return math.ceil(n / 4) * 4


def make_glyph_plan(font_file, spec, text):
    font = ImageFont.truetype(str(font_file), spec['font_size'])
    glyphs = []
    pad = spec['ink_padding']
    for char in sorted(set(text) - {'\n'}):
        if unicodedata.category(char) == 'Zs':
            width = max(1, math.ceil(font.getlength(char)))
            glyphs.append(dict(character=char, texture_index=0, x=0, y=0,
                               width=round4(width), height=round4(spec['metric_height']),
                               metric_width=width, layout='blank-advance'))
            continue
        if char.isspace():
            raise ValueError('Unsupported control separator in specimen')
        x0, _, x1, _ = font.getbbox(char, anchor='ls')
        width = x1 - x0 + pad['left'] + pad['right']
        if unicodedata.category(char).startswith('L') and unicodedata.east_asian_width(char) in ('W', 'F'):
            width = max(width, spec['wide_letter_advance'])
        glyphs.append(dict(character=char, texture_index=0, x=0, y=0,
                           width=round4(max(width, x1-x0+4)), height=round4(spec['metric_height']),
                           metric_width=width))
    return dict(schema_version=1, in_game_verified=False, font_size=spec['font_size'], metric_height=spec['metric_height'],
                ink_padding=pad, glyphs=glyphs)


def bc3_white(alpha, width, height):
    blocks = bytearray()
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            samples = [alpha[(y+iy)*width+x+ix] for iy in range(4) for ix in range(4)]
            blocks.extend(encode_white_bc3_block(samples))
    return decode_dxt5(bytes(blocks), width, height)


def bc3_rgba(rgba, width, height):
    blocks = bytearray()
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            block = b''.join(rgba[((y+iy)*width+x)*4:((y+iy)*width+x+4)*4] for iy in range(4))
            blocks.extend(encode_rgba_block(block))
    return decode_dxt5(bytes(blocks), width, height)


def raster_font(font_file, font_spec, role, text):
    raw = font_file.read_bytes()
    with TTFont(io.BytesIO(raw)) as font:
        names = {n.toUnicode() for n in font['name'].names if n.nameID == 6}
        if font_spec['postscript_name'] not in names:
            raise ValueError('Wrong font face: ' + font_spec['id'])
        source_weight = font['OS/2'].usWeightClass
    weight = font_spec.get('embolden')
    if weight is not None:
        if (not isinstance(weight, dict) or set(weight) != {'target_weight', 'stroke_em'}
                or type(weight['target_weight']) is not int
                or not source_weight < weight['target_weight'] <= 900
                or isinstance(weight['stroke_em'], bool)
                or not isinstance(weight['stroke_em'], (int, float))
                or not math.isfinite(weight['stroke_em']) or not 0 < weight['stroke_em'] <= 0.02):
            raise ValueError('Invalid explicit synthetic weight preview')
    plan = make_glyph_plan(font_file, role, text)
    alphas, records = rasterize_plan(font_file, font_spec['sha256'], plan)
    glyphs = {}
    shadows = 0
    clipped = 0
    alpha_before = alpha_after = boundary = 0
    outline_font = ImageFont.truetype(str(font_file), role['font_size']) if weight else None
    for cell, record in zip(plan['glyphs'], records):
        w, h = cell['width'], cell['height']
        alpha = alphas[ord(cell['character'])]
        alpha_before += sum(alpha)
        if weight:
            alpha, growth = embolden_glyph(outline_font, cell, record, alpha, role['metric_height'], weight['stroke_em'])
            boundary += growth['boundary_samples']
        alpha_after += sum(alpha)
        pixels = bc3_white(alpha, w, h)
        if role['shadow']:
            changed, added, lost = shadow_pixels(pixels, w, h, cell['metric_width'], role['metric_height'], 1, 1)
            pixels = bc3_rgba(changed, w, h)
            shadows += added
            clipped += lost
        image = Image.frombytes('RGBA', (w, h), pixels).crop((0, 0, cell['metric_width'], role['metric_height']))
        glyphs[cell['character']] = image
    if any(r['raster_bbox'][2] > c['metric_width'] or r['raster_bbox'][3] > role['metric_height']
           for r, c in zip(records, plan['glyphs']) if r['raster_bbox'] is not None):
        raise ValueError('Foreground exceeds visible metrics')
    return glyphs, dict(font=font_spec['id'], size=role['font_size'], metric_height=role['metric_height'],
                        glyphs=len(glyphs), glyph_plan=plan, raster_records=records,
                        missing_glyphs=0, foreground_clipping=False, added_shadow_pixels=shadows, clipped_shadow_samples=clipped,
                        source_weight_class=source_weight, requested_weight=weight['target_weight'] if weight else source_weight,
                        synthetic_weight=weight is not None, stroke_em=weight['stroke_em'] if weight else 0, stroke_px=role['font_size']*weight['stroke_em'] if weight else 0,
                        weight_method='freetype-fractional-outline-stroke-v1' if weight else 'original',
                        alpha_sum_before=alpha_before, alpha_sum_after=alpha_after, bounded_growth_samples=boundary,
                        rgba_sha256={char:sha(image.tobytes()) for char,image in glyphs.items()})


def line_image(glyphs, text, metric_height, max_width):
    lines = text.split('\n')
    widths = [sum(glyphs[c].width for c in line) for line in lines]
    if max(widths, default=0) > max_width:
        raise ValueError('Specimen line exceeds canvas; never silently shrink or clip')
    pitch = metric_height + 7
    image = Image.new('RGBA', (max(1, max(widths, default=0)), max(1, len(lines)*pitch)))
    for index, line in enumerate(lines):
        x = 0
        for char in line:
            image.alpha_composite(glyphs[char], (x, index*pitch))
            x += glyphs[char].width
    return image, widths


def label(draw, xy, text, font, fill='#cbd2dc'):
    draw.text(xy, text, font=font, fill=fill, anchor='lt')


def render(profile_path, root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root / 'build') or output == root/'build':
        raise ValueError('Preview output must be a new child of project build/')
    profile = json.loads(Path(profile_path).read_bytes())
    if profile.get('kind') != 'dynamic-font-comparison' or not 1 <= len(profile['fonts']) <= 8:
        raise ValueError('Invalid preview profile')
    text = source_text(root, profile['text_source'])
    roles = role_specs(root, profile['roles'])
    label_path, _ = locked(root, profile['label_font'])
    ui = {size:ImageFont.truetype(str(label_path), size) for size in (12, 14, 16, 20, 28)}
    snapshots = {str(Path(profile_path).resolve()):sha(Path(profile_path).read_bytes())}
    input_items = [profile['text_source'], profile['label_font']] + [r['glyph_source'] for r in roles] + profile['fonts']
    input_items += [dict(path=f['license_path'], sha256=f['license_sha256'])
                    for f in profile['fonts'] + [profile['label_font']] if 'license_path' in f]
    for item in input_items:
        p, raw = locked(root, item); snapshots[str(p)] = sha(raw)
    fonts = profile['fonts']
    if len({f['id'] for f in fonts}) != len(fonts):
        raise ValueError('Duplicate font ID')
    for font in fonts:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', font['id']):
            raise ValueError('Unsafe output font ID')
    prepared = []
    proofs = []
    for font in fonts:
        role_images = []
        for role in roles:
            glyphs, proof = raster_font(local(root, font['path']), font, role, text)
            # The overview has a size-label column: it is narrower than a card.
            picture, widths = line_image(glyphs, text, role['metric_height'], 1064)
            role_images.append(picture)
            proofs.append(dict(proof, line_widths=widths))
        prepared.append(role_images)
    output.mkdir(parents=True)
    paths = []
    overview = Image.new('RGBA', (1280, 130+len(fonts)*284), '#0d1118')
    od = ImageDraw.Draw(overview)
    label(od, (48, 26), profile['overview_title'], ui[28], '#f0dfbb')
    label(od, (48, 72), profile['overview_note'], ui[14])
    for index, (font, role_images) in enumerate(zip(fonts, prepared)):
        sheet = Image.new('RGBA', (1280, 1120), '#0d1118')
        draw = ImageDraw.Draw(sheet)
        label(draw, (48, 28), f"MC2 / DYNAMIC TYPE / {index+1:02}", ui[14], '#b8a17a')
        label(draw, (48, 64), font['label'], ui[28], '#f0dfbb')
        label(draw, (48, 112), f"{font['postscript_name']}  |  {font['release']}", ui[16])
        draw.line((48, 152, 1232, 152), fill='#68543b', width=1)
        for role, picture, y in zip(roles, role_images, (176, 378, 580)):
            draw.rounded_rectangle((48, y, 1232, y+180), radius=12, fill='#171e29', outline='#293447')
            label(draw, (72, y+18), f"{role['font_size']} px  /  {role['label']}", ui[16], '#ead6b0')
            label(draw, (640, y+20), role['object'] + '  |  ' + role['effect_label'], ui[12], '#9caabe')
            sheet.alpha_composite(picture, (72, y+70))
        draw.rounded_rectangle((48, 792, 1232, 1010), radius=12, fill='#e9e5dc')
        label(draw, (72, 812), profile['light_title'], ui[16], '#48433b')
        sheet.alpha_composite(role_images[-1], (72, 874))
        label(draw, (48, 1042), profile['footer'], ui[14], '#a0adbf')
        label(draw, (48, 1074), profile['source_label'], ui[12], '#7f8c9e')
        stem=f"{index+1:02}-{font['id']}"
        native=output/(stem+'-1x.png'); large=output/(stem+'-2x.png')
        sheet.convert('RGB').save(native)
        sheet.resize((2560,2240),Image.Resampling.BILINEAR).convert('RGB').save(large)
        paths.extend([native,large])
        oy=112+index*284
        od.rounded_rectangle((32, oy, 1248, oy+270),radius=10,fill='#171e29',outline='#293447')
        label(od,(52,oy+12),f"{index+1:02}  {font['label']}  /  {font['release']}",ui[20],'#f0dfbb')
        for role,picture,dy in zip(roles,role_images,(54,112,184)):
            label(od,(54,oy+dy+3),f"{role['font_size']} px",ui[14],'#bca987')
            overview.alpha_composite(picture,(160,oy+dy))
    overview_path=output/'00-comparison-1x.png'
    overview.convert('RGB').save(overview_path); paths.insert(0,overview_path)
    cards=''.join(f'<section><h2>{i+1:02} · {html.escape(f["label"])}</h2><p>{html.escape(f["postscript_name"])} · {html.escape(f["release"])}</p><a href="{i+1:02}-{f["id"]}-2x.png">2× PNG</a> · <a href="{i+1:02}-{f["id"]}-1x.png">1× PNG</a><img src="{i+1:02}-{f["id"]}-1x.png" alt="{html.escape(f["label"])}"></section>' for i,f in enumerate(fonts))
    sources=''.join(f'<li><a href="{html.escape(f["download_url"])}">{html.escape(f["postscript_name"])} / {html.escape(f["release"])}</a> · SHA256 {f["sha256"]}</li>' for f in fonts)
    page=f'''<!doctype html><html lang="{html.escape(profile['locale'])}"><meta charset="utf-8"><title>{html.escape(profile['overview_title'])}</title><style>body{{margin:32px auto;max-width:1320px;background:#0d1118;color:#d7dfeb;font:16px system-ui}}h1,h2{{color:#f0dfbb}}a{{color:#d6bd8e}}section{{margin:32px 0 64px}}img{{display:block;max-width:100%;height:auto;margin-top:18px}}pre{{white-space:pre-wrap}}li{{overflow-wrap:anywhere;margin:12px 0}}</style><h1>{html.escape(profile['overview_title'])}</h1><p>{html.escape(profile['overview_note'])}</p><p>{html.escape(profile['footer'])}</p><p><a href="00-comparison-1x.png">{html.escape(profile['comparison_link'])}</a> · <a href="../VERIFICATION.txt">Verification</a></p><pre>{html.escape(text)}</pre><img src="00-comparison-1x.png" alt="Comparison">{cards}<h2>Font sources</h2><ul>{sources}</ul></html>'''
    (output/'index.html').write_text(page,encoding='utf-8')
    results=[]
    for p in paths:
        with Image.open(p) as image:
            image.load(); results.append(dict(path=p.name,size=list(image.size),sha256=sha(p.read_bytes())))
    for name, expected in snapshots.items():
        if sha(Path(name).read_bytes()) != expected:
            raise ValueError('Source changed during rendering')
    report=dict(schema_version=1,status='PASS',font_count=len(fonts),sizes=[r['font_size'] for r in roles],text=text,
                text_source=profile['text_source'],source_inputs=snapshots,fonts=fonts,glyph_proofs=proofs,outputs=results,
                specimen_canvas='1280px-wide, 1 native raster pixel per image pixel; 2x is bilinear enlargement, not rerasterization',
                toolchain=dict(pillow=pillow_version,fonttools=fonttools_version,
                               generator_sha256=sha(Path(__file__).read_bytes())),
                previews_only=True,inputs_unchanged=True,game_started=False,game_resources_written=False,game_rendering_verified=False)
    (output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',fonts=len(fonts),sizes=report['sizes'],images=len(results),game_resources_written=False,output=str(output)),ensure_ascii=False))
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fetch-fonts',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.fetch_fonts:fetch_fonts(json.loads(args.profile.read_bytes()),args.root)
        render(args.profile,args.root,args.output)
    except (ValueError,KeyError,OSError,AssertionError) as exc:
        parser.exit(1,'ERROR: '+str(exc)+'\n')


if __name__=='__main__':main()
