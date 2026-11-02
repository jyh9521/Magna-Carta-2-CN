"""Translate existing native lettering in bounded transparent atlas regions.

Integer-pixel copies preserve the existing shape, size and prior colour fixes.
Aligned moves copy BC3 blocks exactly; sub-block moves use the established
bounded encoder. No font is rerendered, no English or terrain is inferred.
"""
import argparse
import json
from pathlib import Path

from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .replace_texture_regions import selected, replace_tiles
from .runtime_envelope import ALIGNMENT, require_raw_envelope
from .texture_layout import decode_texture, overlay_rect, rect_units
from .texture_overlay import rgba_crop
from .ui_ink_revision import clean_alpha


def shift_pixels(rgba, width, height, offset):
    if (type(width) is not int or type(height) is not int or min(width, height) <= 0
            or not isinstance(rgba, bytes) or len(rgba) != width*height*4
            or not isinstance(offset, list) or len(offset) != 2
            or any(type(n) is not int for n in offset) or offset == [0, 0]
            or abs(offset[0]) >= width or abs(offset[1]) >= height):
        raise ValueError('bounded nonzero integer translation and RGBA pixels required')
    dx, dy = offset
    out = bytearray(len(rgba))
    for y in range(height):
        for x in range(width):
            at = (y*width+x)*4
            tx, ty = x+dx, y+dy
            if not (0 <= tx < width and 0 <= ty < height):
                if rgba[at+3]:
                    raise ValueError('translation would clip visible pixels')
                continue
            target = (ty*width+tx)*4
            out[target:target+4] = rgba[at:at+4]
    return bytes(out)


