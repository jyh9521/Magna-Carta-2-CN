from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryCh04AftermathLettersConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-ch04-aftermath-letters.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(220,15))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(220,220))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),220)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_chapter_four_complete_disjoint_coverage(self):
  def load(p):return json.loads((R/p).read_bytes())
  names=['story-ch04-return-proof.json','story-ch04-aftermath-letters.json'];seen=set();scopes=set()
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  for name in names:
   r=load('locales/zh-Hans/consistency-reviews/'+name);ids={e['id'] for e in r['entries']};self.assertFalse(ids&seen);seen|=ids
   for scope in r['scopes']:
    self.assertNotIn(scope['section'],scopes);scopes.add(scope['section']);self.assertEqual(scope['original_retained'],0);self.assertEqual(scope['physical'],scope['planned'])
  self.assertTrue(seen<=set(entries));self.assertEqual((len(seen),len(scopes)),(411,30))
if __name__=='__main__':unittest.main()
