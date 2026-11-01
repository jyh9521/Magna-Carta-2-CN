"""Measure native UI ink and real localized fragments without starting the game."""
import argparse
import json
from pathlib import Path
import struct

from PIL import Image

from .audit_font_optical_size import Sampler
from .audit_mixed_text_layout import span
from .audit_ui_spacing import audit as spacing_audit, ini_rows
from .build_font_supplement import context
from .coalesced import parse
from .font_binding_plan import confined_path
from .patch_tagged_fields import select_field
from .replace_texture_regions import selected
from .texture_layout import decode_texture


def core_box(im):
    points = [(x, y) for y in range(im.height) for x in range(im.width)
              if (lambda p: p[3] >= 160 and min(p[:3]) >= 128
                  and max(p[:3]) - min(p[:3]) < 50)(im.getpixel((x, y)))]
    if not points:
        raise ValueError('empty native neutral foreground')
    return [min(x for x, _ in points), min(y for _, y in points),
            max(x for x, _ in points)+1, max(y for _, y in points)+1]


def visible_right(x, width, alignment, metrics):
    if alignment not in (0, 2) or metrics['advance'] > width:
        raise ValueError('unsupported alignment or clipped numeric cell')
    return x + (width-metrics['advance'] if alignment == 2 else 0) + metrics['box'][2]


def runtime_value(value):
    """The quoted INI value preserves an otherwise-trimmed ASCII spacer."""
    value = value.strip()
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value


