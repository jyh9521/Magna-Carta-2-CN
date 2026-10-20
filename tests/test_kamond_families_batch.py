"""Source-free contracts for complete ability/status/composite Kamond triples."""
from pathlib import Path
import unittest,json,hashlib,collections,re
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class KamondFamiliesTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-102.json');self.r=load('locales/zh-Hans/batch-102.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_scope_and_complete_triples(self):
  self.assertEqual(len(self.ts),204);self.assertEqual(len({e['id'] for e in self.p['entries']}),204)
  self.assertEqual(self.r['coverage'],[{'document':'MC2Kamond.int','section':'Karmond','entries':204}]);self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':68,'item_description':136})
  self.assertEqual([e['records'] for e in self.r['families']],[120,39,45]);self.assertEqual(self.r['status'],'draft')
  self.assertEqual({e['id'] for e in self.p['entries']},{e['id'] for e in self.r['entries']})
 def test_lv_and_stat_amounts(self):
  for n,stat in enumerate(['体力','速度','攻击','防御','抗性','精神','耐力','耐力恢复']):
   for level in range(1,6):
    name,short,full=self.ts[(n*5+level-1)*3:(n*5+level-1)*3+3];amount=str(level*2)+('%' if n==0 else '')
    self.assertEqual(name,f'{stat} LV{level}');self.assertEqual(short,stat+'+'+amount);self.assertEqual(full,'能力卡蒙德'+chr(92)+'n'+short)
 def test_protected_layout_signs_and_no_invented_effect(self):
  self.assertEqual(len(self.r['preserved_functional_break_ids']),204);self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  self.assertEqual(sum(t.count('+') for t in self.ts),140);self.assertEqual(sum(t.count('%') for t in self.ts),18);self.assertEqual(sum(t.count(chr(92)+'n') for t in self.ts),83)
  self.assertIn('风之卡蒙德',self.ts);self.assertIn('体力+15%'+chr(92)+'n速度+15',self.ts);self.assertNotIn('风属性',self.ts)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_status_scope_and_duplicate_labels_do_not_merge(self):
  self.assertEqual(sum(t.strip()=='眩晕防护' for t in self.ts),2)
  for t in ['眩晕、沉默免疫','炎热、烧伤免疫','麻痹、触电免疫 ','寒冷、冻伤免疫','力竭免疫']:
   self.assertIn(t,self.ts)
  self.assertFalse(any('冰冻' in t or '火属性' in t for t in self.ts));self.assertNotIn('英雄卡蒙德',self.ts)
 def test_prior_translations_holds_and_candidates(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:101] for e in load(b['plan']['path'])['entries']};new={e['id'] for e in self.p['entries']}
  self.assertEqual(len(old),10916);self.assertFalse(old&new)
  held={e['id'] for n in range(1,103) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&new);self.assertEqual(self.r['held_entries'],[])
  terms=load('locales/zh-Hans/terms.json')['terms'][575:612];self.assertEqual(len(terms),37);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));self.assertFalse(any('LV' in e['source'] for e in terms))
 def test_workflow_and_subtitle_identity(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][101].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
