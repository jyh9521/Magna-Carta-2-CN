"""Audit native ink spacing and row centering, including separately bound digits.

The locale supplies scripts, fonts, widgets and tolerances. This measures original
atlas pixels and serialized fields, not a replacement font or a game screenshot.
"""
import argparse
import json
from pathlib import Path
import struct

from .audit_font_optical_size import Sampler, ink_box
from .audit_ui_spacing import audit as audit_spacing
from .build_font_supplement import context
from .coalesced import parse
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest, select_field
from .ue3_package import LzxDecoder


def span(sample, text):
    x = 0
    boxes = []
    heights = set()
    for char in text:
        im = sample.glyph(ord(char))
        heights.add(im.height)
        box = ink_box(im)
        if box:
            boxes.append((x + box[0], box[1], x + box[2], box[3]))
        x += im.width
    if not boxes or len(heights) != 1:
        raise ValueError('nonempty, same-height measured text required')
    return dict(advance=x, height=heights.pop(), box=(min(b[0] for b in boxes),
                min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)))


def visible_gap(left, right, advance_gap=0):
    return left['advance'] - left['box'][2] + advance_gap + right['box'][0]


def center_error(metrics, top, height, band_height):
    if height < metrics['height']:
        raise ValueError('text cell clips vertically')
    return top + (height - metrics['height']) / 2 + (metrics['box'][1] + metrics['box'][3]) / 2 - band_height / 2


