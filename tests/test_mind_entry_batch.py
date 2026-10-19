"""Source-free contracts for the Kamond replacement and mind-entry scene."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class MindEntryTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-053.json');self.r=load('locales/zh-Hans/batch-053.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':69,'MC2Compose.int':4,'MC2Quest.int':12,'MC2Item.int':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':77,'narrative':3,'name':3,'quest_progress':2,'quest_description':1,'item_description':1});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:52] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6759,87));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_layout_and_viewpoints(self):
  rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),1);self.assertEqual(rows[0]['translation'].count('\\n'),2);self.assertNotIn('line_break_policy',rows[0]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),35)
  values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('2个人' in t for t in values));self.assertIn('QUEST%s：获得超越卡蒙德',values);self.assertTrue(any(t.startswith('据说连死者') for t in values));self.assertTrue(any('终究只是幻象' in t for t in values));self.assertIn('我会阻止这些化为实体的黑暗攻击朱特和公主一行。',values)
 def test_candidates_and_spacing_alias(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('정신접촉','精神接触'),('정신 접촉','精神接触'),('정신 세계','精神世界'),('초월의 카몬드','超越卡蒙德')]:
   self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified');self.assertIn(ts[s]['source_string_id'],{e['id'] for e in self.p['entries']})
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),33);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:33]),234)
  for s in p['plans'][:33]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
