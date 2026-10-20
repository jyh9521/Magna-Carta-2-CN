"""Source-free contracts for remaining six styles and Kamond weapon bonuses."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class RemainingSkillsTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-101.json');self.r=load('locales/zh-Hans/batch-101.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_combined_complete_scope(self):
  self.assertEqual(len(self.ts),181);self.assertEqual(len({e['id'] for e in self.p['entries']}),181)
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Kamond_EquipBonus':36,'Celestine_style1':29,'Celestine_style2':22,'Rue_Style1':26,'Rue_Style2':25,'Crocell_Style1':23,'Crocell_Style2':20})
  self.assertEqual({e['id'] for e in self.p['entries']},{e['id'] for e in self.r['entries']});self.assertEqual(self.r['status'],'draft')
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'effect_description':36,'skill_name':54,'skill_description':91})
 def test_prior_prefix_and_all_held_entries(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:100] for e in load(b['plan']['path'])['entries']};new={e['id'] for e in self.p['entries']}
  self.assertEqual(len(old),10735);self.assertFalse(old&new)
  held={e['id'] for n in range(1,102) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])}
  self.assertFalse(held&new);self.assertEqual(self.r['held_entries'],[])
 def test_functional_layout_and_bonus_signs(self):
  self.assertEqual(len(self.r['preserved_functional_break_ids']),181);self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
  ts=self.ts[:36];self.assertEqual(sum(t.count('+') for t in ts),39);self.assertEqual(sum(t.count('%') for t in ts),2);self.assertEqual(sum(t.count(chr(92)+'n') for t in ts),16)
  self.assertIn('耐力+5 抗性+6',ts);self.assertIn('攻击+8 速度+5',ts);self.assertIn('防御+10'+chr(92)+'n冰属性 ',ts)
 def test_skill_conditions_source_variants_and_old_terms(self):
  for t in ['精气吸收','连环反射','瞬杀','雷震波','连环爆发','忍法：潜隐','忍法：隐影','忍法：刺闪','镇炎螺旋腿','玉炎旋风','苦无5连投']:
   self.assertIn(t,self.ts)
  for t in ['仅可在潜隐状态下使用','提高瞬杀的发动率','吸收水之KAN','冰之波动','古代之魂','对1名敌人','马雷族的香','使其沉默']:
   self.assertTrue(any(t in x for x in self.ts),t)
 def test_candidate_terms_and_input_locks(self):
  terms=load('locales/zh-Hans/terms.json')['terms'][526:575];self.assertEqual(len(terms),49)
  self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
  self.assertEqual({e['source']:e['target'] for e in terms}['진염나선퇴'],'镇炎螺旋腿')
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][100].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
 def test_subtitle_plans_remain_locked(self):
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
