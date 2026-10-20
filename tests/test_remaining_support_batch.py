"""Source-free contracts for four support banks, duplicate occurrences and unknown fields."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class RemainingSupportTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-113.json');self.r=load('locales/zh-Hans/batch-113.review.json');self.by={e['id']:e['translation'] for e in self.p['entries']};self.ts=list(self.by.values())
 def test_scope_and_dialogue_classification(self):
  self.assertEqual(len(self.ts),287);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['coverage'],[{'document': 'MC2_com_Juto.int', 'section': 'common', 'entries': 36}, {'document': 'MC2_com_Juto.int', 'section': 'Zephi', 'entries': 27}, {'document': 'MC2_com_Juto.int', 'section': 'Crocell', 'entries': 5}, {'document': 'MC2_com_Juto.int', 'section': 'Juto', 'entries': 3}, {'document': 'MC2_com_Crocell.int', 'section': 'common', 'entries': 52}, {'document': 'MC2_com_Crocell.int', 'section': 'Juto', 'entries': 3}, {'document': 'MC2_com_Crocell.int', 'section': 'Zephi', 'entries': 7}, {'document': 'MC2_com_Crocell.int', 'section': 'Celestin', 'entries': 2}, {'document': 'MC2_com_Crocell.int', 'section': 'Rue', 'entries': 1}, {'document': 'MC2_com_Crocell.int', 'section': 'Crocell', 'entries': 3}, {'document': 'MC2_com_Celestin.int', 'section': 'common', 'entries': 43}, {'document': 'MC2_com_Celestin.int', 'section': 'Zephi', 'entries': 1}, {'document': 'MC2_com_Celestin.int', 'section': 'Argo', 'entries': 28}, {'document': 'MC2_com_Celestin.int', 'section': 'Crocell', 'entries': 4}, {'document': 'MC2_com_Celestin.int', 'section': 'Rue', 'entries': 9}, {'document': 'MC2_com_Celestin.int', 'section': 'Celestin', 'entries': 3}, {'document': 'MC2_com_Zephi.int', 'section': 'common', 'entries': 37}, {'document': 'MC2_com_Zephi.int', 'section': 'Juto', 'entries': 9}, {'document': 'MC2_com_Zephi.int', 'section': 'Argo', 'entries': 4}, {'document': 'MC2_com_Zephi.int', 'section': 'Crocell', 'entries': 4}, {'document': 'MC2_com_Zephi.int', 'section': 'Celestin', 'entries': 1}, {'document': 'MC2_com_Zephi.int', 'section': 'Rue', 'entries': 3}, {'document': 'MC2_com_Zephi.int', 'section': 'Zephi', 'entries': 2}]);self.assertEqual({e['text_kind'] for e in self.r['entries']},{'dialogue'});self.assertEqual(set(self.by),{e['id'] for e in self.r['entries']})
  totals=collections.Counter()
  for e in self.r['coverage']:totals[e['document']]+=e['entries']
  self.assertEqual(totals,{'MC2_com_Juto.int':71,'MC2_com_Crocell.int':68,'MC2_com_Celestin.int':88,'MC2_com_Zephi.int':60})
 def test_unknown_escape_and_unfinished_sentence_held(self):
  self.assertEqual({e['id']:e['source_sha256'] for e in self.r['held_entries']},{'coalesced:7352790d84bf0386bdab6c36da81e5cc7fb25f226c3987903dbdc13036c8706e': '59004d1c7395f780086536aefd0a7d09197d0dd2360af66306bf8f6a16681667', 'coalesced:c841224214a4939c304baf2a52f0dcb7301c58fe9f536e73fc28116ecf8b8828': '3396648b66ca119c785984c774c93aa5ad4e9f1364a0f3019657f8a5a713370a'})
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:112] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),13235);self.assertFalse(old&self.by.keys())
  held={e['id'] for n in range(1,114) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&self.by.keys())
 def test_functional_whitespace_shapes(self):
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']));self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('\\n', 485), ('～', 63), ('１', 1), ('\t', 2), ('\u3000', 4)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count)
  for i,t in {'coalesced:1092d7c22f7f23a20f958665e7d3218e869b2532fea45f30e0f7281fac874fb1': '等我过去，\\n千万别１个人\\n勉强往前冲。', 'coalesced:2ba433b4210cb5ae071af1beada3bc3c18f82f2d56dde75a6826036deaf73d43': '抱歉。\t', 'coalesced:ef79b9114f3cf1c761be2f9ba5ff125136bdcff93248e806ea2870d4917375c0': '我来！\t', 'coalesced:f98ef4e0cfa6259f6d4c66f8b31caabe0ea13b105a97958f658f2c1e3455974a': '有时也需要\\n依靠别人吧？\u3000洁菲，\\n随时叫我。', 'coalesced:b487787d7796212539092fac132ac7f3f5ecdce4e47fa54e25e9a9a407cd0aef': '需要我的力量了吧？\\n等着！\u3000我马上\\n就来帮你。', 'coalesced:215d7d5a1dcab70eeaa836265fd753b4131566521a24d846dc71641fb765acc6': '实在抱歉……', 'coalesced:50cd57eec0536bc359cd99578399d826676cb951c1e60ca1cbc9ea135e62c30d': '阿尔戈～！\\n我会用爱之力，\\n马上来帮你哦！', 'coalesced:f7b2b3b43b6645ba5097653773d6987eb30b2ff6b23474676380d0eac3fe509e': '阿尔戈！\\n再这样下去不行啦。\\n交给我！', 'coalesced:7d3848d4b3a9d1e898107fbc298f8bc9ca005697fb2e776c386f8ab99efa164e': '阿尔戈 ～\\n是想见\\n可爱的我了吧～', 'coalesced:03347c5410357202db9e1db8e7ea251163902511ab4e8edfc720c4725673d5e8': '冲啊\u3000阿尔戈！\\n把碍事的家伙\\n统统打倒！', 'coalesced:a7b66ee9a92770c38cd9e4aef77cb1a102a0e4d671ce38dac9bf3674d2e29a74': '阿尔戈～，\u3000真的\\n不需要\\n我帮忙吗？', 'coalesced:9f280cc551cbd3e997d1931871763b179897638295a44485dcf11f919512f490': '能看到露\\n帅气的战斗啦！\\n我很期待哦！', 'coalesced:267ffcf6b3a86fa47f613ec26ccde4c3a8d7246166e4b0e8463241dee153c370': '能看到露\\n帅气的战斗啦！\\n我很期待哦！'}.items():self.assertEqual(self.by[i],t)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_duplicate_occurrence_translations_are_distinct(self):
  first='coalesced:50cd57eec0536bc359cd99578399d826676cb951c1e60ca1cbc9ea135e62c30d';second='coalesced:f7b2b3b43b6645ba5097653773d6987eb30b2ff6b23474676380d0eac3fe509e'
  self.assertNotEqual(first,second);self.assertNotEqual(self.by[first],self.by[second]);self.assertIn('爱之力',self.by[first]);self.assertIn('交给我',self.by[second])
 def test_candidate_aliases_append_without_review_upgrade(self):
  new=load('locales/zh-Hans/terms.json')['terms'][1096:1104];self.assertEqual(len(new),8);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));by={e['source']:e['target'] for e in new}
  self.assertEqual(by['ジュト'],'朱特');self.assertEqual(by['ルウ'],'露');self.assertEqual(by['水のタミ'],'水之民');self.assertEqual(by['対センティネル部隊'],'反哨兵部队')
 def test_workflow_and_existing_subtitles(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][112].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
