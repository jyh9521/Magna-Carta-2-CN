"""Source-free contracts for three characters' six complete skill styles."""
from pathlib import Path
import unittest,json,hashlib
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class StyleSkillsTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-100.json');self.r=load('locales/zh-Hans/batch-100.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_complete_combined_scope(self):
  self.assertEqual(len(self.ts),164);self.assertEqual(len({e['id'] for e in self.p['entries']}),164)
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Common':9,'StatUP':1,'Juto_Style1':25,'Juto_Style2':25,'Argo_Style1':23,'Argo_Style2':21,'Zephie_Style1':35,'Zephie_Style2':25})
  self.assertEqual({e['document'] for e in self.r['coverage']},{'MC2Skill.int'})
  self.assertEqual({e['id'] for e in self.p['entries']},{e['id'] for e in self.r['entries']});self.assertEqual(self.r['status'],'draft')
 def test_old_translations_and_held_fragments(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'][:99]
  old={e['id'] for b in batches for e in load(b['plan']['path'])['entries']};new={e['id'] for e in self.p['entries']}
  self.assertEqual(len(old),10571);self.assertFalse(old&new)
  held={e['id'] for n in range(1,101) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])}
  self.assertFalse(held&new);self.assertEqual(len(self.r['held_entries']),10)
 def test_protected_layout(self):
  self.assertEqual(len(self.r['preserved_functional_break_ids']),164)
  self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e)
   self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
  self.assertTrue(any(t.startswith(' ') for t in self.ts));self.assertTrue(any(t.endswith(' ') for t in self.ts))
 def test_selected_names_and_exact_scope(self):
  for t in ['空进斩','刚进斩','铁一影','幻隐闪','破锁乱闪','超绝破天舞','重击','狮子吼','破甲','疗愈术','医疗术','风之盾']:
   self.assertIn(t,self.ts)
  for t in ['对1名敌人','3次连续攻击','4次光弹','5连击','一名友军','全体友军','周围敌人','KAN消耗量减少1']:
   self.assertTrue(any(t in x for x in self.ts),t)
 def test_new_terms_and_dependency_locks(self):
  terms=load('locales/zh-Hans/terms.json')['terms'][475:526];self.assertEqual(len(terms),51)
  self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
  self.assertEqual({e['source']:e['target'] for e in terms}['철일영'],'铁一影')
  b=load('locales/zh-Hans/translation-workflow.json')['batches'][99]
  for e in b.values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
 def test_prior_subtitle_identity(self):
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44)
  self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
