"""Build and audit source-locked Coalesced and timed-text line layout copies."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .build_font_supplement import context
from .coalesced import extract_entries, parse
from .build_coalesced import rebuild
from .font_binding_plan import confined_path
from .reface_font import sha
from .subtitle_text import parse as parse_cues, rebuild_reversible
from .ue3_fonts import parse_font_payload
from .text_line_layout import audit, reflow
from .replay_text_consumers import property_value
from .ue3_package import LzxDecoder


def canonical(data):
    return sha(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('output already exists: '+str(path))
    with path.open('xb') as f:
        f.write(data)
    if path.read_bytes() != data:
        raise ValueError('output reopening mismatch')


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode()


def verify_disc_sources(spec, data):
    records = spec['source_by_disc']
    discs = [r['disc'] for r in records]
    if not records or len(set(discs)) != len(discs) or sorted(discs) != spec['discs']:
        raise ValueError('resource disc provenance mismatch')
    if any(type(r['disc']) is not int or r['disc'] not in (1, 2) or r['sha256'] != sha(data)
           or r['size'] != len(data) for r in records):
        raise ValueError('resource per-disc source identity mismatch')


def font_metrics(root, specs):
    result = {}
    for role, spec in specs.items():
        data = confined_path(root, spec['resource']).read_bytes()
        ctx = context(data, None)
        es = [e for e in ctx['tables']['exports'] if e['path'] == spec['object']]
        if len(es) != 1:
            raise ValueError('exact font object missing')
        e = es[0]
        f = parse_font_payload(ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']], ctx['tables']['names'])
        values = ({r['codepoint']:f['characters'][r['glyph_index']]['USize'] for r in f['remap']}
                  if f['is_remapped'] else {i:g['USize'] for i, g in enumerate(f['characters'])})
        if canonical(values) != spec['advances_sha256']:
            raise ValueError('font advance table changed: '+role)
        if max(g['VSize'] for g in f['characters']) != spec['max_glyph_height']:
            raise ValueError('font line height changed: '+role)
        result[role] = values
    return result


def verify_consumers(profile, root, decoder=None):
    contexts = {}
    count = 0
    extents = {}
    for spec in profile['consumer_contracts']:
        if spec['resource'] not in contexts:
            contexts[spec['resource']] = context(confined_path(root, spec['resource']).read_bytes(), decoder)
        ctx = contexts[spec['resource']]
        es = [e for e in ctx['tables']['exports'] if e['path'] == spec['object']]
        if len(es) != 1:
            raise ValueError('consumer object missing')
        e = es[0]
        payload = ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        if sha(payload) != spec['payload_sha256']:
            raise ValueError('consumer payload mismatch')
        for field in spec.get('fields', []):
            if property_value(payload, ctx['tables']['names'], spec['prefix'], field['path']) != field['expected']:
                raise ValueError('consumer field mismatch')
            if field.get('role') in ('width', 'height'):
                extents.setdefault(spec['family'], {}).setdefault(field['role'], []).append(field['expected'])
        count += 1
    for family in profile['families']:
        actual = extents.get(family['id'], {})
        if 'width' in actual and family['width'] > min(actual['width']) + .001:
            raise ValueError('declared line width exceeds serialized consumer')
        if 'height' in actual:
            height = max(profile['fonts'][r]['max_glyph_height'] for r in family['fonts'])
            if family['max_lines']*height > min(actual['height']) + .001:
                raise ValueError('declared line count exceeds serialized consumer height')
    return dict(packages=len(contexts), contracts=count, actual_extents=extents)


def run(profile, text_root, font_root, consumer_root, output, mode='modified', decoder=None):
    if profile.get('kind') != 'metric-text-layout-revision' or profile.get('schema_version') != 1:
        raise ValueError('text layout profile schema')
    text_root, font_root, consumer_root, output = [Path(x).resolve() for x in (text_root, font_root, consumer_root, output)]
    if output.exists() or any(output.is_relative_to(r) or r.is_relative_to(output) for r in (text_root, font_root, consumer_root)):
        raise ValueError('new disjoint output required')
    if mode not in ('baseline', 'modified'):
        raise ValueError('unknown audit mode')
    fonts = font_metrics(font_root, profile['fonts'])
    consumers = verify_consumers(profile, consumer_root, decoder)
    icons = {key:fonts[role] for key, role in profile['icon_styles'].items()}
    rules = profile['rules']
    text_spec = profile['coalesced']
    raw = confined_path(text_root, text_spec['resource']).read_bytes()
    if sha(raw) != text_spec['sha256']:
        raise ValueError('Coalesced source identity mismatch')
    verify_disc_sources(text_spec, raw)
    entries = extract_entries(parse(raw), text_spec['resource'])
    by_id = {r['id']:r for r in entries}
    if len(entries) != text_spec['entry_count']:
        raise ValueError('Coalesced entry count changed')
    assignment = {}
    for family in profile['families']:
        for identity in family['entry_ids']:
            if identity in assignment or identity not in by_id:
                raise ValueError('duplicate/missing layout target')
            assignment[identity] = family
    fixes = {r['id']:r for r in profile['literal_edits']}
    if len(fixes) != len(profile['literal_edits']):
        raise ValueError('duplicate literal edit')
    planned = []
    checks = []
    unsupported = []
    held = {r['id']:r for r in profile['held_fields']}
    if len(held) != len(profile['held_fields']) or set(held)-set(assignment) or set(held)&set(fixes):
        raise ValueError('invalid explicit held fields')
    for identity, spec in held.items():
        if sha(by_id[identity]['source'].encode()) != spec['source_sha256'] or not spec['reason'].strip():
            raise ValueError('held field identity/reason mismatch')
    options = {r['id']:r for r in profile['reflow_options']}
    if len(options) != len(profile['reflow_options']) or set(options)-set(assignment):
        raise ValueError('invalid per-field reflow options')
    for row in entries:
        identity, source = row['id'], row['source']
        target = source
        if identity in fixes:
            f = fixes[identity]
            if sha(source.encode()) != f['source_sha256']:
                raise ValueError('literal edit source changed')
            target = f['translation']
        family = assignment.get(identity)
        if family and identity not in held:
            tables = [fonts[r] for r in family['fonts']]
            # Explicitly use the maximum native advance across declared routes.
            table = {cp:max(t[cp] for t in tables) for cp in set.intersection(*(set(t) for t in tables))}
            try:
                opts = options.get(identity, {})
                if opts and sha(source.encode()) != opts['source_sha256']:
                    raise ValueError('per-field reflow source identity mismatch')
                active_rules = rules | ({'natural_break_min_fraction':opts['natural_break_min_fraction']}
                                        if 'natural_break_min_fraction' in opts else {})
                candidate = reflow(target, table, family['width'], active_rules, icon_widths=icons,
                                   merge_soft_breaks=opts.get('merge_soft_breaks', False))
                try:
                    before = audit(target, table, family['width'], rules, icon_widths=icons,
                                   max_lines=family.get('max_lines'))
                except ValueError as exc:
                    before = dict(passed=False, reason=str(exc))
                after = audit(candidate, table, family['width'], rules, icon_widths=icons,
                              max_lines=family.get('max_lines'))
                if not after['passed']:
                    raise ValueError('reflow exceeds declared line/height envelope')
                if mode == 'modified':
                    target = candidate
                checks.append(dict(id=identity, family=family['id'], before=before, after=after,
                                   passed=after['passed'] if mode == 'modified' else before['passed']))
            except ValueError as exc:
                unsupported.append(dict(id=identity, family=family['id'], reason=str(exc)))
        if target != source:
            planned.append(dict(id=identity, source_sha256=sha(source.encode()), translation=target,
                                line_break_policy=dict(source_count=source.count('\\n'), target_count=target.count('\\n'))))
    if set(fixes)-set(by_id):
        raise ValueError('literal edit target missing')
    plan = dict(schema_version=1, source_mode='sha256-utf8', resource=text_spec['resource'],
                input_sha256=sha(raw), entries=planned)
    new = rebuild(raw, plan) if mode == 'modified' else raw
    if mode == 'modified':
        reverse = dict(schema_version=1, source_mode='sha256-utf8', resource=text_spec['resource'],
                       input_sha256=sha(new), entries=[dict(id=e['id'], source_sha256=sha(e['translation'].encode()),
                           translation=by_id[e['id']]['source'], line_break_policy=dict(
                               source_count=e['translation'].count('\\n'), target_count=by_id[e['id']]['source'].count('\\n')))
                           for e in planned])
        if rebuild(new, reverse) != raw:
            raise ValueError('Coalesced inverse is not byte identical')
        write(output/'coalesced-rollback-plan.json', json_bytes(reverse))
    write(output/'coalesced-plan.json', json_bytes(plan))
    resources = [dict(path=text_spec['resource'], before_sha256=sha(raw), sha256=sha(new), size=len(new),
                      discs=text_spec['discs'], source_by_disc=text_spec['source_by_disc'])]
    if mode == 'modified':
        write(confined_path(output, 'candidate/'+text_spec['resource']), new)
    subtitle_checks = []
    for spec in profile['subtitles']:
        src = confined_path(text_root, spec['path']).read_bytes()
        if sha(src) != spec['sha256']:
            raise ValueError('subtitle source hash mismatch')
        verify_disc_sources(spec, src)
        _, cues = parse_cues(src)
        if len(cues) != spec['cue_count']:
            raise ValueError('subtitle cue count mismatch')
        changes = []
        for cue in cues:
            before = audit(cue[4], fonts['subtitle'], spec['width'], rules, '<br>', max_lines=spec['max_lines'])
            target = reflow(cue[4], fonts['subtitle'], spec['width'], rules, '<br>')
            after = audit(target, fonts['subtitle'], spec['width'], rules, '<br>', max_lines=spec['max_lines'])
            if not after['passed']:
                raise ValueError('subtitle reflow exceeds declared envelope')
            subtitle_checks.append(dict(resource=spec['path'], start=int(cue[2]), end=int(cue[6]),
                before=before, after=after, passed=after['passed'] if mode == 'modified' else before['passed']))
            if mode == 'modified' and target != cue[4]:
                changes.append(dict(start=int(cue[2]), end=int(cue[6]), source_sha256=sha(cue[4].encode()),
                    translation=target, break_policy=dict(token='<br>', source_count=cue[4].count('<br>'), target_count=target.count('<br>'))))
        if changes:
            sp = dict(schema_version=1, kind='timed-subtitle-text', resource=spec['path'], input_sha256=sha(src), entries=changes)
            new, proof = rebuild_reversible(src, sp)
            write(confined_path(output, 'candidate/'+spec['path']), new)
            write(output/'subtitle-plans'/Path(spec['path']).with_suffix('.json').name, json_bytes(sp))
            resources.append(dict(path=spec['path'], before_sha256=sha(src), sha256=sha(new), size=len(new), proof=proof,
                                  discs=spec['discs'], source_by_disc=spec['source_by_disc']))
    literal_checks = []
    actual_text = rebuild(raw, plan) if mode == 'modified' else raw
    actual = {r['id']:r['source'] for r in extract_entries(parse(actual_text), text_spec['resource'])}
    for identity, fix in fixes.items():
        # Layout may add breaks after a literal edit; compare visible content.
        literal_checks.append(dict(id=identity, passed=actual[identity].replace('\\n', '') == fix['translation'].replace('\\n', '')))
    explicit_findings = []
    for identity, source in actual.items():
        lines = source.split('\\n')
        for n, line in enumerate(lines):
            edge = line.lstrip()[:1]
            paragraph_pause = edge in rules['repeat_pairs'] and (not n or not lines[n-1].strip())
            if n and edge and edge in rules['no_line_start'] and not paragraph_pause:
                explicit_findings.append(dict(id=identity, line=n+1, first=edge))
    report = dict(schema_version=1, mode=mode, profile_content_sha256=canonical(profile), coalesced_fields_scanned=len(entries),
        assigned_fields=len(assignment), layout_checked=len(checks), subtitle_files=len(profile['subtitles']),
        subtitle_cues=len(subtitle_checks), literal_edits=len(fixes), changed_fields=len(planned) if mode == 'modified' else 0,
        failures=len(unsupported)+sum(not r['passed'] for r in checks+subtitle_checks+literal_checks),
        held_fields=list(held.values()), unsupported=unsupported, checks=checks, subtitle_checks=subtitle_checks, literal_checks=literal_checks,
        unassigned_fields=[r['id'] for r in entries if r['id'] not in assignment], consumer_verification=consumers,
        global_explicit_break_scan=dict(fields=len(actual), findings=explicit_findings),
        resources=resources, game_started=False, game_rendering_verified=False)
    write(output/'report.json', json_bytes(report))
    write(output/'manifest.json', json_bytes(dict(schema_version=1, kind='text-layout-revision-build', resources=resources)))
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'text-root', 'font-root', 'consumer-root', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--mode', choices=('baseline', 'modified'), default='modified')
    p.add_argument('--lzx-library', type=Path)
    a = p.parse_args(argv)
    r = run(json.loads(a.profile.read_bytes()), a.text_root, a.font_root, a.consumer_root, a.output, a.mode,
            LzxDecoder(a.lzx_library) if a.lzx_library else None)
    print(json.dumps({k:r[k] for k in ('mode', 'coalesced_fields_scanned', 'assigned_fields', 'layout_checked',
                                       'subtitle_files', 'subtitle_cues', 'literal_edits', 'changed_fields', 'failures')} |
                     dict(unsupported=len(r['unsupported']), held=len(r['held_fields']), game_started=False)))
    return int(r['failures'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())
