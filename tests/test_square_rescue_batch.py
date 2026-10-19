"""Source-free contracts for rescue, retreat and linked split-log holds."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class SquareRescueTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-051.json');self.r=load('locales/zh-Hans/batch-051.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':100,'MC2Compose.int':6});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':97,'narrative':9});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:50] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6538,106));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_linked_fragments_and_prior_corrupt_source_held(self):
  held=self.r['held_entries'];self.assertEqual({(e['document'],e['section'],e['key']) for e in held},{('MC2UI.int','Battle_Log','beeljebubRecover_1'),('MC2UI.int','Battle_Log','beeljebubRecover_2')});ids={e['id'] for e in self.p['entries']};self.assertTrue(all(e['id'] not in ids for e in held));self.assertTrue(all('拼接' in e['reason'] for e in held));self.assertNotIn(load('locales/zh-Hans/batch-050.review.json')['held_entries'][0]['id'],ids);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),52)
 def test_candidate_and_narrative_questions(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']};e=ts['벨제붑'];self.assertEqual(e['target'],'别西卜');self.assertEqual(e['review_status'],'candidate');self.assertEqual(e['relation'],'unverified');self.assertIn(e['source_string_id'],{e['id'] for e in self.p['entries']})
  values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('自然灾害吗？' in t for t in values));self.assertTrue(any('难民，到底消失到哪里去了？' in t for t in values));self.assertTrue(any(t=='那一天，我们成了世界的敌人。' for t in values))
 def test_subtitle_prefix_and_rescue(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),32);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:31]),207);new=load(p['plans'][31]['path']);self.assertEqual(new['resource'],'MC2Game/Movies/csm09-40.txt');self.assertEqual(len(new['entries']),25);self.assertEqual(sum(e['translation'].count('<br>') for e in new['entries']),15)
  for s in p['plans'][:32]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
  for e in new['entries']:self.assertLess(e['start'],e['end']);self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
if __name__=='__main__':unittest.main()
