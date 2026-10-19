"""Source-free contracts for the two chapter-twelve confrontations."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class ConfrontationTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-065.json');self.r=load('locales/zh-Hans/batch-065.review.json')
 def test_scope_and_all_character_speech(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB12_030':19,'CSMB12_040':14,'CSMB12_050':25,'CSMB12_060':17,'Chapter12':4});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':79});self.assertEqual(self.r['status'],'draft')
 def test_source_locks_no_overlap_or_old_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:64] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7772,79));self.assertFalse(old&ids);self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(ids&{e['id'] for e in load('locales/zh-Hans/batch-063.review.json')['held_entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_shout_layout_and_punctuation(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual([e['translation'].count('\\n') for e in rows],[0,1,1,0]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),41);ts=[e['translation'] for e in self.p['entries']];self.assertIn('！！',ts);self.assertIn('……',ts);self.assertIn(r'站住！\n公主必须被处决！',ts)
 def test_positions_and_uncertainty_preserved(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('我认为，那才是正确的选择' in t for t in ts));self.assertTrue(any('我并不后悔' in t for t in ts));self.assertTrue(any('该离开了吧' in t and '也许' in t for t in ts));self.assertTrue(any('我是真心感谢你的' in t for t in ts));self.assertFalse(any('原谅你' in t for t in ts));self.assertTrue(any('如果当初' in t and '斯特拉斯' in t for t in ts))
 def test_existing_candidates_reused(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('라우드','劳德'),('알렉스','亚历克斯'),('스트라스','斯特拉斯'),('재화종','灾祸种'),('란츠하임','兰兹海姆')]:self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate')
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),37);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:37]),270)
  for s in p['plans'][:37]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
