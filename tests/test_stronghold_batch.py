"""Source-free contracts for the fortress aftermath and chapter-four errands."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class StrongholdBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-019.json')
        self.review = load('locales/zh-Hans/batch-019.review.json')
    def test_scope_and_narrative(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 84, 'MC2NpcTalk.int': 30, 'MC2Quest.int': 29,
                                 'MC2CharacterName.int': 1, 'MC2FieldName.int': 1, 'MC2Item.int': 2})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 132, 'narrative': 3, 'name': 6, 'quest_description': 3,
                          'quest_progress': 1, 'quest_objective': 1, 'item_description': 1})
        self.assertEqual(self.review['status'], 'draft')
    def test_disjoint_increment(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[18]['plan']['path'], 'locales/zh-Hans/batch-019.json')
        old = {e['id'] for b in batches[:18] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (3140, 147, 147))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        quests = {c['section']: c['entries'] for c in self.review['coverage'] if c['document'] == 'MC2Quest.int'}
        self.assertEqual(quests, {'04_404_0': 8, '04_405_0': 11, '04_406_0': 10})
    def test_quest_layout_and_single_placeholder(self):
        rows = [e for e in self.plan['entries'] if e['id'] in self.review['preserved_functional_break_ids']]
        self.assertEqual([e['translation'].count('\\n') for e in rows], [1, 1])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        self.assertIn('[古文书]', rows[0]['translation'])
        self.assertIn('[科洛瑟斯]', rows[1]['translation'])
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST%s : 击败科洛瑟斯'])
        self.assertEqual(progress[0].count('%s'), 1)
        self.assertTrue(any('第2哨所' in e['translation'] for e in self.plan['entries']))
    def test_character_viewpoint_and_linked_fields(self):
        values = [e['translation'] for e in self.plan['entries']]
        for value in ['生物学家', '古文书', '风息岛', '记载着用于拉提族的药剂配方的古文书']:
            self.assertIn(value, values)
        self.assertIn('朱特……正义在北部军这一边。', values)
        self.assertIn('……马伦，艾菲斯……', values)
        self.assertTrue(any('很好的特雷瓦族人' in t for t in values))
        self.assertTrue(any('德普廷矿山' in t for t in values))
    def test_candidate_terms(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 188)
        for source, target in [('마룬', '马伦'), ('에피스', '艾菲斯'), ('콜러서스', '科洛瑟斯'),
                               ('고문서', '古文书'), ('생물학자', '生物学家')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
            self.assertEqual(terms[source]['relation'], 'unverified')
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
