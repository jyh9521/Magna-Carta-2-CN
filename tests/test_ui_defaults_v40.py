"""Portable evidence/translation-plan contracts; original game files not needed."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

from tools.rebuild_tagged_strings import NESTED_PROFILE, _plan

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/name).read_bytes())


class UIDefaultClosureTests(unittest.TestCase):
    def test_all_31_prior_candidates_are_resolved_by_exact_owner_and_field(self):
        previous = read('locales/zh-Hans/coverage-closure-v39.json')['ui_defaults']
        audit = read('locales/zh-Hans/ui-defaults-audit-v40.json')
        self.assertEqual(len(audit['fields']), 31)
        self.assertEqual({r['id'] for r in audit['fields']}, {r['id'] for r in previous})
        self.assertEqual(len({r['object_path'] for r in audit['fields']}), 31)
        self.assertTrue(all(r['disposition'] == 'clear-dynamic-development-placeholder' for r in audit['fields']))
        self.assertTrue(all(r['after'] == '' and r['after_serialized_hex'] == '00000000' for r in audit['fields']))

    def test_plan_has_only_reviewed_empty_defaults_no_ids_or_dynamic_text_edits(self):
        p = read('locales/zh-Hans/ui-defaults-v40.json'); _plan(p)
        self.assertEqual(p['profile'], NESTED_PROFILE); self.assertEqual(len(p['objects']), 31)
        values = Counter()
        for obj in p['objects']:
            self.assertEqual(len(obj['fields']), 1)
            field = obj['fields'][0]; values[field['before']] += 1
            self.assertEqual(field['before_encoding'], 'ascii'); self.assertEqual(field['after'], '')
            self.assertIn([part['name'] for part in field['path']],
                          [['DataSource', 'MarkupString'], ['CaptionDataSource', 'MarkupString']])
            arrays = [[part['name'] for part in path] for path in obj['object_reference_arrays']]
            self.assertEqual(arrays, [['InactiveStates'], ['Children']] if field['before'] == 'NO DATA' else [['InactiveStates']])
        self.assertEqual(values, {'initial text': 5, 'Item Name': 6, 'Quest Title': 9, 'Level UP': 1, 'Level Up': 1, 'NO DATA': 9})

    def test_independent_profiles_and_plan_are_content_locked(self):
        lock = read('references/ui-defaults-research.lock.json')
        self.assertEqual(len(lock['components']), 3)
        for row in lock['components'] + lock['supplemental_evidence']:
            self.assertEqual(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest(), row['sha256'])
        audit = read('locales/zh-Hans/ui-defaults-audit-v40.json')
        self.assertEqual(audit['plan_sha256'], hashlib.sha256((ROOT/audit['plan']).read_bytes()).hexdigest())
        self.assertEqual(audit['research_lock_sha256'], hashlib.sha256((ROOT/audit['research_lock']).read_bytes()).hexdigest())
        self.assertEqual({v['id'] for v in audit['fields']}, {f'UI-{i:02d}' for i in range(1,32)})

    def test_empty_defaults_do_not_claim_game_or_whole_language_acceptance(self):
        audit = read('locales/zh-Hans/ui-defaults-audit-v40.json')
        self.assertFalse(audit['game_execution_observed'])
        self.assertFalse(audit['complete_game_language_coverage_claimed'])
        self.assertEqual(audit['chapter_cards'], 'user-ended; not investigated')
        self.assertTrue(audit['dynamic_text_and_identifiers_preserved'])
        self.assertEqual(audit['source_sha256'], '9bcc6e024b155f58fd841c9d75ff794c584e016e292500375388c80020b294f7')
        self.assertEqual(audit['output_sha256'], '076d165efe18b64d36b5106dc3913aada71ff80f790ee56a7c77a87d7477408b')
        for row in audit['fields']:
            self.assertFalse(row['runtime_visibility_observed'])
            self.assertTrue(row['static_consumer_bound'])

    def test_levelup_positive_content_and_array_declarations_are_not_assumed(self):
        level = read('references/ui-defaults-levelup.lock.json')
        self.assertEqual(level['controls']['state_cases'], 6)
        self.assertEqual(level['controls']['positive_combinations'], 126)
        self.assertTrue(level['controls']['all_final_states_identical'])
        self.assertTrue(level['controls']['all_positive_text_preserved'])
        self.assertLess(level['control_flow']['fade_in_at'], level['control_flow']['set_information_at'])
        lock = read('references/ui-defaults-research.lock.json')
        self.assertEqual(len(lock['object_array_declarations']), 2)
        self.assertTrue(all(r['inner']['kind'] == 'ObjectProperty' for r in lock['object_array_declarations']))
        self.assertEqual(len(lock['existing_canonical_empty_examples']), 5)


if __name__ == '__main__': unittest.main()
