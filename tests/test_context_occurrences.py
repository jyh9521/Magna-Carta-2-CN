import copy
import unittest

from test_translation_variant_audit import fixture
from tools.audit_line_context import audit, canonical, digest, lock
from tools.audit_line_context_suite import audit_many
from tools.coalesced import extract_entries, parse


def duplicate_profile(keep_both=False):
    data, plan = fixture('[Scene]\nitem=first\nitem=deleted marker\n')
    for entry in plan['entries']:
        entry['translation'] = 'translated draft'
    if not keep_both:
        plan['entries'].pop()
    rows = extract_entries(parse(data), 'fixture')
    selected = rows if keep_both else rows[:1]
    profile = dict(
        schema_version=1, kind='source-locked-context-observations',
        resource='fixture', input_sha256=digest(data),
        plan_canonical_sha256=canonical(plan), human_finalized=False,
        runtime_layout_approved=False,
        scopes=[dict(document='fixture.int', section='Scene', keys=['item'],
                     complete_section=False, reason='Exact physical occurrence',
                     occurrences={'item': [1, 2] if keep_both else [1]})],
        entries=[lock(row, plan['entries'][i]['translation'])
                 for i, row in enumerate(selected)], protected_breaks=[])
    return data, plan, profile, rows


class ContextOccurrenceTests(unittest.TestCase):
    def test_planned_first_and_unplanned_second_are_distinct(self):
        data, plan, profile, rows = duplicate_profile()
        before = copy.deepcopy((plan, profile))
        report = audit(data, plan, profile)
        self.assertEqual(report['context_entries'], 1)
        self.assertEqual(report['context'][0]['next_id'], rows[1]['id'])
        self.assertEqual(report['context'][0]['occurrence'], 1)
        self.assertEqual((plan, profile), before)
        self.assertFalse(report['human_finalized'])
        self.assertFalse(report['runtime_layout_approved'])

    def test_second_occurrence_can_be_selected_without_first(self):
        data, plan, profile, rows = duplicate_profile(True)
        profile['scopes'][0]['occurrences'] = {'item': [2]}
        profile['entries'] = profile['entries'][1:]
        report = audit(data, plan, profile)
        self.assertEqual(report['context'][0]['id'], rows[1]['id'])
        self.assertEqual(report['context'][0]['previous_id'], rows[0]['id'])

    def test_absent_filter_keeps_legacy_all_occurrences_contract(self):
        data, plan, profile, rows = duplicate_profile()
        profile['scopes'][0].pop('occurrences')
        with self.assertRaisesRegex(ValueError, 'unplanned original'):
            audit(data, plan, profile)

    def test_invalid_filter_types_values_and_stale_occurrences_rejected(self):
        values = [None, [], {}, 'item', {'missing': [1]}, {'item': []},
                  {'item': [0]}, {'item': [-1]}, {'item': [True]},
                  {'item': [1.0]}, {'item': ['1']}, {'item': [1, 1]},
                  {'item': [3]}, {'item': [1, 3]}]
        for value in values:
            data, plan, profile, rows = duplicate_profile()
            profile['scopes'][0]['occurrences'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                audit(data, plan, profile)

    def test_complete_section_cannot_hide_an_occurrence_filter(self):
        data, plan, profile, rows = duplicate_profile()
        profile['scopes'][0].update(complete_section=True)
        profile['scopes'][0].pop('keys')
        with self.assertRaisesRegex(ValueError, 'complete section'):
            audit(data, plan, profile)

    def test_explicit_filter_does_not_approve_unplanned_second(self):
        data, plan, profile, rows = duplicate_profile()
        profile['scopes'][0]['occurrences'] = {'item': [2]}
        with self.assertRaisesRegex(ValueError, 'unplanned original'):
            audit(data, plan, profile)

    def test_expected_occurrence_identity_and_hash_are_still_required(self):
        data, plan, profile, rows = duplicate_profile(True)
        profile['scopes'][0]['occurrences'] = {'item': [2]}
        profile['entries'] = profile['entries'][:1]
        with self.assertRaisesRegex(ValueError, 'membership/order/hash'):
            audit(data, plan, profile)

    def test_overlap_rejected_and_source_order_not_filter_order(self):
        data, plan, profile, rows = duplicate_profile(True)
        profile['scopes'][0]['occurrences'] = {'item': [2, 1]}
        report = audit(data, plan, profile)
        self.assertEqual([e['id'] for e in report['context']],
                         [e['id'] for e in rows])
        with self.assertRaisesRegex(ValueError, 'overlapping context profiles'):
            audit_many(data, plan, [profile, profile])
