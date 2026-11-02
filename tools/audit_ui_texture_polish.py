"""Compare visible button frames, clean native labels and bounded text sizing.

Names, sizes and assets belong to the locale contract. The neutral foreground
predicate is shared with the existing ink audit. Actual BC3 bytes are decoded;
this does not claim final game rendering.
"""
import argparse
import json
from pathlib import Path
import struct

from PIL import Image

from .audit_ui_ink_revision import core_box
from .build_font_supplement import context
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest, select_field
from .replace_texture_regions import selected
from .texture_layout import decode_texture, overlay_rect, rect_units
from .texture_overlay import render_label


def scaled_center(box, texture_size, widget_size):
    if (len(box) != 4 or len(texture_size) != 2 or len(widget_size) != 2
            or any(n <= 0 for n in texture_size + widget_size)
            or any(not 0 <= box[i] < box[i+2] <= texture_size[i] for i in (0, 1))):
        raise ValueError('visible frame must be inside the texture')
    return [(box[i]+box[i+2])/2 * widget_size[i]/texture_size[i] for i in (0, 1)]


def clean_block_differences(texture, label, font):
    """Reference is a single fresh layer on transparent pixels, not old art."""
    expected, _ = overlay_rect(texture['tiles'], texture['layout'], label['rect'],
                              render_label(font, label), alpha_encoding='adaptive-range')
    rect_units(texture['layout'], label['rect'])
    actual_pixels = decode_texture(texture)
    expected_pixels = decode_texture(dict(texture, tiles=expected))
    x, y, w, h = label['rect']
    blocks = set()
    for yy in range(y, y+h):
        for xx in range(x, x+w):
            at = (yy*texture['width']+xx)*4
            a, b = actual_pixels[at:at+4], expected_pixels[at:at+4]
            # Native encodings and RGB beneath zero alpha need not be unique.
            if (a[3] or b[3]) and a != b:
                blocks.add((xx//4, yy//4))
    return len(blocks)


def audit(root, plan, project):
    if plan.get('schema_version') != 1 or plan.get('kind') != 'native-ui-texture-polish':
        raise ValueError('unsupported UI texture polish contract')
    root, project = Path(root).resolve(), Path(project).resolve()
    blobs, contexts, textures = {}, {}, {}

    def read(relative):
        if relative not in blobs:
            blobs[relative] = confined_path(root, relative).read_bytes()
        return blobs[relative]

    def texture(resource, obj):
        key = resource, obj
        if key not in textures:
            _, _, _, t = selected(read(resource), obj, None)
            textures[key] = (t, Image.frombytes('RGBA', (t['width'], t['height']), decode_texture(t)))
        return textures[key]

    def scalar(resource, obj, path, prefix=4):
        if resource not in contexts:
            contexts[resource] = context(read(resource), None)
        c = contexts[resource]
        es = [e for e in c['tables']['exports'] if e['path'] == obj]
        if len(es) != 1:
            raise ValueError('missing or ambiguous serialized widget')
        e = es[0]
        payload = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        kind, _, raw = select_field(payload, c['tables']['names'], prefix,
            [dict(name=n, array_index=i) for n, i in path])
        if kind != 'FloatProperty':
            raise ValueError('widget position/UV must be float')
        return struct.unpack('>f', raw)[0]

    def position(resource, obj):
        return [scalar(resource, obj, [('Position', 0), ('Value', i)]) for i in range(4)]

    checks = []
    for spec in plan['buttons']:
        parent = position(plan['ui_resource'], spec['parent'])
        label = position(plan['ui_resource'], spec['label'])
        bg = spec['background']
        _, image = texture(bg['resource'], bg['object'])
        frame = core_box(image)
        target = scaled_center(frame, list(image.size), parent[2:])
        for state in spec['states']:
            _, image = texture(state['resource'], state['object'])
            x, y, w, h = state['uv']
            if spec.get('verify_v') and scalar(plan['ui_resource'],
                    spec['label']+'.ImageComponentTemplate',
                    [('StyleCustomization', 0), ('Coordinates', 0), ('V', 0)], 8) != y:
                raise ValueError('sample window V disagrees with the actual consumer')
            if label[2:] != [w, h]:
                raise ValueError('label dimensions disagree with native sample window')
            box = core_box(image.crop((x, y, x+w, y+h)))
            actual = [label[i] + (box[i]+box[i+2])/2 for i in (0, 1)]
            error = [actual[i]-target[i] for i in (0, 1)]
            checks.append(dict(kind='button', name=spec['name']+':'+state['name'],
                frame_box=frame, target=target, actual=actual, center_error=error,
                passed=max(map(abs, error)) <= spec.get('tolerance', plan['button_tolerance'])))

    ref = plan['clean_labels']['plan']
    raw = confined_path(project, ref['path']).read_bytes()
    if digest(raw) != ref['sha256']:
        raise ValueError('clean label reference SHA256 mismatch')
    labels = json.loads(raw)['labels']
    for spec in plan['clean_labels']['textures']:
        t, _ = texture(spec['resource'], spec['object'])
        for label in labels:
            font_ref = label['font']
            font = confined_path(project, font_ref['path']).read_bytes()
            if digest(font) != font_ref['sha256']:
                raise ValueError('clean label font SHA256 mismatch')
            differences = clean_block_differences(t, label, font)
            checks.append(dict(kind='clean-label', name=spec['resource']+':'+label['id'],
                differing_blocks=differences, passed=differences == 0))
    for spec in plan['sized_labels']:
        _, image = texture(spec['resource'], spec['object'])
        x, y, w, h = spec['region']
        box = core_box(image.crop((x, y, x+w, y+h)))
        width, height = box[2]-box[0], box[3]-box[1]
        checks.append(dict(kind='size', name=spec['resource']+':'+spec['object'], core_box=box,
            width=width, height=height, passed=spec['width'][0] <= width <= spec['width'][1]
                and spec['height'][0] <= height <= spec['height'][1]))
    for spec in plan.get('sampling_edges', []):
        uv = [scalar(plan['ui_resource'], spec['component'],
              [('StyleCustomization', 0), ('Coordinates', 0), (n, 0)], 8)
              for n in ('U', 'V', 'UL', 'VL')]
        x, y, w, h = spec['clear_region']
        if (uv != spec['uv'] or y != uv[1]+uv[3]-1 or h != 1
                or not uv[0] <= x < x+w <= uv[0]+uv[2]):
            raise ValueError('edge guard is not the actual final sampled texel row')
        _, image = texture(spec['resource'], spec['object'])
        n = sum(p[3] != 0 for p in image.crop((x, y, x+w, y+h)).get_flattened_data())
        checks.append(dict(kind='sampling-edge', name=spec['resource']+':'+spec['component'],
                           uv=uv, residue_pixels=n, passed=n == 0))
    return dict(passed=bool(checks) and all(r['passed'] for r in checks), checks=checks,
                input_sha256={r: digest(b) for r, b in blobs.items()}, game_rendering_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'plan', 'report'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--project-root', type=Path, default=Path('.'))
    a = p.parse_args()
    result = audit(a.root, json.loads(a.plan.read_bytes()), a.project_root)
    with a.report.open('x', encoding='utf8') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write('\n')
    n = sum(not r['passed'] for r in result['checks'])
    print(f'CHECKS={len(result["checks"])} FAILURES={n} RESULT={"PASS" if result["passed"] else "FAIL"}')
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
