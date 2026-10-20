"""Source-free contracts for the combined systems, movies and tutorial batch."""
from pathlib import Path
import unittest,json,hashlib,re
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class SystemTutorialTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-099.json');self.r=load('locales/zh-Hans/batch-099.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_scope_and_classification(self):
  self.assertEqual(len(self.ts),200);self.assertEqual(len({e['id'] for e in self.p['entries']}),200)
  self.assertEqual(sum(e['entries'] for e in self.r['coverage']),200)
  counts={}
  for e in self.r['coverage']:counts[e['document']]=counts.get(e['document'],0)+e['entries']
  self.assertEqual(counts,{'MC2UI.int':19,'MC2UI_Field.int':104,'MC2UI_Pillar.int':13,'MC2Tutorial.int':64})
  self.assertEqual({e['id'] for e in self.p['entries']},{e['id'] for e in self.r['entries']})
  self.assertEqual(self.r['status'],'draft');self.assertTrue(all(e['text_kind']!='unclassified' for e in self.r['entries']))
 def test_old_prefix_and_held_fragments(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'][:98]
  old={e['id'] for b in batches for e in load(b['plan']['path'])['entries']}
  self.assertEqual(len(old),10371);new={e['id'] for e in self.p['entries']};self.assertFalse(old&new)
  held={e['id'] for n in range(1,100) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])}
  self.assertFalse(held&new);self.assertEqual(len(self.r['held_entries']),45)
 def test_functional_layout_and_source_locks(self):
  self.assertEqual(len(self.r['preserved_functional_break_ids']),200)
  self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e)
   self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
  self.assertTrue(any(t.endswith('\t') for t in self.ts));self.assertTrue(any(t.endswith(' ') for t in self.ts))
  self.assertIn('<Styles:MC2_StyleFont_0>A<Styles:/>下一步',self.ts)
 def test_exact_tutorial_numbers_buttons_and_conditions(self):
  text='\n'.join(self.ts)
  for token in ['[ChainBreak]','1.5倍','2倍','50%','5秒','第3人','[RB]','[LB]','[X键]','[B键]','[AI设置]','<Styles:MC2_StyleFont_0>U<Styles:/>']:
   self.assertIn(token,text)
  self.assertIn('武器已附加冰属性',self.ts)
  self.assertTrue(any('4大属性KAN分别为火、冰、风、雷这4种' in t for t in self.ts))
  self.assertIn('风息岛的朱特',self.ts);self.assertIn('前往拉·斯特拉达',self.ts)
 def test_candidate_terms_and_workflow_locks(self):
  terms=load('locales/zh-Hans/terms.json')['terms'][468:475];self.assertEqual(len(terms),7)
  self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
  self.assertEqual({e['source']:e['target'] for e in terms}['카몬드보드'],'卡蒙德盘')
  b=load('locales/zh-Hans/translation-workflow.json')['batches'][98]
  for e in b.values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
 def test_old_subtitle_locks(self):
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans']
  self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
