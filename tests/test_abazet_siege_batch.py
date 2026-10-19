"""Source-free contracts for the pre-siege Abazet NPC collection."""
from pathlib import Path
import unittest,json,hashlib
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class AbazetSiegeTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-084.json');self.r=L('locales/zh-Hans/batch-084.review.json')
 def test_scope_and_layout(self):
  self.assertEqual(self.r['coverage'],[{'document':'MC2NpcTalk.int','section':'Ch04_Abazet_1','entries':38}]);self.assertEqual(len(self.p['entries']),38);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),21);self.assertFalse(self.r['held_entries']);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(self.r['status'],'draft');self.assertTrue(all(e['text_kind']=='dialogue' for e in self.r['entries']))
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:83] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8828);self.assertEqual(len(ids),38);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_shared_candidates_not_new_guard_identity(self):
  ts=''.join(e['translation'] for e in self.p['entries'])
  for t in ['反哨兵部队','希昂·雷格拉尔','泽格隆','拉提族','狼人','杜南丘陵','老狐峡谷','黑刃要塞','阿维斯族']:self.assertIn(t,ts)
  self.assertIn('一位新来的女战士',ts);self.assertNotIn('蕾洁菲尔妲守卫黑刃要塞',ts)
 def test_early_questions_not_future_exposition(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('盲目追随' in t and t.endswith('呢？') for t in ts));self.assertIn('怎么会落到，修恩扎伊特那种家伙手里……',ts);self.assertTrue(any('是不是在哪里，有工厂或研究所' in t for t in ts));self.assertFalse(any('工厂确实位于' in t or '北部军必须盲目服从' in t for t in ts))
 def test_two_question_variants_and_joke_context(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('不过，到底是在哪里制造的呢？是不是在哪里，有工厂或研究所？',ts);self.assertIn('不过，到底是在哪里制造的呢？有工厂或研究所吗？',ts);self.assertIn('嘻嘻呵——其实，我是阿维斯族的王子。',ts);self.assertIn('我是来寻找，人类新娘的。',ts);self.assertIn('……',ts);self.assertIn('你该不会，真的信了吧？',ts)
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,84) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
