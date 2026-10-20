"""Hash-indexed context pages; never relax the original single-suite contract."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re

from .audit_line_context import canonical, digest
from .audit_line_context_suite import MAX_PROFILES, audit_many
from .coalesced import extract_entries, parse
from .font_binding_plan import parse_json_object


MAX_PAGES = 16
MAX_MEMBERS = 16000  # Original suite's 16 * 1000 total-member budget.


def audit_pages(data, plan, pages):
    """Each page still passes audit_many; overlap across pages is an error.

    Pages are explicit, not recursive, and may not add to the total row budget.
    Source order and the one global policy set determine the combined report.
    """
    if not isinstance(pages, list) or not 1 <= len(pages) <= MAX_PAGES:
        raise ValueError('context archive page bound')
    contexts, protected, provenance, profiles = {}, {}, [], []
    for page in pages:
        result = audit_many(data, plan, page)
        for row in result['context']:
            if row['id'] in contexts:
                raise ValueError('overlapping context pages')
            contexts[row['id']] = row
        if len(contexts) > MAX_MEMBERS:
            raise ValueError('context archive total member bound')
        protected.update({row['id']: row for row in result['protected_breaks']})
        provenance.append(dict(profile_start=len(profiles),
                               profile_count=len(result['profiles']),
                               context_entries=result['context_entries']))
        profiles.extend(result['profiles'])
    order = [r['id'] for r in extract_entries(parse(data), plan['resource'])]
    result['kind'] = 'read-only-line-context-archive-audit'
    result['pages'] = provenance
    result['profiles'] = profiles
    result['context'] = [contexts[i] for i in order if i in contexts]
    if len(result['context']) != len(contexts):
        raise ValueError('context archive source identity mismatch')
    result['protected_breaks'] = [protected[i] for i in order if i in protected]
    result['context_entries'] = len(contexts)
    for row in result['policies']:
        row['context_observed'] = row['id'] in contexts
    result['context_observed_policies'] = sum(
        r['context_observed'] for r in result['policies'])
    result['pending_context_policies'] = (
        result['policy_entries'] - result['context_observed_policies'])
    return result


def load_pages(index, root, data, plan):
    """Return validated page objects and exact input snapshots for CLI rechecks."""
    if (type(index.get('schema_version')) is not int or index['schema_version'] != 1
            or index.get('kind') != 'source-locked-context-archive'
            or index.get('resource') != plan['resource']
            or index.get('input_sha256') != digest(data)
            or index.get('plan_canonical_sha256') != canonical(plan)
            or index.get('human_finalized') is not False
            or index.get('runtime_layout_approved') is not False):
        raise ValueError('context archive identity or approval mismatch')
    refs = index.get('pages')
    if not isinstance(refs, list) or not 1 <= len(refs) <= MAX_PAGES:
        raise ValueError('context archive page bound')
    pages, snapshots, names, paths = [], [], set(), set()
    root = Path(root).resolve()
    for page in refs:
        name = page.get('id')
        if (not isinstance(name, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', name)
                or name in names):
            raise ValueError('invalid or duplicate context page id')
        names.add(name)
        profiles = page.get('profiles')
        if not isinstance(profiles, list) or not 1 <= len(profiles) <= MAX_PROFILES:
            raise ValueError('context profile suite bound')
        objects = []
        for ref in profiles:
            text = ref.get('path')
            if (not isinstance(text, str) or not text or '\\' in text or ':' in text
                    or '\x00' in text or any(p in ('', '.', '..') for p in text.split('/'))
                    or PurePosixPath(text).is_absolute()):
                raise ValueError('invalid context profile path')
            path = root / text
            if (not path.resolve().is_relative_to(root)
                    or any(p.is_symlink() for p in [path, *path.parents] if p != root)):
                raise ValueError('context profile path escapes or aliases root')
            path = path.resolve()
            if path in paths:
                raise ValueError('duplicate context profile path')
            paths.add(path)
            raw = path.read_bytes()
            if ref.get('sha256') != digest(raw):
                raise ValueError('context profile byte hash mismatch')
            objects.append(parse_json_object(raw))
            snapshots.append((path, raw))
        pages.append(objects)
    return pages, snapshots


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'plan', 'index', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('context output must be new')
        snapshots = [(p, p.read_bytes()) for p in (args.source, args.plan, args.index)]
        data = snapshots[0][1]
        plan = parse_json_object(snapshots[1][1])
        index = parse_json_object(snapshots[2][1])
        pages, members = load_pages(index, args.index.parent, data, plan)
        snapshots += members
        report = audit_pages(data, plan, pages)
        if any(p.read_bytes() != raw for p, raw in snapshots):
            raise ValueError('context archive input changed')
        encoded = (json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as stream:
            stream.write(encoded)
        if args.output.read_bytes() != encoded:
            raise ValueError('context output reopening mismatch')
        print(json.dumps({k: report[k] for k in (
            'context_entries', 'context_observed_policies', 'pending_context_policies',
            'pending_runtime_layout_policies', 'translation_edits')}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print('ERROR: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
