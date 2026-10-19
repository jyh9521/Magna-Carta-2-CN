"""Prepare shared, source-verified translation queues without merging discs.

Only exact resource + container SHA256 identities share work. Domain hints and
term substring hits are triage aids, never runtime or semantic evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import tempfile

try:
    from .export_translation_catalogs import export_sources, digest, write_json
    from .sample_catalog import import_plan
    from .validate_catalog import validate
except ImportError:
    from export_translation_catalogs import export_sources, digest, write_json
    from sample_catalog import import_plan
    from validate_catalog import validate


def read_locked(root, spec, snapshots):
    name = spec['path']
    if (not isinstance(name, str) or '\\' in name or ':' in name
            or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError('invalid dependency path')
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('dependency escapes root')
    raw = path.read_bytes()
    if digest(raw) != spec['sha256']:
        raise ValueError('dependency SHA256 mismatch: ' + name)
    snapshots[path] = raw
    return json.loads(raw)


def prepare(root, workflow, output):
    root, output = Path(root).resolve(), Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError('output must be new')
    if workflow.get('schema_version') != 1:
        raise ValueError('unsupported workflow schema')
    snapshots = {}
    profile = read_locked(root, workflow['extraction_profile'], snapshots)
    rules = read_locked(root, workflow['style_rules'], snapshots)
    terms = read_locked(root, workflow['terms'], snapshots)['terms']
    # Exporter verifies every real container and byte-identical roundtrip.
    # Track inputs too, so changes during queue preparation prevent publication.
    for source in profile['sources']:
        read_path = root / source['path']
        if not read_path.resolve().is_relative_to(root):
            raise ValueError('source escapes root')
        if output.resolve() == read_path.resolve() or output.resolve() in read_path.resolve().parents:
            raise ValueError('output contains input')
        snapshots[read_path] = read_path.read_bytes()
    plans = {}
    for batch in workflow['batches']:
        plan = read_locked(root, batch['plan'], snapshots)
        review = read_locked(root, batch['review'], snapshots)
        if plan.get('source_mode') != 'sha256-utf8' or review.get('status') != 'draft':
            raise ValueError('expected source-hash plan and explicit draft review')
        kind_rows = review['entries']
        kinds = {e['id']: e['text_kind'] for e in kind_rows}
        if len(kinds) != len(kind_rows) or set(kinds) != {e['id'] for e in plan['entries']}:
            raise ValueError('review IDs must exactly match plan IDs')
        identity = (plan['resource'], plan['input_sha256'])
        edits = plans.setdefault(identity, {})
        for edit in plan['entries']:
            if edit['id'] in edits:
                raise ValueError('overlapping batches require explicit resolution')
            if not edit['translation'].strip() or kinds[edit['id']] == 'unclassified':
                raise ValueError('translated entry needs nonempty translation and classification')
            edits[edit['id']] = (edit, kinds[edit['id']])
    primary = workflow['primary_resource']
    if primary not in {s['resource'] for s in profile['sources'] if s['role'] == 'translation'}:
        raise ValueError('primary resource not in translation profile')
    # Build privately and rename only after every check succeeds. No partial
    # workspace is published when a plan is stale, malformed or unknown.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.translation-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'workspace'
        manifest = export_sources(root, profile, stage / 'source')
        identities = {(g['resource'], g['sha256']) for g in manifest['groups']}
        if not set(plans) <= identities:
            raise ValueError('batch refers to unknown source identity')
        source_index = {(s['resource'], s['sha256']): root / s['path'] for s in profile['sources']}
        groups, term_hits = [], []
        for group in manifest['groups']:
            identity = (group['resource'], group['sha256'])
            edits = plans.get(identity, {})
            merged, selected, seen = [], [], set()
            counters = Counter()
            catalogs = []
            all_rows = []
            for info in group['catalogs']:
                catalog = json.loads((stage / 'source' / info['path']).read_bytes())
                for row in catalog['entries']:
                    seen.add(row['id'])
                    if row['id'] in edits:
                        edit, kind = edits[row['id']]
                        if row['source_sha256'] != edit['source_sha256']:
                            raise ValueError('batch source value SHA256 mismatch')
                        if edit['translation'] == row['source']:
                            raise ValueError('unchanged source is not a translation')
                        row.update(translation=edit['translation'], status='draft', text_kind=kind)
                        if 'line_break_policy' in edit:
                            row['line_break_policy'] = edit['line_break_policy']
                        merged.append(edit)
                        selected.append(row)
                        queue = 'translated-draft'
                    elif group['resource'] != primary:
                        queue = 'alternate-resource-review'
                    elif row['domain_hint'] == 'editor':
                        queue = 'editor-reference'
                    elif row['domain_hint'] == 'unclassified':
                        queue = 'context-review'
                    else:
                        queue = 'translation-candidate'
                    row['work_queue'] = queue
                    counters[queue] += 1
                    all_rows.append(row)
                errors = validate(catalog, rules)
                if errors:
                    raise ValueError('; '.join(errors))
                target = 'work/' + info['path']
                write_json(stage / target, catalog)
                catalogs.append(dict(info, work_path=target))
            if not set(edits) <= seen:
                raise ValueError('batch contains unknown ID')
            plan_path = None
            if merged:
                selected_catalog = dict(schema_version=1, kind='selected-coalesced-catalog',
                    resource=group['resource'], input_sha256=group['sha256'], entries=selected)
                plan = import_plan(source_index[identity].read_bytes(), selected_catalog, rules)
                # import_plan rechecks source/selector/markers and rebuilds.
                plan_path = 'plans/' + group['sha256'] + '.json'
                write_json(stage / plan_path, plan)
            for term in terms:
                if term['resource'] != group['resource']:
                    continue
                exact = [r for r in all_rows if r['source'] == term['source']]
                occurrences = [r for r in all_rows if term['source'] in r['source']]
                source_row = next((r for r in all_rows if r['id'] == term['source_string_id']), None)
                if source_row is None or term['source'] not in source_row['source']:
                    raise ValueError('term source ID or source spelling mismatch: ' + term['id'])
                term_hits.append(dict(term_id=term['id'], review_status=term['review_status'],
                    resource=group['resource'], container_sha256=group['sha256'],
                    exact_ids=[r['id'] for r in exact],
                    substring_ids=[r['id'] for r in occurrences],
                    note='substring hits are review leads, not semantic matches or replacements'))
            groups.append(dict(resource=group['resource'], sha256=group['sha256'],
                discs=sorted(group['discs']), entries=len(all_rows), queues=dict(sorted(counters.items())),
                catalogs=catalogs, translated_plan=plan_path))
        matched_terms = {hit['term_id'] for hit in term_hits}
        if len(matched_terms) != len(terms):
            raise ValueError('duplicate term ID or missing term resource')
        report = dict(schema_version=1, primary_resource=primary, groups=groups,
            catalogs=manifest['catalog_count'], unique_entries=manifest['unique_catalog_entries'],
            physical_disc_entries=sum(s['entries'] for s in manifest['sources'] if s['role']=='translation'),
            terms=len(terms), terms_reviewed=sum(t['review_status']!='candidate' for t in terms),
            scope='Coalesced only; queue labels are triage, not player visibility or runtime proof',
            excluded_scope=['Movies subtitles', 'xxx embedded text', 'hard-coded and image text'],
            inputs={str(p.relative_to(root)).replace('\\', '/'): digest(raw) for p, raw in snapshots.items()})
        write_json(stage / 'term-concordance.json', dict(schema_version=1, entries=term_hits))
        write_json(stage / 'manifest.json', report)
        for path, raw in snapshots.items():
            if path.read_bytes() != raw:
                raise ValueError('input changed during workspace preparation')
        stage.rename(output)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--workflow', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare(args.source_root, json.loads(args.workflow.read_bytes()), args.output)
        print(json.dumps(dict(catalogs=result['catalogs'], unique_entries=result['unique_entries'],
            physical_disc_entries=result['physical_disc_entries'],
            translated=sum(g['queues'].get('translated-draft', 0) for g in result['groups']),
            terms=result['terms'], game_started=False), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('ERROR: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