def audit(root, fallback, contract_path, project):
    root, fallback, project = map(lambda p: Path(p).resolve(), (root, fallback, project))
    contract = json.loads(Path(contract_path).read_bytes())
    if contract.get('schema_version') != 1 or contract.get('kind') != 'native-ui-ink-audit':
        raise ValueError('unsupported ink audit contract')
    blobs, images = {}, {}

    def read(relative):
        if relative not in blobs:
            path = confined_path(root, relative)
            if not path.is_file():
                path = confined_path(fallback, relative)
            blobs[relative] = path.read_bytes()
        return blobs[relative]

    def texture(resource, obj):
        key = resource, obj
        if key not in images:
            _, _, _, t = selected(read(resource), obj, None)
            images[key] = Image.frombytes('RGBA', (t['width'], t['height']), decode_texture(t))
        return images[key]

    data = read(contract['ui_resource'])
    c = context(data, None)

    def scalar(obj, parts, prefix=4):
        es = [e for e in c['tables']['exports'] if e['path'] == obj]
        if len(es) != 1:
            raise ValueError('missing or ambiguous serialized UI object')
        e = es[0]
        kind, _, raw = select_field(data[e['serial_offset']:e['serial_offset']+e['serial_size']],
            c['tables']['names'], prefix, [dict(name=n, array_index=i) for n, i in parts])
        return struct.unpack({'FloatProperty': '>f', 'ByteProperty': '>B'}[kind], raw)[0]

    def pos(obj, i):
        return scalar(obj, [('Position', 0), ('Value', i)])

    failures, buttons = [], []
    for spec in contract['buttons']:
        for state in spec['states']:
            im = texture(state['resource'], state['object'])
            x, y, w, h = state['uv']
            box = core_box(im.crop((x, y, x+w, y+h)))
            error = [pos(spec['label'], i) + (box[i]+box[i+2])/2 - pos(spec['parent'], i+2)/2
                     for i in (0, 1)]
            ok = max(map(abs, error)) <= contract['button_core_tolerance']
            if not ok:
                failures.append('button:' + spec['name'] + ':' + state['name'])
            buttons.append(dict(name=spec['name'], state=state['name'], core_box=box,
                                center_error=error, passed=ok))
    sp = json.loads(confined_path(project, contract['spacing_plan']).read_bytes())
    contexts = {key: context(read(value), None) for key, value in sp['packages'].items()}
    texts = parse(read(sp['text_resource']))
    spacing = spacing_audit(contexts, texts, sp)
    if not spacing['passed']:
        failures.append('skill-slot-spacing')
    number_font = Sampler(data, contract['number_font'])
    name_font = Sampler(data, contract['name_font'])
    reference = contract['right_reference']
    metrics = span(name_font, reference['text'])
    edge = pos(reference['parent'], 0) + visible_right(pos(reference['label'], 0),
        pos(reference['label'], 2), 2, metrics)
    rights = []
    for role in sp['cost_roles']:
        label = role['number_label']
        alignment = scalar(label+'.LabelStringRenderer', [('TextStyleCustomization', 0), ('TextAlignment', 0)], 8)
        for n in spacing['tested_numeric_values']:
            right = visible_right(pos(label, 0), pos(label, 2), alignment, span(number_font, str(n)))
            ok = abs(right-edge) <= contract['right_tolerance']
            if not ok:
                failures.append('right-edge:' + role['name'] + ':' + str(n))
            rights.append(dict(role=role['name'], number=n, ink_right=right, reference=edge, passed=ok))
    maps = []
    for spec in contract['english']:
        im = texture(spec['resource'], spec['object'])
        dark = 0
        for x, y, w, h in spec['rectangles']:
            dark += sum(p[3] > 0 and max(p[:3]) <= spec['rgb_ceiling']
                        for p in im.crop((x, y, x+w, y+h)).get_flattened_data())
        if dark:
            failures.append('map-background:' + spec['resource'] + ':' + spec['object'])
        maps.append(dict(resource=spec['resource'], object=spec['object'], dark_background_pixels=dark))
    guests = []
    for spec in contract['guests']:
        im = texture(spec['resource'], spec['object'])
        x, y, w, h = spec['ink_box']
        green = [max((p[1] for p in im.crop((x, yy, x+w, yy+1)).get_flattened_data()
                      if p[3] >= 80), default=0) for yy in range(y+h-2, y+h)]
        ok = min(green) >= spec.get('minimum_green', contract['guest_bottom_green_min'])
        if not ok:
            failures.append('guest-bottom:' + spec['id'] + ':' + spec['resource'])
        guests.append(dict(**spec, bottom_green=green, passed=ok))
    v = {(r['section'], r['key']): runtime_value(r['value'])
         for r in ini_rows(texts, contract['party_file'])}
    joins = []
    for sample in contract['party_samples']:
        for subject in contract['subject_keys']:
            for verb in contract['party_keys']:
                value = sample + v[tuple(subject)] + v[tuple(verb)]
                lines = value.split('\\n')
                ok = len(lines) == 2 and lines[0].strip() == sample and bool(lines[1])
                if not ok:
                    failures.append('party-names-line:' + '/'.join(verb))
                joins.append(dict(names=sample, subject=subject, verb=verb, lines=lines, passed=ok))
    # All other native consumers of the shared subject suffix move the action
    # prefix together; check the paired records rather than only JoinGuest.
    atomic = []
    for row in contract['atomic_text']:
        matches = [r for r in ini_rows(texts, row['file'])
                   if r['section'] == row['section'] and r['key'] == row['key']]
        ok = len(matches) == 1 and runtime_value(matches[0]['value']) == row['expected']
        if not ok:
            failures.append('atomic-fragment:' + row['key'])
        atomic.append(dict(key=row['key'], passed=ok))
    return dict(schema_version=1, passed=not failures, failure_count=len(failures),
        failures=failures, buttons=buttons, spacing=spacing, right_edges=rights,
        maps=maps, guests=guests, party_cases=joins, atomic_fragments=atomic,
        game_started=False, game_rendering_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'fallback', 'contract', 'report'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--project', type=Path, default=Path('.'))
    a = p.parse_args()
    result = audit(a.root, a.fallback, a.contract, a.project)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode()
    a.report.write_bytes(raw)
    if a.report.read_bytes() != raw:
        raise ValueError('audit report readback mismatch')
    print(('PASS' if result['passed'] else 'FAIL') + ' UI ink: '
          + f"buttons={len(result['buttons'])}; combinations={result['spacing']['combinations']}; "
          + f"right_edges={len(result['right_edges'])}; map_textures={len(result['maps'])}; "
          + f"guest_layers={len(result['guests'])}; party_cases={len(result['party_cases'])}; "
          + f"violations={result['failure_count']}; game_rendering_verified=false")
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
