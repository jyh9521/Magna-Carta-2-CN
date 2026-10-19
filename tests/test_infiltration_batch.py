"""Source-free contracts for chapter-seven closure and infiltration props."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class InfiltrationTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-043.json');self.r=load('locales/zh-Hans/batch-043.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':64,'MC2NpcTalk.int':4,'MC2Compose.int':2,'MC2Item.int':5,'MC2Skill.int':1});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':68,'name':4,'system_message':2,'item_description':2});self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:42] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5821,76));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_layout_and_source_conditions(self):
        rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),2);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual([e['translation'].count('\\n') for e in rows],[1,1]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),39)
        self.assertIn('装备弓后',rows[0]['translation']);self.assertIn('装备斧后',rows[1]['translation']);self.assertTrue(all('暴雪之刃' in e['translation'] for e in rows))
        values=[e['translation'] for e in self.p['entries']];self.assertIn('哨兵研究所通行卡 ',values);self.assertIn('用于出入哨兵研究所的钥匙',values);self.assertTrue(any('只有3个' in t for t in values));self.assertTrue(any('再给你3个' in t for t in values));self.assertTrue(any('大概是中间那座石像' in t for t in values));self.assertTrue(any('退出北部军' in t for t in values))
    def test_candidates_and_spelling_variants(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('소용돌이 폭탄','漩涡炸弹'),('필러제어장치','晶柱控制装置'),('센티넬 연구소 출입카드','哨兵研究所通行卡'),('블리자드엣지','暴雪之刃'),('블리자드 엣지','暴雪之刃')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        self.assertNotEqual(ts['블리자드엣지']['source_string_id'],ts['블리자드 엣지']['source_string_id'])
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
