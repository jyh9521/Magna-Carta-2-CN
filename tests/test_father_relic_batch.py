"""Source-free contracts for the father meeting and inherited relic."""
from pathlib import Path
import unittest,json,hashlib
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class FatherRelicTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-082.json');self.r=L('locales/zh-Hans/batch-082.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ10_40':19,'10_cerestin_2':7});self.assertEqual(len(self.p['entries']),26);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),11);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),2);self.assertEqual(self.r['status'],'draft');self.assertEqual(sum(e['text_kind']=='dialogue' for e in self.r['entries']),24)
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:81] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8775);self.assertEqual(len(ids),26);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_family_names_and_candidate(self):
  terms=L('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),411);e=terms[410];self.assertEqual((e['source'],e['target']),('세리틴','塞莉汀'));self.assertEqual(e['review_status'],'candidate');self.assertEqual(e['relation'],'unverified');self.assertIn(e['source_string_id'],{e['id'] for e in self.p['entries']});s=''.join(e['translation'] for e in self.p['entries']);self.assertIn('[塞莉汀]',s);self.assertIn('塞蕾丝汀',s);self.assertNotIn('塞莉娅',s)
 def test_uncertainty_and_unfinished_talk(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('嗯……应该就是爸爸了。',ts);self.assertIn('这样啊……拜泽恩他……',ts);self.assertTrue(any(t.startswith('看来，拜泽恩') for t in ts));self.assertTrue(any('时间，已经不多了' in t for t in ts));self.assertIn('爸爸……别走。',ts);self.assertFalse(any('复活' in t or '附身' in t or '已经修好了' in t for t in ts))
 def test_relic_objective_and_future_work(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('将[拜泽恩的遗物]交给凯汀',ts);self.assertIn('父亲的遗物',ts);self.assertTrue(any('武器的原形' in t for t in ts));self.assertIn('我来修整一下，把它打磨成武器吧。',ts);protected=set(self.r['preserved_functional_break_ids']);self.assertTrue(all('line_break_policy' not in e for e in self.p['entries'] if e['id'] in protected));self.assertTrue(all(not e['translation'].endswith('。') for e in self.p['entries'] if e['id'] in protected))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,82) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
