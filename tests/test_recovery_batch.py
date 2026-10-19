"""Source-free contracts for Juto recovery and the held editor-annotated line."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RecoveryTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-056.json');self.r=load('locales/zh-Hans/batch-056.review.json')
 def test_scope(self):
  self.assertEqual(self.r['coverage'],[{'document':'MC2CSMB.int','section':'CSMB10_80','entries':75}]);self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':72,'narrative':3});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:55] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7028,75));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_editor_note_is_held(self):
  self.assertEqual(len(self.r['held_entries']),1);h=self.r['held_entries'][0];self.assertEqual((h['document'],h['section'],h['key']),('MC2CSMB.int','CSMB10_80','voc_csmb_1080_48'));self.assertNotIn(h['id'],{e['id'] for e in self.p['entries']});self.assertRegex(h['source_sha256'],r'^[0-9a-f]{64}$');self.assertIn('编辑注记',h['reason']);self.assertTrue(all('游戏中不出现' not in e['translation'] for e in self.p['entries']));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),40)
 def test_commitment_and_narrative_not_final_ending(self):
  values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('不能违抗公主的命令' in t for t in values));self.assertTrue(any('好好休息' in t for t in values));self.assertTrue(any('一直赎罪，继续活下去' in t for t in values));self.assertTrue(any('寻找其他办法' in t for t in values));self.assertTrue(any('意想不到的选择' in t for t in values));self.assertFalse(self.r['preserved_functional_break_ids'])
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),35);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:35]),254)
  for s in p['plans'][:35]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
