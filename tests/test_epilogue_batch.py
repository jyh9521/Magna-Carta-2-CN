"""Source-free contracts for epilogue speech, recollection and future hopes."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class EpilogueTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-073.json');self.r=load('locales/zh-Hans/batch-073.review.json')
 def test_scope_and_narrative_classification(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBE_10':17,'CSMBE_20':13,'CSMBE_30':16,'CSMBE_40':5});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':43,'narrative':8});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries']);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),33)
 def test_no_overlap_or_held_changes(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:72] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8320,51));self.assertFalse(old&ids);self.assertFalse(ids&{e['id'] for n in [63,68] for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json')['held_entries']});self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_three_year_fields_and_actual_narration(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual([re.findall(r'[0-9]+',t) for t in ts if re.search(r'[0-9]',t)],[['3'],['3'],['3']]);kinds={e['id']:e['text_kind'] for e in self.r['entries']};ns=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='narrative'];self.assertEqual(len(ns),8);self.assertIn('卡尔玛被弃置，哨兵陷入了沉睡……',ns);self.assertTrue(any('世界存续了下来' in t for t in ns));self.assertTrue(any('我仍然坚信' in t for t in ns));self.assertFalse(any('哨兵全部死亡' in t for t in ts))
 def test_rumours_predictions_and_reunion_not_expanded(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('听说' in t and '好几十个人' in t for t in ts));self.assertTrue(any('说不定还能飞上天空' in t for t in ts));self.assertTrue(any('应该就能代替卡尔玛' in t for t in ts));self.assertIn('开玩笑的。',ts);self.assertTrue(any('并不后悔' in t for t in ts));self.assertFalse(any('已经结婚' in t for t in ts))
 def test_existing_terms_reused(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),390);ts={e['source']:e['target'] for e in terms}
  for s,t in [('르제필다','蕾洁菲尔妲'),('치유연환술','治愈连环术'),('카르마','卡尔玛'),('재화종','灾祸种'),('코타마레','柯塔马雷')]:self.assertEqual(ts[s],t)
 def test_all_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
