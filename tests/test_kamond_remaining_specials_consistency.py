from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class KamondRemainingSpecialsConsistencyTests(unittest.TestCase):
 def test_remaining_families_locked_without_primary_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/kamond-remaining-specials.json');self.assertEqual((len(r['entries']),len(r['scopes'])),(165,1))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0));self.assertEqual(r['retained_originals'],[])
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  scope=r['scopes'][0];ss=scope['selection'];self.assertEqual(scope['section'],'Karmond');self.assertEqual((scope['physical'],scope['planned'],scope['original_retained']),(165,165,0));self.assertFalse(ss['complete_section'])
  self.assertEqual((ss['full_section_source'],ss['full_section_planned'],ss['total_families'],ss['selected_families']),(309,309,103,55));self.assertEqual(len(ss['family_keys']),55);self.assertEqual(len(set(ss['family_keys'])),55)
  ids={e['id'] for e in r['entries']};self.assertEqual(len(ids),165);self.assertEqual(len(ss['source_ids']),165);self.assertEqual(ids,set(ss['source_ids']))
  previous=load('locales/zh-Hans/consistency-reviews/kamond-stats-bonuses.json');prior=next(s for s in previous['scopes'] if s['section']=='Karmond')['selection'];self.assertFalse(ids&set(prior['source_ids']));self.assertEqual(len(ids|set(prior['source_ids'])),309)
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
if __name__=='__main__':unittest.main()
