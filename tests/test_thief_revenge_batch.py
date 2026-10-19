"""Source-free contracts for the thief's accusation, protection and heirloom."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class ThiefRevengeTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-080.json');self.r=load('locales/zh-Hans/batch-080.review.json')
 def test_scope_types_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ10_10':3,'CSMBQ10_15':15,'CSMBQ10_20':24,'Weapon_twohanded sword_juto':3,'Default':1});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':42,'name':2,'item_description':2});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),4);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),23)
 def test_new_ids_preserve_old_and_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:79] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8707,46));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  held={e['id'] for n in range(1,80) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held)
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_role_label_and_weapon_stats(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('盗贼',ts);self.assertNotIn('盗贼头目',ts);self.assertIn('幻影之刃',ts);self.assertIn('据说是雷恩波尔特的名匠打造的最强双手剑\\n攻击+240',ts);self.assertIn('双手剑\\n攻击+240',ts);self.assertEqual([re.findall(r'[0-9]+',t) for t in ts if re.search(r'[0-9]',t)],[['240'],['240']]);protected=set(self.r['preserved_functional_break_ids']);self.assertTrue(all('line_break_policy' not in e for e in self.p['entries'] if e['id'] in protected))
 def test_guilt_protection_and_withdrawal_not_expanded(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('我有想要守护的东西……',ts);self.assertIn('无所谓……因为，我已经不想杀你了。',ts);self.assertIn('总有一天，他会理解朱特的。',ts);self.assertIn('但愿如此……',ts);self.assertTrue(any('躲起来，瑟瑟发抖' in t for t in ts));self.assertFalse(any('我完全原谅你了' in t or '朱特不必承担任何责任' in t for t in ts))
 def test_candidates_and_old_key_card_ids(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),409);new=terms[407:409];self.assertEqual([(e['source'],e['target'],e['category']) for e in new],[('팬텀 블레이드','幻影之刃','weapon'),('도적','盗贼','role')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));old={e['id']:e['translation'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:79] for e in load(b['plan']['path'])['entries']}
  for i,t in [('coalesced:22f361b7bcf01648e114220572dcea5fda07c2548dd2ed39d05fa75dbddbf607','研究所钥匙 '),('coalesced:41480d3d2e33c26493aec2504ab8efd18a0262ddc9ab1dd6d0fc8f223723d895','研究室通行卡')]:self.assertEqual(old[i],t);self.assertNotIn(i,{e['id'] for e in self.p['entries']})
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
