"""Source-free contracts for paired sidequests and occurrence-specific skill text."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class SkillSidequestTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-071.json');self.r=load('locales/zh-Hans/batch-071.review.json')
 def test_scope_and_explicit_kinds(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ11_10':10,'CSMBQ11_11':8,'CSMBQ11_12':9,'CSMBQ11_13':4,'CSMBQ11_20':5,'CSMBQ11_21':12,'CSMBQ11_22':5,'CSMBQ11_23':9,'zuto_crocell':10,'Chapter12':4,'Renkai_Ougi':6});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':70,'name':3,'quest_description':1,'system_message':4,'skill_description':4});self.assertEqual(self.r['status'],'draft')
 def test_no_overlap_or_previous_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:70] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8198,82));self.assertFalse(old&ids);self.assertFalse(ids&{e['id'] for n in [63,68] for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json')['held_entries']});self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_duplicate_skill_key_changes_only_occurrence_two(self):
  oldid='coalesced:d02cca0a45466b43635aa14caa97a7a936f0c90f0f5f0dbae180097f716d8183';newid='coalesced:dacc826ac97f366f530bdf7db67ae20723de9f871e311ff2351b8ea5bc160a68';new={e['id']:e for e in self.p['entries']};self.assertNotIn(oldid,new);self.assertEqual(new[newid]['source_sha256'],'aebd919bd063cdb7e58ba4b276909b0bcfd0e9cd8219bac2bc37e110baf01f1b');self.assertEqual(new[newid]['translation'],'以冰与雷的连环术施展连携奥义，对1名敌人造成强大伤害');old=next(e for e in load('locales/zh-Hans/batch-055.json')['entries'] if e['id']==oldid);self.assertEqual(old['translation'],'以风与雷的连环术施展连携奥义，对1名敌人造成强大伤害')
 def test_acquired_layout_and_skill_numeric_targets(self):
  kinds={e['id']:e['text_kind'] for e in self.r['entries']};msgs=[e for e in self.p['entries'] if kinds[e['id']]=='system_message'];self.assertEqual([e['translation'].count('\\n') for e in msgs],[1]*4);self.assertTrue(all('line_break_policy' not in e for e in msgs));des=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='skill_description'];self.assertEqual(len(des),4);self.assertTrue(all('对1名敌人' in t and not t.endswith('。') for t in des));self.assertEqual(len(self.r['preserved_functional_break_ids']),6);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),49)
 def test_candidates_source_forms_and_existing_names(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];new=terms[383:387];self.assertEqual({e['source']:e['target'] for e in new},{'마레의 비약':'马雷灵药','노바 슬래시':'新星斩','노바슬래시':'新星斩','초빙결뇌진폭':'超冰结雷震爆'});self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));self.assertEqual(new[2]['form'],'alias');self.assertIn('原汉字与词源待核',new[-1]['basis']);ts={e['source']:e['target'] for e in terms};self.assertEqual(ts['마리스'],'玛莉丝');self.assertEqual(ts['검은 네코네코'],'黑猫猫');self.assertTrue(any('猫猫喵喵' in e['translation'] for e in self.p['entries']))
 def test_previous_subtitle_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),38);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:38]),271)
  for s in p['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
