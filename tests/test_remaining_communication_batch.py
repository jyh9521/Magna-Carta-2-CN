"""Source-free regression contracts for the three retained communication banks."""
from pathlib import Path
import json,hashlib,unittest,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class RemainingCommunicationTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-116.json');self.r=load('locales/zh-Hans/batch-116.review.json');self.by={e['id']:e for e in self.p['entries']}
 def test_complete_nonempty_banks(self):
  self.assertEqual(len(self.by),256);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['held_entries'],[]);self.assertEqual({e['text_kind'] for e in self.r['entries']},{'dialogue'})
  totals=collections.Counter()
  for c in self.r['coverage']:totals[c['document']]+=c['entries']
  self.assertEqual(totals,{'MC2_communi_Crocell.int':28,'MC2_communi_Zephi.int':114,'MC2_communi_Zephie.int':114})
 def test_preserved_shapes(self):
  ts=[e['translation'] for e in self.by.values()]
  for c,n in [('\\n',55),('~',6),('～',2)]:self.assertEqual(sum(t.count(c) for t in ts),n)
  self.assertEqual(sum(t.endswith(' ') for t in ts),16);self.assertTrue(all(not any(c in t for c in '\r\n\0') for t in ts))
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']))
 def test_old_translations_and_source_locks(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:115] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),13826);self.assertFalse(old&self.by.keys())
  for e in self.by.values():self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertNotIn('line_break_policy',e)
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][115].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
 def test_exact_source_reuse_preserves_dual_ids(self):
  self.assertEqual(len({e['source_sha256'] for e in self.by.values()}),80)
  seen={}
  for e in self.by.values():
   h=e['source_sha256']
   if h in seen:self.assertEqual(seen[h],e['translation'])
   seen[h]=e['translation']
  a,b=['coalesced:180d3daf9e6eb63836c093bbc60e6ced9a651f77e1d556004d635c823139966f', 'coalesced:d8374e61d9879a2aa3dfe38310a8b263890f9b931360f7c24a28252fb28cef09']
  self.assertNotEqual(a,b);self.assertEqual(self.by[a]['source_sha256'],self.by[b]['source_sha256']);self.assertEqual(self.by[a]['translation'],self.by[b]['translation'])
 def test_terms_and_subtitles_unchanged(self):
  self.assertGreaterEqual(len(load('locales/zh-Hans/terms.json')['terms']),1104)
  ps=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(ps),44);self.assertEqual(sum(len(load(p['path'])['entries']) for p in ps),315)
  for e in ps:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
