"""Plan whole unobserved scene cohorts in original container order, never lexical order."""
import argparse
import json
from pathlib import Path
from .audit_line_context import canonical, digest, lock
from .audit_line_context_suite import audit_many
from .build_coalesced import resolve_changes
from .coalesced import parse, extract_entries
from .font_binding_plan import parse_json_object


def next_scenes(rows, document, planned_ids, observed_ids, target_entries=180):
    if type(target_entries) is not int or not 1 <= target_entries <= 300:
        raise ValueError('scene target bound')
    if not isinstance(document, str) or not document:
        raise ValueError('scene document required')
    ids = [row['id'] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate source identity')
    planned_ids, observed_ids = set(planned_ids), set(observed_ids)
    if not planned_ids <= set(ids) or not observed_ids <= planned_ids:
        raise ValueError('stale planned or observed identity')
    groups = {}
    for row in rows:
        if row['embedded_path'] == document:
            groups.setdefault(row['section'], []).append(row)
    if not groups:
        raise ValueError('scene document not found')
    selected, deferred, planned_count = [], [], 0
    for section, hits in groups.items():
        planned = {row['id'] for row in hits if row['id'] in planned_ids}
        pending = planned - observed_ids
        unknown = [row['id'] for row in hits if row['id'] not in planned_ids]
        if unknown:
            deferred.append(dict(section=section, unplanned_original_ids=unknown))
        if pending and planned & observed_ids:
            raise ValueError('partially observed planned scene needs explicit review')
        if pending and planned_count < target_entries:
            selected.append(dict(section=section, source_entries=len(hits),
                                 planned_drafts=len(planned), unplanned_original_ids=unknown))
            planned_count += len(planned)
    return dict(schema_version=1, kind='source-order-scene-context-queue', document=document,
                target_entries=target_entries, source_order_sections=selected,
                scene_entries=sum(s['source_entries'] for s in selected),
                planned_scene_entries=planned_count, deferred_unplanned_sections=deferred,
                status='source-plan-preflight-only; not observed or counted',
                translation_edits=0, human_finalized=False, runtime_layout_approved=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'plan', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--profile', type=Path, action='append', required=True)
    parser.add_argument('--document', required=True)
    parser.add_argument('--target-entries', type=int, default=180)
    args = parser.parse_args(argv)
    try:
        if not 1 <= len(args.profile) <= 16:
            raise ValueError('context profile suite bound')
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('scene output must be new')
        paths = [args.source, args.plan] + args.profile
        before = [path.read_bytes() for path in paths]
        data, plan = before[0], parse_json_object(before[1])
        profiles = [parse_json_object(raw) for raw in before[2:]]
        observed = audit_many(data, plan, profiles)
        changes = {row['id']: row for row in resolve_changes(data, plan)['entries']}
        rows = extract_entries(parse(data), plan['resource'])
        report = next_scenes(rows, args.document, changes,
                             {row['id'] for row in observed['context']}, args.target_entries)
        sections = {row['section'] for row in report['source_order_sections']}
        report.update(input_sha256=digest(data), plan_canonical_sha256=canonical(plan),
                      profiles=observed['profiles'], source_order_locks=[lock(row, changes[row['id']]['translation'])
                      for row in rows if row['embedded_path'] == args.document and row['section'] in sections and row['id'] in changes])
        if any(path.read_bytes() != raw for path, raw in zip(paths, before)):
            raise ValueError('scene input changed')
        encoded = (json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + '\n').encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as stream:
            stream.write(encoded)
        if args.output.read_bytes() != encoded:
            raise ValueError('scene output reopening mismatch')
        print(json.dumps({key: report[key] for key in ('scene_entries', 'planned_scene_entries', 'translation_edits')}, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('ERROR: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
