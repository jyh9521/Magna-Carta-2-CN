"""Source-free contracts for the Kamond collection and delivery chain."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class KamondDeliveryTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-093.json');self.r=L('locales/zh-Hans/batch-093.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'03_363_0':18,'03_363_1':14,'Valuables':4});self.assertEqual(len(self.p['entries']),36);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),15);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),10);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':26,'name':4,'quest_description':2,'system_message':1,'quest_objective':1,'item_description':2})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:92] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9319);self.assertEqual(len(ids),36);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_candidates_and_actual_items(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][437:440];self.assertEqual([(e['source'],e['target']) for e in terms],[('카몬드 파편','卡蒙德碎片'),('카몬드 조각','卡蒙德碎片'),('카몬드 파편 꾸러미','卡蒙德碎片包裹')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms))
  for t in ['卡蒙德碎片 ','卡蒙德碎片包裹','装有受托运送的卡蒙德碎片的包裹']:self.assertIn(t,self.ts)
 def test_functional_tokens_and_whitespace(self):
  self.assertEqual(sum(t.count('%s') for t in self.ts),3);self.assertIn('QUEST%s: 卡蒙德碎片 (%s / %s)',self.ts);self.assertEqual(sum(t.count('8') for t in self.ts),2);self.assertEqual(sum(t.endswith(' ') for t in self.ts),2);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_context_branches_and_storage_offer(self):
  self.assertEqual(sum(t=='卡蒙德碎片，应该能从这附近，所有的怪物身上得到喵。' for t in self.ts),2);self.assertIn('下次作战要用的炸弹，也交给我们保管吧，喵～',self.ts);self.assertTrue(any('最近' in t and '没见到' in t for t in self.ts));self.assertFalse(any('死亡' in t or '失踪' in t or '伤害+' in t for t in self.ts));self.assertIn('送往阿巴泽特',self.ts)
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,93) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
