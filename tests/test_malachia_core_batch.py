"""Source-free contracts for Malachia's rescue, lightning core and key occurrences."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class MalachiaCoreTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-079.json');self.r=load('locales/zh-Hans/batch-079.review.json')
 def test_scope_types_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ09_10':16,'CSMBQ09_15':5,'CSMBQ10_50':4,'CSMBQ10_55':10,'rue_0':3,'Rue_1':14,'Q11_0':2,'Weapon_katana_rue':3,'Valuables':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':48,'name':4,'quest_description':2,'mail_subject':1,'mail_body':1,'item_description':3});self.assertEqual(self.r['status'],'draft');self.assertEqual(len(self.r['preserved_functional_break_ids']),11);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),28)
 def test_new_ids_preserve_old_and_six_holds(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:78] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8648,59));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertEqual(len(self.r['held_entries']),6)
  held={e['id'] for n in range(1,80) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held)
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_mail_blank_paragraph_trailing_space_and_stats(self):
  kinds={e['id']:e['text_kind'] for e in self.r['entries']};body=next(e for e in self.p['entries'] if kinds[e['id']]=='mail_body');self.assertEqual(body['translation'].count('\\n'),5);self.assertIn('\\n\\n',body['translation']);self.assertTrue(body['translation'].endswith(' '));self.assertNotIn('line_break_policy',body);self.assertTrue(body['translation'].startswith('露，我打听到了之前提到的玛拉基亚的消息。'));ts=[e['translation'] for e in self.p['entries']];self.assertIn('蕴含雷电之力的终极短刀\\n攻击+270',ts);self.assertIn('短刀\\n攻击+270',ts);self.assertEqual([re.findall(r'[0-9]+',t) for t in ts if re.search(r'[0-9]',t)],[['270'],['270']])
 def test_laboratory_key_and_card_occurrences_distinct(self):
  edits={e['id']:e['translation'] for e in self.p['entries']};self.assertEqual(edits['coalesced:22f361b7bcf01648e114220572dcea5fda07c2548dd2ed39d05fa75dbddbf607'],'研究所钥匙 ');self.assertEqual(edits['coalesced:22a4a7a895f08128388a2c3b0dc063c3841102a927abb54aa980c2f309dc7e3b'],'打开研究所上锁房门的钥匙')
  old={e['id']:e['translation'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:78] for e in load(b['plan']['path'])['entries']};card='coalesced:41480d3d2e33c26493aec2504ab8efd18a0262ddc9ab1dd6d0fc8f223723d895';self.assertNotIn(card,edits);self.assertEqual(old[card],'研究室通行卡')
 def test_candidate_names_and_qualified_outcomes(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),407);new=terms[403:407];self.assertEqual([(e['source'],e['target']) for e in new],[('번개의 핵','雷之核心'),('뇌제','雷帝'),('연구소의 열쇠','研究所钥匙'),('단도','短刀')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('似乎被转移' in t for t in ts));self.assertTrue(any('希望以后，不会因为违抗命令受罚' in t for t in ts));self.assertTrue(any('究竟能不能运用这股力量……还是未知数' in t for t in ts));self.assertTrue(any(t.endswith('成分，') for t in ts))
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
