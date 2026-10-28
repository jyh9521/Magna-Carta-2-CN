"""Source-free square-speech, held corrupt source, and opening subtitle contracts."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class SquareSpeechTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-050.json');self.r=load('locales/zh-Hans/batch-050.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':68,'MC2Compose.int':5,'MC2NpcTalk.int':20});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':88,'narrative':5});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:49] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6445,93));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_corrupt_source_is_held(self):
  self.assertEqual(len(self.r['held_entries']),1);h=self.r['held_entries'][0];self.assertEqual((h['document'],h['section'],h['key']),('MC2CSMB.int','CSMB09_20','voc_csmb_0920_06'));self.assertNotIn(h['id'],{e['id'] for e in self.p['entries']});self.assertRegex(h['source_sha256'],r'^[0-9a-f]{64}$');self.assertIn('감Ｒ',h['reason']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),64);self.assertFalse(self.r['preserved_functional_break_ids'])
 def test_existing_candidates_and_distinct_speakers(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('라 스트라다','拉·斯特拉达'),('스트라스','斯特拉斯'),('마그나카르타','真名法典')]:
   self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate')
  values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('谎言' in t for t in values));self.assertTrue(any('诬为叛徒' in t for t in values));self.assertTrue(any('不能在这里闹事' in t for t in values))
 def test_subtitle_prefix_and_opening(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),31);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:30]),203);new=load(p['plans'][30]['path']);self.assertEqual(new['resource'],'MC2Game/Movies/csm09-10.txt');self.assertEqual(len(new['entries']),4)
  for s in p['plans'][:31]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
  for e in new['entries']:self.assertLess(e['start'],e['end']);self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
if __name__=='__main__':unittest.main()
