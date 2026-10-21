from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryCh10RenewalChoiceConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-ch10-renewal-choice.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(192,9))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(193,192))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),192)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_chapter_ten_complete_disjoint_coverage(self):
  seen=set();scopes=set();physical=planned=originals=0
  for name in ['story-ch10-contract-memory.json','story-ch10-renewal-choice.json']:
   d=json.loads((R/'locales/zh-Hans/consistency-reviews'/name).read_bytes());ids={e['id'] for e in d['entries']};self.assertFalse(ids&seen);seen|=ids;self.assertEqual(len(ids),len(d['entries']))
   self.assertEqual((d['new_translations'],d['new_context_entries']),(0,0))
   for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
   for sec in d['scopes']:
    self.assertNotIn(sec['section'],scopes);scopes.add(sec['section']);physical+=sec['physical'];planned+=sec['planned'];originals+=sec['original_retained']
  self.assertEqual((len(seen),physical,planned,originals,len(scopes)),(365,366,365,1,18))

if __name__=='__main__':unittest.main()
