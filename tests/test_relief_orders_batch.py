"""Source-free contracts for relief gameplay and the operation-order quest chain."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class ReliefOrdersTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-090.json');self.r=L('locales/zh-Hans/batch-090.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'02_3_01':15,'03_302_2':13,'03_302_0':16,'03_302_1':16,'Tutorial_Scene_22':4,'Valuables':2});self.assertEqual(len(self.p['entries']),66);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),31);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),20);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':46,'name':6,'system_message':3,'menu_option':1,'quest_description':4,'quest_objective':2,'tutorial':3,'item_description':1})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:89] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9126);self.assertEqual(len(ids),66);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_candidates_source_variants_and_item(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][427:432];self.assertEqual([(e['source'],e['target']) for e in terms],[('누렌스','努伦斯'),('작전 지령서','作战指令书'),('작전지령서','作战指令书'),('북부군 전령','北部军传令兵'),('부상자 치료','伤员救治')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));ts=[e['translation'] for e in self.p['entries']];self.assertIn('作战指令书',ts);self.assertIn('北部军的作战指令书',ts);self.assertIn('用于秘密传达北部军作战命令的指令书',ts);self.assertEqual(ts.count('伤员救治'),2)
 def test_tutorial_controls_hp_and_functional_tokens(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t.count('%s') for t in ts),4);self.assertEqual(sum(t.count('HP') for t in ts),3);self.assertTrue(any('只有洁菲能进行' in t for t in ts));self.assertIn('请在伤员的HP降到0之前，使用[左摇杆]\\n移动洁菲，为伤员治疗。\\n\\n[A键]消耗一个KAN，进行小回复，\\n[X键]消耗两个KAN，进行大回复。',ts);self.assertIn('QUEST%s: 消灭努伦斯',ts);self.assertIn('QUEST%s: 消灭北部军传令兵 (%s / %s)',ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_goals_not_overclaimed_and_distinct_orders(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('全力保住所有士兵' in t for t in ts));self.assertTrue(any('兵力损失，降到最低' in t for t in ts));self.assertFalse(any('保证成功且零伤亡' in t or '努伦斯坐标' in t for t in ts));self.assertTrue(any('不要主动进攻' in t for t in ts));self.assertTrue(any('可以先发制人' in t for t in ts));self.assertIn('听说，他们是3人一组行动的。',ts);self.assertEqual(sum(t=='现在，还不知道他在哪里，得亲自去找找。' for t in ts),2);self.assertIn('不需要……',ts)
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,90) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
