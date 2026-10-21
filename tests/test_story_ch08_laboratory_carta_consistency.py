from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryCh08LaboratoryCartaConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-ch08-laboratory-carta.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(239,17))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(239,239))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),239)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_chapter_eight_complete_scope_totals(self):
  d=json.loads((R/'locales/zh-Hans/consistency-reviews/story-ch08-laboratory-carta.json').read_bytes());self.assertEqual(len({e['id'] for e in d['entries']}),239);self.assertEqual(len({s['section'] for s in d['scopes']}),17)
  self.assertTrue(all(s['section'].startswith('CSMB08_') and s['physical']==s['planned'] and s['original_retained']==0 for s in d['scopes']));self.assertEqual(sum(s['physical'] for s in d['scopes']),239)

if __name__=='__main__':unittest.main()
