"""Source-free contracts for the independently reviewed Korean communication bank."""
from pathlib import Path
import json,hashlib,unittest,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class ArgoCommunicationTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-114.json');self.r=load('locales/zh-Hans/batch-114.review.json')
 def test_complete_nonempty_bank(self):
  self.assertEqual(len(self.p['entries']),152);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['held_entries'],[])
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'overheat':24,'focus':14,'bad_abnormal':14,'good_abnormal':17,'HP_30':17,'communi_order':24,'communi_cancel':14,'communi_success':14,'communi_failure':14})
  self.assertEqual({e['document'] for e in self.r['coverage']},{'MC2_communi_Argo.int'});self.assertEqual({e['text_kind'] for e in self.r['entries']},{'dialogue'})
 def test_independent_ids_and_locked_sources(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:113] for e in load(b['plan']['path'])['entries']};new={e['id'] for e in self.p['entries']}
  self.assertEqual(len(old),13522);self.assertEqual(len(new),152);self.assertFalse(old&new)
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertNotIn('line_break_policy',e)
  self.assertEqual(new,{e['id'] for e in self.r['entries']});self.assertEqual(new,set(self.r['preserved_functional_break_ids']))
 def test_exact_source_reuse_and_trailing_spaces(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertEqual(len(set(ts)),53);self.assertEqual(sum(t.endswith(' ') for t in ts),18)
  self.assertTrue(all(not any(c in t for c in '\r\n\0') for t in ts));self.assertTrue(all('\\' not in t for t in ts))
  self.assertIn('抱歉，塞蕾丝汀。',ts);self.assertIn('洁菲，别鲁莽行事。',ts);self.assertIn('我已经做好战斗准备了。 ',ts)
 def test_plan_and_subtitle_locks(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][113].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  self.assertGreaterEqual(len(load('locales/zh-Hans/terms.json')['terms']),1104)
if __name__=='__main__':unittest.main()
