"""Source-free contracts for the dated omission/retention snapshot."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_text_residuals import policy_tables,prefix_matches

ROOT=Path(__file__).resolve().parents[1]


class OmissionSnapshotTests(unittest.TestCase):
    def read(self,name):return json.loads((ROOT/'locales/zh-Hans'/name).read_bytes())

    def test_known_fields_remain_explicit_pending_or_excluded_not_translated(self):
        p=self.read('omission-screen-v34.json');_,known,rules=policy_tables(p)
        self.assertEqual(len(p['known_dispositions']),63);self.assertEqual(len(known),126)
        self.assertEqual(Counter(r['status'] for r in p['known_dispositions']),dict(pending=40,excluded=23))
        self.assertTrue(all(r['discs']==[1,2] and r['runtime_display_observed'] is False for r in p['known_dispositions']))
        self.assertEqual(len(rules),1);self.assertTrue(prefix_matches('Quest%s: sample',rules[0]))
        self.assertFalse(prefix_matches('QuestResource',rules[0]))

    def test_confirmed_snapshot_preserves_carriers_and_does_not_claim_runtime(self):
        v=self.read('omission-findings-v34.json');rows=v['findings'];self.assertEqual(len(rows),29)
        self.assertEqual(len({r['id'] for r in rows}),29);self.assertEqual(sum(r['newly_discovered'] for r in rows),18)
        counts=Counter(r['kind'] for r in rows)
        self.assertEqual(counts,{'baked-movie-text':13,'normal-ui-texture':8,'untranslated-notification-prefix':8})
        self.assertTrue(v['coverage_is_bounded']);self.assertFalse(v['game_resources_modified'])
        self.assertTrue(all(r['runtime_display_observed'] is False for r in rows))
        images=[r for r in rows if r['kind']=='normal-ui-texture']
        self.assertEqual(sum(len(r['carriers']) for r in images),32)
        self.assertEqual(sum(r['typed_ui_reference_count'] for r in images),60)
        self.assertEqual(len(v['related_unbound_texture_copies']),2)
        for r in rows:
            if r['kind']=='untranslated-notification-prefix':
                self.assertEqual(hashlib.sha256(r['effective_value'].encode()).hexdigest(),r['effective_value_sha256'])

    def test_input_roles_keep_alternate_language_banks_separate(self):
        p=self.read('omission-screen-inputs-v34.json');self.assertEqual(len(p['selectors']),3)
        roles=p['selectors'][0]['role_by_suffix']
        self.assertEqual(roles,{'.int':'primary','.jpn':'alternate-locale','.kor':'alternate-locale'})
