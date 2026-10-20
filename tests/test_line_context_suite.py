import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_line_context_audit import setup
from tools.audit_line_context import audit, canonical, digest
from tools.audit_line_context_suite import audit_many, main


def split():
    data, plan, profile = setup()
    first, second = copy.deepcopy(profile), copy.deepcopy(profile)
    first['scopes'] = first['scopes'][:1]
    first['entries'] = first['entries'][:2]
    first['protected_breaks'] = []
    second['scopes'] = second['scopes'][1:]
    second['entries'] = second['entries'][2:]
    return data, plan, profile, [first, second]


class LineContextSuiteTests(unittest.TestCase):
    def test_union_matches_original_observations_without_edits(self):
        data, plan, profile, parts = split()
        before = copy.deepcopy((plan, parts))
        original = audit(data, plan, profile)
        combined = audit_many(data, plan, parts)
        self.assertEqual(combined.pop('kind'), 'read-only-line-context-suite-audit')
        self.assertEqual(len(combined.pop('profiles')), 2)
        original.pop('kind')
        self.assertEqual(combined, original)
        self.assertEqual((plan, parts), before)

    def test_source_order_not_profile_order(self):
        data, plan, profile, parts = split()
        left, right = audit_many(data, plan, parts), audit_many(data, plan, parts[::-1])
        self.assertNotEqual(left.pop('profiles'), right.pop('profiles'))
        self.assertEqual(left, right)

    def test_overlap_is_error_not_silent_deduplication(self):
        data, plan, profile, parts = split()
        with self.assertRaisesRegex(ValueError, 'overlapping context profiles'):
            audit_many(data, plan, parts + [parts[0]])

    def test_single_profile_old_audit_unchanged(self):
        data, plan, profile, parts = split()
        baseline = audit(data, plan, profile)
        suite = audit_many(data, plan, [profile])
        suite.pop('profiles');suite['kind'] = baseline['kind']
        self.assertEqual(suite, baseline)

    def test_profile_count_and_types_are_bounded(self):
        data, plan, profile, parts = split()
        for value in (None, [], (), [profile] * 17, [None]):
            with self.subTest(value=type(value)), self.assertRaises(ValueError):
                audit_many(data, plan, value)

    def test_existing_scope_and_member_guards_not_raised(self):
        data, plan, profile, parts = split()
        profile['scopes'] = profile['scopes'] * 17
        with self.assertRaisesRegex(ValueError, 'scope bound'):
            audit_many(data, plan, [profile])
        from test_translation_variant_audit import fixture
        data, plan = fixture('[Scene]\n' + ''.join(f'k{i}=word\n' for i in range(1001)))
        profile['scopes'] = profile['scopes'][:1]
        profile.update(input_sha256=digest(data), plan_canonical_sha256=canonical(plan))
        with self.assertRaisesRegex(ValueError, 'cohort bound'):
            audit_many(data, plan, [profile])

    def test_stale_identity_draft_and_approval_rejected_per_profile(self):
        for key, value in (('input_sha256', '0' * 64), ('plan_canonical_sha256', '0' * 64),
                           ('human_finalized', True), ('runtime_layout_approved', True)):
            data, plan, profile, parts = split();parts[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit_many(data, plan, parts)
        data, plan, profile, parts = split()
        parts[1]['entries'][0]['translation_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'membership/order/hash'):
            audit_many(data, plan, parts)

    def test_no_runtime_or_human_approval_and_no_double_count(self):
        data, plan, profile, parts = split();report = audit_many(data, plan, parts)
        self.assertEqual((report['context_entries'], report['context_observed_policies'],
                          report['pending_context_policies'], report['pending_runtime_layout_policies']), (3, 1, 0, 1))
        for key in ('human_finalized', 'runtime_layout_approved', 'game_rendering_verified'):
            self.assertIs(report[key], False)
        self.assertEqual(report['translation_edits'], 0)

    def test_cli_repeatable_profiles_and_readonly_failure(self):
        data, plan, profile, parts = split()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);source = root/'source';p = root/'plan';out = root/'out'
            source.write_bytes(data);p.write_text(json.dumps(plan), encoding='utf8')
            args = ['--source', str(source), '--plan', str(p), '--output', str(out)]
            for n, part in enumerate(parts):
                path = root/str(n);path.write_text(json.dumps(part), encoding='utf8')
                args += ['--profile', str(path)]
            snapshots = {path: path.read_bytes() for path in root.iterdir()}
            self.assertEqual(main(args), 0)
            self.assertEqual(json.loads(out.read_bytes())['context_entries'], 3)
            result = out.read_bytes();self.assertEqual(main(args), 2)
            self.assertEqual(out.read_bytes(), result)
            out.unlink()
            self.assertEqual(main(args + ['--profile', str(root/'0')]), 2)
            self.assertFalse(out.exists())
            self.assertTrue(all(path.read_bytes() == raw for path, raw in snapshots.items()))

    def test_cli_bound_before_reading_missing_inputs(self):
        args = ['--source', 'absent', '--plan', 'absent', '--output', 'absent']
        with patch('pathlib.Path.read_bytes', side_effect=AssertionError('unexpected read')):
            self.assertEqual(main(args + ['--profile', 'absent'] * 17), 2)
