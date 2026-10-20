"""Source-free, future-compatible contracts for the combined quest/world batch."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class QuestWorldTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-094.json');self.r=L('locales/zh-Hans/batch-094.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_full_combined_scope(self):
  self.assertEqual(len(self.p['entries']),254);self.assertEqual(sum(e['entries'] for e in self.r['coverage']),254);by=collections.Counter()
  for e in self.r['coverage']:by[e['document']]+=e['entries']
  self.assertEqual(by,{'MC2Quest.int':70,'MC2CharacterName.int':101,'MC2FieldName.int':16,'MC2UI.int':63,'MC2Item.int':4});self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),32);self.assertEqual(len(self.r['preserved_functional_break_ids']),205);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'name':186,'dialogue':49,'system_message':9,'quest_description':3,'quest_objective':3,'menu_option':2,'item_description':2})
 def test_ids_hashes_and_historical_prefix(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:93] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),9355);self.assertEqual(len(ids),254);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_candidate_slice_and_distinct_source_spellings(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][440:453];self.assertEqual(len(terms),13);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));by={e['source']:e['target'] for e in terms}
  for k,v in [('파인','帕因'),('헤르가','赫尔加'),('번개의 영혼','雷之魂'),('바람의 영혼','风之魂'),('폭풍의 석판','风暴石板'),('크랩퍼스','克拉普斯')]:self.assertEqual(by[k],v)
  old=L('locales/zh-Hans/terms.json')['terms'][:440];self.assertTrue(any(e['source']=='클로퍼스' and e['target']=='克洛普斯' for e in old));self.assertNotIn('克洛普斯壳',self.ts)
 def test_menu_controls_values_and_warning(self):
  self.assertIn(r'<Styles:MC2_StyleFont_0>X<Styles:/> 嗯。\n<Styles:MC2_StyleFont_0>Y<Styles:/> 还没有。',self.ts);self.assertEqual(sum(t.count('%s') for t in self.ts),8);self.assertEqual(sum(t.endswith(' ') for t in self.ts),3);self.assertIn('QUEST : %s 开始',self.ts);self.assertIn('以下任务将无法继续进行',self.ts);self.assertIn('以下任务已无法继续进行',self.ts);self.assertTrue(any('护送途中' in t and '读取存档' in t and '失败' in t for t in self.ts));self.assertIn('杜南丘陵第1哨所',self.ts);self.assertIn('杜南丘陵第2哨所',self.ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_context_not_english_key_guessing(self):
  for t in ['生物学家的女婿','阿巴泽特孩童','派驻商人','制动装置','动力装置','水之开关','酒桶','水桶','用于破除风之祭坛结界的媒介','元气恢复剂？']:self.assertIn(t,self.ts)
  self.assertTrue(any('已经通过试炼' in t and '什么都帮不了' in t for t in self.ts));self.assertTrue(any('两位魂灵' in t and '已经选中' in t for t in self.ts));self.assertFalse(any('商人失踪' in t or '黑市商人' in t for t in self.ts));self.assertTrue(any('背上生长的植物' in t for t in self.ts))
 def test_unknown_and_all_subtitles_preserved(self):
  self.assertEqual(len(self.r['held_entries']),1);held={e['id'] for n in range(1,95) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
