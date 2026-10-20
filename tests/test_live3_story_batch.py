"""Contracts for complete Live3 dialogue and the three dramas' associated UI."""
from pathlib import Path
import unittest,json,hashlib,re,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class Live3StoryTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-097.json');self.r=L('locales/zh-Hans/batch-097.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_complete_scene_and_ui_scope(self):
  self.assertEqual(len(self.p['entries']),186);self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB_Live3_001':22,'CSMB_Live3_002':35,'CSMB_Live3_003':22,'CSMB_Live3_004':48,'CSMB_Live3_005':10,'CSMB_Live3_006':38,'Live Drama':11});self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),99);self.assertEqual(len(self.r['preserved_functional_break_ids']),11);self.assertFalse(self.r['held_entries']);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':175,'name':6,'narrative':3,'menu_option':2})
 def test_distinct_ids_and_previous_translations(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:96] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9996);self.assertEqual(len(ids),186);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'));self.assertNotIn('speaker',e)
 def test_new_candidates_and_source_numeral(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][453:455];self.assertEqual([(e['source'],e['target']) for e in terms],[('쳉','铖'),('라이브 드라마','短剧')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));self.assertEqual([x for t in self.ts for x in re.findall(r'[0-9]+',t)],['3']);self.assertTrue(any('铖' in t for t in self.ts));self.assertTrue(any('猫猫不是宠物' in t for t in self.ts));self.assertTrue(any('特雷瓦族' in t for t in self.ts))
 def test_associated_summaries_keep_layout(self):
  game_break=chr(92)+'n';summaries=[t for e,t in zip(self.r['entries'],self.ts) if e['text_kind']=='narrative'];self.assertEqual(len(summaries),3);self.assertEqual([t.count(game_break) for t in summaries],[7,7,7]);self.assertEqual([[i for i,s in enumerate(t.split(game_break)) if not s] for t in summaries],[[3],[2,5],[4]]);self.assertTrue(summaries[2].startswith(' '));self.assertEqual(sum(t.startswith(' ') for t in self.ts),1);self.assertIn('洁菲, 朱特, 塞蕾丝汀, 伊格顿',self.ts);self.assertIn('另一个洁菲',self.ts);self.assertIn('回忆',self.ts);self.assertIn('被讨厌的人',self.ts);self.assertIn('是否结束短剧？',self.ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_speculation_and_reported_cat_story(self):
  self.assertTrue(any('或许' in t and '血腥味' in t for t in self.ts));self.assertTrue(any('可能' in t and '相处的时间不够' in t for t in self.ts));self.assertTrue(any('听说' in t and '临死' in t for t in self.ts));self.assertTrue(any('不知道是不是' in t and '体弱' in t for t in self.ts));self.assertFalse(any('确认是杀手' in t or '小猫全死了' in t for t in self.ts));self.assertIn('……',self.ts);self.assertTrue(any('反哨兵部队' in t for t in self.ts))
 def test_old_held_and_all_subtitle_plans(self):
  held={e['id'] for n in range(1,98) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
