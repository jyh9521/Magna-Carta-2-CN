import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
class TutorialNativeCohortTests(unittest.TestCase):
 def setUp(self):
  self.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/tutorial-native-captions.json').read_bytes())
 def test_all16_objects_51captions_32aliases_adopted(self):
  d=self.d;self.assertEqual((d['reviewed_standalone_objects'],d['new_image_groups'],d['new_text_layers'],d['new_aliases']),(16,16,51,32));self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['all_game_image_text_translated']);self.assertEqual(hashlib.sha256((R/d['plan']['path']).read_bytes()).hexdigest(),d['plan']['sha256'])
 def test_old1212_layers_unchanged_and_new51_are_complete(self):
  self.assertEqual(hashlib.sha256(json.dumps(self.p['labels'][:1212],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'7d447485c331c3be9686b03834b42f5e52102193c2af2231f06efbb88a8c0d21');ls=[l for g in self.d['groups']for l in g['labels']];self.assertEqual(self.p['labels'][1212:1263],ls);self.assertEqual(len(ls),51);self.assertEqual(len({l['id']for l in ls}),51)
 def test_sparse_glyph_repair_is_hash_locked(self):
  for g in self.d['groups']:
   self.assertTrue(g['manually_reviewed_native_output'])
   for l in g['labels']:
    rr=l['restoration'];ims={}
    for k in ['mask','patch']:
     ref=rr[k];p=R/ref['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),ref['sha256']);ims[k]=Image.open(p);self.assertEqual(ims[k].size,tuple(l['rect'][2:]))
    mask=ims['mask'].tobytes();patch=ims['patch'].convert('RGBA').tobytes();self.assertTrue(0<sum(bool(x)for x in mask)<len(mask));self.assertLessEqual(set(mask),{0,255});self.assertTrue(all(patch[i*4:i*4+4]==bytes(4)for i,x in enumerate(mask)if not x))
 def test_full_numeric_pixels_and_portraits_preserved(self):
  gs={g['reference_id']:g for g in self.d['groups']}
  for i in [326,334]:
   g=gs[i];p=g['native_encoded_proof'];guard=p['protected_pixel_regions'][0];self.assertEqual(guard['rect'],[144,67,104,61]);self.assertTrue(guard['pixels_preserved']);self.assertEqual(guard['before_rgba_sha256'],guard['after_rgba_sha256']);self.assertTrue(any(r['id']=='portrait'and r['blocks_preserved']for r in p['protected_regions']));self.assertEqual(g['labels'][0]['render_window'],dict(canvas=[88,28],crop=[0,4,88,24]))
  for g in self.d['groups']:
   for row in g['native_encoded_proof'].get('protected_regions',[]):self.assertTrue(row['blocks_preserved']);self.assertEqual(row['before_rgba_sha256'],row['after_rgba_sha256'])
 def test_canonical_namespace_guid_not_pixel_deduplication(self):
  self.assertEqual(len(self.d['aliases']),32);self.assertEqual(len({(g['canonical_path'],g['namespace_guid'])for g in self.d['groups']}),16);self.assertTrue(all(a['canonical_identity']['namespace_guid']and not a['canonical_identity']['runtime_instance_selected']for a in self.d['aliases']))
 def test_three_cropped_footers_remain_held(self):
  self.assertEqual(self.d['unbound_cropped_footer_fragments'],3);gs={g['reference_id']:g for g in self.d['groups']}
  for rid,rect in [(59,[128,112,128,16]),(68,[128,44,128,20]),(68,[128,108,128,20])]:self.assertTrue(any(p['rect']==rect and p['blocks_preserved']for p in gs[rid]['native_encoded_proof']['protected_regions']))
if __name__=='__main__':unittest.main()
