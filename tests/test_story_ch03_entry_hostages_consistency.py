from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryCh03EntryHostagesConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-ch03-entry-hostages.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(280,10))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(281,280))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),280)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])

 def test_chapter03_primary_snapshots_cover_687_once(self):
  names=['story-ch03-hostage-invasion.json','story-ch03-alliance-tomb.json','story-ch03-entry-hostages.json'];seen=set();scopes=set();physical=planned=originals=0
  for name in names:
   d=json.loads((R/'locales/zh-Hans/consistency-reviews'/name).read_bytes());ids={e['id'] for e in d['entries']};self.assertFalse(ids&seen);seen|=ids;self.assertEqual(len(ids),len(d['entries']))
   self.assertEqual((d['new_translations'],d['new_context_entries']),(0,0))
   for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
   for sec in d['scopes']:
    self.assertNotIn(sec['section'],scopes);scopes.add(sec['section']);physical+=sec['physical'];planned+=sec['planned'];originals+=sec['original_retained']
  self.assertEqual((len(seen),physical,planned,originals,len(scopes)),(687,688,687,1,27))
  cur=json.loads((R/'locales/zh-Hans/consistency-reviews/story-ch03-entry-hostages.json').read_bytes());prior=json.loads((R/'locales/zh-Hans/consistency-reviews/npc-kotamare-pong.json').read_bytes());lm={e['id']:e for e in prior['linked_context']};cm={e['id']:e for e in cur['entries']}
  self.assertEqual(set(cur['reused_linked_context_ids']),set(lm));self.assertEqual(cur['new_primary_consistency_fields'],227)
  for i,e in lm.items():self.assertEqual(cm[i],e)

if __name__=='__main__':unittest.main()
