"""Source-free contracts for bounded chapter-four dialogue and quest completion."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class Chapter04BatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-021.json')
        self.review = load('locales/zh-Hans/batch-021.review.json')
    def test_scope_and_classification(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 54, 'MC2NpcTalk.int': 30, 'MC2Quest.int': 77, 'MC2Item.int': 1})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 140, 'narrative': 2, 'menu': 1, 'name': 7,
                          'quest_description': 6, 'quest_progress': 3, 'quest_objective': 3})
        self.assertEqual(self.review['status'], 'draft')
    def test_disjoint_increment_and_bounded_completion(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[20]['plan']['path'], 'locales/zh-Hans/batch-021.json')
        old = {e['id'] for b in batches[:20] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (3454, 162, 162))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        coverage = [c for b in batches[:21] for c in load(b['review']['path']).get('coverage', [])]
        self.assertEqual(sum(c['entries'] for c in coverage if c.get('document') == 'MC2CSMB.int'
                             and c.get('section', '').startswith('CSMB04_')), 411)
        self.assertEqual(sum(c['entries'] for c in coverage if c.get('document') == 'MC2Quest.int'
                             and c.get('section', '').startswith('04_')), 186)
    def test_functional_choice_paragraphs_and_progress(self):
        rows = [e for e in self.plan['entries'] if e['id'] in self.review['preserved_functional_break_ids']]
        self.assertEqual([e['translation'].count('\\n') for e in rows], [1, 4, 1, 2, 2, 1])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        self.assertEqual(rows[0]['translation'], '<Styles:MC2_StyleFont_0>X<Styles:/> 买下\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 不需要')
        self.assertIn('\\n\\n', rows[1]['translation'])
        values = [e['translation'] for e in self.plan['entries']]
        progress = [v for v in values if v.startswith('QUEST')]
        self.assertEqual([v.count('%s') for v in progress], [1, 3, 1])
        self.assertTrue(all(v.startswith('QUEST%s: ') for v in progress))
        self.assertIn('要不是各位，恐怕就糟了。 ', values)
    def test_numbers_directions_and_distinct_source_ids(self):
        values = [e['translation'] for e in self.plan['entries']]
        self.assertTrue(any('10名卫兵' in v for v in values))
        self.assertIn('要不要便宜买下来？只要500SID。', values)
        self.assertTrue(any('荒野南部' in v for v in values))
        self.assertTrue(any('远处用弓攻击' in v for v in values))
        repeated = '我们去那里采集九节草，有些危险，恐怕得请各位亲自去一趟了。'
        self.assertEqual(values.count(repeated), 2)
    def test_linked_candidate(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 192)
        term = terms['도난 당한 카몬드']
        self.assertEqual(term['target'], '被盗的卡蒙德')
        self.assertEqual(term['review_status'], 'candidate')
        self.assertEqual(term['relation'], 'unverified')
        self.assertIn('被盗的卡蒙德', [e['translation'] for e in self.plan['entries']])
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
