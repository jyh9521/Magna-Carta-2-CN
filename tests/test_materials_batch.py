"""Source-free contracts for the teleport-core material chain."""
from collections import Counter
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class MaterialsTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-060.json');self.r=load('locales/zh-Hans/batch-060.review.json')
 def test_scope_and_stages(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB11_35':21,'11_1002_0':9,'11_363_0':15,'11_363_1':5,'11_1002_1':17,'Chapter11':6,'Valuables':8,'CSMB11_40':8});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':61,'name':8,'quest_progress':6,'narrative':6,'quest_description':4,'item_description':4});self.assertEqual(self.r['status'],'draft')
 def test_unique_source_locks(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:59] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7364,89));self.assertFalse(old&ids);self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_layout_tokens_spaces(self):
  ids=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in ids];self.assertEqual([e['translation'].count('\\n') for e in rows],[2,3,0,1]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),38)
  values=[e['translation'] for e in self.p['entries']];self.assertIn('QUEST%s: 梅雷花粉 (%s/%s)',values);self.assertIn('QUEST%s: 黑珍珠 (%s/%s)',values);self.assertIn('QUEST%s: 获得巨型卡蒙德',values);self.assertIn('请找来4份花粉、2颗珍珠喵。',values);self.assertIn('梅雷花粉 ',values);self.assertIn('猫猫有收集闪亮物品的习性。 ',values);self.assertIn('请把特种合金带给柯塔马雷的伊格顿',values)
 def test_new_candidates_not_approved_or_conflated(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for source,target in [('특수합금','特种合金'),('메레','梅雷'),('메레의 꽃가루','梅雷花粉'),('검은 진주','黑珍珠'),('블레보러','布莱博拉'),('아이보러','艾博拉'),('영겁의 카몬드','永劫卡蒙德'),('전송장치','传送装置'),('거대한 카몬드','巨型卡蒙德'),('코어','核心')]:self.assertEqual(ts[source]['target'],target);self.assertEqual(ts[source]['review_status'],'candidate');self.assertEqual(ts[source]['relation'],'unverified');self.assertIn(ts[source]['source_string_id'],{e['id'] for e in self.p['entries']})
  self.assertNotEqual(ts['영겁의 카몬드']['target'],ts['거대한 카몬드']['target'])
 def test_no_early_subtitle_or_mail_claims(self):
  self.assertEqual(sum(len(load(p['path'])['entries']) for p in load('locales/zh-Hans/subtitle-profile.json')['plans'][:35]),254);self.assertTrue(any('11_303_0' in n and '不擅自纠正' in n for n in self.r['notes']))
if __name__=='__main__':unittest.main()
