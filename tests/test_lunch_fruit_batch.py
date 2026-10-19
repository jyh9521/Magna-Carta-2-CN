"""Source-free contracts for the lunch delivery and fruit quest branches."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class LunchFruitTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-088.json');self.r=L('locales/zh-Hans/batch-088.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Ch01_103_0':13,'Ch01_103_1':20,'Default':2,'Valuables':2,'Weapon_onehanded sword_juto':1});self.assertEqual(len(self.p['entries']),38);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),18);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),12);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':26,'name':5,'system_message':2,'quest_description':2,'quest_objective':1,'item_description':2})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:87] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9016);self.assertEqual(len(ids),38);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_names_and_candidates(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('莉安娜',ts);self.assertIn('哈曼',ts);self.assertIn('便当 ',ts);self.assertIn('莉安娜亲手做的便当',ts);terms=L('locales/zh-Hans/terms.json')['terms'][416:420];self.assertEqual([(e['source'],e['target']) for e in terms],[('리안나','莉安娜'),('하만','哈曼'),('마마 웜','玛玛蠕虫'),('리안나의 도시락','莉安娜的便当')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
 def test_functional_tokens_and_sword(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('QUEST%s: 获得莉安娜的便当',ts);self.assertIn('QUEST%s: 获得利安达尔果实 (%s / %s)',ts);self.assertEqual(sum(t.count('%s') for t in ts),4);self.assertIn('木剑\\n攻击+5',ts);self.assertIn('请将莉安娜的便当\\n送给正在青灵森林工作的[哈曼]',ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_distinct_branches_and_unfinished_grief(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t=='他们应该都在森林入口附近。从东边的升降梯过去，比较方便吧？' for t in ts),2);self.assertIn('朱……朱特……呜呜……大叔……大叔已经……',ts);self.assertIn('呃……我……要是，我能再快一点……',ts);self.assertIn('呃……我……我要是，能再快一点……',ts);self.assertTrue(any('爸爸……爸爸！！' in t for t in ts));self.assertFalse(any('大叔已经成功获救' in t or '倒计时60秒' in t for t in ts));self.assertTrue(any('角十分危险' in t for t in ts))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,88) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
