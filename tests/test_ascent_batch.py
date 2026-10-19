"""Source-free contracts for device sendoff, arrival and repeat access."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class AscentTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-066.json');self.r=load('locales/zh-Hans/batch-066.review.json')
 def test_scope_and_status(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB12_070':28,'CSMB12_090':8,'Chapter12':9});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':44,'menu_option':1});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
 def test_source_locks_no_overlap(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:65] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7851,45));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_repeat_menu_exact_reuse(self):
  value=r'<Styles:MC2_StyleFont_0>X<Styles:/> 出发\n<Styles:MC2_StyleFont_0>Y<Styles:/> 还需要准备';a=next(e for e in self.p['entries'] if '<Styles:' in e['translation']);b=next(e for e in load('locales/zh-Hans/batch-064.json')['entries'] if '<Styles:' in e['translation']);self.assertEqual(a['source_sha256'],b['source_sha256']);self.assertEqual(a['translation'],value);self.assertEqual(a['translation'],b['translation']);self.assertNotIn('line_break_policy',a)
 def test_functional_layout_and_space(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual(len(rows),9);self.assertEqual([e['translation'].count('\\n') for e in rows],[1,1,0,1,1,0,2,0,1]);self.assertTrue(rows[1]['translation'].endswith('。 '));self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),22)
 def test_existing_candidates_and_uncertainty(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('이그톤','伊格顿'),('라 스트라다','拉·斯特拉达'),('전송장치','传送装置')]:self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate')
  self.assertTrue(any('应该也能' in e['translation'] for e in self.p['entries']));self.assertTrue(any('只有我能操纵' in e['translation'] for e in self.p['entries']))
 def test_subtitle_is_sendoff_and_preserves_timing(self):
  p=load('locales/zh-Hans/subtitles/batch-066-csm12-80.txt.json');self.assertEqual(p['resource'],'MC2Game/Movies/csm12-80.txt');self.assertEqual(p['entries'],[{'start':44406,'end':48664,'source_sha256':'5af02af3482ec2bbc123226148d2a7a474c52e9ceef1fb1a2ed4d8a781dda11e','translation':'各位……一路顺风！'}]);profile=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(profile['plans']),38);self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:38]),271)
  for s in profile['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