def translate_tiles(texture, rect, offset, max_alpha_delta, max_premultiplied_delta):
    if (texture['format'] != 7 or type(max_alpha_delta) is not int
            or not 0 <= max_alpha_delta <= 32 or type(max_premultiplied_delta) is not int
            or not 0 <= max_premultiplied_delta <= 64):
        raise ValueError('explicit BC3 translation error bounds required')
    offsets = rect_units(texture['layout'], rect)
    pixels = decode_texture(texture)
    before = rgba_crop(pixels, texture['width'], rect)
    wanted = shift_pixels(before, *rect[2:], offset)
    x, y, w, h = rect
    aligned = all(n % 4 == 0 for n in offset)
    if aligned:
        # Source tiles are immutable: overlapping shifts must never read back a
        # block already overwritten by an earlier destination.
        old = texture['tiles']; result = bytearray(old)
        stride = texture['width']//4; dx, dy = offset
        for by in range(h//4):
            for bx in range(w//4):
                to = texture['layout']['offsets'][(y//4+by)*stride+x//4+bx]
                sx, sy = bx-dx//4, by-dy//4
                if 0 <= sx < w//4 and 0 <= sy < h//4:
                    src = texture['layout']['offsets'][(y//4+sy)*stride+x//4+sx]
                    result[to:to+16] = old[src:src+16]
                else:
                    result[to:to+16] = bytes(16)
        result = bytes(result)
    else:
        result, _ = overlay_rect(texture['tiles'], texture['layout'], rect, wanted,
                                 alpha_encoding='adaptive-range', rgb_encoding='weighted-fit-v1')
    actual = rgba_crop(decode_texture(texture, result), texture['width'], rect)
    alpha_error = max(abs(a-b) for a, b in zip(wanted[3::4], actual[3::4], strict=True))
    rgb_error = max(abs(wanted[i+c]*wanted[i+3]/255 - actual[i+c]*actual[i+3]/255)
                    for i in range(0, len(wanted), 4) for c in range(3))
    if alpha_error > max_alpha_delta or rgb_error > max_premultiplied_delta:
        raise ValueError(f'translation quantization exceeds contract: alpha={alpha_error} rgb={rgb_error}')
    if any(actual[i+3] for i in range(0, len(wanted), 4) if not wanted[i+3]):
        raise ValueError('translation introduced alpha outside the moved silhouette')
    changed = {i for i in range(0, len(result), 16) if result[i:i+16] != texture['tiles'][i:i+16]}
    if not changed or not changed <= set(offsets):
        raise ValueError('empty translation or change outside selected blocks')
    return result, dict(rect=rect, offset=offset, native_block_copy=aligned,
                        source_rgba_sha256=digest(before), translated_rgba_sha256=digest(wanted),
                        decoded_rgba_sha256=digest(actual), alpha_max_delta=alpha_error,
                        premultiplied_max_delta=rgb_error, shape_resized=False,
                        clipped_pixels=0, changed_blocks=len(changed))


def validate(profile):
    if (set(profile) != {'schema_version', 'kind', 'resources'}
            or type(profile['schema_version']) is not int or profile['schema_version'] != 1
            or profile['kind'] != 'native-texture-translation-v1'
            or not isinstance(profile['resources'], list) or not 1 <= len(profile['resources']) <= 128):
        raise ValueError('unsupported bounded translation profile')
    seen = set()
    for row in profile['resources']:
        if (set(row) != {'path', 'sha256', 'discs', 'textures'}
                or not row['path'].lower().endswith('.xxx') or row['path'].casefold() in seen
                or row['discs'] not in ([1], [2], [1, 2])
                or not isinstance(row['textures'], list) or not 1 <= len(row['textures']) <= 128):
            raise ValueError('invalid or duplicate native resource')
        seen.add(row['path'].casefold()); objects = set()
        for t in row['textures']:
            if (set(t) != {'object', 'tiled_sha256', 'operations'} or t['object'] in objects
                    or not isinstance(t['operations'], list) or not 1 <= len(t['operations']) <= 32):
                raise ValueError('invalid or duplicate texture')
            objects.add(t['object'])
            for op in t['operations']:
                fields = ({'kind', 'rect', 'offset', 'max_alpha_delta', 'max_premultiplied_delta'}
                          if op.get('kind') == 'translate' else
                          {'kind', 'rectangles', 'rgb_ceiling', 'max_retained_delta'})
                if op.get('kind') not in ('translate', 'clear-dark-alpha') or set(op) != fields:
                    raise ValueError('unknown or incomplete texture operation')


def build(profile, source, output):
    validate(profile)
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('new disjoint output required')
    for row in profile['resources']:
        if digest(confined_path(source, row['path']).read_bytes()) != row['sha256']:
            raise ValueError('source SHA256 mismatch: ' + row['path'])
    cache, blobs, resources, proofs = {}, {}, [], []
    for row in profile['resources']:
        original = confined_path(source, row['path']).read_bytes()
        if digest(original) != row['sha256']:
            raise ValueError('source changed during build')
        require_raw_envelope(original); data = original
        for spec in row['textures']:
            tx = selected(data, spec['object'], None)[3]
            if digest(tx['tiles']) != spec['tiled_sha256']:
                raise ValueError('native texture SHA256 mismatch')
            used = set()
            for op in spec['operations']:
                rects = [op['rect']] if op['kind'] == 'translate' else op['rectangles']
                for rect in rects:
                    units = set(rect_units(tx['layout'], rect))
                    if units & used:
                        raise ValueError('overlapping texture operations')
                    used.update(units)
            for op in spec['operations']:
                if op['kind'] == 'translate':
                    tx = selected(data, spec['object'], None)[3]
                    key = (tx['width'], tx['height'], digest(tx['tiles']), json.dumps(op, sort_keys=True))
                    if key not in cache:
                        cache[key] = translate_tiles(tx, op['rect'], op['offset'],
                            op['max_alpha_delta'], op['max_premultiplied_delta'])
                    tiles, details = cache[key]
                    data, proof = replace_tiles(data, digest(data), spec['object'], tiles, [op['rect']], None)
                else:
                    data, proof = clean_alpha(data, spec['object'], op['rectangles'], op['rgb_ceiling'], op['max_retained_delta'])
                    details = op
                proofs.append(dict(resource=row['path'], object=spec['object'], operation=details, proof=proof))
        data += bytes((-len(data)) % ALIGNMENT); require_raw_envelope(data)
        if data == original:
            raise ValueError('empty resource revision')
        blobs['candidate/'+row['path']] = data
        resources.append(dict(path=row['path'], file='candidate/'+row['path'], before_sha256=row['sha256'],
                              sha256=digest(data), size=len(data), discs=row['discs']))
    for row in profile['resources']:
        if digest(confined_path(source, row['path']).read_bytes()) != row['sha256']:
            raise ValueError('source changed before publication')
    manifest = dict(schema_version=1, resources=resources, operations=proofs,
                    game_started=False, game_rendering_verified=False)
    files = {'manifest.json': manifest}
    for disc in (1, 2):
        files[f'replacements-disc{disc}.json'] = dict(schema_version=1,
            kind='incremental-comparison-replacements', disc=disc, toc_path='MC2Game/Xbox360TOC.txt',
            resources=[{k: v for k, v in r.items() if k != 'discs'} for r in resources if disc in r['discs']])
    for name, obj in files.items():
        blobs[name] = (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    output.mkdir(parents=True)
    for name, data in blobs.items():
        p = confined_path(output, name); p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(data)
        if p.read_bytes() != data:
            raise ValueError('published file readback mismatch')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'source-root', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--profile-sha256', required=True)
    a = p.parse_args(); raw = a.profile.read_bytes()
    if digest(raw) != a.profile_sha256:
        raise ValueError('profile SHA256 mismatch')
    result = build(json.loads(raw), a.source_root, a.output)
    if a.profile.read_bytes() != raw:
        raise ValueError('profile changed during build')
    print(f'RESOURCES={len(result["resources"])} OPERATIONS={len(result["operations"])} RESULT=PASS')


if __name__ == '__main__':
    main()
