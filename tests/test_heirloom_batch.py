"""Source-free contracts for Crocell's keepsake, council debate and Rati tasks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class HeirloomBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-020.json')
        self.review = load('locales/zh-Hans/batch-020.review.json')
    def test_scope_and_narrative(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 96, 'MC2NpcTalk.int': 30, 'MC2Quest.int': 38,
                                 'MC2CharacterName.int': 2, 'MC2Item.int': 1})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 154, 'narrative': 4, 'name': 6, 'quest_description': 3})
        self.assertEqual(self.review['status'], 'draft')
    def test_disjoint_increment(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[19]['plan']['path'], 'locales/zh-Hans/batch-020.json')
        old = {e['id'] for b in batches[:19] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (3287, 167, 167))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        quests = {c['section']: c['entries'] for c in self.review['coverage'] if c['document'] == 'MC2Quest.int'}
        self.assertEqual(quests, {'04_4202_0': 11, '04_4203_0': 18, '04_4203_1': 9})
    def test_functional_layout_and_trailing_space(self):
        rows = [e for e in self.plan['entries'] if e['id'] in self.review['preserved_functional_break_ids']]
        self.assertEqual([e['translation'].count('\\n') for e in rows], [1, 1])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        self.assertIn('[生物学家]', rows[0]['translation'])
        self.assertIn('生物学家的儿子[阿尔斯]', rows[1]['translation'])
        values = [e['translation'] for e in self.plan['entries']]
        self.assertIn('九节草 ', values)
        self.assertIn('请前往公会联盟，领取[九节草] ', values)
        self.assertFalse([t for t in values if t.startswith('QUEST')])
    def test_debate_viewpoints_and_unidentified_keepsake(self):
        values = [e['translation'] for e in self.plan['entries']]
        for value in ['玛莉丝', '黛芭', '黛芭的请求', '寻找九节草']:
            self.assertIn(value, values)
        self.assertIn('之前，为了对抗北部军，我也认为我们应该制造哨兵。但现在，必须停止这项计划。', values)
        self.assertIn('当然，若我军陷入严重劣势，我也会冷静地考虑制造哨兵。', values)
        self.assertTrue(any('恐怕也是这样制造出来的' in t for t in values))
        self.assertTrue(any('阿维斯族' in t for t in values))
    def test_candidate_terms(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 191)
        for source, target in [('마리스', '玛莉丝'), ('데바', '黛芭'), ('구절초', '九节草')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
            self.assertEqual(terms[source]['relation'], 'unverified')
        self.assertEqual(terms['루']['target'], '露')
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
