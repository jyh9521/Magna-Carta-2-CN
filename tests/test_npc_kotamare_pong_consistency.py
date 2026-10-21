from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class NpcKotamarePongConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/npc-kotamare-pong.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(143,5))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(143,143))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),143)
  self.assertEqual(len(r['linked_context']),53)
  for e in r['entries']+r['linked_context']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])

 def test_all_npc_reviews_cover_1443_once(self):
  paths=['late-npc.json','npc-early-abazet.json','npc-opening-oldfox.json','npc-kotamare-pong.json','npc-legacy-scenes.json'];seen=set();sections=set();physical=planned=originals=0;targets={}
  def load(p):return json.loads((R/p).read_bytes())
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:targets.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  for name in paths:
   d=load('locales/zh-Hans/consistency-reviews/'+name);ids={e['id'] for e in d['entries']};self.assertFalse(ids&seen);seen|=ids;self.assertEqual(len(ids),len(d['entries']))
   self.assertEqual((d['new_translations'],d['new_context_entries']),(0,0))
   for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
   for e in d['entries']:
    p=targets[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
   for s in d['scopes']:
    self.assertNotIn(s['section'],sections);sections.add(s['section']);physical+=s['physical'];planned+=s['planned'];originals+=s['original_retained']
  self.assertEqual((len(seen),physical,planned,originals),(1443,1473,1443,30))

if __name__=='__main__':unittest.main()
