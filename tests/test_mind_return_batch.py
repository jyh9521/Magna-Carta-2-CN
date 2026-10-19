"""Source-free contracts for waking Juto, recovery dialogue and linked Renkai skill."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class MindReturnTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-055.json');self.r=load('locales/zh-Hans/batch-055.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':56,'MC2NpcTalk.int':13,'MC2Compose.int':2,'MC2Skill.int':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':69,'system':2,'name':1,'skill_description':1});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:54] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6955,73));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_learning_and_commands(self):
  rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),2);self.assertEqual([e['translation'].count('\\n') for e in rows],[1,1]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),35)
  values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('不能杀死她。也不能放任她死去' in t for t in values));self.assertTrue(any('装备扇后' in t for t in values));self.assertTrue(any('装备手里剑后' in t for t in values));self.assertTrue(any('对1名敌人' in t for t in values))
 def test_skill_candidate(self):
  e=next(e for e in load('locales/zh-Hans/terms.json')['terms'] if e['source']=='천뇌천풍인');self.assertEqual(e['target'],'天雷天风印');self.assertEqual(e['review_status'],'candidate');self.assertEqual(e['relation'],'unverified');self.assertIn(e['source_string_id'],{e['id'] for e in self.p['entries']})
 def test_subtitle_prefix_and_return(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),35);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:33]),234);new=[load(s['path']) for s in p['plans'][33:35]];self.assertEqual([e['resource'] for e in new],['MC2Game/Movies/csm10-65.txt','MC2Game/Movies/csm10-70.txt']);self.assertEqual([len(e['entries']) for e in new],[2,18]);self.assertEqual([e['translation'].count('<br>') for e in new[1]['entries']],[0,0,1,1,1,0,1,1,0,0,0,0,0,1,0,0,1,1])
  for s in p['plans'][:35]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
  for c in new:
   for e in c['entries']:self.assertLess(e['start'],e['end']);self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
if __name__=='__main__':unittest.main()
