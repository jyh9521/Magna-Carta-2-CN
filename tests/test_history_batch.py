"""Source-free contracts for the five inscriptions and historical records."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class HistoryTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-057.json');self.r=load('locales/zh-Hans/batch-057.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':85,'MC2Compose.int':5,'MC2Item.int':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':85,'narrative':5,'name':1,'item_description':1});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:56] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7103,92));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_inscription_order_layout_and_numbers(self):
  rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),5);self.assertEqual([e['translation'].count('\\n') for e in rows],[2,2,2,2,3]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertTrue(rows[3]['translation'].endswith('    '));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),62)
  values=[e['translation'] for e in self.p['entries']];self.assertIn('马雷族印章 ',values);self.assertTrue(any('18岁' in t for t in values));self.assertTrue(any('800余年' in t for t in values));self.assertTrue(any('150年' in t for t in values));self.assertTrue(any('会不会是自然发出的强烈警告' in t for t in values))
 def test_candidate_names_not_collapsed(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('아비스 전쟁','阿维斯战争'),('타스','塔斯'),('스라츠','斯拉茨'),('데몬','恶魔'),('쉐도우','暗影'),('마레의 인장','马雷族印章'),('스트라스의 비석','斯特拉斯石碑')]:
   self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified');self.assertIn(ts[s]['source_string_id'],{e['id'] for e in self.p['entries']})
  self.assertEqual(ts['스트라스']['target'],'斯特拉斯');self.assertNotEqual(ts['스트라스']['target'],ts['스라츠']['target'])
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),35);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:35]),254)
  for s in p['plans'][:35]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
