"""Contracts for five complete Live1 narrative scenes, without game files."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class Live1StoryTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-095.json');self.r=L('locales/zh-Hans/batch-095.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_complete_scene_scope(self):
  self.assertEqual(len(self.p['entries']),201);self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB_Live1_001':12,'CSMB_Live1_002':87,'CSMB_Live1_003':33,'CSMB_Live1_004':31,'CSMB_Live1_005':38});self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),73);self.assertEqual(self.r['preserved_functional_break_ids'],[]);self.assertEqual(self.r['held_entries'],[]);self.assertEqual(self.r['status'],'draft');self.assertEqual({e['text_kind'] for e in self.r['entries']},{'dialogue'})
 def test_distinct_ids_and_previous_translations(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:94] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9609);self.assertEqual(len(ids),201);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'));self.assertNotIn('speaker',e)
 def test_shared_names_and_no_new_numerals(self):
  self.assertTrue(any('洁菲' in t for t in self.ts));self.assertTrue(any('阿维斯族' in t for t in self.ts));self.assertTrue(any('阿巴泽特' in t for t in self.ts));self.assertTrue(any('修恩扎伊特' in t and '兰兹海姆' in t for t in self.ts));self.assertFalse(any(c.isdigit() for t in self.ts for c in t));terms=L('locales/zh-Hans/terms.json')['terms'][:453];self.assertEqual(len(terms),453);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
 def test_honorific_changes_and_uncertain_explanations(self):
  self.assertTrue(any('公主殿下' in t for t in self.ts));self.assertTrue(any('女王' in t for t in self.ts));self.assertTrue(any('愚民' in t for t in self.ts));self.assertTrue(any('哥哥' in t for t in self.ts));self.assertTrue(any('失忆' in t and '吗' in t for t in self.ts));self.assertTrue(any('本性' in t and '难道' in t for t in self.ts));self.assertFalse(any('人格分裂症' in t or '确诊' in t for t in self.ts));self.assertIn('……',self.ts)
 def test_repeated_falls_and_open_ending(self):
  self.assertIn('啊，姐姐！你又摔倒了！',self.ts);self.assertEqual(self.ts[-1],'呃，完蛋了……');self.assertTrue(any('今晚的烤全鸡' in t and '吗' in t for t in self.ts));self.assertTrue(any('赌上这条命' in t for t in self.ts));self.assertTrue(any('没用过' in t or '连环术' in t for t in self.ts));self.assertTrue(any('变成可怕的姐姐' in t for t in self.ts));self.assertFalse(any('彻底康复了' in t for t in self.ts))
 def test_all_historical_held_and_subtitles(self):
  held={e['id'] for n in range(1,96) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
