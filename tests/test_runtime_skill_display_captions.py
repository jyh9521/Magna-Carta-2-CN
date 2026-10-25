import json,hashlib,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class RuntimeSkillDisplayCaptionTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/runtime-skill-display-captions.json').read_bytes());self.p=json.loads((R/self.d['plan']['path']).read_bytes());self.labels={l['id']:l for l in self.p['labels']}
 def test_whole106_batch_and_prior1217_layers(self):
  from tools.build_font_route_probe import encoded
  self.assertTrue(self.d['applied']);self.assertFalse(self.d['game_rendering_verified']);self.assertEqual((self.d['new_groups'],self.d['new_layers'],self.d['new_physical_aliases']),(106,106,1143));self.assertEqual(len(self.d['groups']),106);self.assertEqual(hashlib.sha256(encoded(self.p['labels'][:1217])).hexdigest(),self.d['prior1217_layers_canonical_sha256']);self.assertGreaterEqual(len(self.p['labels']),1323)
 def test_actual_strings_and_texture_consumers_not_ocr_guess(self):
  for g in self.d['groups']:
   l=self.labels[g['image_id']];self.assertEqual(l['text'],g['new_text']);self.assertEqual(set(l['source_ids']),{b['current_source']['id']for b in g['actual_consumers']})
   for b in g['actual_consumers']:self.assertEqual(b['adopted']['translation'],l['text']);self.assertEqual(b['adopted']['source_sha256'],b['current_source']['source_sha256']);self.assertEqual(b['texture_property']['reference_path'],g['normal_image_reference']);self.assertTrue(b['name_property']['value'].startswith('<Strings:MC2Skill.'))
 def test_all1143_disc_aliases_keep_namespace_and_byte_locks(self):
  aliases=self.d['aliases'];self.assertEqual(len(aliases),1143);self.assertEqual(len({(a['disc'],a['path'],a['object'])for a in aliases}),1143);groups={g['image_id']:g for g in self.d['groups']}
  for a in aliases:
   self.assertEqual(a['canonical_namespace_guid'],self.d['canonical_namespace_guid']);self.assertEqual(a['rgba_sha256'],groups[a['image_id']]['original_native']);self.assertEqual(a['native_dimensions'],[512,64]);self.assertEqual(len(a['payload_sha256']),64);self.assertEqual(len(a['tiled_sha256']),64)
 def test_sparse_original_glyph_masks_and_owned_text_only(self):
  from PIL import Image
  for g in self.d['groups']:
   l=self.labels[g['image_id']];r=l['restoration'];m=Image.open(R/r['mask']['path']);p=Image.open(R/r['patch']['path']);self.assertEqual(m.size,(512,64));self.assertEqual(set(m.tobytes()),{0,255});self.assertEqual(set(p.tobytes()),{0});self.assertEqual(r['source_rgba_sha256'],g['original_native']);self.assertTrue(g['assistant_visual_native_review'])
 def test_unbound15_original_images_not_silently_adopted(self):
  self.assertEqual(len(self.d['unbound_originals']),15);blocked={r['object']for r in self.d['unbound_originals']}
  for s in self.p['sources']:
   for e in s['textures']:
    if s['path'].lower().endswith('/skillname_jpn.xxx'):self.assertNotIn(e['object'],blocked)
    elif e['object'].startswith('SkillName_Jpn.'):self.assertNotIn(e['object'].split('.',1)[1],blocked)
 def test_new_original_inputs_have_reproducible_subset_descriptor(self):
  d=json.loads((R/self.d['source_materialization']).read_bytes());self.assertEqual(d['kind'],'locked-resource-source-subset');self.assertEqual(len(d['resources']),133);refs={s['original']['path']:s['original']['sha256']for s in self.p['sources']}
  for r in d['resources']:self.assertTrue(r['destination'].startswith('build/poc-game/'));self.assertEqual(refs[r['destination']],r['expected_sha256']);self.assertTrue(r['discs'])
if __name__=='__main__':unittest.main()
