from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryCh09SquareFlightConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-ch09-square-flight.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(168,9))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(169,168))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),168)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_chapter_nine_complete_scope_totals(self):
  d=json.loads((R/'locales/zh-Hans/consistency-reviews/story-ch09-square-flight.json').read_bytes());self.assertEqual(len({e['id'] for e in d['entries']}),168);self.assertEqual(len({s['section'] for s in d['scopes']}),9)
  self.assertTrue(all(s['section'].startswith('CSMB09_') for s in d['scopes']));self.assertEqual((sum(s['physical'] for s in d['scopes']),sum(s['planned'] for s in d['scopes']),sum(s['original_retained'] for s in d['scopes'])),(169,168,1))

if __name__=='__main__':unittest.main()
