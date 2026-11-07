"""Reproduce source-locked sparse reconstruction patches from owned ink masks."""
import argparse
import io
import json
from pathlib import Path

from .build_font_supplement import context
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .sparse_rgba_repair import interpolate_rgba, exemplar_rgba
from .sparse_artifact_paths import validate_patch_paths
from .texture_layout import read_texture, decode_texture
from .texture_overlay import select_texture_export, rgba_crop
from .ue3_package import LzxDecoder


def build(recipe, root, output, decoder):
    from PIL import Image
    root, output = Path(root).resolve(), Path(output).resolve()
    if (recipe.get('schema_version') != 1
            or recipe.get('kind') != 'sparse-texture-repair-v1'
            or recipe.get('method') not in ('premultiplied-front-laplace-v1', 'premultiplied-exemplar-v1')
            or recipe.get('hidden_artwork') != 'reconstruction-not-original'
            or not isinstance(recipe.get('cases'), list)
            or not 1 <= len(recipe['cases']) <= 128):
        raise ValueError('unsupported sparse texture repair recipe')
    if output.exists() or not output.is_relative_to(root) or output == root:
        raise ValueError('new project-contained repair output required')
    validate_patch_paths(recipe['cases'],output)
    contexts, snapshots, files, records = {}, {}, {}, []

    def locked(ref):
        path = confined_path(root, ref['path'])
        raw = path.read_bytes()
        if digest(raw) != ref['sha256']:
            raise ValueError('sparse repair dependency SHA256 mismatch')
        snapshots[path] = ref['sha256']
        return raw

    for case in recipe['cases']:
        ref = case['source']
        if ref['path'] not in contexts:
            contexts[ref['path']] = context(locked(ref), decoder)
        c = contexts[ref['path']]
        if c['sha256'] != ref['sha256']:
            raise ValueError('inconsistent sparse repair source identity')
        e = select_texture_export(c['tables'], case['object'])
        payload = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        texture = read_texture(payload, c['tables']['names'], e['serial_offset'],
                               case['profile'], decoder)
        rect=case['rect']
        if (not isinstance(rect,list) or len(rect)!=4
                or any(type(v) is not int for v in rect)
                or min(rect[:2])<0 or min(rect[2:])<=0
                or rect[0]+rect[2]>texture['width'] or rect[1]+rect[3]>texture['height']):
            raise ValueError('sparse repair source rectangle outside native texture')
        native=decode_texture(texture)
        pixels = rgba_crop(native, texture['width'], rect)
        if digest(pixels) != case['source_rgba_sha256']:
            raise ValueError('sparse repair native source crop changed')
        width, height = case['rect'][2:]
        raw_mask = locked(case['mask'])
        with Image.open(io.BytesIO(raw_mask)) as im:
            if im.format != 'PNG' or im.mode != 'L' or im.size != (width, height):
                raise ValueError('sparse repair mask PNG mismatch')
            mask = im.tobytes()
        if recipe['method']=='premultiplied-front-laplace-v1':
            repaired = interpolate_rgba(pixels, width, height, mask, case['iterations'])
        else:
            margin=case['context_margin']
            if type(margin) is not int or not 0<=margin<=96:
                raise ValueError('bounded sparse repair context margin required')
            x,y,w,h=rect;cx=max(0,x-margin);cy=max(0,y-margin)
            cr=min(texture['width'],x+w+margin);cb=min(texture['height'],y+h+margin)
            context_pixels=rgba_crop(native,texture['width'],[cx,cy,cr-cx,cb-cy])
            context_mask=Image.new('L',(cr-cx,cb-cy))
            context_mask.paste(Image.frombytes('L',(width,height),mask),(x-cx,y-cy))
            rebuilt=exemplar_rgba(context_pixels,cr-cx,cb-cy,context_mask.tobytes(),
                                  case['patch_radius'],case['search_radius'])
            repaired=Image.frombytes('RGBA',(cr-cx,cb-cy),rebuilt).crop((x-cx,y-cy,x+w-cx,y+h-cy)).tobytes()
        sparse = b''.join(repaired[i*4:i*4+4] if value else bytes(4)
                          for i, value in enumerate(mask))
        buffer = io.BytesIO()
        Image.frombytes('RGBA', (width, height), sparse).save(buffer, format='PNG')
        patch = buffer.getvalue()
        name = case['patch']['path']
        if name in files or digest(patch) != case['patch']['sha256']:
            raise ValueError('sparse repair patch replay mismatch or duplicate')
        files[name] = patch
        records.append(dict(id=case['id'], selected_pixels=mask.count(255),
                            total_pixels=width*height, unmasked_pixels_preserved=True,
                            patch_sha256=digest(patch)))
    if any(digest(p.read_bytes()) != sha for p, sha in snapshots.items()):
        raise ValueError('sparse repair dependency changed during build')
    output.mkdir()
    for name, raw in files.items():
        path = confined_path(output, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
        if path.read_bytes() != raw:
            raise ValueError('sparse repair patch readback mismatch')
    result = dict(schema_version=1, cases=records, game_rendering_verified=False,
                  hidden_artwork='reconstruction-not-original')
    metadata=(json.dumps(result,indent=2)+'\n').encode('utf8')
    with (output/'manifest.json').open('xb') as stream:stream.write(metadata)
    if (output/'manifest.json').read_bytes()!=metadata:
        raise ValueError('sparse repair manifest readback mismatch')
    if any(confined_path(output,name).read_bytes()!=raw for name,raw in files.items()):
        raise ValueError('sparse repair patch changed after metadata publication')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('recipe', 'project-root', 'output-dir', 'lzx-library'):
        p.add_argument('--'+key, required=True, type=Path)
    p.add_argument('--recipe-sha256', required=True)
    a = p.parse_args()
    raw = a.recipe.read_bytes()
    if digest(raw) != a.recipe_sha256:
        raise ValueError('sparse recipe SHA256 mismatch')
    result = build(json.loads(raw), a.project_root, a.output_dir, LzxDecoder(a.lzx_library))
    if a.recipe.read_bytes() != raw:
        raise ValueError('sparse recipe changed during build')
    print(f"REPAIRS={len(result['cases'])} UNMASKED_PRESERVED=ALL RESULT=PASS")


if __name__ == '__main__':
    main()
