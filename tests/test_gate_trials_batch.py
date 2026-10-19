"""Source-free contracts for the first two gate trials and intervening speech."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class GateTrialTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-067.json');self.r=load('locales/zh-Hans/batch-067.review.json')
 def test_scope_and_status(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB12_091':15,'CSMB12_092':2,'CSMB12_100':5,'CSMB12_110':5,'CSMB12_111':18,'CSMB12_112':2,'CSMB12_113':2,'CSMB12_114':2,'CSMB12_115':2,'CSMB12_116':2,'CSMB12_117':3,'Chapter12':3});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':58,'tutorial':3});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
 def test_source_locks_overlap_and_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:66] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7896,61));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(ids&{e['id'] for e in load('locales/zh-Hans/batch-063.review.json')['held_entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_tutorial_layout_markers_and_numbers(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual(len(rows),3);self.assertEqual([e['translation'].count('\\n') for e in rows],[3,2,2]);self.assertEqual([e['translation'].count('*') for e in rows],[0,2,3]);self.assertEqual([re.findall(r'[0-9]+',e['translation']) for e in rows],[[],['10'],['3']]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),34)
 def test_mechanics_and_character_claim_remain_distinct(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('这可难办了。我和朱特，都无法产生属性KAN。',ts);self.assertTrue(any('再触发一次同一个开关' in t for t in ts));self.assertTrue(any('中央' in t and '一切都会回到原点' in t for t in ts));self.assertTrue(any('10次爆炸' in t and '即使还有剩余时间' in t for t in ts));self.assertTrue(any('碰撞10次' in t for t in ts));self.assertTrue(any('我一直都很想' in t and '哨兵' in t for t in ts))
 def test_distinct_candidates_not_approved(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),363);new=terms[352:363];self.assertEqual(len(new),11);self.assertEqual({e['source']:e['target'] for e in new},{'명석의 시련':'明智之试炼','지혜':'智慧','명민':'聪敏','통찰':'洞察','시동의 스위치':'启动开关','제물의 시련':'祭品之试炼','용기':'勇气','용맹':'勇猛','진용':'真勇','시련의 구체':'试炼之球','가호의 빛':'庇护之光'});self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));self.assertIn('汉字与词源待核',next(e for e in new if e['source']=='진용')['basis'])
 def test_previous_subtitle_prefix(self):
  profile=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(profile['plans']),38);self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:38]),271)
  for s in profile['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
