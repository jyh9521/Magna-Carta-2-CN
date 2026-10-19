"""Export an editable selected Coalesced catalog, then import a guarded plan.

Full source text stays in local build output. Public plans need only stable IDs,
source hashes and translations. Neither operation deploys or starts a game.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .build_coalesced import rebuild, resolve_changes, sha256
    from .coalesced import extract_entries, parse, MAX_BYTES
    from .font_binding_plan import parse_json_object
    from .validate_catalog import validate
except ImportError:
    from build_coalesced import rebuild, resolve_changes, sha256
    from coalesced import extract_entries, parse, MAX_BYTES
    from font_binding_plan import parse_json_object
    from validate_catalog import validate

SELECTOR = ('embedded_path', 'section', 'key', 'occurrence')


def export_catalog(data, plan):
    resolved = resolve_changes(data, plan)
    rebuild(data, resolved)
    rows = {r['id']: r for r in extract_entries(parse(data), plan['resource'])}
    selected = []
    for edit in resolved['entries']:
        row = dict(rows[edit['id']], translation=edit['translation'], status='draft')
        row['source_sha256'] = sha256(row['source'].encode('utf8'))
        if 'line_break_policy' in edit:row['line_break_policy']=edit['line_break_policy']
        selected.append(row)
    if not selected:
        raise ValueError('selected catalog must not be empty')
    return dict(schema_version=1, kind='selected-coalesced-catalog',
                input_sha256=sha256(data), resource=plan['resource'], entries=selected)


def import_plan(data, catalog, style_rules=None):
    if (catalog.get('kind') != 'selected-coalesced-catalog'
            or type(catalog.get('schema_version')) is not int
            or catalog.get('input_sha256') != sha256(data)):
        raise ValueError('catalog schema or input SHA256 mismatch')
    errors = validate(catalog, style_rules)
    if errors:
        raise ValueError('; '.join(errors))
    resource = catalog.get('resource')
    if not isinstance(resource, str) or not resource or not catalog['entries']:
        raise ValueError('catalog resource and nonempty entries required')
    rows = {r['id']: r for r in extract_entries(parse(data), resource)}
    edits = []
    for entry in catalog['entries']:
        row = rows.get(entry['id'])
        if (row is None or entry['resource'] != resource or entry['source'] != row['source']
                or any(type(entry.get(k)) is not type(row[k]) or entry[k] != row[k] for k in SELECTOR)
                or entry.get('source_sha256') != sha256(row['source'].encode('utf8'))):
            raise ValueError('catalog ID, selector or source mismatch')
        if not entry['translation'].strip():
            raise ValueError('unexpected empty translation')
        edit=dict(id=entry['id'], source_sha256=entry['source_sha256'], translation=entry['translation'])
        if 'line_break_policy' in entry:edit['line_break_policy']=entry['line_break_policy']
        edits.append(edit)
    plan = dict(schema_version=1, resource=resource, input_sha256=sha256(data),
                source_mode='sha256-utf8', entries=edits)
    rebuild(data, plan)  # exact protected-token sequence, encoding, every unedited value
    return plan


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('export', 'import'))
    p.add_argument('source', type=Path)
    p.add_argument('document', type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--style-rules', type=Path)
    a = p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in (a.source.resolve(), a.document.resolve()):
            raise ValueError('output must be new and distinct from inputs')
        if max(a.source.stat().st_size, a.document.stat().st_size) > MAX_BYTES:
            raise ValueError('input size limit')
        data, document = a.source.read_bytes(), a.document.read_bytes()
        parsed = parse_json_object(document)
        rules = parse_json_object(a.style_rules.read_bytes()) if a.style_rules else None
        result = export_catalog(data, parsed) if a.mode == 'export' else import_plan(data, parsed, rules)
        if a.source.read_bytes() != data or a.document.read_bytes() != document:
            raise ValueError('input changed during catalog operation')
        raw = (json.dumps(result, ensure_ascii=True, indent=2) + '\n').encode()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('xb') as f:
            f.write(raw)
        if a.output.read_bytes() != raw:
            raise ValueError('catalog output reopening mismatch')
        print(json.dumps(dict(mode=a.mode, entries=len(result['entries']), source_unchanged=True, game_started=False), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('ERROR: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
