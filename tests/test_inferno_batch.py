"""Source-free contracts for the hunt, invitation and related item labels."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class InfernoTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-069.json');self.r=load('locales/zh-Hans/batch-069.review.json')
 def test_scope_and_explicit_kinds(self):
  self.assertEqual({(e['document'],e['section']):e['entries'] for e in self.r['coverage']},{('MC2Quest.int','12_zuto_1'):9,('MC2Quest.int','12_Inferno_0'):16,('MC2Quest.int','12_Inferno_1'):24,('MC2Quest.int','12_Inferno_2'):13,('MC2CharacterName.int','Default'):2,('MC2Item.int','Valuables'):4,('MC2QubeMail.int','Q12_qube_1'):2,('MC2QubeMail.int','E12_001'):2,('MC2QubeMail.int','E12_002'):2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':50,'name':8,'quest_description':4,'quest_progress':4,'mail_subject':3,'mail_body':3,'item_description':2});self.assertEqual(self.r['status'],'draft')
 def test_no_overlap_or_previous_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:68] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8031,74));self.assertFalse(old&ids);self.assertFalse(ids&{e['id'] for n in [63,68] for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json')['held_entries']});self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_protected_quest_tokens_and_item_space(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('QUEST%s: 获得布雷兹之尾 (%s / %s)',ts);self.assertIn('QUEST : 讨伐因费尔诺',ts);self.assertIn('反费尔诺弹 ',ts);self.assertTrue(any('100年' in t for t in ts));self.assertIn('请找来4条布雷兹之尾。',ts);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),41);self.assertEqual(len(self.r['preserved_functional_break_ids']),18)
 def test_mail_layout_and_inner_spaces(self):
  kinds={e['id']:e['text_kind'] for e in self.r['entries']};m=[e for e in self.p['entries'] if kinds[e['id']]=='mail_body'];self.assertEqual([e['translation'].count('\\n') for e in m],[9,8,4]);self.assertEqual([[i for i,t in enumerate(e['translation'].split('\\n')) if not t] for e in m],[[2,8],[4],[]]);q=m[0]['translation'].split('\\n');self.assertTrue(q[6].endswith('。 '));self.assertTrue(q[7].endswith('！ '));self.assertTrue(all('line_break_policy' not in e for e in m))
 def test_candidates_and_source_spelling_separation(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];new=terms[364:371];self.assertEqual({e['source']:e['target'] for e in new},{'호그톤':'霍格顿','마이어':'迈耶','인페르노':'因费尔诺','블레이즈':'布雷兹','블레이즈의 꼬리':'布雷兹之尾','안티 페르노탄':'反费尔诺弹','헌터 길드':'猎人公会'});self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));self.assertTrue(any('亲戚伊格顿' in e['translation'] for e in self.p['entries']));self.assertTrue(any('听说，北部军' in e['translation'] for e in self.p['entries']));self.assertTrue(any('雷恩波尔特废墟' in e['translation'] for e in self.p['entries']))
 def test_previous_subtitle_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),38);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:38]),271)
  for s in p['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
