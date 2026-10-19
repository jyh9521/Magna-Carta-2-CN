"""Source-free contracts for the second Elgar confrontation and emergency rescue."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class LabRescueTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-048.json');self.r=load('locales/zh-Hans/batch-048.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':56,'MC2Quest.int':22,'MC2Compose.int':11,'MC2CharacterName.int':1});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':86,'name':2,'quest_description':1,'quest_progress':1});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:47] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6251,90));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_distinct_clocks_and_branch_qualifiers(self):
  values=[e['translation'] for e in self.p['entries']];des=next(e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids'])
  self.assertNotIn('line_break_policy',des);self.assertEqual(des['translation'].count('\\n'),4);self.assertIn('3分钟',des['translation']);self.assertTrue(any('2小时' in t for t in values));self.assertTrue(any('也许就在第1研究室' in t for t in values));self.assertTrue(any(t=='QUEST%s：关闭制动装置' for t in values));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),50)
 def test_candidates(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('발포어','巴尔福'),('제동장치','制动装置'),('퍼스트','一号'),('슈엔자이트','修恩扎伊特')]:
   self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
 def test_subtitle_prefix_and_additions(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),30);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
  new=[load(s['path']) for s in p['plans'][28:30]];self.assertEqual([c['resource'] for c in new],['MC2Game/Movies/csm08-30.txt','MC2Game/Movies/csm08-40.txt']);self.assertEqual([len(c['entries']) for c in new],[2,7]);self.assertEqual([e['translation'].count('<br>') for e in new[1]['entries']],[1,0,0,0,1,0,1])
  for s in p['plans'][:30]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
  for c in new:
   for e in c['entries']:self.assertLess(e['start'],e['end']);self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
if __name__=='__main__':unittest.main()
