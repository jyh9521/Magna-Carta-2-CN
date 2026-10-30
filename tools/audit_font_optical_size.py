"""Measure and preview actual native glyph cells, not a substitute TTF render."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw

from .build_font_supplement import context
from .font_binding_plan import confined_path
from .reface_font import sha
from .supplement_font import parse_atlas_payload, atlas_tiles
from .ue3_fonts import parse_font_payload
from .ue3_textures import decode_dxt5, xbox_tiled_block_offset


class Sampler:
    def __init__(self, data, obj):
        self.ctx = context(data, None)
        exports = [e for e in self.ctx['tables']['exports']
                   if e['path'] == obj and e['class_path'] in ('Font', 'Engine.Font')]
        if len(exports) != 1:
            raise ValueError('unique Font object required')
        e = exports[0]
        self.font = parse_font_payload(data[e['serial_offset']:e['serial_offset']+e['serial_size']],
                                       self.ctx['tables']['names'])
        self.mapping = ({r['codepoint']:r['glyph_index'] for r in self.font['remap']}
                        if self.font['is_remapped'] else
                        {i: i for i in range(len(self.font['characters']))})
        self.atlases = {}

    def glyph(self, cp):
        if cp not in self.mapping:
            raise ValueError('missing mapped glyph: U+%04X' % cp)
        g = self.font['characters'][self.mapping[cp]]
        ti = g['TextureIndex']
        if ti not in self.atlases:
            e = self.ctx['tables']['exports'][self.font['textures'][ti]-1]
            p = self.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
            t = parse_atlas_payload(p, self.ctx['tables']['names'], e['serial_offset'])
            self.atlases[ti] = t, atlas_tiles(p, t, None)
        t, tiles = self.atlases[ti]
        x, y, w, h = [g[k] for k in ('StartU', 'StartV', 'USize', 'VSize')]
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > t['width'] or y+h > t['height']:
            raise ValueError('invalid glyph geometry')
        x0, y0 = x//4, y//4
        x1, y1 = (x+w+3)//4, (y+h+3)//4
        linear = bytearray()
        for by in range(y0, y1):
            for bx in range(x0, x1):
                at = xbox_tiled_block_offset(bx, by, ((t['width']+127)&~127)//4)*16
                b = tiles[at:at+16]
                if len(b) != 16:
                    raise ValueError('glyph block outside atlas')
                linear.extend(b''.join(b[i:i+2][::-1] for i in range(0, 16, 2)))
        bw, bh = (x1-x0)*4, (y1-y0)*4
        im = Image.frombytes('RGBA', (bw, bh), decode_dxt5(bytes(linear), bw, bh))
        return im.crop((x%4, y%4, x%4+w, y%4+h))


def ink_box(im, threshold=80):
    # Exclude black subtitle shadows; measure visible white foreground only.
    mask = Image.new('L', im.size)
    rgba = im.tobytes()
    mask.putdata([255 if rgba[i+3] >= threshold and max(rgba[i:i+3]) >= 128 else 0
                  for i in range(0, len(rgba), 4)])
    return mask.getbbox()


def measure(sampler, characters, reference, min_ratio, max_ratio, max_bottom_delta=None):
    refs = [ink_box(sampler.glyph(ord(c))) for c in reference]
    if not refs or any(b is None for b in refs):
        raise ValueError('empty reference glyph')
    ref_height = median(b[3]-b[1] for b in refs)
    ref_bottom = median(b[3] for b in refs)
    rows = []
    for char in characters:
        im = sampler.glyph(ord(char))
        box = ink_box(im)
        height = box[3]-box[1] if box else 0
        ratio = height/ref_height
        bottom_delta = box[3]-ref_bottom if box else None
        rows.append(dict(codepoint=ord(char), bbox=box, height=height,
                         advance=im.width, reference_height=ref_height,
                         ratio=round(ratio, 6), bottom_delta=bottom_delta,
                         passed=min_ratio <= ratio <= max_ratio and
                         (max_bottom_delta is None or (bottom_delta is not None and
                          abs(bottom_delta) <= max_bottom_delta))))
    return rows


def run(root, profile, output, before_root=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError('new external report path required')
    if profile.get('kind') != 'native-font-optical-audit' or profile.get('schema_version') != 1:
        raise ValueError('optical audit schema')
    rows, strips = [], []
    for spec in profile['fonts']:
        data = confined_path(root, spec['resource']).read_bytes()
        sampler = Sampler(data, spec['object'])
        measures = measure(sampler, profile['characters'], profile['reference'],
                           profile['min_ratio'], profile['max_ratio'], profile.get('max_bottom_delta'))
        row = dict(resource=spec['resource'], object=spec['object'], role=spec['role'],
                   sha256=sha(data), glyphs=measures)
        if before_root is not None:
            old = Sampler(confined_path(Path(before_root).resolve(), spec['resource']).read_bytes(), spec['object'])
            selected = set(map(ord, profile['characters']))
            unchanged = sampled = 0
            selected_atlases = {old.font['characters'][old.mapping[cp]]['TextureIndex'] for cp in selected}
            preserved_atlases = set()
            if old.mapping != sampler.mapping:
                raise ValueError('font mapping changed')
            for cp in old.mapping:
                if cp in selected:
                    continue
                i = old.mapping[cp]
                if old.font['characters'][i] != sampler.font['characters'][i]:
                    raise ValueError('unselected glyph metrics changed')
                g = old.font['characters'][i]
                ti = g['TextureIndex']
                if ti not in selected_atlases and ti not in preserved_atlases:
                    # Nonselected original atlases may be LZX-compressed. Prove
                    # their complete payload identity instead of decoding them.
                    payloads = []
                    for sample in (old, sampler):
                        e = sample.ctx['tables']['exports'][sample.font['textures'][ti]-1]
                        payloads.append(sample.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']])
                    if payloads[0] != payloads[1]:
                        raise ValueError('unselected atlas payload changed')
                    preserved_atlases.add(ti)
                if ti in selected_atlases and g['USize'] and g['VSize']:
                    if old.glyph(cp).tobytes() != sampler.glyph(cp).tobytes():
                        raise ValueError('unselected native glyph pixels changed')
                    sampled += 1
                unchanged += 1
            row['unselected_glyphs_byte_identical'] = unchanged
            row['unselected_glyphs_sampled'] = sampled
            row['other_atlases_byte_identical'] = len(preserved_atlases)
        rows.append(row)
        if spec['preview']:
            ims = [sampler.glyph(ord(c)) for c in profile['sample']]
            strip = Image.new('RGBA', (sum(im.width for im in ims), max(im.height for im in ims)))
            x = 0
            for im in ims:
                strip.alpha_composite(im, (x, 0)); x += im.width
            strips.append((spec['role'], strip))
    report = dict(fonts=rows, glyphs=sum(len(r['glyphs']) for r in rows),
                  failures=sum(not g['passed'] for r in rows for g in r['glyphs']),
                  sample=profile['sample'], game_started=False, game_rendering_verified=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    png = output.with_suffix('.png')
    if png.exists():
        raise ValueError('preview output already exists')
    canvas = Image.new('RGB', (max(im.width for _, im in strips)*3+32,
                               sum(im.height*3+40 for _, im in strips)+16), (35, 39, 43))
    y = 8
    for role, strip in strips:
        ImageDraw.Draw(canvas).text((16, y), role+' / native cells, 3x nearest', fill='white')
        scaled = strip.resize((strip.width*3, strip.height*3), Image.Resampling.NEAREST)
        canvas.paste(scaled, (16, y+20), scaled)
        y += strip.height*3+40
    canvas.save(png)
    report['preview_sha256'] = sha(png.read_bytes())
    raw = (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode()
    output.write_bytes(raw)
    if output.read_bytes() != raw:
        raise ValueError('report reopening mismatch')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'profile', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--before-root', type=Path)
    a = p.parse_args()
    report = run(a.root, json.loads(a.profile.read_bytes()), a.output, a.before_root)
    print(json.dumps(dict(fonts=len(report['fonts']), glyphs=report['glyphs'],
                          failures=report['failures'], game_started=False)))
    return int(report['failures'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())
