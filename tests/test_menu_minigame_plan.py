import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
class MenuMinigameBatchTests(unittest.TestCase):
 def setUp(self):
  self.plan=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/menu-minigame-image-labels.json').read_bytes())
 def test_whole27_objects_are_one_coherent_adopted_batch(self):
  d=self.d;self.assertEqual((d['reviewed_standalone_objects'],d['new_image_groups'],d['new_text_layers'],d['new_aliases']),(27,26,75,83));self.assertEqual(len(set(d['selected_object_ids'])),27);self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['all_game_image_text_translated']);self.assertEqual(hashlib.sha256((R/d['plan']['path']).read_bytes()).hexdigest(),d['plan']['sha256'])
 def test_prior1137_layers_are_exact_and_new75_unique(self):
  raw=json.dumps(self.plan['labels'][:1137],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),'90d9fee33c6ed3ce4c8793c1607ebf447351169dfeac7b9e083e75914b589330');self.assertGreaterEqual(len(self.plan['labels']),1212);labels=[l for g in self.d['groups']for l in g['labels']];self.assertEqual(len(labels),75);self.assertEqual(len({l['id']for l in labels}),75);self.assertEqual(self.plan['labels'][1137:1212],labels)
 def test_sparse_repair_material_is_hash_locked_and_confined(self):
  for g in self.d['groups']:
   self.assertTrue(g['manually_reviewed_native_output'])
   for l in g['labels']:
    rr=l['restoration'];im={}
    for k in ['mask','patch']:
     ref=rr[k];p=R/ref['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),ref['sha256']);im[k]=Image.open(p);self.assertEqual(im[k].size,tuple(l['rect'][2:]))
    mask=im['mask'].tobytes();patch=im['patch'].tobytes();self.assertTrue(0<sum(bool(x)for x in mask)<len(mask));self.assertLessEqual(set(mask),{0,255});self.assertTrue(all(patch[i*4:i*4+4]==bytes(4)for i,x in enumerate(mask)if not x))
 def test_original_buttons_values_portraits_and_counter_boxes_protected(self):
  gs={g['reference_id']:g for g in self.d['groups']}
  for rid in [1089,1090,1098,1099]:self.assertTrue(any(p['id']=='original_number_and_button'and p['blocks_preserved']for p in gs[rid]['native_encoded_proof']['protected_regions']))
  for rid in [1093,1071,1082]:self.assertTrue(any(p['id']=='original_portrait'and p['blocks_preserved']for p in gs[rid]['native_encoded_proof']['protected_regions']))
  labels={l['id']:l for l in self.plan['labels']};self.assertEqual(labels['ui_batch_1073_time']['rect'],[0,204,64,20]);self.assertEqual(labels['ui_batch_1075_time']['rect'],[0,0,128,16]);self.assertTrue(any(p['id']=='counter_box'and p['blocks_preserved']for p in gs[1075]['native_encoded_proof']['protected_regions']))
 def test_namespace_identity_not_same_pixel_deduplication(self):
  gs={g['reference_id']:g for g in self.d['groups']};self.assertEqual(set(gs[925]['input_objects']),{925,1488});self.assertNotEqual((gs[1071]['canonical_path'],gs[1071]['namespace_guid']),(gs[1082]['canonical_path'],gs[1082]['namespace_guid']));self.assertEqual(len(self.d['aliases']),83);self.assertTrue(all(a['canonical_identity']['namespace_guid']and not a['canonical_identity']['runtime_instance_selected']for a in self.d['aliases']))
if __name__=='__main__':unittest.main()
