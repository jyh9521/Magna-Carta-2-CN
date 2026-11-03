"""Measure separate right-anchored skill and cost fields using their native ink.

The contract supplies the locale, field bindings and permitted source domain.
Logical advances can overlap by transparent bearings; visible ink must not.
"""
import argparse
import json
from pathlib import Path
import struct
import copy

from .audit_font_optical_size import Sampler
from .audit_mixed_text_layout import span
from .audit_ui_spacing import audit as spacing_audit
from .build_font_supplement import context
from .coalesced import parse
from .font_binding_plan import confined_path
from .patch_tagged_fields import select_field
from .ue3_package import LzxDecoder


def pair_gap(name, number, name_right, number_right):
    return number_right - number['advance'] + number['box'][0] - (
        name_right - name['advance'] + name['box'][2])


def audit(root, fallback, plan, decoder):
    roots = [Path(root).resolve(), Path(fallback).resolve()]
    def read(relative):
        for base in roots:
            p = confined_path(base, relative)
            if p.is_file():
                return p.read_bytes()
        raise ValueError('missing declared input: ' + relative)
    contexts = {k: context(read(v), decoder) for k, v in plan['packages'].items()}
    effective = copy.deepcopy(plan)
    binding_failures = []
    if 'number_font_binding' in plan:
        cfg = plan['number_font_binding']; c = contexts[plan['ui_package']]
        actual_fonts = []
        for role in plan['cost_roles']:
            obj = role['number_label'] + '.LabelStringRenderer'
            e = next(e for e in c['tables']['exports'] if e['path'] == obj)
            payload = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
            try:
                fields = lambda name: [dict(name=n, array_index=0) for n in ('TextStyleCustomization', name)]
                ref = struct.unpack('>i', select_field(payload, c['tables']['names'], 8, fields('DrawFont'))[2])[0]
                enabled = struct.unpack('>I', select_field(payload, c['tables']['names'], 8, fields('bOverrideDrawFont'))[2])[0]
                actual = c['tables']['exports'][ref-1]['path'] if ref > 0 and enabled == 1 else None
            except ValueError:
                actual = None
            if actual != cfg['expected']:
                binding_failures.append('number-font-binding:' + role['name'])
            actual_fonts.append(actual or cfg['baseline'])
        if len(set(actual_fonts)) != 1:
            raise ValueError('numeric slots have different active fonts')
        effective['fonts']['numbers']['object'] = actual_fonts[0]
    result = spacing_audit(contexts, parse(read(plan['text_resource'])), effective)
    result['failures'].extend(binding_failures)
    c = contexts[plan['ui_package']]
    raw = c['logical']
    exports = {e['path']: e for e in c['tables']['exports']}
    def pos(obj, index):
        e = exports[obj]
        return struct.unpack('>f', select_field(raw[e['serial_offset']:e['serial_offset']+e['serial_size']],
            c['tables']['names'], 4, [dict(name='Position', array_index=0),
            dict(name='Value', array_index=index)])[2])[0]
    def sampler(key):
        requested = effective['fonts'][key]['object']
        matches = [name for name in exports if name.casefold() == requested.casefold()]
        if len(matches) != 1:
            raise ValueError('missing or ambiguous native Font binding')
        return Sampler(raw, matches[0])
    nf, df = sampler('names'), sampler('numbers')
    names = {r['value']: span(nf, r['value']) for r in result['measured_names']}
    nums = {n: span(df, str(n)) for n in result['tested_numeric_values']}
    ref = plan['ink_right_reference']
    m = span(nf, ref['text'])
    edge = pos(ref['parent'], 0) + pos(ref['label'], 0) + pos(ref['label'], 2) - m['advance'] + m['box'][2]
    measurements = []
    vertical = []
    for role, logical in zip(plan['cost_roles'], result['cost_roles'], strict=True):
        gaps = []
        for row in result['measured_names']:
            name = row['value']
            for number, metric in nums.items():
                right = pos(role['number_label'], 0) + pos(role['number_label'], 2)
                gap = pair_gap(names[name], metric, logical['name_right'], right)
                gaps.append(gap)
                if not plan['ink_gap'][0] <= gap <= plan['ink_gap'][1]:
                    result['failures'].append(f"ink-gap:{role['name']}:{row['key']}/{number}:{gap:g}")
                if abs(right - metric['advance'] + metric['box'][2] - edge) > plan['ink_right_tolerance']:
                    result['failures'].append(f"ink-right:{role['name']}:{number}")
        measurements.append(dict(role=role['name'], ink_gap_min=min(gaps), ink_gap_max=max(gaps),
                                 combinations=len(gaps), numeric_ink_right=edge))
        if 'optical_alignment' in plan:
            cfg = plan['optical_alignment']; ds = cfg['height_default']
            dc = contexts[ds['package']]
            de = next(e for e in dc['tables']['exports'] if e['path'] == ds['object'])
            height = struct.unpack('>f', select_field(dc['logical'][de['serial_offset']:de['serial_offset']+de['serial_size']],
                dc['tables']['names'], 4, [dict(name='Position', array_index=0), dict(name='Value', array_index=3)])[2])[0]
            if height != ds['value']:
                raise ValueError('numeric inherited height changed')
            try:
                height = pos(role['number_label'], 3)
            except ValueError as exc:
                if 'missing/ambiguous indexed tag: Value' not in str(exc):
                    raise
            name_top = pos(role['name_parent'], 1) + pos(role['name_label'], 1)
            name_height = pos(role['name_label'], 3)
            bounds = []
            for nm in names.values():
                nt = name_top + (name_height - nm['height']) / 2 + nm['box'][1]
                nb = name_top + (name_height - nm['height']) / 2 + nm['box'][3]
                for value, dm in nums.items():
                    dt = pos(role['number_label'], 1) + (height - dm['height']) / 2 + dm['box'][1]
                    db = pos(role['number_label'], 1) + (height - dm['height']) / 2 + dm['box'][3]
                    delta = max(abs(dt-nt), abs(db-nb))
                    bounds.append(delta)
                    if delta > cfg['edge_tolerance']:
                        result['failures'].append(f'number-optical-alignment:{role["name"]}:{value}:{delta:g}')
            vertical.append(dict(role=role['name'], maximum_edge_delta=max(bounds),
                number_ink_heights=sorted({m['box'][3]-m['box'][1] for m in nums.values()}),
                name_ink_heights=sorted({m['box'][3]-m['box'][1] for m in names.values()})))
    result.update(native_measurements=measurements, failure_count=len(result['failures']),
                  optical_alignment=vertical, effective_number_font=effective['fonts']['numbers']['object'],
                  passed=not result['failures'], game_started=False)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'fallback', 'plan', 'report', 'lzx-library'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    result = audit(a.root, a.fallback, json.loads(a.plan.read_bytes()), LzxDecoder(a.lzx_library))
    raw = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode()
    a.report.write_bytes(raw)
    if a.report.read_bytes() != raw:
        raise ValueError('audit report readback mismatch')
    m = result['native_measurements']
    print(f"SKILL_NAMES={result['skill_name_count']} COST_SOURCES={result['numeric_source_count']} "
          f"COMBINATIONS={result['combinations']} INK_GAP={min(r['ink_gap_min'] for r in m):g}.."
          f"{max(r['ink_gap_max'] for r in m):g} RIGHT={m[0]['numeric_ink_right']:g} "
          f"RESULT={'PASS' if result['passed'] else 'FAIL'}")
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
