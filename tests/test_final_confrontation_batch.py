"""Source-free contracts for final dialogue and the last extracted movie cues."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class FinalConfrontationTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-072.json');self.r=load('locales/zh-Hans/batch-072.review.json')
 def test_scope_and_draft(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB13_20':17,'CSMB13_35':9,'CSMB13_45':14});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':40});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries']);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),25)
 def test_no_overlap_or_held_changes(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:71] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8280,40));self.assertFalse(old&ids);self.assertFalse(ids&{e['id'] for n in [63,68] for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json')['held_entries']});self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_candidates_distinguish_war_names(self):
  ts=load('locales/zh-Hans/terms.json')['terms'];new=ts[387:390];self.assertEqual({e['source']:e['target'] for e in new},{'아비스베르크 전쟁':'阿维斯贝尔克战争','복제':'复制','칸의 순환':'KAN循环'});self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));d={e['source']:e['target'] for e in ts};self.assertEqual(d['아비스 전쟁'],'阿维斯战争');self.assertEqual(d['카르마'],'卡尔玛');self.assertTrue(any('不是我，却也可以说是我' in e['translation'] for e in self.p['entries']))
 def test_six_movie_plans_and_source_locks(self):
  specs=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertGreaterEqual(len(specs),44);ps=[load(s['path']) for s in specs[38:44]];self.assertEqual([p['resource'].rsplit('/',1)[-1] for p in ps],['csm13-10.txt','csm13-30.txt','csm13-40.txt','csm13-50.txt','csmep-45.txt','csmep-50.txt']);self.assertEqual([len(p['entries']) for p in ps],[4,5,4,24,5,2]);self.assertEqual(sum(len(load(s['path'])['entries']) for s in specs[:44]),315)
  for p in ps:
   self.assertEqual(p['kind'],'timed-subtitle-text');self.assertRegex(p['input_sha256'],r'^[0-9a-f]{64}$')
   for e in p['entries']:self.assertLessEqual(e['start'],e['end']);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertTrue(e['translation']);self.assertFalse(any(c in e['translation'] for c in '\r\n\0&'))
  for s in specs[:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
 def test_revelation_follows_its_movie_and_promises_not_extra_outcomes(self):
  ps=[load(s['path']) for s in load('locales/zh-Hans/subtitle-profile.json')['plans'][38:44]];opening=ps[0]['entries'];self.assertEqual((opening[0]['start'],opening[0]['end']),(8843,11735));self.assertEqual([e['translation'].count('<br>') for e in opening],[0,1,0,0]);self.assertEqual(opening[-1]['translation'],'没错……我是斯特拉斯的复制体。');end=ps[3]['entries'];self.assertIn('不过，这是命令。<br>绝对不许死！',[e['translation'] for e in end]);self.assertIn('我答应你。<br>我们一定，还能再次相见……',[e['translation'] for e in end]);self.assertTrue(any('希望随着时间流逝' in e['translation'] for e in ps[4]['entries']));self.assertEqual(ps[-1]['entries'][-1]['translation'],'欢迎回来。')
 def test_previous_subtitle_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:38]),271)
  for s in p['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
