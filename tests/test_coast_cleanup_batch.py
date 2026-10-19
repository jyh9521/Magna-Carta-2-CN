"""Source-free contracts for the coast quest and neutral farewell."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class CoastCleanupTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-087.json');self.r=L('locales/zh-Hans/batch-087.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Ch00_104_0':42,'ruhalt':1});self.assertEqual(len(self.p['entries']),43);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),21);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),8);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':35,'system_message':4,'name':1,'menu_option':1,'quest_description':1,'quest_objective':1})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:86] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8973);self.assertEqual(len(ids),43);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_monster_distinction_and_candidate(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('只要对付没有壳的[克洛普斯]就行。',ts);self.assertTrue(any('有壳的[拉普斯]' in t and '木剑' in t for t in ts));self.assertIn('消灭克洛普斯',ts);terms=L('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),416);e=terms[415];self.assertEqual((e['source'],e['target']),('클로퍼스','克洛普斯'));self.assertEqual(e['review_status'],'candidate');self.assertEqual(e['relation'],'unverified')
 def test_functional_tags_keys_and_placeholders(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('<Styles:MC2_StyleFont_0>X<Styles:/> 不，那个……(进行教程)\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 当然记得(跳过教程)',ts);self.assertIn('QUEST%s: 消灭克洛普斯 (%s / %s)',ts);self.assertIn('QUEST: %s 开始',ts);self.assertIn('QUEST: %s 完成',ts);self.assertEqual(sum(t.count('%s') for t in ts),5);self.assertIn('为了让村民能安全地工作，\\n请消灭海边的3只克洛普斯',ts);es={e['id']:e for e in self.p['entries']};self.assertTrue(all('line_break_policy' not in es[i] for i in self.r['preserved_functional_break_ids']))
 def test_farewell_and_early_scene_context(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('露……请别担心我。期待下次，还能再见到你。',ts);self.assertTrue(any('比尔特大叔' in t for t in ts));self.assertTrue(any('风歌洞窟' in t for t in ts));self.assertTrue(any('把守护者带走' in t for t in ts));self.assertIn('……',ts);self.assertFalse(any('说话人就是' in t or '克洛普斯其实是拉普斯变种' in t for t in ts))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,87) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
