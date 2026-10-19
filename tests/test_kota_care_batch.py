"""Source-free contracts for Kota Mare care and the monster-search lead."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class KotaCareTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-052.json');self.r=load('locales/zh-Hans/batch-052.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':72,'MC2NpcTalk.int':23,'MC2Quest.int':18,'MC2Item.int':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':109,'name':3,'quest_description':2,'item_description':1});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:51] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6644,115));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_layout_and_context(self):
  rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),2);self.assertEqual([e['translation'].count('\\n') for e in rows],[1,3]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),69)
  values=[e['translation'] for e in self.p['entries']];self.assertIn('觉醒之香 ',values);self.assertTrue(any(t.startswith('没事，没事。') and '妹妹' in t and '弟弟' not in t for t in values));self.assertTrue(any('从来没有人尝试过' in t for t in values));self.assertTrue(any('可能都会永远无法醒来' in t for t in values))
 def test_candidates(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('조파','佐帕'),('각성의 향','觉醒之香')]:
   self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified');self.assertIn(ts[s]['source_string_id'],{e['id'] for e in self.p['entries']})
 def test_subtitle_prefix_and_opening(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),33);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:32]),232);new=load(p['plans'][32]['path']);self.assertEqual(new['resource'],'MC2Game/Movies/csm10-10.txt');self.assertEqual(len(new['entries']),2);self.assertEqual([e['translation'].count('<br>') for e in new['entries']],[1,0])
  for s in p['plans'][:33]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
  for e in new['entries']:self.assertLess(e['start'],e['end']);self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
if __name__=='__main__':unittest.main()
