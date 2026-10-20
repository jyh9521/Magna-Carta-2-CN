"""Read-only exact-source variants with source-and-draft-locked dispositions."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from tools.build_coalesced import rebuild
from tools.coalesced import extract_entries, parse, write_json_atomic


def digest(value):
    return hashlib.sha256(value).hexdigest()


def audit(data, plan, review=None):
    # Reuse the existing full source/token validation; never save rebuilt bytes.
    rebuild(data, plan)
    resource = plan['resource']
    source_hash = digest(data)
    rows = {r['id']: r for r in extract_entries(parse(data), resource)}
    groups = defaultdict(list)
    for e in plan['entries']:
        r = rows[e['id']]
        key = (r['embedded_path'], r['section'], digest(r['source'].encode('utf8')))
        groups[key].append(dict(id=r['id'], key=r['key'], occurrence=r['occurrence'],
                                translation_sha256=digest(e['translation'].encode('utf8'))))
    candidates = []
    for (doc, section, sha), entries in sorted(groups.items()):
        if len({e['translation_sha256'] for e in entries}) > 1:
            candidates.append(dict(embedded_path=doc, section=section, source_sha256=sha,
                                   entries=sorted(entries, key=lambda e: e['id']),
                                   disposition='pending-context-review'))
    if review is not None:
        if (not isinstance(review, dict)
                or type(review.get('schema_version')) is not int or review['schema_version'] != 1
                or review.get('resource') != resource or review.get('input_sha256') != source_hash
                or not isinstance(review.get('groups'), list)):
            raise ValueError('review source envelope mismatch')
        by_key = {(c['embedded_path'], c['section'], c['source_sha256']): c for c in candidates}
        seen = set()
        for decision in review['groups']:
            key = (decision['embedded_path'], decision['section'], decision['source_sha256'])
            if key not in by_key or key in seen:
                raise ValueError('duplicate or stale review group')
            seen.add(key)
            c = by_key[key]
            locks = {e['id']: e['translation_sha256'] for e in decision['entries']}
            actual = {e['id']: e['translation_sha256'] for e in c['entries']}
            if len(locks) != len(decision['entries']) or locks != actual:
                raise ValueError('review draft membership/hash mismatch')
            if (decision.get('disposition') != 'context-variant-retained'
                    or not isinstance(decision.get('reason'), str) or not decision['reason'].strip()):
                raise ValueError('invalid context disposition')
            c['disposition'] = decision['disposition']
            c['reason'] = decision['reason']
    pending = sum(c['disposition'] == 'pending-context-review' for c in candidates)
    return dict(schema_version=1, resource=resource, input_sha256=source_hash,
                translated_entries=len(plan['entries']), groups=candidates,
                pending_groups=pending, context_variant_groups=len(candidates) - pending,
                policy='no translation edits; no reviewer/status upgrade; context review only')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--review-profile', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('output must be new')
        paths = [args.source, args.plan] + ([args.review_profile] if args.review_profile else [])
        if any(args.output.resolve() == p.resolve() for p in paths):
            raise ValueError('output aliases an input')
        originals = {p: p.read_bytes() for p in paths}
        plan = json.loads(originals[args.plan])
        review = json.loads(originals[args.review_profile]) if args.review_profile else None
        report = audit(originals[args.source], plan, review)
        if any(p.read_bytes() != b for p, b in originals.items()):
            raise ValueError('input changed during audit')
        write_json_atomic(args.output, report)
        print(f"PASS variants: {len(report['groups'])} groups, {report['pending_groups']} pending, "
              f"{report['context_variant_groups']} context variants; translations unchanged")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'ERROR: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
