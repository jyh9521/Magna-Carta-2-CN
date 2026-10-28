"""Source-free regression contracts for the cost of paradise scene."""
from collections import Counter
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class ParadiseTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-059.json');self.r=load('locales/zh-Hans/batch-059.review.json')
 def test_scope_and_narrator(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB11_30':88,'CSMB11_32':25});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':111,'narrative':2});self.assertEqual(self.r['status'],'draft')
  ids={e['id'] for e in self.r['entries'] if e['text_kind']=='narrative'};self.assertEqual([e['translation'] for e in self.p['entries'] if e['id'] in ids],['仿佛在迷雾中徘徊许久，终于找到了名为拉·斯特拉达的路标。','如今，已经不必再迷惘。只要向前迈进就好。'])
 def test_source_locks_and_disjoint_ids(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:58] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7251,113));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_layout_and_punctuation(self):
  self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),74)
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('……！',ts);self.assertIn('……',ts)
  for e in self.p['entries']:
   self.assertNotIn('\\n',e['translation'])
   if 'line_break_policy' in e:self.assertGreater(e['line_break_policy']['source_count'],0);self.assertEqual(e['line_break_policy']['target_count'],0)
 def test_numbers_and_uncertain_claims(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum('800年' in t for t in ts),1);self.assertEqual(sum('150年' in t for t in ts),2);self.assertTrue(any('去世吧' in t for t in ts));self.assertTrue(any('看来' in t and '北部军' in t for t in ts));self.assertTrue(any('不敢保证' in t for t in ts));self.assertTrue(any('据' not in t and '听说' in t and 'KAN流' in t for t in ts))
 def test_candidates_reused_not_approved(self):
  ts={t['source']:t for t in load('locales/zh-Hans/terms.json')['terms']}
  for source,target in [('필러','晶柱'),('이그톤','伊格顿'),('마그나카르타','真名法典'),('스트라스','斯特拉斯')]:self.assertEqual(ts[source]['target'],target);self.assertEqual(ts[source]['review_status'],'candidate')
if __name__=='__main__':unittest.main()
