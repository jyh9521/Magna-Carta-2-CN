"""Contracts for seven complete Live2 scenes and their two distinct viewpoints."""
from pathlib import Path
import unittest,json,hashlib,re
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class Live2StoryTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-096.json');self.r=L('locales/zh-Hans/batch-096.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_complete_scene_scope(self):
  self.assertEqual(len(self.p['entries']),186);self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB_Live2_001':42,'CSMB_Live2_002':17,'CSMB_Live2_003':18,'CSMB_Live2_004':37,'CSMB_Live2_005':27,'CSMB_Live2_006':28,'CSMB_Live2_007':17});self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),91);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertFalse(self.r['held_entries']);self.assertEqual(self.r['status'],'draft');self.assertEqual({e['text_kind'] for e in self.r['entries']},{'dialogue'})
 def test_distinct_ids_and_previous_translations(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:95] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9810);self.assertEqual(len(ids),186);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'));self.assertNotIn('speaker',e)
 def test_shared_terms_and_exact_ages(self):
  for term in ['贝尔利内特王室','伊芙琳','贝尔福特','阿巴泽特','哨兵','修恩扎伊特']:self.assertTrue(any(term in t for t in self.ts))
  self.assertEqual([x for t in self.ts for x in re.findall(r'[0-9]+',t)],['9','9']);self.assertIn('……',self.ts);self.assertEqual(len(L('locales/zh-Hans/terms.json')['terms'][:453]),453)
 def test_viewpoints_not_flattened(self):
  self.assertTrue(any('受了很重的伤' in t and '露' in t for t in self.ts));self.assertTrue(any('其实，我' in t and '没有受伤' in t for t in self.ts));self.assertTrue(any('绝不能告诉公主殿下' in t and '演戏' in t for t in self.ts));self.assertTrue(any('或许' in t and '演戏' in t for t in self.ts));self.assertTrue(any('希望' in t and '父亲' in t for t in self.ts));self.assertTrue(any('先王陛下' in t for t in self.ts));self.assertFalse(any('亲生父亲' in t or '人格分裂症' in t for t in self.ts))
 def test_food_jokes_and_open_questions(self):
  for t in ['盐味苹果派','巧克力','胡椒','特制三文鱼排','芥末','蜂蜜','鲜奶油','番茄酱']:self.assertTrue(any(t in x for x in self.ts))
  self.assertFalse(any('香煎' in t or '确诊中毒' in t for t in self.ts));self.assertTrue(any('下锅' in t for t in self.ts));self.assertTrue(any('什么正义可言' in t for t in self.ts));self.assertTrue(any('独自' in t or '一个人' in t for t in self.ts));self.assertEqual(self.ts[-1],'呃……那我就，不客气了。')
 def test_all_historical_held_and_subtitles(self):
  held={e['id'] for n in range(1,97) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
