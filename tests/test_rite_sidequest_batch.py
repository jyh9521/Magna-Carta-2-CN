"""Source-free contracts for the coming-of-age invitation, celebration and token."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RiteSidequestTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-074.json');self.r=load('locales/zh-Hans/batch-074.review.json')
 def test_scope_and_narrative_classification(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ06_010':15,'CSMBQ06_060':12,'Valuables':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':24,'narrative':3,'name':1,'item_description':1});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries']);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),18)
 def test_no_overlap_or_held_changes(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:73] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8371,29));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  held={e['id'] for n in range(1,74) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held)
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_age_and_marriage_proposals_not_rewritten(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual([re.findall(r'[0-9]+',t) for t in ts if re.search(r'[0-9]',t)],[['12']]);self.assertIn('一生？明明才活了12年。',ts);self.assertTrue(any('随时都能结婚' in t for t in ts));self.assertTrue(any('我们快点结婚吧' in t for t in ts));self.assertFalse(any('已经结婚' in t for t in ts))
 def test_narrative_and_item_names_stay_distinct(self):
  kinds={e['id']:e['text_kind'] for e in self.r['entries']};ns=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='narrative'];self.assertEqual(ns,['我们暂时忘却了纷乱的现实，尽情享受庆典。','短暂的休息……不过，从明天起，又有战斗在等着我们吧。','第二天……']);items=[e['translation'] for e in self.p['entries'] if kinds[e['id']] in ['name','item_description']];self.assertEqual(items,['仪式信物','马雷族举行成人礼所需的信物，上面盖有族长的印章']);self.assertFalse(any(t.endswith('。') for t in items))
 def test_candidate_term_and_old_prefix(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),391);new=terms[390];self.assertEqual((new['source'],new['target'],new['review_status'],new['relation']),('의식의 증표','仪式信物','candidate','unverified'));self.assertIn(new['source_string_id'],{e['id'] for e in self.p['entries']});self.assertEqual(next(e['target'] for e in terms if e['source']=='성인식'),'成人礼');self.assertEqual(len({e['id'] for e in terms[:391]}),391)
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
