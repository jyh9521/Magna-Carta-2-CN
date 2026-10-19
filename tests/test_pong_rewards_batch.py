"""Source-free contracts for pong rules, reward tables and descriptions."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class PongRewardTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-086.json');self.r=L('locales/zh-Hans/batch-086.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'pong game':25,'Recover':9,'Karmond':3,'Tutorial_Scene_21':3});self.assertEqual(len(self.p['entries']),40);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),14);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),19);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':21,'system_message':4,'name':5,'item_description':6,'effect_description':2,'tutorial':2})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:85] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8933);self.assertEqual(len(ids),40);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_price_threshold_and_reward_table(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('客人也想试试吗？\\n只要1000SID。\\n怎么样？',ts);self.assertIn('超过20分，还有奖品哦！',ts);self.assertIn('20分: 治愈叶\\n25分: 疗愈花',ts);self.assertIn('30分: 英雄卡蒙德\\n不过，这个奖品只发放一次，\\n之后会改发苏生丸。',ts);self.assertFalse(any('至少20分' in t for t in ts));es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_item_values_and_trailing_spaces(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t=='恢复1名我方成员700点体力 ' for t in ts),2);self.assertEqual(sum(t=='恢复全体我方成员1500点体力 ' for t in ts),2);self.assertIn('使全体无法战斗的我方成员以20%体力复苏 ',ts);self.assertIn('使全体无法战斗的我方成员\\n以20%体力复苏 ',ts);self.assertIn('攻击+10\\n防御+10',ts);self.assertIn('特殊卡蒙德\\n攻击+10 防御+10',ts)
 def test_tutorial_and_candidate_terms(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('捕捉怪物[蓬蓬]',ts);self.assertTrue(any('只有阿尔戈能参加' in t and '手持锤子' in t for t in ts));self.assertTrue(any('限定时间' in t and '抓得越多' in t for t in ts));terms=L('locales/zh-Hans/terms.json')['terms'][411:415];self.assertEqual([(e['source'],e['target']) for e in terms],[('힐 리프','治愈叶'),('큐어 플라워','疗愈花'),('영웅의 카몬드','英雄卡蒙德'),('소생환','苏生丸')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,86) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
