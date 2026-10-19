"""Source-free contracts for the island preparation quest branches."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class IslandPreparationTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-089.json');self.r=L('locales/zh-Hans/batch-089.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Ch01_104_0':21,'Ch01_105_0':20,'Ch01_120_0':19,'Ingredient':6,'Valuables':4,'information':2});self.assertEqual(len(self.p['entries']),72);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),31);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),31);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':41,'name':10,'system_message':9,'quest_description':3,'quest_objective':4,'item_description':5})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:88] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9054);self.assertEqual(len(ids),72);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_candidates_and_source_variant(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][420:427];self.assertEqual([(e['source'],e['target']) for e in terms],[('화염초','火焰草'),('공구','工具'),('빌터의 열쇠','比尔特的钥匙'),('덫의 재료','陷阱材料'),('단단한 뿔','坚硬的角'),('빌터의 상자','比尔特的箱子'),('피어스웜','穿刺蠕虫')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));ts=[e['translation'] for e in self.p['entries']];self.assertIn('工具',ts);self.assertNotIn('工具箱',ts);self.assertIn('比尔特的箱子',ts)
 def test_functional_placeholders_spaces_and_numbers(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t.count('%s') for t in ts),17);self.assertEqual(sum(t.endswith(' ') for t in ts),4);self.assertIn('QUEST%s: 获得火焰草 %s / %s',ts);self.assertIn('QUEST%s: 获得陷阱材料 (%s / %s)',ts);self.assertIn('火焰草带来了吗？ ',ts);self.assertIn('比尔特的钥匙 ',ts);self.assertIn('陷阱材料 ',ts);self.assertIn('消灭穿刺蠕虫，获得5个[坚硬的角]\\n取得5个后，向[哈曼]报告',ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_branches_locations_and_level_caution(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t=='哈哈，拜托你了，朱特。青灵森林各处，都有不少穿刺蠕虫。' for t in ts),2);self.assertTrue(any('村长家前面的箱子' in t for t in ts));self.assertTrue(any('村长家旁边的箱子' in t for t in ts));self.assertTrue(any('命中' in t or '很难打中' in t for t in ts));self.assertTrue(any('伤害也会降低' in t and '暴击' in t for t in ts));self.assertFalse(any('等级差10级' in t for t in ts));self.assertTrue(any('太急，或者太慢' in t for t in ts))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,89) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
