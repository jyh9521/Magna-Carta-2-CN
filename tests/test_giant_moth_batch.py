"""Source-free contracts for the giant moth hunt and elemental item set."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class GiantMothTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-070.json');self.r=load('locales/zh-Hans/batch-070.review.json')
 def test_scope_and_explicit_kinds(self):
  self.assertEqual({(e['document'],e['section']):e['entries'] for e in self.r['coverage']},{('MC2Quest.int','12_GiantMoth_0'):10,('MC2Quest.int','12_GiantMoth_1'):22,('MC2Quest.int','12_GiantMoth_2'):20,('MC2Quest.int','12_GiantMoth_3'):3,('MC2Quest.int','12_GiantMoth_4'):18,('MC2Item.int','FieldAction'):10,('MC2Item.int','Valuables'):10});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':55,'name':15,'quest_description':5,'quest_progress':8,'item_description':10});self.assertEqual(self.r['status'],'draft')
 def test_no_overlap_or_previous_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:69] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8105,93));self.assertFalse(old&ids);self.assertFalse(ids&{e['id'] for n in [63,68] for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json')['held_entries']});self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_progress_order_layout_and_item_spaces(self):
  kinds={e['id']:e['text_kind'] for e in self.r['entries']};progress=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='quest_progress'];els=['火之精气','水之精气','风之精气','雷之精气'];self.assertEqual(progress,['QUEST : 获得'+t for t in els]+els);des=[e for e in self.p['entries'] if kinds[e['id']]=='quest_description'];self.assertEqual([e['translation'].count('\\n') for e in des],[1,2,4,1,2]);self.assertTrue(all('line_break_policy' not in e for e in des));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),46);self.assertEqual(len(self.r['preserved_functional_break_ids']),18);self.assertEqual(sum(e['translation'].endswith(' ') for e in self.p['entries']),8)
 def test_eye_item_not_english_key_and_claims_not_facts(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('KAN之眼',ts);self.assertIn('能够看见平时不可见的KAN精气的眼镜',ts);self.assertIn('我想，巨蛾大概具有追逐光亮的习性。',ts);self.assertTrue(any('还从未有人捕获过它' in t for t in ts));self.assertTrue(any('抓蓬蓬来卖' in t for t in ts));self.assertTrue(any('[雷之精气]位于鲁哈尔特盆地' in t for t in ts));self.assertFalse(any('水之魂' in t for t in ts))
 def test_candidates_alias_and_unverified_state(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];new=terms[371:383];self.assertEqual(len(new),12);self.assertEqual({e['source']:e['target'] for e in new},{'자이언트 모스':'巨蛾','자이언트모스':'巨蛾','칸의 정기':'KAN精气','불의 정기':'火之精气','물의 정기':'水之精气','바람의 정기':'风之精气','번개의 정기':'雷之精气','불의 그릇':'火之容器','물의 그릇':'水之容器','번개의 그릇':'雷之容器','바람의 그릇':'风之容器','칸 아이즈':'KAN之眼'});self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));self.assertEqual(new[1]['form'],'alias');self.assertIn('不凭英文key',new[-1]['basis'])
 def test_previous_subtitle_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),38);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:38]),271)
  for s in p['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
