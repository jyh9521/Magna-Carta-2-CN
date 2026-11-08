"""A repair ledger must resolve the dated29 without absorbing pending reports."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OmissionRepairsV35Tests(unittest.TestCase):
    def read(self, name):
        return json.loads((ROOT/'locales/zh-Hans'/name).read_bytes())

    def test_every_dated_finding_has_one_offline_repair(self):
        old = self.read('omission-findings-v34.json')
        new = self.read('omission-repairs-v35.json')
        self.assertEqual({r['id'] for r in old['findings']}, {r['id'] for r in new['entries']})
        self.assertEqual(len(new['entries']), 29)
        self.assertEqual(Counter(r['kind'] for r in new['entries']),
                         Counter(r['kind'] for r in old['findings']))
        self.assertTrue(all(r['repair_status'] == 'repaired-offline' for r in new['entries']))
        self.assertTrue(all(r['runtime_display_observed'] is False
                            and r['artistic_user_acceptance'] is False for r in new['entries']))
        self.assertFalse(new['game_started'])
        self.assertFalse(new['full_game_copy_created'])
        self.assertTrue(new['coverage_is_bounded'])

    def test_source_plans_and_all_carrier_counts_are_consistent(self):
        new = self.read('omission-repairs-v35.json')
        unique_resources = {}
        counts = Counter()
        for row in new['entries']:
            for key in ('source_plan', 'alias_plan'):
                if key in row:
                    ref = row[key]
                    raw = (ROOT/ref['path']).read_bytes()
                    self.assertNotIn(b'\r', raw)  # Git pins JSON to LF on every platform.
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])
            counts[row['kind']] += len(row['after_carriers'])
            for carrier in row['after_carriers']:
                key = carrier['disc'], carrier['path']
                self.assertTrue(re.fullmatch('[0-9a-f]{64}', carrier['sha256']))
                self.assertEqual(unique_resources.setdefault(key, carrier['sha256']), carrier['sha256'])
        self.assertEqual(counts, {'baked-movie-text': 20, 'normal-ui-texture': 32,
                                  'untranslated-notification-prefix': 16})
        self.assertEqual(len(unique_resources), 26)
        self.assertEqual(new['counts']['changed_resource_records'], 28)  # two TOCs
        copies = new['related_attack_copies']
        self.assertEqual(copies['physical_aliases'], 2)
        self.assertEqual(copies['original_language'], 'Japanese')
        self.assertFalse(copies['runtime_use_observed'])

    def test_known_holds_and_independent_chapter_card_remain_explicit(self):
        new = self.read('omission-repairs-v35.json')
        holds = new['known_hangul_holds']
        self.assertEqual((holds['count'], holds['pending'], holds['excluded']), (63, 40, 23))
        self.assertEqual(holds['status'], 'unchanged')
        ref = holds['policy']
        raw = (ROOT/ref['path']).read_bytes()
        self.assertNotIn(b'\r', raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])
        report, = new['unresolved']
        self.assertEqual(report['id'], 'UI-20261107-02')
        self.assertEqual(report['status'], 'actual-independent-chapter-card-not-identified')
        self.assertEqual(report['new_verified_routes'], 2)
        self.assertTrue(report['alias_counts_overlap'])
        self.assertTrue((ROOT/report['report']).is_file())


if __name__ == '__main__':
    unittest.main()
