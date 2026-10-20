"""Aggregate bounded, disjoint context cohorts without approving runtime layout."""
import argparse
import json
from pathlib import Path

from .audit_line_context import audit, canonical
from .coalesced import extract_entries, parse
from .font_binding_plan import parse_json_object


MAX_PROFILES = 16


def audit_many(data, plan, profiles):
    """Validate every original profile contract, then union by source identity.

    Profile order is provenance only; context and functional controls follow the
    original container order. Overlap is an error, never a deduplication hint.
    Single-profile audit() and its 32-scope/1000-member bounds are unchanged.
    """
    if not isinstance(profiles, list) or not 1 <= len(profiles) <= MAX_PROFILES:
        raise ValueError('context profile suite bound')
    contexts = {}
    protected = {}
    provenance = []
    result = None
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError('context profile must be an object')
        report = audit(data, plan, profile)
        for row in report['context']:
            if row['id'] in contexts:
                raise ValueError('overlapping context profiles')
            contexts[row['id']] = row
        protected.update({row['id']: row for row in report['protected_breaks']})
        provenance.append(dict(profile_canonical_sha256=canonical(profile),
                               scope_count=len(profile['scopes']),
                               context_entries=report['context_entries']))
        result = report
    order = [row['id'] for row in extract_entries(parse(data), plan['resource'])]
    result['kind'] = 'read-only-line-context-suite-audit'
    result['profiles'] = provenance
    result['context'] = [contexts[i] for i in order if i in contexts]
    result['protected_breaks'] = [protected[i] for i in order if i in protected]
    result['context_entries'] = len(contexts)
    for row in result['policies']:
        row['context_observed'] = row['id'] in contexts
    observed = sum(row['context_observed'] for row in result['policies'])
    result['context_observed_policies'] = observed
    result['pending_context_policies'] = result['policy_entries'] - observed
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'plan', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--profile', type=Path, action='append', required=True)
    args = parser.parse_args(argv)
    try:
        if not 1 <= len(args.profile) <= MAX_PROFILES:
            raise ValueError('context profile suite bound')
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('context output must be new')
        paths = [args.source, args.plan] + args.profile
        before = [path.read_bytes() for path in paths]
        report = audit_many(before[0], parse_json_object(before[1]),
                            [parse_json_object(raw) for raw in before[2:]])
        if any(path.read_bytes() != raw for path, raw in zip(paths, before)):
            raise ValueError('context input changed')
        encoded = (json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as stream:
            stream.write(encoded)
        if args.output.read_bytes() != encoded:
            raise ValueError('context output reopening mismatch')
        print(json.dumps({key: report[key] for key in (
            'context_entries', 'context_observed_policies', 'pending_context_policies',
            'pending_runtime_layout_policies', 'translation_edits')}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('ERROR: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
