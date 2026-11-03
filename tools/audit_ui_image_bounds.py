"""Measure native image ink through actual serialized UI image bindings.

Regions, thresholds, aliases and inherited defaults are explicit contract data.
The result is offline geometry, not a claim about a game's final compositor.
"""
import argparse
import json
from pathlib import Path
import struct

from .build_font_supplement import context
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest, select_field
from .texture_layout import decode_texture, read_texture
from .ue3_fonts import read_properties
from .ue3_package import Reader, LzxDecoder


def ink_points(pixels, size, region, threshold):
    width, height = size
    x, y, w, h = region
    if (len(pixels) != width * height * 4 or min(w, h) <= 0 or
            any(type(v) is not int for v in region) or
            not (0 <= x < x+w <= width and 0 <= y < y+h <= height) or
            len(threshold) != 4 or any(type(v) is not int or not 0 <= v <= 255 for v in threshold)):
        raise ValueError('invalid native ink window')
    points = [(xx, yy) for yy in range(y, y+h) for xx in range(x, x+w)
              if all(pixels[(yy*width+xx)*4+i] >= threshold[i] for i in range(4))]
    if not points:
        raise ValueError('empty native ink window')
    return points


def measure(points, position, uv):
    x, y, width, height = position
    u, v, uw, vh = uv
    if min(width, height, uw, vh) <= 0:
        raise ValueError('non-positive image dimensions')
    bounds = [min(p[0] for p in points), min(p[1] for p in points),
              max(p[0] for p in points)+1, max(p[1] for p in points)+1]
    scale = [width/uw, height/vh]
    clipped = sum(not (u <= px < u+uw and v <= py < v+vh) for px, py in points)
    screen = [x+(bounds[0]-u)*scale[0], y+(bounds[1]-v)*scale[1],
              x+(bounds[2]-u)*scale[0], y+(bounds[3]-v)*scale[1]]
    return dict(native_bounds=bounds, position=position, uv=uv, scale=scale,
                clipped_pixels=clipped, screen_bounds=screen,
                center=[(screen[0]+screen[2])/2, (screen[1]+screen[3])/2])


def center_delta(label, frame):
    return [label['center'][i]-frame['center'][i] for i in range(2)]


def audit(root, fallback, plan, decoder):
    if plan.get('schema_version') != 1 or plan.get('kind') != 'native-ui-image-bounds-v1':
        raise ValueError('unsupported native image contract')
    roots = [Path(root).resolve(), Path(fallback).resolve()]
    contexts, raw = {}, {}
    for key, relative in plan['packages'].items():
        paths = [confined_path(base, relative) for base in roots]
        path = next((p for p in paths if p.is_file()), None)
        if path is None:
            raise ValueError('missing declared package: '+relative)
        raw[key] = path.read_bytes()
        contexts[key] = context(raw[key], decoder)

    def export(key, name):
        matches = [e for e in contexts[key]['tables']['exports'] if e['path'] == name]
        if len(matches) != 1:
            raise ValueError('missing or ambiguous image export: '+name)
        return matches[0]

    def field(key, e, path, prefix=4):
        c = contexts[key]
        data = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        kind, _, value = select_field(data, c['tables']['names'], prefix,
                                     [dict(name=n, array_index=i) for n, i in path])
        return struct.unpack({'FloatProperty': '>f', 'ObjectProperty': '>i',
                              'BoolProperty': '>I'}[kind], value)[0]

    def ref(key, e, name, prefix, expected_class):
        index = field(key, e, [(name, 0)], prefix)
        exports = contexts[key]['tables']['exports']
        if not 1 <= index <= len(exports) or exports[index-1]['class_path'].split('.')[-1] != expected_class:
            raise ValueError('unexpected local image binding')
        return exports[index-1]

    textures, images = {}, {}
    for spec in plan['images']:
        key = spec['package']; c = contexts[key]; e = export(key, spec['object'])
        component = ref(key, e, 'ImageComponent', 4, 'UIComp_DrawImage')
        image = ref(key, component, 'ImageRef', 8, 'UITexture')
        index = field(key, image, [('ImageTexture', 0)])
        if index == 0:
            raise ValueError('image has no explicit texture binding')
        target = (c['tables']['exports'][index-1] if index > 0 else c['tables']['imports'][-index-1])['path']
        if target != spec['texture_reference']:
            raise ValueError('native image texture reference changed')
        position = []
        for i in range(4):
            try:
                value = field(key, e, [('Position', 0), ('Value', i)])
            except ValueError as error:
                if i != 3 or 'height_default' not in spec or str(error) != 'missing/ambiguous indexed tag: Value':
                    raise
                default = spec['height_default']
                value = field(default['package'], export(default['package'], default['object']),
                              [('Position', 0), ('Value', 3)])
                if value != default['value']:
                    raise ValueError('inherited image height changed')
            position.append(value)
        uv = []
        for name in ('U', 'V', 'UL', 'VL'):
            try:
                value = field(key, component, [('StyleCustomization', 0), ('Coordinates', 0), (name, 0)], 8)
            except ValueError as error:
                if name not in spec.get('zero_coordinate_defaults', []) or str(error) != 'missing/ambiguous indexed tag: '+name:
                    raise
                value = 0.0
            uv.append(value)
        if field(key, component, [('StyleCustomization', 0), ('bOverrideCoordinates', 0)], 8) != 1:
            raise ValueError('image coordinate override disabled')
        tk = (spec['texture_package'], spec['texture_object'])
        if tk not in textures:
            tc = contexts[tk[0]]; te = export(*tk)
            data = tc['logical'][te['serial_offset']:te['serial_offset']+te['serial_size']]
            reader = Reader(data); reader.seek(4)
            props = read_properties(reader, tc['tables']['names'])
            fmt = next(p['raw'][0] for p in props if p['name'] == 'Format')
            native = read_texture(data, tc['tables']['names'], te['serial_offset'],
                                  dict(kind='xbox-inline-bc-v1', format=fmt), decoder)
            textures[tk] = (native, decode_texture(native))
        native, pixels = textures[tk]
        if digest(native['tiles']) != spec['native_sha256']:
            raise ValueError('native image bytes changed')
        points = ink_points(pixels, (native['width'], native['height']), spec['region'], spec['rgba_min'])
        result = measure(points, position, uv)
        result['passed'] = result['clipped_pixels'] == 0 and result['scale'] == spec['expected_scale']
        if spec['id'] in images:
            raise ValueError('duplicate image ID')
        images[spec['id']] = result
    centers = []
    for case in plan['centers']:
        delta = center_delta(images[case['label']], images[case['frame']])
        centers.append(dict(name=case['name'], delta=delta,
                            passed=max(map(abs, delta)) <= case['tolerance']))
    return dict(passed=all(i['passed'] for i in images.values()) and all(c['passed'] for c in centers),
                images=images, centers=centers, input_sha256={k: digest(v) for k, v in raw.items()},
                game_rendering_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'fallback', 'plan', 'lzx-library', 'report'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.fallback, json.loads(args.plan.read_bytes()), LzxDecoder(args.lzx_library))
    raw = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode()
    args.report.write_bytes(raw)
    if args.report.read_bytes() != raw:
        raise ValueError('image bounds report readback mismatch')
    clipped = sum(r['clipped_pixels'] for r in result['images'].values())
    failed_centers = sum(not r['passed'] for r in result['centers'])
    print(f"IMAGES={len(result['images'])} CLIPPED_PIXELS={clipped} CENTER_FAILURES={failed_centers} RESULT={'PASS' if result['passed'] else 'FAIL'}")
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
