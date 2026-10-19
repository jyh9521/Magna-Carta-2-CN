"""Source-free contracts for the recorded report, search lead and party stages."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class SentinelRecordTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-078.json');self.r=load('locales/zh-Hans/batch-078.review.json')
 def test_scope_types_and_breaks(self):
  c={e['section']:e['entries'] for e in self.r['coverage']};self.assertEqual({k:v for k,v in c.items() if not k.startswith('PartyTalk_')},{'CSMBQ08_10':20,'CSMBQ08_15':6,'9_cerestin_1':12});self.assertEqual({k:v for k,v in c.items() if k.startswith('PartyTalk_')},{'PartyTalk_Juto':4,'PartyTalk_Argo':4,'PartyTalk_Crocell':4,'PartyTalk_Rue':3,'PartyTalk_Celestin':4});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':55,'quest_description':1,'name':1});self.assertEqual(self.r['status'],'draft');self.assertEqual(len(self.r['preserved_functional_break_ids']),2);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),38)
 def test_disjoint_ids_and_eleven_silent_holds(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:77] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8591,57));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertEqual(len(self.r['held_entries']),11)
  held={e['id'] for n in range(1,79) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held)
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_report_uncertainty_and_wording_not_expanded(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('无法确定' in t and '意志' in t and '肉体' in t for t in ts));self.assertIn('在鲁哈尔特高原处理……塞蕾丝汀……很遗憾。',ts);self.assertTrue(any('哨兵巨大化，并陷入暴走' in t for t in ts));self.assertTrue(any('怪物型哨兵' in t for t in ts));self.assertIn('这种时候，可以哭的。',ts);self.assertFalse(any('已经证明是肉体导致' in t or '已在高原处决' in t for t in ts))
 def test_interrupted_clauses_and_quest_layout(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('不过，据我所知，拜泽恩这个人，已经……',ts);self.assertIn('去那里，应该就能找到。如果找到那块最大的残骸……',ts);self.assertIn('请在鲁哈尔特高原寻找石灰丘陵',ts);self.assertIn('拜泽恩之墓',ts);self.assertFalse(any(t=='……' for t in ts));self.assertFalse(any('\\n' in t for t in ts));ids=set(self.r['preserved_functional_break_ids']);self.assertTrue(all('line_break_policy' not in e for e in self.p['entries'] if e['id'] in ids))
 def test_alias_and_party_stage_distinctions(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),403);new=terms[402];self.assertEqual((new['source'],new['target'],new['form'],new['review_status'],new['relation']),('센티넬연구소','哨兵研究所','alias','candidate','unverified'));d={e['source']:e['target'] for e in terms};self.assertEqual(d['센티넬 연구소'],new['target']);self.assertEqual(d['석회 언덕'],'石灰丘陵');self.assertEqual(d['소용돌이 폭탄'],'漩涡炸弹');ts=[e['translation'] for e in self.p['entries']];self.assertIn('在露回来之前，先休息吧。',ts);self.assertTrue(any('没法用火破坏石像' in t and '风的力量' in t for t in ts))
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
