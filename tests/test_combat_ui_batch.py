"""Source-free contracts for combat/UI localization with held concatenation fragments."""
from pathlib import Path
import unittest,json,hashlib,re,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class CombatUiTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-098.json');self.r=L('locales/zh-Hans/batch-098.review.json');self.ts=[e['translation'] for e in self.p['entries']]
 def test_combined_scope_and_classification(self):
  self.assertEqual(len(self.p['entries']),189);self.assertEqual(sum(e['entries'] for e in self.r['coverage']),189);self.assertEqual({e['document'] for e in self.r['coverage']},{'MC2UI.int'});self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']}['Battle_Style'],36);self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']}['AISetting_Description'],36);self.assertEqual(len(self.r['preserved_functional_break_ids']),177);self.assertFalse(any('line_break_policy' in e for e in self.p['entries']));self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'menu_option':97,'menu_description':39,'tutorial':17,'skill_description':12,'effect_description':12,'dialogue':12})
 def test_ids_and_previous_prefix(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:97] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),10182);self.assertEqual(len(ids),189);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_new_terms_remain_candidates(self):
  terms=L('locales/zh-Hans/terms.json')['terms'][455:468];self.assertEqual(len(terms),13);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));by={e['source']:e['target'] for e in terms}
  for k,v in [('사자후','狮子吼'),('방어구파괴','破甲'),('연환력증대','连环力增幅'),('기의 칸','气之KAN'),('고대령','古代灵')]:self.assertEqual(by[k],v)
  self.assertIn('单手剑',self.ts);self.assertIn('太刀',self.ts);self.assertTrue(any('短刀' in t for t in self.ts));self.assertFalse(any('领队' in t or '普通技' in t or '场景行动' in t for t in self.ts));self.assertIn('公会联盟总部',self.ts)
 def test_style_glyphs_layout_and_duplicate_occurrences(self):
  glyphs=[x for t in self.ts for x in re.findall(r'<Styles:MC2_StyleFont_0>([^<]+)<Styles:/>',t)];self.assertEqual(glyphs,['A','L','A','A','A','A','B','X','A','A','X','X','A','L','X','U','L','A']);self.assertEqual(sum(t=='<Styles:MC2_StyleFont_0>A<Styles:/> 结束' for t in self.ts),5);self.assertTrue(any('。 '+chr(92)+'n' in t for t in self.ts));self.assertEqual(sum(t.count(chr(92)+'n') for t in self.ts),13)
 def test_values_ai_and_navigation_use_source_meaning(self):
  self.assertEqual(sum('受到的' in t and '伤害固定为1' in t for t in self.ts),4);self.assertIn('耐力恢复增加30',self.ts);self.assertIn('获得的SID增加30%',self.ts);self.assertIn('获得的经验值增加20%',self.ts);self.assertTrue(any('一定概率' in t and '武器' in t for t in self.ts));self.assertIn('攻击队长的目标',self.ts);self.assertIn('阿巴泽特草原',self.ts);self.assertIn('寂静荒野',self.ts);self.assertIn('石碑',self.ts);self.assertIn('第4研究室',self.ts);self.assertIn('必做任务',self.ts);self.assertIn('可选任务',self.ts);self.assertTrue(any('超限' in t and '除移动外' in t for t in self.ts))
 def test_four_holds_and_all_old_subtitles(self):
  held=self.r['held_entries'];self.assertEqual(len(held),4);self.assertTrue(all(e['reason'] for e in held));self.assertEqual(sum(e['source_sha256']==hashlib.sha256(b'').hexdigest() for e in held),1);allheld={e['id'] for n in range(1,99) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(allheld&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
