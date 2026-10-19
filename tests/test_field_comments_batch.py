"""Source-free contracts for chapter-four town completion and field comments."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class FieldCommentsBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-022.json')
        self.review = load('locales/zh-Hans/batch-022.review.json')
    def test_scope_and_classification(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2NpcTalk.int': 91, 'MC2Compose.int': 68})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 120, 'narrative': 38, 'menu': 1})
        self.assertEqual(self.review['status'], 'draft')
    def test_disjoint_increment_and_bounded_town_completion(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[21]['plan']['path'], 'locales/zh-Hans/batch-022.json')
        old = {e['id'] for b in batches[:21] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (3616, 159, 159))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        coverage = [c for b in batches[:22] for c in load(b['review']['path']).get('coverage', [])]
        self.assertEqual(sum(c['entries'] for c in coverage if c.get('document') == 'MC2NpcTalk.int'
                             and c.get('section') == 'Ch04_Abazet'), 242)
    def test_functional_choice_and_parenthesis_boundaries(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        menu = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(menu['translation'], '<Styles:MC2_StyleFont_0>X<Styles:/> 随时可以出发\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 还需要点时间')
        self.assertNotIn('line_break_policy', menu)
        inner = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('(')]
        self.assertEqual(len(inner), 37)
        self.assertTrue(all(t.endswith(')') for t in inner))
        self.assertIn('会议结束后……', [e['translation'] for e in self.plan['entries']])
    def test_numeric_literals_and_phase_viewpoints(self):
        values = [e['translation'] for e in self.plan['entries']]
        self.assertTrue(any('第2首都' in v for v in values))
        self.assertIn('前往黑刃要塞，需要经过2处哨所。', values)
        self.assertIn('第1哨所的晶柱已经占领。', values)
        self.assertTrue(any('第2哨所有' in v for v in values))
        self.assertTrue(any('虽然只是传闻' in v for v in values))
        self.assertTrue(any('露' not in v and '北部军的新将领' in v for v in values))
    def test_unproven_boss_spellings_are_separate_candidates(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 194)
        for source, target in [('베카스', '贝卡斯'), ('레카스', '雷卡斯')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
            self.assertEqual(terms[source]['relation'], 'unverified')
        self.assertNotEqual(terms['베카스']['id'], terms['레카스']['id'])
        values = [e['translation'] for e in self.plan['entries']]
        self.assertTrue(any('[贝卡斯]' in v for v in values))
        self.assertIn('竟然连雷卡斯都击败了！', values)
    def test_locked_payload_and_movie_nonduplication(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 18)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:18]), 141)
        for spec in profile['plans'][:18]:
            self.assertEqual(hashlib.sha256((ROOT / spec['path']).read_bytes()).hexdigest(), spec['sha256'])
if __name__ == '__main__':
    unittest.main()
