"""Source-free contracts for Velfort civilians and Starlight Field quests."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class CityQuestsTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-044.json');self.r=load('locales/zh-Hans/batch-044.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Quest.int':97,'MC2CharacterName.int':2,'MC2Item.int':6});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':79,'name':10,'quest_description':5,'quest_progress':4,'quest_objective':4,'item_description':3});self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:43] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5897,105));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_layout_and_literals(self):
        rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),5);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual([e['translation'].count('\\n') for e in rows],[0,0,1,2,1]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),29)
        values=[e['translation'] for e in self.p['entries']];self.assertIn('Quest: 获得红色宝石',values);self.assertIn('QUEST%s: 消灭怪物 (%s/%s)',values);self.assertIn('QUEST%s: 获得怪物皮 %s/%s',values);self.assertIn('求婚大作战(2)',values);self.assertTrue(any('10只怪物' in t for t in values));self.assertTrue(any('3张[怪物皮]' in t for t in values));self.assertTrue(any('明天举行婚礼' in t for t in values));self.assertTrue(any('爸爸妈妈突然都不见了' in t for t in values))
    def test_candidate_associated_fields(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('스트로','斯特萝'),('라즈','拉兹'),('붉은 보석','红色宝石'),('전투식량','战斗口粮'),('몬스터의 가죽','怪物皮'),('웨어보어','野猪人'),('그라운드 비스트','地行兽')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        self.assertIn('斯特萝',[e['translation'] for e in self.p['entries']]);self.assertIn('战斗口粮',[e['translation'] for e in self.p['entries']])
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
