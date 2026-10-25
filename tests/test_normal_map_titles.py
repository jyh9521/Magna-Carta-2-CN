import json,hashlib,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class NormalMapTitleTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/normal-map-view-titles.json').read_bytes());self.p=json.loads((R/self.d['plan']['path']).read_bytes());self.labels={l['id']:l for l in self.p['labels']}
 def test_whole27_batch_and_prior1425_layers(self):
  from tools.build_font_route_probe import encoded
  self.assertTrue(self.d['applied']);self.assertFalse(self.d['game_rendering_verified']);self.assertEqual((self.d['new_groups'],self.d['new_layers'],self.d['new_aliases']),(27,36,28));self.assertEqual(len(self.d['groups']),27);self.assertEqual(hashlib.sha256(encoded(self.p['labels'][:1425])).hexdigest(),self.d['prior1425_layers_canonical_sha256']);self.assertGreaterEqual(len(self.p['labels']),1461)
 def test_actual_consumers_and_current_place_or_trial_anchors(self):
  count=0
  for g in self.d['groups']:
   self.assertTrue(g['actual_map_consumer']);self.assertTrue(g['assistant_visual_native_review'])
   for c in g['cells']:
    count+=1;l=self.labels[c['label_id']];self.assertEqual(l['text'],c['text']);self.assertEqual(set(l['source_ids']),{h['source']['id']for h in c['anchors']})
    for h in c['anchors']:self.assertEqual(h['source']['source_sha256'],h['adopted']['source_sha256'])
    self.assertTrue(any(l['text']in h['adopted']['translation']or h['adopted']['translation']in l['text']for h in c['anchors']))
  self.assertEqual(count,36)
 def test_namespaces_not_collapsed_by_identical_title_pixels(self):
  self.assertEqual(len({(g['canonical_source'],g['canonical_object'],g['namespace_guid'])for g in self.d['groups']}),27);self.assertEqual(sum(g['canonical_object']=='Map_View_Lastrada_Title'for g in self.d['groups']),18);self.assertEqual(len(self.d['aliases']),28)
  lookup={(g['canonical_source'],g['canonical_object']):g for g in self.d['groups']}
  for a in self.d['aliases']:g=lookup[a['canonical_source'],a['canonical_object']];self.assertEqual(a['canonical_namespace_guid'],g['namespace_guid']);self.assertEqual(a['rgba_sha256'],g['original_native']);self.assertEqual(len(a['payload_sha256']),64);self.assertEqual(len(a['tiled_sha256']),64)
 def test_original_latin_and_room_numerals_remain_exact(self):
  for g in self.d['groups']:
   self.assertTrue(g['terrain_never_touched']);self.assertTrue(g['original_English_and_numerals_exact'])
   if g['canonical_object']in['Map_View_DunanHill_Title','Map_View_Lastrada_Title']:p=g['original_latin_pixel_guard'];self.assertTrue(p['exact']);self.assertEqual(p['rgba_sha256'],p['after_sha256'])
   for p in g['native_encoded_proof'].get('protected_regions',[]):self.assertEqual(p['before_rgba_sha256'],p['after_rgba_sha256']);self.assertTrue(p['blocks_preserved'])
 def test_sparse_glyph_masks_not_rectangle_art_replacement(self):
  from PIL import Image
  allowed={'Map_View_DunanHill_Title','Map_View_Lastrada_Title','Map_View_Lastrada_01_Title','Map_View_Lastrada_03_Text0','Map_View_Senti_Title','Map_View_Senti_Title2'}
  for g in self.d['groups']:
   self.assertIn(g['canonical_object'],allowed)
   for c in g['cells']:
    l=self.labels[c['label_id']];r=l['restoration'];m=Image.open(R/r['mask']['path']);p=Image.open(R/r['patch']['path']);self.assertEqual(m.size,tuple(l['rect'][2:]));self.assertEqual(set(m.tobytes()),{0,255});self.assertEqual(set(p.tobytes()),{0})
 def test_subset_inputs_and_remaining_terrain_scope_not_silently_closed(self):
  j=json.loads((R/self.d['source_materialization']).read_bytes());self.assertEqual(len(j['resources']),20);self.assertEqual(sum(len(r['discs'])for r in j['resources']),21);self.assertEqual(self.d['remaining_map_namespace_groups'],57);self.assertTrue(self.d['tutorial_illustrations_all_original']);self.assertIn('원수의언덕',self.d['semantic_holds']);self.assertFalse(self.d['terrain_reconstruction_hypothesis_adopted'])
if __name__=='__main__':unittest.main()
