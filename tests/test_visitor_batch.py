"""Source-free regression contracts for the visitor and historical discussion."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class VisitorTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-058.json');self.r=load('locales/zh-Hans/batch-058.review.json')
 def test_scope(self):
  self.assertEqual({(e['document'],e['section']):e['entries'] for e in self.r['coverage']},{('MC2CSMB.int','CSMB11_10'):19,('MC2CSMB.int','CSMB11_15'):7,('MC2CSMB.int','CSMB11_20'):15,('MC2Compose.int','Chapter11'):6,('MC2NpcTalk.int','10_kotamare_melisa'):9})
  self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':50,'narrative':6});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
 def test_unique_source_locked_edits(self):
  w=load('locales/zh-Hans/translation-workflow.json');old={e['id'] for b in w['batches'][:57] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7195,56));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_layout_and_theories(self):
  self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),34)
  for e in self.p['entries']:
   self.assertNotIn('\\n',e['translation'])
   if 'line_break_policy' in e:self.assertGreater(e['line_break_policy']['source_count'],0);self.assertEqual(e['line_break_policy']['target_count'],0)
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('150年' in t for t in ts));self.assertTrue(any('祖先吧？' in t for t in ts));self.assertTrue(any('我倒觉得' in t and '本人' in t for t in ts));self.assertTrue(any('似乎' in t and '平息' in t for t in ts));self.assertIn('我以为她是北部军的残党，起初本来想解决掉她，',ts)
 def test_shared_candidates_reused(self):
  ts={t['source']:t for t in load('locales/zh-Hans/terms.json')['terms']}
  for source,target in [('마비향','麻痹香'),('타스','塔斯'),('스라츠','斯拉茨'),('마그나카르타','玛格纳卡尔塔'),('트레와 족','特雷瓦族')]:self.assertEqual(ts[source]['target'],target);self.assertEqual(ts[source]['review_status'],'candidate')
 def test_historical_inscriptions_unchanged(self):
  rows=[e for e in load('locales/zh-Hans/batch-057.json')['entries'] if e['id'] in load('locales/zh-Hans/batch-057.review.json')['preserved_functional_break_ids']];self.assertEqual([e['translation'].count('\\n') for e in rows],[2,2,2,2,3]);self.assertTrue(rows[3]['translation'].endswith('    '));self.assertEqual(sum(len(load(p['path'])['entries']) for p in load('locales/zh-Hans/subtitle-profile.json')['plans'][:35]),254)
if __name__=='__main__':unittest.main()
