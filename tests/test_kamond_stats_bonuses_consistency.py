from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class KamondStatsBonusesConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_with_mixed_scope_selection(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/kamond-stats-bonuses.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(180,2))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(180,180))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0));self.assertEqual(r['retained_originals'],[])
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  scopes={s['section']:s for s in r['scopes']};bonus=scopes['Kamond_EquipBonus'];partial=scopes['Karmond'];selection=partial['selection']
  self.assertEqual((bonus['physical'],bonus['planned'],bonus['original_retained']),(36,36,0));self.assertNotIn('selection',bonus)
  self.assertEqual((partial['physical'],partial['planned'],partial['original_retained']),(144,144,0));self.assertFalse(selection['complete_section'])
  self.assertEqual((selection['full_section_source'],selection['full_section_planned'],selection['total_families'],selection['selected_families']),(309,309,103,48))
  self.assertEqual(len(set(selection['family_keys'])),48);self.assertEqual(len(selection['family_keys']),48);self.assertEqual(len(selection['source_ids']),144);self.assertEqual(len(set(selection['source_ids'])),144)
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),180);self.assertTrue(set(selection['source_ids'])<={e['id'] for e in r['entries']})
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
if __name__=='__main__':unittest.main()
