from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class QuestTailCharacterConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/quest-tail-character-links.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(94,9))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(97,94))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),94)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])

 def test_all_quest_review_ids_cover_1954_once(self):
  paths=sorted((R/'locales/zh-Hans/consistency-reviews').glob('quest-*.json'))
  self.assertEqual(len(paths),10);seen=set();sections=set();physical=planned=retained=0
  for path in paths:
   d=json.loads(path.read_bytes());ids={e['id'] for e in d['entries']}
   self.assertFalse(seen & ids);self.assertEqual(len(ids),len(d['entries']));seen |= ids
   for scope in d['scopes']:
    self.assertNotIn(scope['section'],sections);sections.add(scope['section'])
    physical+=scope['physical'];planned+=scope['planned'];retained+=scope['original_retained']
   self.assertEqual((d['new_translations'],d['new_context_entries']),(0,0))
   for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
  self.assertEqual(len(seen),1954)
  self.assertEqual((physical,planned,retained),(1961,1954,7))

if __name__=='__main__':unittest.main()
