"""Source-free contracts for Ridun home, Zerohah reunion and party reminders."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RidunPartyTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-077.json');self.r=load('locales/zh-Hans/batch-077.review.json')
 def test_scope_types_and_breaks(self):
  coverage={e['section']:e['entries'] for e in self.r['coverage']};self.assertEqual({k:v for k,v in coverage.items() if not k.startswith('PartyTalk_')},{'CSMBQ07_20':7,'CSMBQ07_30':6,'CSMBQ07_40':7,'CSMBQ07_45':3,'CSMBQ07_48':4,'Q07_qube_1':2});self.assertEqual({k:v for k,v in coverage.items() if k.startswith('PartyTalk_')},{'PartyTalk_'+w:2 for w in ['Juto','Argo','Crocell','Rue','Celestin']});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':37,'quest_description':1,'name':1});self.assertEqual(self.r['status'],'draft');self.assertEqual(len(self.r['preserved_functional_break_ids']),2);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),23)
 def test_disjoint_ids_and_explicit_holds(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:76] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8552,39));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertEqual(len(self.r['held_entries']),3)
  held={e['id'] for n in range(1,78) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held)
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_quest_layout_and_no_placeholder_translation(self):
  ids=set(self.r['preserved_functional_break_ids']);protected=[e for e in self.p['entries'] if e['id'] in ids];self.assertEqual(sorted(e['translation'].count('\\n') for e in protected),[0,2]);self.assertTrue(all('line_break_policy' not in e for e in protected));ts=[e['translation'] for e in self.p['entries']];self.assertIn('泽罗哈的下落',ts);self.assertFalse(any('Default Value' in t or t=='……' or t=='...' for t in ts))
 def test_clues_and_family_reflection_not_expanded(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('也许能找到什么线索' in t for t in ts));self.assertTrue(any('曾经的利登家族宅邸' in t for t in ts));self.assertTrue(any('唯独修恩扎伊特' in t for t in ts));self.assertTrue(any('可靠的同伴' in t for t in ts));self.assertFalse(any('父亲现在就在王城' in t or '机关无需火焰也能打开' in t for t in ts))
 def test_party_targets_and_existing_candidates(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(ts.count('快去贝尔福特的南部军占领区吧。'),2);self.assertIn('我们快去贝尔福特的南部军驻地吧。',ts);self.assertTrue(any('情报员应该知道' in t for t in ts));terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),402);d={e['source']:e['target'] for e in terms}
  for s,t in [('제로하','泽罗哈'),('리든 가','利登家族'),('마리스','玛莉丝'),('센티넬 연구소','哨兵研究所'),('바이젠','拜泽恩')]:self.assertEqual(d[s],t)
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
