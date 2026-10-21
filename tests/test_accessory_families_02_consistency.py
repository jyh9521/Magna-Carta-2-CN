from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class AccessoryFamilies02ConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/accessory-families-02.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(219,1))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(219,219))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  self.assertEqual(len(r['retained_originals']),0)
  self.assertTrue(all(not e['runtime_role_verified'] and e['source_discs']==[1,2] and hashlib.sha256(e['source'].encode()).hexdigest()==e['source_sha256'] for e in r['retained_originals']))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  scope=r['scopes'][0];selection=scope['selection']
  self.assertFalse(selection['complete_section'])
  self.assertEqual((selection['full_section_source'],selection['full_section_planned'],selection['total_families'],selection['selected_families']),(438,438,146,73))
  self.assertEqual(len(selection['family_keys']),73)
  self.assertEqual(len(set(selection['family_keys'])),73)
  self.assertEqual(len(selection['source_ids']),219)
  self.assertEqual(set(selection['source_ids']),{e['id'] for e in r['entries']})
  prior=load('locales/zh-Hans/consistency-reviews/accessory-families-01.json')
  self.assertFalse(set(selection['source_ids']) & {e['id'] for e in prior['entries']})
  self.assertEqual(len(set(selection['source_ids']) | {e['id'] for e in prior['entries']}),438)
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),219)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
if __name__=='__main__':unittest.main()
