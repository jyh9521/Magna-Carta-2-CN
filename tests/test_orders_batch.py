"""Source-free contracts for the headquarters, new orders and hunting quest."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class OrdersBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-007.json')
        self.review = load('locales/zh-Hans/batch-007.review.json')

    def test_scope_includes_suffix_branches(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 71, 'MC2NpcTalk.int': 20,
                                 'MC2Quest.int': 19, 'linked-name-fields': 2})
        sections = {r.get('section'): r['entries'] for r in self.review['coverage']}
        self.assertEqual(sections['CSMB02_38_1'], 7)
        self.assertEqual(sections['CSMB02_38_2'], 18)
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 104, 'name': 3, 'narrative': 2,
                          'quest_description': 1, 'quest_progress': 1, 'quest_objective': 1})

    def test_ids_are_disjoint_and_review_complete(self):
        paths = [b['plan']['path'] for b in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(paths[6], 'locales/zh-Hans/batch-007.json')
        old = {e['id'] for p in paths[:6] for e in load(p)['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (1389, 112, 112))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        self.assertEqual(self.review['status'], 'draft')

    def test_quest_layout_and_progress(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        row = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(row['translation'].count('\\n'), 2)
        self.assertNotIn('line_break_policy', row)
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST%s: 狩猎蓬蓬 (%s / %s)'])
        self.assertEqual(progress[0].count('%s'), 3)
        self.assertIn('3只', '\n'.join(e['translation'] for e in self.plan['entries']))

    def test_names_remain_candidates(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 131)
        for source, target in [('라우드', '劳德'), ('라우드 사령관', '劳德司令官'),
                               ('코타마레', '柯塔马雷'), ('방어구 파괴', '破甲')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')

    def test_public_plan_and_break_policies(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)


if __name__ == '__main__':
    unittest.main()
