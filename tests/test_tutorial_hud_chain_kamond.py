import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
class TutorialHUDChainKamondTests(unittest.TestCase):
 def setUp(self):self.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/tutorial-hud-chain-kamond-captions.json').read_bytes())
 def test_coherent35layer36source_caption_batch(self):
  d=self.d;self.assertEqual((d['new_image_groups'],d['new_text_layers'],d['new_source_caption_fields'],d['new_aliases']),(12,35,36,24));self.assertEqual(d['fully_localized_selected_objects'],11);self.assertEqual(d['partially_localized_selected_objects'],[200]);self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['all_game_image_text_translated']);self.assertEqual(hashlib.sha256((R/d['plan']['path']).read_bytes()).hexdigest(),d['plan']['sha256'])
 def test_old1304_layers_exact_new35_structured(self):
  self.assertEqual(hashlib.sha256(json.dumps(self.p['labels'][:1304],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'86fd96b7bc5716e13b2b5d83119a00593c337bf8fbd5d3e1ca4d47a3cf99a1cf');self.assertEqual(self.p['labels'][1304:1339],[l for g in self.d['groups']for l in g['labels']]);self.assertEqual(len({l['id']for g in self.d['groups']for l in g['labels']}),35)
 def test_sparse_footprints_and_hashes(self):
  for g in self.d['groups']:
   self.assertTrue(g['manually_reviewed_native_output'])
   for l in g['labels']:
    ims={}
    for k in['mask','patch']:
     q=l['restoration'][k];p=R/q['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),q['sha256']);ims[k]=Image.open(p);self.assertEqual(ims[k].size,tuple(l['rect'][2:]))
    m=ims['mask'].tobytes();b=ims['patch'].convert('RGBA').tobytes();self.assertTrue(0<sum(bool(x)for x in m)<len(m));self.assertTrue(all(b[i*4:i*4+4]==bytes(4)for i,x in enumerate(m)if not x))
 def test_all_values_gauges_and_art_exact(self):
  from tools.bc_palette_guard import MAX_RGB_ERROR
  self.assertEqual(MAX_RGB_ERROR,32)
  for g in self.d['groups']:
   for p in g['native_encoded_proof'].get('protected_regions',[]):self.assertTrue(p['blocks_preserved']);self.assertEqual(p['before_rgba_sha256'],p['after_rgba_sha256'])
   for p in g['native_encoded_proof'].get('protected_pixel_regions',[]):self.assertTrue(p['pixels_preserved']);self.assertEqual(p['before_rgba_sha256'],p['after_rgba_sha256'])
 def test_unconfirmed_legacy_row_and_old5_crops_stay_held(self):
  self.assertTrue(self.d['original_five_cropped_fields_still_held']);self.assertIsNone(self.d['held_semantic_fields'][0]['translation']);g=next(g for g in self.d['groups']if g['reference_id']==200);self.assertTrue(any(p['id']=='unconfirmed_last_card_whole_row'and p['blocks_preserved']for p in g['native_encoded_proof']['protected_regions']))
 def test_compound_caption_is_explicit_and_namespace_distinct(self):
  g=next(g for g in self.d['groups']if g['reference_id']==381);self.assertEqual(g['compound_caption_source_fields'],['CHAIN BREAK','CROCELL']);self.assertEqual(g['labels'][0]['text'],'连锁终结·克罗塞尔');self.assertEqual(g['labels'][0]['render_window'],dict(canvas=[160,52],crop=[0,2,160,36]));self.assertEqual(len({(g['canonical_path'],g['namespace_guid'])for g in self.d['groups']}),12);self.assertTrue(all(a['canonical_identity']['namespace_guid']and not a['canonical_identity']['runtime_instance_selected']for a in self.d['aliases']))
if __name__=='__main__':unittest.main()
