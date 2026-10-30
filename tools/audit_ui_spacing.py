"""Offline serialized UI spacing audit using font advances and a locale contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct

try:
    from .build_font_supplement import context
    from .coalesced import parse as parse_coalesced
    from .patch_tagged_fields import digest, select_field
    from .ue3_fonts import parse_font_payload, read_properties
    from .ue3_package import FormatError, LzxDecoder, Reader
except ImportError:
    from build_font_supplement import context
    from coalesced import parse as parse_coalesced
    from patch_tagged_fields import digest, select_field
    from ue3_fonts import parse_font_payload, read_properties
    from ue3_package import FormatError, LzxDecoder, Reader


def ini_rows(files, filename):
    matches = [f for f in files if f.path.text.replace('\\', '/').rsplit('/', 1)[-1].casefold() == filename.casefold()]
    if len(matches) != 1:
        raise FormatError('missing/ambiguous embedded text file')
    section = ''; rows = []
    for line in matches[0].content.text.splitlines():
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif '=' in line and not line.startswith(';'):
            key, value = line.split('=', 1)
            rows.append(dict(section=section, key=key, value=value))
    return rows


def width(text, font):
    remap = {r['codepoint']: r['glyph_index'] for r in font['remap']}
    total = 0
    for char in text:
        cp = ord(char)
        index = remap.get(cp) if font['is_remapped'] else cp
        if index is None or not 0 <= index < len(font['characters']):
            raise FormatError('missing measured glyph U+%04X' % cp)
        total += font['characters'][index]['USize']
    return total


def audit(contexts, files, plan):
    if plan.get('schema_version') != 1 or plan.get('profile') != 'serialized-ui-spacing-v1':
        raise FormatError('unsupported spacing contract')

    def obj(label, path):
        c = contexts[label]
        es = [e for e in c['tables']['exports'] if e['path'].casefold() == path.casefold()]
        if len(es) != 1:
            raise FormatError('missing/ambiguous measured export: ' + path)
        e = es[0]
        return c, e, c['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']]

    def field(label, path, prop_path, prefix=4, missing=None):
        c, e, payload = obj(label, path)
        ppath = [dict(name=name, array_index=i) for name, i in prop_path]
        try:
            kind, _, raw = select_field(payload, c['tables']['names'], prefix, ppath)
        except ValueError:
            if missing is not None:
                # Defaults are only used after the outer tag is absent, not after a malformed path.
                r = Reader(payload); r.seek(prefix); ps = read_properties(r, c['tables']['names'])
                if not any(p['name'] == prop_path[0][0] and p['array_index'] == prop_path[0][1] for p in ps):
                    return missing
            raise
        formats = {'FloatProperty': '>f', 'IntProperty': '>i', 'BoolProperty': '>I', 'ByteProperty': '>B'}
        if kind not in formats:
            raise FormatError('non-scalar layout field')
        return struct.unpack(formats[kind], raw)[0]

    def font(spec):
        c, _, payload = obj(spec['package'], spec['object'])
        return parse_font_payload(payload, c['tables']['names'])

    fonts = {k: font(v) for k, v in plan['fonts'].items()}
    failures = []; footer_rows = []; package = plan['ui_package']
    for group in plan['footer_groups']:
        labels = []
        for spec in group['labels']:
            rows = ini_rows(files, spec['file'])
            values = [r['value'] for r in rows if r['section'] == spec['section'] and r['key'] == spec['key']]
            if len(values) != 1:
                raise FormatError('footer localization lookup missing/ambiguous')
            text = values[0]
            # Width includes the original button glyph; markup and labels are never rewritten here.
            advance = width(spec['icon'], fonts['icons']) + width(text, fonts['footer'])
            path = spec['object']; x = field(package, path, [('Position', 0), ('Value', 0)])
            w = field(package, path, [('Position', 0), ('Value', 2)])
            right_mode = spec.get('right_scale_field', False)
            if right_mode and field(package, path, [('Position', 0), ('ScaleType', 2)]) != 0:
                # Evaluate the original absolute viewport right edge in the supplied verified parent frame.
                w -= x + group['owner_left']
            renderer = path + '.LabelStringRenderer'
            if spec['autosize_field']:
                auto = field(package, renderer, [('AutoSizeParameters', 0), ('bAutoSizeEnabled', 0)], 8)
                if auto:
                    failures.append(f'{group["name"]}:{spec["key"]}:horizontal-autosize-enabled')
            alignment = field(package, renderer, [('TextStyleCustomization', 0), ('TextAlignment', 0)], 8)
            if alignment != 2:
                raise FormatError('footer measurement expects verified right alignment')
            left, right = x + w - advance, x + w
            labels.append(dict(key=spec['key'], text=text, icon=spec['icon'], slot_left=x,
                               slot_width=w, advance=advance, occupied_left=left, occupied_right=right))
            if advance > w:
                failures.append(f'{group["name"]}:{spec["key"]}:advance={advance}>slot={w:g}')
        for a, b in zip(labels, labels[1:]):
            if b['occupied_left'] - a['occupied_right'] < group['minimum_gap']:
                failures.append(f'{group["name"]}:{a["key"]}/{b["key"]}:insufficient-gap')
        if labels[-1]['occupied_right'] > group['right_limit']:
            failures.append(group['name'] + ':right-overflow')
        footer_rows.append(dict(name=group['name'], labels=labels))

    ns = plan['names']; names = [r for r in ini_rows(files, ns['file']) if r['section'] in ns['sections'] and re.fullmatch(ns['key_pattern'], r['key'])]
    if len(names) != ns['expected_count']:
        raise FormatError('skill-name coverage count changed')
    # Derive the numeric domain from all matching resource instances and the real class default.
    domain = plan['numeric_domain']; default = field(package, domain['default_object'], [(domain['field'], 0)])
    c = contexts[domain['package']]; numeric_rows = []
    for index, e in enumerate(c['tables']['exports'], 1):
        if e['class_path'] != domain['class_path']:
            continue
        if e.get('archetype', 0):
            raise FormatError('numeric source has an unhandled explicit archetype')
        payload = c['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']]
        reader = Reader(payload); reader.seek(4)
        ps = [p for p in read_properties(reader, c['tables']['names']) if p['name'] == domain['field']]
        if not ps:
            value = default
        elif len(ps) == 1 and not ps[0]['array_index'] and ps[0]['type'] == 'FloatProperty':
            value = struct.unpack('>f', ps[0]['raw'])[0]
        else:
            raise FormatError('numeric source field is duplicated/indexed/wrong type')
        if value != int(value) or not 0 <= value <= domain['maximum_value']:
            raise FormatError('numeric source outside integral contract')
        numeric_rows.append(dict(object_index=index, object=e['path'], value=int(value)))
    if len(numeric_rows) != domain['expected_count']:
        raise FormatError('numeric source coverage count changed')
    numbers = sorted({r['value'] for r in numeric_rows})
    envelope = sorted(set(numbers + domain['extra_boundary_values']))
    measured_names = [dict(**r, advance=width(r['value'], fonts['names'])) for r in names]
    measured_numbers = [dict(value=n, advance=width(str(n), fonts['numbers'])) for n in envelope]
    combinations = 0; cost_rows = []
    for role in plan['cost_roles']:
        parent_x = field(package, role['name_parent'], [('Position', 0), ('Value', 0)])
        name_x = field(package, role['name_label'], [('Position', 0), ('Value', 0)])
        name_w = field(package, role['name_label'], [('Position', 0), ('Value', 2)])
        x = field(package, role['number_label'], [('Position', 0), ('Value', 0)])
        w = field(package, role['number_label'], [('Position', 0), ('Value', 2)])
        align = field(package, role['number_label'] + '.LabelStringRenderer', [('TextStyleCustomization', 0), ('TextAlignment', 0)], 8)
        if align not in (0, 2):
            raise FormatError('unknown cost horizontal alignment')
        if 'cost_right_edge' in plan and (align != 2 or abs(x + w - plan['cost_right_edge']) > .01):
            failures.append(role['name'] + ':cost-right-edge-mismatch')
        gaps = []
        for name in measured_names:
            for number in measured_numbers:
                combinations += 1
                number_left = x if align == 0 else x + w - number['advance']
                gap = number_left - (parent_x + name_x + name_w)
                gaps.append(gap)
                if not plan['cost_gap'][0] <= gap <= plan['cost_gap'][1]:
                    failures.append(f'{role["name"]}:{name["key"]}/{number["value"]}:gap={gap:g}')
                if name['advance'] > name_w or number['advance'] > w:
                    failures.append(f'{role["name"]}:{name["key"]}/{number["value"]}:slot-overflow')
        shadow_rights = []
        for shadow in role['shadows']:
            sx = field(package, shadow, [('Position', 0), ('Value', 0)])
            sw = field(package, shadow, [('Position', 0), ('Value', 2)])
            shadow_rights.append(parent_x + sx + sw)
            if abs(sx + sw - name_x - name_w) > 1:
                failures.append(role['name'] + ':shadow-anchor-divergence')
        cost_rows.append(dict(name=role['name'], name_right=parent_x + name_x + name_w,
                              number_left=x, number_slot_width=w, alignment=align,
                              gap_min=min(gaps), gap_max=max(gaps), shadow_rights=shadow_rights))
    return dict(schema_version=1, passed=not failures, failure_count=len(failures), failures=failures,
                footer_groups=footer_rows, skill_name_count=len(names), numeric_source_count=len(numeric_rows),
                numeric_values=numbers, tested_numeric_values=envelope, cost_roles=cost_rows,
                combinations=combinations, measured_names=measured_names, measured_numbers=measured_numbers,
                numeric_sources=numeric_rows, source_default=default, measurement='serialized-font-USize-advance',
                actual_skill_to_cost_mapping_claimed=False, exhaustive_name_cost_envelope=True,
                game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--lzx-library', type=Path)
    p.add_argument('--package-override', nargs=2, action='append', default=[], metavar=('LABEL', 'PATH'))
    a = p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink():
            raise FormatError('audit report must be new')
        plan_bytes = a.plan.read_bytes(); plan = json.loads(plan_bytes)
        decoder = LzxDecoder(a.lzx_library) if a.lzx_library else None
        contexts = {}; inputs = []; overrides = {}
        for label, path in a.package_override:
            if label in overrides or label not in plan['packages']:
                raise FormatError('duplicate/unknown package override')
            overrides[label] = Path(path).resolve()
        for label, relative in plan['packages'].items():
            path = overrides.get(label, (a.root / relative).resolve())
            if label not in overrides and not path.is_relative_to(a.root.resolve()):
                raise FormatError('resource path escapes root')
            raw = path.read_bytes(); contexts[label] = context(raw, decoder)
            inputs.append(dict(path=relative, actual_path=str(path), sha256=digest(raw)))
        raw_text = (a.root / plan['text_resource']).read_bytes()
        result = audit(contexts, parse_coalesced(raw_text), plan)
        inputs.append(dict(path=plan['text_resource'], actual_path=str((a.root / plan['text_resource']).resolve()), sha256=digest(raw_text)))
        result.update(inputs=inputs, plan_sha256=digest(plan_bytes))
        for item in inputs:
            if digest(Path(item['actual_path']).read_bytes()) != item['sha256']:
                raise FormatError('input changed during audit')
        encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
        a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_bytes(encoded)
        if a.output.read_bytes() != encoded:
            raise FormatError('report readback mismatch')
        print(f'{"PASS" if result["passed"] else "FAIL"} UI spacing: footer_groups={len(result["footer_groups"])}; skill_names={result["skill_name_count"]}; skill_resources={result["numeric_source_count"]}; combinations={result["combinations"]}; violations={result["failure_count"]}; game_rendering_verified=false')
        return 0 if result['passed'] else 1
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        print('ERROR ' + str(exc)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
