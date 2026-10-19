"""Source-free contracts for Elgar origins and laboratory prisoner rescue."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class LabTruthTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-047.json');self.r=load('locales/zh-Hans/batch-047.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':61,'MC2Quest.int':20,'MC2Compose.int':5,'MC2Item.int':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':79,'narrative':3,'name':2,'quest_description':1,'quest_progress':1,'menu':1,'item_description':1});self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:46] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(6163,88));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_layout_and_orders(self):
        rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),2);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual([e['translation'].count('\\n') for e in rows],[1,1]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),42)
        values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('只能对哨兵下达一次“绝对命令”' in t for t in values));self.assertTrue(any('既不能杀死公主，也不能放任她死去' in t for t in values));self.assertTrue(any(t.endswith('打开房门。 ') for t in values));menu=next(t for t in values if 'X<Styles:/>' in t);self.assertEqual(menu,'<Styles:MC2_StyleFont_0>X<Styles:/> 休息\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 不休息')
    def test_candidates_and_duplicated_item_key_coverage(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('인간형 센티넬','人形哨兵'),('세컨드','二号'),('퍼스트 엘가','一号艾尔加'),('세컨드 엘가','二号艾尔加'),('절대명령','绝对命令'),('연구실 출입카드','研究室通行卡')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        cov=[e for e in self.r['coverage'] if e['document']=='MC2Item.int'];self.assertEqual(cov,[{'document':'MC2Item.int','section':'Valuables','entries':2}]);self.assertTrue(any('第二组' in n and '第一组保持原值' in n for n in self.r['notes']))
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
