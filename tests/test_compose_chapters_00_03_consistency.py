from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class ComposeChapters0003ConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/compose-chapters-00-03.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(182,4))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(183,182))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  self.assertEqual(len(r['retained_originals']),1)
  original=r['retained_originals'][0];self.assertEqual(original['source'],'......');self.assertEqual(original['source_sha256'],hashlib.sha256(b'......').hexdigest());self.assertFalse(original['runtime_role_verified']);self.assertFalse(original['human_finalized'])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),182)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
if __name__=='__main__':unittest.main()
