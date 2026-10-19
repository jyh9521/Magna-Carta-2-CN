"""Source-free contracts for Abazet return and obstacle-operation state branches."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class AbazetReturnBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-017.json')
        self.review = load('locales/zh-Hans/batch-017.review.json')
    def test_scope_and_classification(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 86, 'MC2NpcTalk.int': 30, 'MC2Quest.int': 34})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 146, 'menu': 1, 'name': 1, 'quest_description': 1, 'quest_progress': 1})
        self.assertEqual(self.review['status'], 'draft')
    def test_disjoint_increment(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[16]['plan']['path'], 'locales/zh-Hans/batch-017.json')
        old = {e['id'] for b in batches[:16] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2821, 150, 150))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        quest = {c['section']: c['entries'] for c in self.review['coverage'] if c['document'] == 'MC2Quest.int'}
        self.assertEqual(quest, {'Ch02_291_00': 20, 'Ch02_291_01': 14})
    def test_functional_layout_and_buttons(self):
        rows = [e for e in self.plan['entries'] if e['id'] in self.review['preserved_functional_break_ids']]
        self.assertEqual(len(rows), 2)
        menu, description = rows
        self.assertEqual(menu['translation'], '<Styles:MC2_StyleFont_0>X<Styles:/> 出发\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 暂时待命')
        self.assertEqual(description['translation'].count('\\n'), 2)
        self.assertIn('[猫猫炸弹]', description['translation'])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        rt = [e['translation'] for e in self.plan['entries'] if '[RT]' in e['translation']]
        self.assertEqual(rt, ['请在移动模式下按[RT]，从场地行动列表中选择炸弹并使用。'])
        self.assertIn('QUEST : 障碍物破坏完成', [e['translation'] for e in self.plan['entries']])
    def test_operation_semantics_and_queen(self):
        values = [e['translation'] for e in self.plan['entries']]
        self.assertIn('目前的作战计划是，在三条路中的中央和南侧投入少量兵力进行扰乱，同时将主力集中在北侧。', values)
        self.assertTrue(any('我的母亲……先女王陛下' in t for t in values))
        self.assertEqual(values.count('下面报告当前情况。'), 2)
    def test_candidate_terms(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 178)
        for source, target in [('루할트', '鲁哈尔特'), ('네코폭탄', '猫猫炸弹'), ('데스발리스타', '死亡弩炮')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
        self.assertNotEqual(terms['네코폭탄']['id'], terms['네코족 특제 폭탄']['id'])
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
