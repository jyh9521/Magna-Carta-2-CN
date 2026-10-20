"""Source-free contracts for wetland quests and associated map/item fields."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class WetlandGhostTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-092.json');self.r=L('locales/zh-Hans/batch-092.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'03_352_00':15,'03_360_0':20,'Kotamare':1,'Valuables':2});self.assertEqual(len(self.p['entries']),38);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),18);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),10);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':28,'name':4,'quest_description':2,'system_message':2,'quest_objective':1,'item_description':1})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:91] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9281);self.assertEqual(len(ids),38);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_shared_candidates_and_fields(self):
  terms=L('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),437)
  for source,target in [('블레보러','布莱博拉'),('어둠의 은신처','暗影藏身处')]:self.assertTrue(any(e['source']==source and e['target']==target and e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
  for target in ['暗影藏身处','马雷的吊坠','被怪物杀死的马雷族留下的吊坠']:self.assertIn(target,self.ts)
 def test_functional_tokens_and_counts(self):
  self.assertEqual(sum(t.count('%s') for t in self.ts),4);self.assertIn('QUEST%s: 讨伐布莱博拉 (%s / %s)',self.ts);self.assertIn('Quest%s: 获得马雷的吊坠',self.ts);self.assertEqual(sum(t.count('6') for t in self.ts),3);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_context_and_incomplete_knowledge(self):
  self.assertIn('马雷的幽灵',self.ts);self.assertIn('马雷族的尸体……',self.ts);self.assertTrue(any('死后化为幽灵' in t and '凯汀' in t for t in self.ts));self.assertTrue(any('据说' in t and '制造怪物' in t for t in self.ts));self.assertTrue(any('西北方' in t for t in self.ts));self.assertTrue(any('北方' in t for t in self.ts));self.assertFalse(any('复活' in t for t in self.ts));self.assertTrue(any('我还以为' in t for t in self.ts))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,92) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