def audit(root, plan_path, overlay=None, decoder=None):
    root = Path(root).resolve()
    plan_path = Path(plan_path).resolve()
    raw_plan = plan_path.read_bytes()
    plan = json.loads(raw_plan)
    if plan.get('schema_version') != 1 or plan.get('kind') != 'native-mixed-text-layout':
        raise ValueError('unsupported mixed layout plan')
    sources = {}

    def read(relative):
        if relative not in sources:
            path = confined_path(root, relative)
            if overlay is not None:
                candidate = confined_path(Path(overlay).resolve(), relative)
                if candidate.exists():
                    path = candidate
            sources[relative] = (path, path.read_bytes())
        return sources[relative][1]

    spacing_path = confined_path(plan_path.parent, plan['spacing_plan'])
    spacing_raw = spacing_path.read_bytes()
    spacing_plan = json.loads(spacing_raw)
    contexts = {k: context(read(v), decoder) for k, v in spacing_plan['packages'].items()}
    spacing = audit_spacing(contexts, parse(read(spacing_plan['text_resource'])), spacing_plan)
    failures = list(spacing['failures'])
    fonts = []
    samples = {}
    lo, hi = plan['mixed_gap']
    for spec in plan['fonts']:
        sample = Sampler(read(spec['resource']), spec['object'])
        samples[(spec['resource'], spec['object'])] = sample
        letters = [cp for cp in sample.mapping if any(a <= cp <= b for a, b in plan['letter_ranges'])]
        digits = [cp for cp in sample.mapping if any(a <= cp <= b for a, b in plan['digit_ranges'])]
        if len(letters) != plan['letter_count'] or len(digits) != plan['digit_count']:
            raise ValueError('mapped script coverage changed')
        cells = {cp: span(sample, chr(cp)) for cp in letters + digits}
        gaps = []
        bad = 0
        examples = []
        for cp in letters:
            for digit in digits:
                for a, b in ((cp, digit), (digit, cp)):
                    gap = visible_gap(cells[a], cells[b])
                    gaps.append(gap)
                    if not lo <= gap <= hi:
                        bad += 1
                        if len(examples) < 12:
                            examples.append(dict(codepoints=[a, b], gap=gap))
        if bad:
            failures.append(f'{spec["object"]}:mixed-pairs={bad}')
        fonts.append(dict(**spec, letters=len(letters), digits=len(digits), pair_checks=len(gaps),
                          gap_min=min(gaps), gap_max=max(gaps), violations=bad, examples=examples))

    ui = contexts[spacing_plan['ui_package']]

    def scalar(c, path, parts, prefix=4):
        matches = [e for e in c['tables']['exports'] if e['path'] == path]
        if len(matches) != 1:
            raise ValueError('unique UI export required')
        e = matches[0]
        payload = c['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']]
        kind, _, raw = select_field(payload, c['tables']['names'], prefix,
                                   [dict(name=n, array_index=i) for n, i in parts])
        return struct.unpack({'FloatProperty': '>f', 'ByteProperty': '>B',
                              'IntProperty': '>i', 'BoolProperty': '>I', 'ObjectProperty': '>i'}[kind], raw)[0]

    def field(path, prop, index, prefix=4):
        return scalar(ui, path, [(prop[0], 0), (prop[1], index)], prefix)

    def flag(path, name):
        return field(path, ('TextStyleCustomization', name), 0, 8)

    def style_binding(renderer, key):
        spec = plan['styles'][key]
        c = contexts[spec['package']]
        for component in 'ABCD':
            actual = scalar(ui, renderer, [('StringStyle', 0), ('AssignedStyleID', 0), (component, 0)], 8)
            expected = scalar(c, spec['object'], [('StyleID', 0), (component, 0)])
            if actual != expected:
                raise ValueError('style identity mismatch')
        states = [e for e in c['tables']['exports'] if e['path'].startswith(spec['object'] + '.')
                  and e['class_path'] == 'Engine.UIStyle_Text']
        if len(states) != spec['states']:
            raise ValueError('style state coverage changed')
        for e in states:
            ref = scalar(c, e['path'], [('StyleFont', 0)])
            if not ref:
                raise ValueError('null style font')
            table = c['tables']['exports' if ref > 0 else 'imports']
            if table[abs(ref) - 1]['path'] != spec['font']:
                raise ValueError('style font binding changed')

    name_spec = spacing_plan['fonts']['names']
    name_resource = spacing_plan['packages'][name_spec['package']]
    name_sample = samples[(name_resource, name_spec['object'])]
    names = {n['value']: span(name_sample, n['value']) for n in spacing['measured_names']}
    number_spec = spacing_plan['fonts']['numbers']
    number_resource = spacing_plan['packages'][number_spec['package']]
    # Export identities are case-insensitive in the package namespace.
    number_obj = next(e['path'] for e in ui['tables']['exports']
                      if e['path'].casefold() == number_spec['object'].casefold())
    number_sample = Sampler(read(number_resource), number_obj)
    native_number = plan['number_source']
    resident_number = Sampler(read(native_number['resource']), native_number['object'])
    # The standalone font may store its atlas in external TFC bulk data. Compare
    # the native cells here; measure pixels from the embedded resident atlas.
    for digit in range(48, 58):
        a = number_sample.font['characters'][number_sample.mapping[digit]]
        b = resident_number.font['characters'][resident_number.mapping[digit]]
        if any(a[k] != b[k] for k in ('StartU', 'StartV', 'USize', 'VSize', 'TextureIndex')):
            raise ValueError('resident numeric font metrics differ')
    numbers = {n: span(number_sample, str(n)) for n in spacing['tested_numeric_values']}
    costs = []
    for role, serial in zip(spacing_plan['cost_roles'], spacing['cost_roles'], strict=True):
        renderer = role['number_label'] + '.LabelStringRenderer'
        style_binding(renderer, 'numbers')
        if flag(renderer, 'bOverrideAlignment') != 1:
            failures.append(role['name'] + ':number-alignment-override-off')
        gaps = []
        for metrics in names.values():
            for number in numbers.values():
                left = serial['number_left']
                if serial['alignment'] == 2:
                    left += serial['number_slot_width'] - number['advance']
                gaps.append(visible_gap(metrics, number, left - serial['name_right']))
        bad = sum(not plan['cost_ink_gap'][0] <= g <= plan['cost_ink_gap'][1] for g in gaps)
        if bad:
            failures.append(role['name'] + f':visible-cost-gaps={bad}')
        costs.append(dict(name=role['name'], gap_min=min(gaps), gap_max=max(gaps), violations=bad))

    vertical = []
    for role in plan['vertical_roles']:
        path = role['label']
        renderer = path + '.LabelStringRenderer'
        if flag(renderer, 'bOverrideAlignment') != 1 or field(renderer, ('TextStyleCustomization', 'TextAlignment'), 1, 8) != 1:
            failures.append(role['name'] + ':vertical-center-override-mismatch')
        if field(renderer, ('TextStyleCustomization', 'TextAlignment'), 0, 8) != 2:
            failures.append(role['name'] + ':name-right-anchor-mismatch')
        if 'style' in role:
            style_binding(renderer, role['style'])
        else:
            font_ref = field(renderer, ('TextStyleCustomization', 'DrawFont'), 0, 8)
            if font_ref <= 0 or ui['tables']['exports'][font_ref - 1]['path'] != name_spec['object'] or flag(renderer, 'bOverrideDrawFont') != 1:
                failures.append(role['name'] + ':name-font-binding-mismatch')
        y = field(path, ('Position', 'Value'), 1)
        height = field(path, ('Position', 'Value'), 3)
        parent_y = field(role['parent'], ('Position', 'Value'), 1)
        band_height = field(role['band'], ('Position', 'Value'), 3)
        if field(path, ('Position', 'ScaleType'), 1) != 3:
            raise ValueError('unhandled label Y scale')
        metrics = list(names.values()) if role['text'] is None else [span(name_sample, role['text'])]
        errors = [center_error(m, parent_y + y, height, band_height) for m in metrics]
        if max(abs(e) for e in errors) > plan['center_tolerance']:
            failures.append(role['name'] + ':ink-not-centered')
        for shadow in role['shadows']:
            if abs(field(shadow['path'], ('Position', 'Value'), 1) - y - shadow['delta_y']) > .001:
                failures.append(role['name'] + ':shadow-center-divergence')
        vertical.append(dict(name=role['name'], names=len(metrics), center_error_min=min(errors),
                             center_error_max=max(errors), row_height=band_height, label_y=y,
                             shadows=len(role['shadows'])))
    for path, data in sources.values():
        if path.read_bytes() != data:
            raise ValueError('input changed during audit')
    if plan_path.read_bytes() != raw_plan or spacing_path.read_bytes() != spacing_raw:
        raise ValueError('plan changed during audit')
    return dict(schema_version=1, passed=not failures, failures=failures, fonts=fonts,
                pair_checks=sum(f['pair_checks'] for f in fonts), costs=costs, vertical=vertical,
                spacing=spacing, plan_sha256=digest(raw_plan), spacing_plan_sha256=digest(spacing_raw),
                inputs=[dict(resource=r, path=str(p), sha256=digest(d)) for r, (p, d) in sources.items()],
                number_alias_check='native-cells; pixels-from-embedded-resident-atlas',
                game_started=False, game_rendering_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'plan', 'output'):
        p.add_argument('--' + key, required=True, type=Path)
    p.add_argument('--overlay', type=Path)
    p.add_argument('--lzx-library', type=Path)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('new report required')
    result = audit(a.root, a.plan, a.overlay, LzxDecoder(a.lzx_library) if a.lzx_library else None)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    a.output.write_bytes(raw)
    if a.output.read_bytes() != raw:
        raise ValueError('report readback mismatch')
    print(json.dumps(dict(passed=result['passed'], mixed_pairs=result['pair_checks'],
        skill_combinations=result['spacing']['combinations'], vertical_rows=len(result['vertical']),
        failures=len(result['failures']), game_rendering_verified=False), separators=(',', ':')))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
