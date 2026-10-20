"""Source-free contracts for special and combined-stat accessory groups."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class SpecialAccessoryTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-106.json');self.r=load('locales/zh-Hans/batch-106.review.json');self.by={e['id']:e['translation'] for e in self.p['entries']};self.ts=list(self.by.values())
 def test_complete_scope(self):
  self.assertEqual(len(self.ts),225);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['held_entries'],[]);self.assertEqual(self.r['coverage'],[dict(document='MC2Item.int',section='Accessory',entries=225)])
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':75,'item_description':150});self.assertEqual(set(self.by),{e['id'] for e in self.r['entries']})
 def test_old_and_held_preserved(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:105] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),11848);self.assertFalse(old&self.by.keys())
  held={e['id'] for n in range(1,107) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&self.by.keys())
 def test_math_widths_and_layout(self):
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']));self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('+', 206), ('%', 52), ('．', 10), ('ＳＩＤ', 2), ('－', 4), ('~', 3), ('～', 1), ('\\n', 153)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_revival_cat_and_stat_source_differences(self):
  expected={'coalesced:d5c319ee5a2c3339798829ce446cbbe6f652aaf2530a088ac1e8f7bbbdbb1a77': '饰品\\n额外获得ＳＩＤ30%', 'coalesced:c9eb81038943e9f50db13ff56c98e9fbdbc0b30cd81815cb73f0506fe6aaac60': '饰品\\n力量KAN生成量为1．5倍', 'coalesced:ba8b4149b3986451b68cf0dde47497d2e9df61e5128f34c6b76dd7169296a924': '饰品\\n耐力消耗－10%', 'coalesced:7cd025f53b699f749920319374be75ae63ce52a8a816b09ba577107a84502be7': '饰品\\n死亡时以体力30%的状态自动复活\\n使用一次后饰品就会损坏', 'coalesced:751d790c8467fbb5fb1aa7afaa0668b40663e881e9d344117708414bd612433a': '饰品\\n以体力30%的状态自动复活', 'coalesced:46255566b443f3a30aba5b546cbbe6c93ab1b45f0e6f319b0651510d0bb263ce': '饰品\\n死亡时以体力50%的状态自动复活\\n使用一次后饰品就会损坏', 'coalesced:3b81b89d958addf3560553eab72bf29d8cb633561e81c92f7621e0ce72ad2c5d': '饰品\\n死亡时以体力80%的状态自动复活\\n使用一次后饰品就会损坏', 'coalesced:cdfaeb1f5ed0d5dbdd585ab2da6c377df8d588149636d84e0f63864509ec83e8': '饰品\\n体力+30% 速度+15', 'coalesced:89252da9acb58ea69e56c97a69a3e5f5666fffdef1da13f60e58f3217c20a36f': '饰品\\n体力+10% 速度+20', 'coalesced:c36de3370877d5d35275798dd0c64981f3d8b1bd37b4b06c8e4f9845a43f1c68': '饰品\\n体力+30% 速度+10', 'coalesced:cdd4f734546d06c8817c42ff920bca69d3352ae043feaaa10d987a6bb3a99d0b': '饰品\\n攻击+20 速度+10', 'coalesced:4f360732cfdeea03800b153250dfc9d30e5f9f98b2334ee5190b49e10e240cad': '像猫猫一样变快喵~\\n速度+8', 'coalesced:84e740f05bd8c04c956cc6a307bbe2bb530a516f487f396c3638bb3d9560ffbb': '是饰品喵～\\n速度+8', 'coalesced:1983f976a1ec95fe8491465c8541a298a15bcc126fe0a3febab9746afc60aaa4': '像猫猫一样变强喵~\\n攻击+8', 'coalesced:229732147d57c2a49dd8cfdc31d3a29a00cde0b0f5d462180bb60941724a144a': '是饰品喵~\\n攻击+8', 'coalesced:e56afb2bdf571f07a21a41345fdd4e89c0bc8d6870cc4e406d0f1d0306ed4ed1': '艾尔加的耳环\\n全能力值+15 ', 'coalesced:fc1ed6d930286db0d79813008b57fb0a06086268137f93668feb0200f09fdb04': '饰品\\n全能力值+15 '}
  for i,t in expected.items():self.assertEqual(self.by[i],t)
  self.assertEqual(sum('使用一次后饰品就会损坏' in t for t in self.ts),3)
 def test_reuse_and_candidate_append(self):
  ts=load('locales/zh-Hans/terms.json')['terms'];new=ts[852:885];self.assertEqual(len(new),33);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new))
  self.assertNotIn('눈의 수정',{e['source'] for e in new});self.assertIn('雪水晶',self.ts);self.assertIn('生命与隼戒指',self.ts);self.assertIn('力量与魔力戒指',self.ts);self.assertNotIn('魔力量',''.join(self.ts))
 def test_locks_and_existing_subtitles(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][105].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
