"""Source-free contracts for the defense, farewell and chapter-eleven close."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class FarewellTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-062.json');self.r=load('locales/zh-Hans/batch-062.review.json')
 def test_scope(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB11_71':12,'CSMB11_80':10,'CSMB11_90':13,'CSMB11_93':3,'CSMB11_100':17,'CSMB11_110':22,'10_kotamare_after':23,'Chapter11':8});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':95,'narrative':13});self.assertEqual(self.r['status'],'draft')
 def test_source_locks_and_no_overlap(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:61] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7504,108));self.assertFalse(old&ids);self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_interception_layout(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual(len(rows),6);self.assertTrue(all(e['translation'].count('\\n')==1 and 'line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),60)
  self.assertTrue(all('伊格顿' in e['translation'] or '材料' in e['translation'] for e in rows))
 def test_narrator_rumor_and_epitaph(self):
  ids={e['id'] for e in self.r['entries'] if e['text_kind']=='narrative'};ts=[e['translation'] for e in self.p['entries'] if e['id'] in ids];self.assertIn('勇敢的战士梅莉莎，长眠于此……',ts);self.assertTrue(any('魔女洁菲' in t and '传闻' in t for t in ts));self.assertTrue(any('真的成了世界的敌人' in t for t in ts));self.assertTrue(any('32-36' in n and '待审计' in n for n in self.r['notes']))
 def test_sibling_and_positions_remain_distinct(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('就像我保护妹妹一样，你们也要守护公主殿下，直到最后！',ts);self.assertTrue(any('随时欢迎各位' in t for t in ts));self.assertTrue(any('希望各位能离开这里' in t for t in ts));self.assertFalse(any('弟弟' in t for t in ts));self.assertTrue(any('据说' in t and '缘分' in t for t in ts))
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),37);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:37]),270)
  for s in p['plans'][:37]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
