"""Source-free contracts for the Sentinel Lab opening and power route."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class LabOpeningTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-046.json');self.r=load('locales/zh-Hans/batch-046.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':55,'MC2Compose.int':10,'MC2Quest.int':21,'MC2CharacterName.int':2,'MC2FieldName.int':1,'MC2Item.int':4});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':68,'narrative':10,'name':7,'quest_progress':3,'quest_description':2,'item_description':2,'quest_objective':1});self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:45] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(6070,93));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_layout_and_conditions(self):
        rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),2);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual([e['translation'].count('\\n') for e in rows],[4,2]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),38);self.assertEqual([i for i,t in enumerate(rows[0]['translation'].split('\\n')) if not t],[2])
        values=[e['translation'] for e in self.p['entries']];self.assertIn('QUEST%s: 获得动力装置钥匙 ',values);self.assertIn('动力装置钥匙 ',values);self.assertIn('尼克斯的保管箱钥匙 ',values);self.assertTrue(any('地下2层' in t for t in values));self.assertTrue(any('第4研究室' in t for t in values));self.assertTrue(any('或许就是公主殿下' in t for t in values));self.assertEqual(values.count('尼克斯'),2)
    def test_first_uses_real_coalesced_anchor(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('퍼스트','一号'),('닉스','尼克斯'),('중앙연구실','中央研究室'),('중앙 연구소','中央研究所'),('동력 장치','动力装置'),('동력장치','动力装置'),('워프 장치','传送装置'),('워프장치','传送装置'),('동력장치 열쇠','动力装置钥匙'),('닉스의 보관함','尼克斯的保管箱'),('닉스의 보관함 열쇠','尼克斯的保管箱钥匙')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        first=ts['퍼스트'];self.assertEqual(first['resource'],'MC2Game/Localization/Coalesced.int');self.assertIn(first['source_string_id'],{e['id'] for e in self.p['entries']});old=load('locales/zh-Hans/batch-033.review.json')['subtitle_term_candidates'][0];self.assertEqual((old['source'],old['target']),(first['source'],first['target']));self.assertNotEqual(old['source_string_id'],first['source_string_id'])
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
