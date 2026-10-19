"""Source-free contracts for the invasion and movie-sidecar plans."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class InvasionTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-061.json');self.r=load('locales/zh-Hans/batch-061.review.json')
 def test_scope_and_narrator(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB11_65':15,'CSMB11_70':21,'10_kotamare_battle':9,'Chapter11':6});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':42,'narrative':9});ids={e['id'] for e in self.r['entries'] if e['text_kind']=='narrative'};self.assertEqual(sum(e['id'] in ids for e in self.p['entries'][:15]),3);self.assertEqual(self.r['status'],'draft')
 def test_source_locks_no_overlap(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:60] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7453,51));self.assertFalse(old&ids);self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_explicit_layout_and_battle_not_aftermath(self):
  self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),23)
  for e in self.p['entries']:self.assertNotIn('\\n',e['translation'])
  self.assertTrue(any('不战而退' in e['translation'] for e in self.p['entries']));self.assertTrue(any('赶紧造好' in e['translation'] for e in self.p['entries']))
 def test_new_faction_candidate(self):
  t=next(t for t in load('locales/zh-Hans/terms.json')['terms'] if t['source']=='란츠하임 연합군');self.assertEqual(t['target'],'兰兹海姆联合军');self.assertEqual((t['review_status'],t['relation']),('candidate','unverified'));self.assertIn(t['source_string_id'],{e['id'] for e in self.p['entries']});self.assertTrue(any('自称兰兹海姆联合军' in e['translation'] for e in self.p['entries']))
 def test_subtitle_cues_and_breaks(self):
  plans=[load('locales/zh-Hans/subtitles/batch-061-'+n+'.json') for n in ['csm11-50.txt','csm11-60.txt']];self.assertEqual([len(p['entries']) for p in plans],[8,8]);self.assertEqual([sum(e['translation'].count('<br>') for e in p['entries']) for p in plans],[2,1]);self.assertEqual([(p['entries'][0]['start'],p['entries'][-1]['end']) for p in plans],[(500,47970),(6999,85993)])
  for p in plans:
   self.assertEqual(p['kind'],'timed-subtitle-text')
   for e in p['entries']:self.assertLess(e['start'],e['end']);self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
  self.assertIn('难道……是克蕾尔！？',[e['translation'] for e in plans[0]['entries']])
 def test_subtitle_profile_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),37);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:37]),270)
  for s in p['plans'][:37]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
