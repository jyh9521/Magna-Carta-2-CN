"""Source-free contracts for crafting resources and guarded recipe display syntax."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class CraftingTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-104.json');self.r=load('locales/zh-Hans/batch-104.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_scope_and_classification(self):
  self.assertEqual(len(self.ts),220);self.assertEqual(len({e['id'] for e in self.p['entries']}),220)
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Ingredient':28,'FieldAction':34,'Recipe':158});self.assertEqual({e['document'] for e in self.r['coverage']},{'MC2Item.int'})
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':84,'item_description':136});self.assertEqual(self.r['status'],'draft');self.assertEqual({e['id'] for e in self.p['entries']},{e['id'] for e in self.r['entries']})
 def test_unknown_recipe_escape_held_and_old_prefix(self):
  held=self.r['held_entries'];self.assertEqual(len(held),1);self.assertEqual(held[0]['id'],'coalesced:bd69e92a84f9e995da63138b4dd2ff6945381c90c3de1f46be73f14c7cf0ed81');self.assertEqual(held[0]['source_sha256'],'d5f4c0687af9e30bc270768e9d203eec9782e23a369a0d3e517a6a90131fa765')
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:103] for e in load(b['plan']['path'])['entries']};new={e['id'] for e in self.p['entries']};self.assertEqual(len(old),11416);self.assertFalse(old&new)
  allheld={e['id'] for n in range(1,105) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(allheld&new)
 def test_recipe_math_shapes_and_layout(self):
  self.assertEqual(len(self.r['preserved_functional_break_ids']),220);self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('+',174),('%',40),('ＬＶ',29),('（',6),('）',6),('(',24),(')',24),('．',1),('「',49),('」',49),(':',53),(chr(92)+'n',112)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count,symbol)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_source_variants_are_not_repaired(self):
  text='\n'.join(self.ts)
  for t in ['体力+20%． 速度+20','用于制作「力量与守护项链」的配方'+chr(92)+'n攻击+15 防御+15','精神+5抗性+5','用于制作「 魔力与守护脚环」的配方','攻击ＬＶ5 (2个)+防御ＬＶ2 (1个)']:
   self.assertIn(t,text)
  self.assertEqual(sum(t.strip()=='空瓶' for t in self.ts),2);self.assertEqual(sum(t.strip()=='麻痹陷阱' for t in self.ts),2);self.assertIn('配方 : 雪水晶',[t.strip() for t in self.ts]);self.assertIn('猫猫炸弹',self.ts)
  self.assertNotIn('MAGIC_WORD',text);self.assertNotIn('魔力量',text)
 def test_candidates_use_base_names_not_recipe_prefix(self):
  terms=load('locales/zh-Hans/terms.json')['terms'][708:787];self.assertEqual(len(terms),79);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));self.assertFalse(any('레시피' in e['source'] for e in terms));by={e['source']:e['target'] for e in terms};self.assertEqual(by['눈의 수정'],'雪水晶');self.assertEqual(by['청수의 향'],'清水之香')
 def test_workflow_and_existing_subtitles(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][103].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
 def test_odorless_material_description_keeps_source_lock_and_draft_status(self):
  identity='coalesced:a236cf4d00f9d2e905f95c1ac1054ac1fb85fcf6f66e6dbaea6feacac3beb1a6'
  entry=next(e for e in self.p['entries'] if e['id']==identity)
  self.assertEqual(entry,{'id':identity,'source_sha256':'98faf56aaa6afa66f15a85e7d705689c620e6626610433991331c27cf08fb070','translation':'用作黏合剂原料的无气味液体'})
  self.assertEqual(self.r['status'],'draft')
  self.assertEqual(next(e for e in self.r['entries'] if e['id']==identity)['text_kind'],'item_description')
if __name__=='__main__':unittest.main()
