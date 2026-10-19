"""Source-free contracts for phase variants, father's diary and flower legend."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class ReinpoltMalachiaTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-076.json');self.r=load('locales/zh-Hans/batch-076.review.json')
 def test_scope_types_and_breaks(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ06_020':5,'CSMBQ06_020_01':9,'CSMBQ06_020_02':8,'CSMBQ06_040':15,'CSMBQ06_050':22,'CSMBQ07_10':13,'Default':2});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':72,'name':2});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['preserved_functional_break_ids']);self.assertFalse(self.r['held_entries']);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),51)
 def test_new_ids_do_not_retranslate_old_or_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:75] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(8478,74));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  held={e['id'] for n in range(1,76) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(ids&held)
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_revenge_phase_variants_stay_separate(self):
  ts=[e['translation'] for e in self.p['entries']];threat=[t for t in ts if t.startswith('切，给我等着。')];self.assertEqual(len(threat),3);self.assertEqual([t[-1] for t in threat],['！','。','。']);self.assertEqual(threat[1],threat[2]);self.assertIn('我也想知道，他究竟是谁。',ts);self.assertTrue(any('今后要是你再背叛我们' in t for t in ts));self.assertIn('等一切结束后，为了赎罪，我会再去找那家伙。',ts)
 def test_diary_inferences_and_rejection_not_reconciled(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('爸爸好像就打算前往贝尔福特' in t for t in ts));self.assertTrue(any('也许会有人知道他的下落' in t for t in ts));self.assertTrue(any('我对你，连一丁点兴趣都没有' in t for t in ts));self.assertTrue(any('是不是也有那么一点意思' in t for t in ts));self.assertFalse(any('露已经爱上' in t or '父亲现在就在贝尔福特' in t for t in ts));self.assertEqual(sum(t=='玛拉基亚' for t in ts),2)
 def test_candidate_names_and_folklore(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),402);new=terms[399:402];self.assertEqual([(e['source'],e['target']) for e in new],[('레인폴트의 참사','雷恩波尔特惨案'),('말라키아','玛拉基亚'),('세야의 눈물','塞娅之泪')]);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('传说能让人' in t for t in ts));self.assertTrue(any('我对相信迷信的人，没有兴趣' in t for t in ts));self.assertEqual(next(e['target'] for e in terms if e['source']=='바이젠'),'拜泽恩')
 def test_previous_subtitle_plans(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),44);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:44]),315)
  for s in p['plans'][:44]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
