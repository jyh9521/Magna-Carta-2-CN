"""Source-free contracts for the sibling search and merchant quest chain."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class MerchantCampTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-091.json');self.r=L('locales/zh-Hans/batch-091.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'03_310_0':18,'03_350_00':16,'03_350_01':17,'03_350_02':14,'03_350_03':16,'Default':2,'FieldAction':2,'Valuables':4});self.assertEqual(len(self.p['entries']),89);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),46);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),25);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':64,'name':10,'quest_description':5,'system_message':4,'quest_objective':3,'item_description':3})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:90] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9192);self.assertEqual(len(ids),89);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_candidates_and_actual_item_names(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][432:437];self.assertEqual([(e['source'],e['target']) for e in terms],[('전스티','琼斯蒂'),('아비스 상인','阿维斯商人'),('가스트랩','气体陷阱'),('빼앗긴 상품','被抢走的商品'),('야영지의 상자의 열쇠','营地箱子的钥匙')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));ts=[e['translation'] for e in self.p['entries']];self.assertIn('琼斯蒂',ts);self.assertIn('阿维斯商人',ts);self.assertIn('被抢走的商品 ',ts);self.assertIn('营地箱子的钥匙 ',ts)
 def test_functional_tokens_and_reward_values(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t.count('%s') for t in ts),6);self.assertEqual(sum(t.endswith(' ') for t in ts),2);self.assertTrue(any('10%' in t for t in ts));self.assertEqual(sum(t.count('4个') for t in ts),3);self.assertIn('QUEST%s: 获得奇怪蘑菇 (%s / %s)',ts);self.assertIn('QUEST%s: 陷阱放置完成',ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_distinct_quests_branches_and_odor(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('以眼还眼',ts);self.assertIn('以牙还牙',ts);self.assertIn('会喷出强烈恶臭的阿维斯制陷阱',ts);self.assertFalse(any('致命毒气' in t or '已强制护送回村' in t for t in ts));self.assertEqual(sum(t=='柯塔马雷，就在这里的南边。' for t in ts),2);self.assertEqual(sum(t=='湿地各处，都有奇怪蘑菇。' for t in ts),2);self.assertIn('知道了，我马上就自己回去，别担心。',ts);self.assertTrue(any('马车坏了' in t for t in ts));self.assertTrue(any('[内斯汀]' in t for t in ts))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,91) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
