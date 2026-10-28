"""Add a bounded black shadow to selected white glyph cells in a raw UE3 copy.

The current font metrics/remap and every nonselected atlas block remain exact.
This post-build stage never regenerates a font or touches an executable. Native
sampling/actual on-screen appearance must be accepted separately from BC3 proof.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from .build_font_supplement import context
from .supplement_font import parse_atlas_payload, atlas_tiles, validate_plan
from .texture_overlay import encode_rgba_block, rgba_crop, region_offsets
from .ue3_fonts import parse_font_payload
from .ue3_package import parse_summary
from .ue3_textures import untile_dxt5, decode_dxt5, scatter_linear_dxt5_cell


def digest(data):
    return hashlib.sha256(data).hexdigest()


def shadow_pixels(rgba, width, height, metric_width, metric_height, dx=1, dy=1):
    if (any(type(v) is not int for v in (width, height, metric_width, metric_height, dx, dy))
            or not 0 <= dx <= 3 or not 0 <= dy <= 3 or not dx + dy
            or not 1 <= metric_width <= width <= 128
            or not 1 <= metric_height <= height <= 128
            or not isinstance(rgba, bytes) or len(rgba) != width * height * 4):
        raise ValueError('invalid bounded shadow cell/delta')
    out = bytearray(rgba)
    added = clipped = 0
    for y in range(metric_height):
        for x in range(metric_width):
            p = (y * width + x) * 4
            alpha = rgba[p + 3]
            if not alpha:
                continue
            if rgba[p:p + 3] != b'\xff\xff\xff':
                raise ValueError('selected glyph must contain white foreground only')
            if x + dx >= metric_width or y + dy >= metric_height:
                clipped += 1
                continue
            q = ((y + dy) * width + x + dx) * 4
            # Preserve every already-visible foreground pixel, including AA.
            if not rgba[q + 3]:
                out[q:q + 4] = bytes((0, 0, 0, alpha))
                added += 1
    return bytes(out), added, clipped


def apply_shadow(data, expected_sha256, font_object, glyph_plan, dx=1, dy=1):
    if not isinstance(data, bytes) or not 0 < len(data) <= 512 * 1024 * 1024 or digest(data) != expected_sha256:
        raise ValueError('package SHA256 mismatch')
    glyphs = validate_plan(glyph_plan)
    if parse_summary(data, len(data))['compression_flags']:
        raise ValueError('shadow requires an already-normalized raw package')
    ctx = context(data, None)
    if ctx['logical'] != data:
        raise ValueError('shadow requires an already-normalized raw package')
    matches = [e for e in ctx['tables']['exports'] if e['path'] == font_object]
    if len(matches) != 1 or matches[0]['class_path'] not in ('Engine.Font', 'Font'):
        raise ValueError('selected Font export is missing or ambiguous')
    e = matches[0]
    payload = data[e['serial_offset']:e['serial_offset'] + e['serial_size']]
    font = parse_font_payload(payload, ctx['tables']['names'])
    mapping = {r['codepoint']:r['glyph_index'] for r in font['remap']}
    atlas_index = glyphs[0]['texture_index']
    if not 0 <= atlas_index < len(font['textures']):
        raise ValueError('selected atlas index is outside Font textures')
    ref = font['textures'][atlas_index]
    if not 1 <= ref <= len(ctx['tables']['exports']):
        raise ValueError('selected atlas must be local')
    atlas_e = ctx['tables']['exports'][ref - 1]
    start, size = atlas_e['serial_offset'], atlas_e['serial_size']
    atlas = data[start:start + size]
    texture = parse_atlas_payload(atlas, ctx['tables']['names'], start)
    bulk = texture['mips'][0]['bulk']
    if bulk['flags'] != 0:
        raise ValueError('shadow requires an already-normalized raw atlas')
    tiles = atlas_tiles(atlas, texture, None)
    width, height = texture['width'], texture['height']
    original_linear = untile_dxt5(tiles, width, height)
    decoded = decode_dxt5(original_linear, width, height)
    allowed = set()
    patches, counts, changed_tiles = [], [], {}
    for g in glyphs:
        cp = ord(g['character'])
        if cp not in mapping:
            raise ValueError('selected codepoint is not mapped')
        metric = font['characters'][mapping[cp]]
        if ([metric[k] for k in ('StartU', 'StartV', 'TextureIndex')]
                != [g['x'], g['y'], atlas_index]
                or metric['USize'] != g.get('metric_width', g['width'])
                or metric['VSize'] != glyph_plan.get('metric_height', g['height'])):
            raise ValueError('selected glyph placement differs from build plan')
        rect = [g['x'], g['y'], g['width'], g['height']]
        blocks = region_offsets(width, height, rect)
        if allowed & blocks:
            raise ValueError('selected glyph cells overlap')
        allowed.update(blocks)
        # A selected cell must not cover any other glyph's visible rectangle.
        for other_index, other in enumerate(font['characters']):
            if other_index == mapping[cp] or other['TextureIndex'] != atlas_index:
                continue
            if (other['USize'] and other['VSize'] and
                    max(g['x'], other['StartU']) < min(g['x'] + g['width'], other['StartU'] + other['USize']) and
                    max(g['y'], other['StartV']) < min(g['y'] + g['height'], other['StartV'] + other['VSize'])):
                raise ValueError('selected shadow cell covers another glyph')
        before = rgba_crop(decoded, width, rect)
        after, count, clipped = shadow_pixels(before, g['width'], g['height'],
                                              metric['USize'], metric['VSize'], dx, dy)
        linear = bytearray()
        for by in range(0, g['height'], 4):
            for bx in range(0, g['width'], 4):
                block_rect = [bx, by, 4, 4]
                pixels = rgba_crop(after, g['width'], block_rect)
                if pixels == rgba_crop(before, g['width'], block_rect):
                    at = (((g['y'] + by) // 4) * (width // 4) + (g['x'] + bx) // 4) * 16
                    linear.extend(original_linear[at:at + 16])
                else:
                    linear.extend(encode_rgba_block(pixels))
        actual = decode_dxt5(bytes(linear), g['width'], g['height'])
        if any(actual[i:i + 4] != before[i:i + 4]
               for i in range(0, len(before), 4) if before[i + 3]):
            raise ValueError('BC3 encoding changed existing foreground pixels')
        if any(actual[i:i + 4] != after[i:i + 4]
               for i in range(0, len(after), 4) if after[i + 3]):
            raise ValueError('BC3 encoding changed shadow pixels')
        patched = scatter_linear_dxt5_cell(tiles, width, height, *rect, bytes(linear))
        for at in blocks:
            if patched[at:at + 16] != tiles[at:at + 16]:
                changed_tiles[at] = patched[at:at + 16]
        counts.append(dict(codepoint=cp, added_shadow_pixels=count, clipped_shadow_samples=clipped))
    out = bytearray(data)
    for at, value in sorted(changed_tiles.items()):
        absolute = start + bulk['payload_offset'] + at
        before = data[absolute:absolute + 16]
        out[absolute:absolute + 16] = value
        patches.append(dict(offset=absolute, before_hex=before.hex(), after_hex=value.hex()))
    output = bytes(out)
    if not changed_tiles:
        raise ValueError('selected glyphs produced no shadow pixels')
    proof = dict(schema_version=1, kind='raw-font-cell-shadow', input_sha256=digest(data),
                 output_sha256=digest(output), size=len(data), font_object=font_object,
                 atlas_object=atlas_e['path'], delta=[dx, dy], glyphs=counts,
                 glyph_plan_sha256=digest(json.dumps(glyph_plan, sort_keys=True, separators=(',', ':')).encode()),
                 patches=patches, added_shadow_pixels=sum(r['added_shadow_pixels'] for r in counts),
                 foreground_pixels_preserved=True, font_metrics_preserved=True,
                 unselected_blocks_and_exports_preserved=True, game_rendering_verified=False)
    if restore_shadow(output, proof) != data:
        raise ValueError('shadow inverse verification failed')
    return output, proof


def restore_shadow(data, proof):
    if (proof.get('schema_version') != 1 or proof.get('kind') != 'raw-font-cell-shadow'
            or len(data) != proof.get('size') or digest(data) != proof.get('output_sha256')):
        raise ValueError('shadow rollback SHA256/identity mismatch')
    out = bytearray(data)
    end = 0
    for patch in proof['patches']:
        at = patch['offset']
        before, after = bytes.fromhex(patch['before_hex']), bytes.fromhex(patch['after_hex'])
        if type(at) is not int or at < end or at + 16 > len(data) or len(before) != 16 or len(after) != 16 or data[at:at + 16] != after:
            raise ValueError('shadow rollback field mismatch')
        out[at:at + 16] = before
        end = at + 16
    result = bytes(out)
    if digest(result) != proof['input_sha256']:
        raise ValueError('shadow rollback restored SHA256 mismatch')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--sha256', required=True)
    p.add_argument('--font-object', required=True)
    p.add_argument('--glyph-plan', type=Path, required=True)
    p.add_argument('--glyph-plan-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.output.exists() or a.report.exists() or len({x.resolve() for x in (a.source, a.glyph_plan, a.output, a.report)}) != 4:
            raise ValueError('outputs must be new and distinct from inputs')
        data, spec = a.source.read_bytes(), a.glyph_plan.read_bytes()
        if digest(spec) != a.glyph_plan_sha256:
            raise ValueError('glyph plan SHA256 mismatch')
        output, report = apply_shadow(data, a.sha256, a.font_object, json.loads(spec))
        if a.source.read_bytes() != data or a.glyph_plan.read_bytes() != spec:
            raise ValueError('input changed during shadow build')
        encoded = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode()
        for path, raw in [(a.output, output), (a.report, encoded)]:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(raw)
            if path.read_bytes() != raw:
                raise ValueError('shadow output reopening mismatch')
        if a.source.read_bytes() != data or a.glyph_plan.read_bytes() != spec:
            raise ValueError('input changed after shadow build')
        print(json.dumps(dict(glyphs=len(report['glyphs']), changed_blocks=len(report['patches']),
                              shadow_pixels=report['added_shadow_pixels'], output_sha256=digest(output),
                              inverse_byte_identical=True, game_started=False), sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print('ERROR: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
