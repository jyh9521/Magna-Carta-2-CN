from pathlib import Path
import copy, hashlib, json, re, unittest
from tools.translation_fragments import whitespace_suffixes
from tools.validate_catalog import RETENTION_TOKEN
R = Path(__file__).resolve().parents[1]
L = lambda p: json.loads((R/p).read_bytes())
H = lambda b: hashlib.sha256(b).hexdigest()


class RemainingUIAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = L('locales/zh-Hans/batch-120.json')
        cls.review = L('locales/zh-Hans/batch-120.review.json')
        cls.record = L('locales/zh-Hans/candidate-decisions/remaining-ui-and-separator-adoption.json')
        cls.evidence = L(cls.record['evidence']['path'])
        cls.byid = {e['id']: e for e in cls.plan['entries']}

    def test_exact_new_fields_and_locks(self):
        self.assertEqual(len(self.byid), 13)
        self.assertEqual(self.record['new_translations'], 13)
        self.assertEqual(H((R/self.record['plan']).read_bytes()), self.record['plan_sha256'])
        self.assertEqual(H((R/self.record['review']).read_bytes()), self.record['review_sha256'])
        self.assertEqual(H((R/self.record['evidence']['path']).read_bytes()), self.record['evidence']['sha256'])
        for e in self.record['entries']:
            p = self.byid[e['id']]
            self.assertEqual(e['source_sha256'], p['source_sha256'])
            self.assertEqual(e['translation_sha256'], H(p['translation'].encode()))
        self.assertFalse(self.record['human_finalized'])
        self.assertFalse(self.record['game_rendering_verified'])

    def test_five_unknown_separators_remain_and_recipe_numbers_are_not_fixed(self):
        cases = self.evidence['escape']['five_source_cases']
        self.assertEqual(len(cases), 5)
        for c in cases:
            p = self.byid[c['id']]
            self.assertEqual(p['source_sha256'], c['source_sha256'])
            self.assertEqual(RETENTION_TOKEN.findall(p['translation']).count('\\'), 1)
            self.assertEqual(p['translation'].count('\\n'), c['post_lookup_model'].count('\n'))
            if c['key'] == '1458_recipe_D':
                self.assertEqual(re.findall('[0-9]+', p['translation']), ['5', '3', '1', '2'])
                self.assertEqual(p['translation'].count('ＬＶ'), 2)
                self.assertEqual(p['translation'].count('+'), 1)

    def test_ui_group_is_atomic_and_direct_coverage_is_bounded(self):
        u = self.evidence['ui']
        self.assertEqual((u['adopted_count'], u['typed_function_count']), (7, 14))
        self.assertEqual(sum(len(r['hits']) for r in u['direct_reference_coverage']['records']), 47)
        self.assertTrue(all(r['all_direct_hits_in_proven_assignments'] for r in u['direct_reference_coverage']['records']))
        self.assertFalse(u['executed'])
        self.assertEqual(whitespace_suffixes(self.plan, self.review), set())
        broken = copy.deepcopy(self.plan)
        i = self.review['fragment_groups'][0]['members'][0]['id']
        next(e for e in broken['entries'] if e['id'] == i)['translation'] += '改'
        with self.assertRaises(ValueError):
            whitespace_suffixes(broken, self.review)
        self.assertTrue(any('Other packages' in s for s in u['scope_limits']))

    def test_corrupt_modifier_is_not_reconstructed_and_raw_source_is_locked(self):
        d = self.evidence['damaged_line']
        self.assertEqual(d['adoptable_count'], 1)
        self.assertEqual(d['complete_scene_fields_per_locale_per_disc'], 69)
        self.assertEqual(len(d['inputs']), 4)
        self.assertEqual(len(d['alignment_window']), 12)
        self.assertEqual(d['unrestored_modifier'], '감Ｒ')
        self.assertFalse(d['protections']['source_repair'])
        self.assertTrue(d['protections']['source_bytes_unchanged'])
        for e in d['inputs']:
            self.assertEqual(H(e['source'].encode()), e['source_sha256'])
        self.assertNotIn('力量之源', d['target_translation'])
        self.assertEqual(d['target_translation'].count('\\n'), 1)


if __name__ == '__main__':
    unittest.main()
