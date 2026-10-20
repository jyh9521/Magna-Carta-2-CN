"""Source-free contracts for special Kamond and complete recovery item fields."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class SpecialRecoverTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-103.json');self.r=load('locales/zh-Hans/batch-103.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_combined_complete_scope(self):
  self.assertEqual(len(self.ts),296);self.assertEqual(len({e['id'] for e in self.p['entries']}),296)
  self.assertEqual(self.r['coverage'],[{'document':'MC2Kamond.int','section':'Karmond','entries':102},{'document':'MC2Item.int','section':'Recover','entries':194}])
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':96,'item_description':200})
  self.assertEqual({e['id'] for e in self.p['entries']},{e['id'] for e in self.r['entries']});self.assertEqual(self.r['status'],'draft')
 def test_old_prefix_and_holds(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:102] for e in load(b['plan']['path'])['entries']};new={e['id'] for e in self.p['entries']}
  self.assertEqual(len(old),11120);self.assertFalse(old&new)
  held={e['id'] for n in range(1,104) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&new);self.assertEqual(self.r['held_entries'],[])
 def test_protected_format_and_voice(self):
  self.assertEqual(len(self.r['preserved_functional_break_ids']),296);self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for char,number in [('+',34),('%',44),(chr(92)+'n',101),('「',11),('」',11),('~',4)]:self.assertEqual(sum(t.count(char) for t in self.ts),number,char)
  self.assertEqual(sum(t.endswith('喵~') for t in self.ts),4)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_kamond_conditions_and_separate_success_rates(self):
  for amount in ['一','两','三']:self.assertTrue(any('消耗的KAN减少'+amount+'个' in t and '重复使用效果不叠加' in t for t in self.ts))
  self.assertTrue(any('攻击时，以一定概率施加冻伤' in t for t in self.ts));self.assertTrue(any('普通攻击成功率提高' in t for t in self.ts));self.assertIn('命中率+30%',self.ts)
  self.assertTrue(any('战斗中获得的SID+50%' in t for t in self.ts));self.assertTrue(any('以一定概率施加「腹痛」' in t for t in self.ts))
 def test_items_follow_source_not_keys(self):
  for t in ['治愈胶囊','疗愈胶囊','苏生水','冻伤药膏','天敌剂','蜂蜜水','空蝉长袍','猫薄荷','黄花鱼干','冰之元素体']:
   self.assertIn(t,[x.strip() for x in self.ts])
  for t in ['恢复1名我方成员5500点体力','恢复全体我方成员4500点体力','30%体力复苏','解除1名我方成员的冰冻状态','使1名敌人陷入虚弱状态','一定时间内提高全体我方成员的','只为1名我方成员恢复20%的体力喵~']:
   self.assertTrue(any(t in x for x in self.ts),t)
 def test_candidate_and_input_locks(self):
  terms=load('locales/zh-Hans/terms.json')['terms'][612:708];self.assertEqual(len(terms),96);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
  self.assertEqual({e['source']:e['target'] for e in terms}['鍛える者'],'锻炼者')
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][102].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
