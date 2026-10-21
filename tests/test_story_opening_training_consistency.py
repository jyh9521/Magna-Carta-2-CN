from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryOpeningTrainingConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-opening-training.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(276,10))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(276,276))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),276)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_complete_opening_scope_inventory(self):
  r=json.loads((R/'locales/zh-Hans/consistency-reviews/story-opening-training.json').read_bytes())
  expected={'CSMB00_10':21,'CSMB00_13':30,'CSMB00_14':19,'CSMB00_15':80,'CSMB00_18':42,'CSMB00_21':21,'CSMB00_22':19,'CSMB00_25':14,'CSMB00_31':17,'CSMB00_50':13}
  self.assertEqual(len(r['scopes']),len(expected));self.assertEqual({s['section']:s['planned'] for s in r['scopes']},expected)
  for s in r['scopes']:self.assertEqual((s['physical'],s['planned'],s['original_retained']),(expected[s['section']],expected[s['section']],0))
  self.assertEqual(sum(expected.values()),276)
if __name__=='__main__':unittest.main()
