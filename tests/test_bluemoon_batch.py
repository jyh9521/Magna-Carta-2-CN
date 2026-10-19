"""Source-free contracts for Bluemoon accusation, rebuilding and sacred relics."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class BluemoonTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-075.json');self.r=load('locales/zh-Hans/batch-075.review.json')
 def test_scope_types_and_layout_policy(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ06_030':12,'CSMBQ06_031':17,'10_901_0':4,'10_910_0':22,'11_trewa':14,'Valuables':6,'Default':3});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':59,'name':8,'quest_description':2,'system_message':3,'quest_objective':3,'item_description':3});self.assertEqual(self.r['status'],'draft');self.assertEqual(len(self.r['preserved_functional_break_ids']),10);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),47)
 def test_disjoint_ids_and_marker_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:74] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8400,78));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertEqual(len(self.r['held_entries']),1)
  held={e['id'] for n in range(1,76) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held);self.assertEqual(self.r['held_entries'][0]['id'],'coalesced:6bbd3b99cfeb1de23780572e284b75cdf69cc96a6a7b2fa2a77fa416a7297cef')
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_quest_controls_whitespace_and_item_kind(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual([t for t in ts if t.startswith('QUEST:')],['QUEST:获得青月之剑 ','QUEST:获得青月之镜 ','QUEST:获得青月宝玉 ']);self.assertEqual([t for t in ts if t.endswith(' ') and not t.startswith('QUEST:')],['青月之剑 ','青月之镜 ','青月宝玉 ']);self.assertEqual(sum(t.count('\\n') for t in ts),2);self.assertEqual([re.findall(r'[0-9]+',t) for t in ts if re.search(r'[0-9]',t)],[['3']]);self.assertFalse(any('青月法杖' in t or '青月帽子' in t for t in ts))
 def test_dialogue_not_expanded_into_facts(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('振作点，阿尔贝多！',ts);self.assertTrue(any('听说，黑角特雷瓦' in t for t in ts));self.assertTrue(any('总有一天能实现吧' in t for t in ts));self.assertIn('等这场战争结束，我会正式求婚。',ts);self.assertFalse(any('阿尔贝多死了' in t or '阿尔戈向露求婚' in t for t in ts));self.assertTrue(any('象征族长身份的青月武器' in t for t in ts))
 def test_candidates_and_existing_faction_names(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),399);new=terms[391:399];self.assertEqual(len(new),8);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));ts={e['source']:e['target'] for e in terms}
  for s,t in [('알베도','阿尔贝多'),('드레고','德雷戈'),('푸른 달 트레와','青月特雷瓦'),('검은 뿔 트레와','黑角特雷瓦'),('다크 트레와 리더','暗黑特雷瓦头领'),('루할트 고원','鲁哈尔特高原')]:self.assertEqual(ts[s],t)
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
