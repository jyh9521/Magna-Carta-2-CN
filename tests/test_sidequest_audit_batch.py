"""Source-free regression contracts for chapter-eleven side-quest auditing."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class SidequestAuditTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-063.json');self.r=load('locales/zh-Hans/batch-063.review.json')
 def test_scope(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Chapter11':10,'11_303_0':18,'11_307_0':17,'11_302_0':16,'11_zuto_0':14,'Valuables':9});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':53,'name':9,'quest_progress':8,'narrative':5,'item_description':5,'quest_description':4});self.assertEqual(self.r['status'],'draft')
 def test_source_locks_disjoint_and_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:62] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};held={e['id'] for e in self.r['held_entries']};self.assertEqual((len(old),len(ids),len(held)),(7612,84,3));self.assertFalse(old&ids);self.assertFalse(held&(old|ids));self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertEqual({(e['section'],e['key']) for e in self.r['held_entries']},{('Chapter11','Chapter11_27'),('11_302_0','302_6'),('11_302_0','302_7')})
  for e in self.p['entries']+self.r['held_entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
 def test_functional_layout_and_spaces(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual([e['translation'].count('\\n') for e in rows],[0,1,1,1,1,2,2,2,1]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),35);ts=[e['translation'] for e in self.p['entries']];self.assertEqual(sum('\\n\\n' in t for t in ts),2)
  for t in ['奇怪蘑菇 ','神奇蘑菇 ','软体动物体液 ','只要收集5份，应该就够了。 ']:self.assertIn(t,ts)
 def test_source_contradictions_not_normalized(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('奇怪蘑菇' in t and '4个' in t for t in ts));self.assertTrue(any('毒蘑菇' in t and '3个' in t for t in ts));self.assertTrue(any('奇怪蘑菇' in t and '5个' in t for t in ts));self.assertIn('Quest%s: 神奇蘑菇 (%s/%s)',ts);self.assertIn('Quest%s: 毒蘑菇 (%s/%s)',ts);self.assertIn('QUEST%s: 软体动物体液 (%s/%s)',ts);self.assertIn('爱情魔药???',ts);self.assertTrue(any('不附加说话者' in n for n in self.r['notes']))
 def test_distinct_candidates_and_aliases(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('신기한 버섯','神奇蘑菇'),('이상한 버섯','奇怪蘑菇'),('독버섯','毒蘑菇'),('사랑의 비약','爱情魔药'),('연체동물의 체액','软体动物体液'),('연체동물의 채액','软体动物体液'),('궁극의 약','终极药'),('헬피쉬','地狱鱼'),('해저 동굴의 향','海底洞窟香料'),('코타메레','柯塔马雷')]:self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified');self.assertIn(ts[s]['source_string_id'],{e['id'] for e in self.p['entries']})
  self.assertEqual(ts['사랑의 묘약']['target'],ts['사랑의 비약']['target']);self.assertEqual(ts['사랑의 비약']['form'],'alias');self.assertEqual(ts['코타메레']['form'],'alias');self.assertEqual(len({ts[s]['target'] for s in ['신기한 버섯','이상한 버섯','독버섯']}),3)
 def test_subtitle_prefix_unchanged(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),37);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:37]),270)
  for s in p['plans'][:37]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
