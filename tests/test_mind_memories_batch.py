"""Source-free contracts for remembered island/war scenes and reality-side defense."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class MindMemoriesTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-054.json');self.r=load('locales/zh-Hans/batch-054.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':93,'MC2Compose.int':4,'MC2NpcTalk.int':12});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':105,'narrative':4});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:53] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6846,109));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_memory_and_reality_viewpoints(self):
  values=[e['translation'] for e in self.p['entries']];self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),42);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertTrue(any('朱特是这座岛上生长的一种草' in t for t in values));self.assertTrue(any('我才是朱特' in t for t in values));self.assertIn('在朱特的精神世界里……',values);self.assertIn('水色湿地的阿尔戈一行……',values);self.assertTrue(any('我们这边已经结束' in t for t in values));self.assertTrue(any('公主和露顺利' in t for t in values))
 def test_existing_term_alias_and_cat_speech(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']};e=ts['물빛저습지'];self.assertEqual(e['target'],ts['물빛 저습지']['target']);self.assertEqual(e['target'],'水色湿地');self.assertEqual(e['review_status'],'candidate');self.assertEqual(e['relation'],'unverified');self.assertIn(e['source_string_id'],{e['id'] for e in self.p['entries']})
  values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('火之KAN' in t for t in values));self.assertEqual(sum('喵' in t for t in values),7);self.assertTrue(any('猫猫可还在打仗喵' in t for t in values));self.assertTrue(any('不知道什么时候才能恢复航行喵' in t for t in values))
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),33);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:33]),234)
  for s in p['plans'][:33]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
