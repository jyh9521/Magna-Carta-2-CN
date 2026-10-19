"""Source-free contracts for council dialogue and the bomb delivery quest."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class CouncilBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-008.json')
        self.review = load('locales/zh-Hans/batch-008.review.json')

    def test_scope_and_narration(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 102, 'MC2NpcTalk.int': 20,
                                 'MC2Quest.int': 8, 'linked-name-fields': 1})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 125, 'narrative': 2, 'name': 2,
                          'quest_description': 1, 'quest_progress': 1})
        self.assertEqual(self.review['status'], 'draft')

    def test_disjoint_ids_and_review_completeness(self):
        paths = [b['plan']['path'] for b in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(paths[7], 'locales/zh-Hans/batch-008.json')
        old = {e['id'] for p in paths[:7] for e in load(p)['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (1501, 131, 131))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})

    def test_progress_prefix_and_dialogue_breaks(self):
        self.assertEqual(self.review['preserved_functional_break_ids'], [])
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST:获得炸弹包'])
        for row in self.plan['entries']:
            self.assertNotIn('\\n', row['translation'])
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)

    def test_contextual_names_and_candidate_status(self):
        text = '\n'.join(e['translation'] for e in self.plan['entries'])
        for phrase in ('反哨兵部队', '守护者', '希昂·雷格拉尔', '恸哭之门'):
            self.assertIn(phrase, text)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 134)
        for source, target in [('통곡의 문', '恸哭之门'), ('총사령부', '总司令部'), ('폭탄 꾸러미', '炸弹包')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')

    def test_public_plan_uses_hashes_not_original_text(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))


if __name__ == '__main__':
    unittest.main()
