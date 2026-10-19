"""Source-free contracts for adult ceremony and first royal trials."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RoyalTrialsTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-038.json');self.r=load('locales/zh-Hans/batch-038.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Quest.int':62,'MC2CharacterName.int':2,'MC2UI.int':5})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':52,'name':11,'quest_description':4,'quest_progress':2})
        self.assertEqual(self.r['status'],'draft');held=self.r['held_entries'];self.assertEqual(len(held),1);self.assertEqual((held[0]['section'],held[0]['key']),('06_zepi_1','order_2'))
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:37] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5331,69));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertNotIn(self.r['held_entries'][0]['id'],old|ids)
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_layout_and_titles(self):
        functional=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in functional]
        self.assertEqual(len(rows),4);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum(e['translation'].count('\\n') for e in rows),3)
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),49)
        values=[e['translation'] for e in self.p['entries']];self.assertIn('王之试炼-水-',values);self.assertIn('王之试炼-火-',values);self.assertIn('QUEST : 完成水之试炼',values);self.assertIn('QUEST : 完成火之试炼',values)
        self.assertTrue(any(t.endswith('作出错误的判断，') for t in values));self.assertTrue(any('卡尔塔与人类' in t for t in values));self.assertTrue(any('两位王的后裔同时出现' in t for t in values))
    def test_candidates_and_ui_names(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('왕의 시련','王之试炼'),('왕가의 사당','王室神殿'),('물의 사당','水之神殿'),('불의 사당','火之神殿'),('번개의 사당','雷之神殿'),('바람의 사당','风之神殿'),('물의 영혼','水之魂'),('불의 영혼','火之魂'),('물의 민족','水之民'),('잔달리아 협곡','赞达利亚峡谷'),('어둠의 은신처','暗影藏身处'),('르제필다 그레나 베를리네트','蕾洁菲尔妲·格蕾娜·贝尔利内特')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']]
        for t in ('水之魂','火之魂','水之神殿','火之神殿','雷之神殿','风之神殿','王室神殿'):self.assertIn(t,values)
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        for s in p['plans'][:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
