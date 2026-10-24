import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
class TutorialMenuCohortTests(unittest.TestCase):
 def setUp(self):self.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/tutorial-menu-native-captions.json').read_bytes())
 def test_complete_coherent41caption_cohort(self):
  d=self.d;self.assertEqual((d['new_image_groups'],d['new_text_layers'],d['new_aliases']),(8,41,16));self.assertEqual(hashlib.sha256((R/d['plan']['path']).read_bytes()).hexdigest(),d['plan']['sha256']);self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['all_game_image_text_translated'])
 def test_old1263_layers_and_new41_exact(self):
  self.assertEqual(hashlib.sha256(json.dumps(self.p['labels'][:1263],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'9eda1c52bb45425228c7099f1706c05dd06b1a0fdecdded1226d0fb4f3fcfb57');self.assertEqual(self.p['labels'][1263:1304],[l for g in self.d['groups']for l in g['labels']])
 def test_sparse_masks_and_patches_hash_locked(self):
  for g in self.d['groups']:
   self.assertTrue(g['manually_reviewed_native_output'])
   for l in g['labels']:
    ims={}
    for k in ['mask','patch']:
     ref=l['restoration'][k];p=R/ref['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),ref['sha256']);ims[k]=Image.open(p);self.assertEqual(ims[k].size,tuple(l['rect'][2:]))
    mask=ims['mask'].tobytes();patch=ims['patch'].convert('RGBA').tobytes();self.assertTrue(0<sum(bool(x)for x in mask)<len(mask));self.assertLessEqual(set(mask),{0,255});self.assertTrue(all(patch[i*4:i*4+4]==bytes(4)for i,v in enumerate(mask)if not v))
 def test_numbers_SP_portraits_and_art_protected(self):
  for g in self.d['groups']:
   for p in g['native_encoded_proof'].get('protected_regions',[]):self.assertTrue(p['blocks_preserved']);self.assertEqual(p['before_rgba_sha256'],p['after_rgba_sha256'])
  gs={g['reference_id']:g for g in self.d['groups']}
  for rid in [257,266]:self.assertTrue(any(p['id']=='original_SP_acronym'for p in gs[rid]['native_encoded_proof']['protected_regions']))
 def test_cropped_backgrounds_held_not_guessed(self):
  self.assertTrue(self.d['original_three_cropped_footer_fragments_still_held']);self.assertEqual(len(self.d['held_cropped_background_fields']),2)
  for g in self.d['groups']:
   if g['reference_id']in[258,273]:self.assertTrue(any(p['id']=='unbound_cropped_faded_background_label'and p['blocks_preserved']for p in g['native_encoded_proof']['protected_regions']))
 def test_current_adopted_term_anchors_and_namespace_distinction(self):
  anchors={r['source']:r['translation']for r in self.d['active_text_anchors']};self.assertEqual(anchors['윈드 커터'],'风刃斩');self.assertEqual(anchors['큐어러'],'疗愈术');self.assertEqual(anchors['이공진퇴'],'凌空震踢');self.assertEqual(len({(g['canonical_path'],g['namespace_guid'])for g in self.d['groups']}),8);self.assertEqual(len(self.d['aliases']),16)
if __name__=='__main__':unittest.main()
