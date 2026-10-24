import hashlib,json,unittest
from pathlib import Path
from tools import texture_overlay as o,texture_layout as t
from tools.ue3_textures import decode_dxt5,encode_white_bc3_block
ROOT=Path(__file__).resolve().parents[1]

class AdaptiveAlphaTests(unittest.TestCase):
 def fixture(self):
  lo=t.unit_layout(64,16,7);rgba=bytes([20,12,8,204])*16;block=o.encode_alpha_range([204]*16)+o.encode_rgba_block(rgba)[8:];native=b''.join(block[i:i+2][::-1]for i in range(0,16,2));tiles=bytearray(lo['storage_bytes'])
  for x in lo['offsets']:tiles[x:x+16]=native
  tx=dict(layout=lo,width=64,height=16,format=7,tiles=bytes(tiles));label=dict(rect=[8,4,8,8],restoration=dict(source_rgba_sha256=o.digest(o.rgba_crop(t.decode_texture(tx),64,[8,4,8,8]))),_repair_mask=bytes([255]+[0]*63),_repair_pixels=bytes([255,255,255,255])+bytes(252));edit=dict(regions=['x'],image_id='owned-translucent-background',profile=dict(kind=t.PROFILE,format=7),channel_mode='rgba',preserve_unchanged_blocks=True,alpha_encoding='adaptive-range');return tx,label,edit
 def test_original204_background_does_not_turn_into_rectangular218_band(self):
  tx,l,e=self.fixture();a,p=o.overlay_profile_regions(tx,e,{'x':(l,bytes(256))});pixels=t.decode_texture(tx,a);self.assertEqual(pixels[(4*64+8)*4+3],255);self.assertEqual(pixels[(4*64+9)*4+3],204);self.assertEqual(p['unchanged_region_blocks_preserved'],3);self.assertEqual(p['alpha_encoding'],'adaptive-range')
 def test_constant_translucency_is_exact(self):
  block=o.encode_alpha_range([204]*16)+o.encode_rgba_block(bytes([20,12,8,204])*16)[8:];self.assertEqual(set(decode_dxt5(block,4,4)[3::4]),{204})
 def test_legacy_encoder_prefix_remains_exact(self):
  rgba=bytes([20,12,8,204])*16;self.assertEqual(o.encode_rgba_block(rgba)[:8],encode_white_bc3_block([204]*16)[:8]);tx,l,e=self.fixture();e.pop('alpha_encoding');a,p=o.overlay_profile_regions(tx,e,{'x':(l,bytes(256))});self.assertNotEqual(t.decode_texture(tx,a)[(4*64+9)*4+3],204);self.assertNotIn('alpha_encoding',p)
 def test_cache_keys_separate_encodings_in_both_orders(self):
  tx,l,e=self.fixture();pixels=bytes([20,12,8,204])*64
  for modes in[(None,'adaptive-range'),('adaptive-range',None)]:
   cache={};results={}
   for mode in modes:results[mode]=t.overlay_rect(tx['tiles'],tx['layout'],l['rect'],pixels,cache,alpha_encoding=mode)[0]
   self.assertEqual(len(cache),2);self.assertNotEqual(results[None],results['adaptive-range'])
 def test_alpha_samples_have_exact_byte_shape(self):
  for alpha in[[204]*15,[True]*16,[-1]*16,[256]*16]:
   with self.assertRaises(ValueError):o.encode_alpha_range(alpha)
 def test_optin_requires_supported_profile_restoration_and_preserve(self):
  tx,l,e=self.fixture()
  for change in[dict(alpha_encoding='unknown'),dict(alpha_encoding=None),dict(preserve_unchanged_blocks=False),dict(channel_mode='opaque-rgb')]:
   with self.assertRaises(ValueError):o.overlay_profile_regions(tx,dict(e,**change),{'x':(l,bytes(256))})
  bare=dict(l);bare.pop('restoration')
  with self.assertRaisesRegex(ValueError,'restoration'):o.overlay_profile_regions(tx,e,{'x':(bare,bytes(256))})
  with self.assertRaises(ValueError):t.overlay_rect(tx['tiles'],dict(tx['layout'],format=5),l['rect'],bytes(256),alpha_encoding='adaptive-range')

class FieldMenuPlanTests(unittest.TestCase):
 def setUp(self):
  self.plan=json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.d=json.loads((ROOT/'locales/zh-Hans/candidate-decisions/field-mainmenu-image-labels.json').read_bytes())
 def test9_coherent_captions_and_scope(self):
  d=self.d;self.assertEqual((d['new_image_groups'],d['new_text_layers'],d['new_aliases']),(1,9,2));self.assertEqual(len(d['entries']),9);self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['all_game_image_text_translated']);labels={l['id']:l for l in self.plan['labels']}
  for row in d['entries']:self.assertTrue(row['manual_review']);self.assertEqual(row['label'],labels[row['label']['id']])
 def test_complete_row_footprints_and_original_side_gutter(self):
  rows={l['id'].removeprefix('field_menu_'):l['rect']for l in self.plan['labels']if l['id'].startswith('field_menu_')}
  self.assertEqual([rows[k]for k in ['weapon_list','style_list','information','current_kamond','kamond_board','equip_list']],[[284,176,92,20],[376,176,80,20],[284,196,128,16],[284,212,128,20],[284,232,128,16],[284,248,128,20]])
  self.assertEqual(self.d['footprint_revision'],2);self.assertTrue(self.d['previous_native_candidate_rejected']);self.assertEqual(self.d['non_glyph_alpha_residuals'],0)
 def test_prior1128_layers_unchanged(self):
  raw=json.dumps(self.plan['labels'][:1128],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),'122843d5aaf0d8ff000cdd7abdc4d7f268d360d08e0535c87a863934f160c253')
 def test_original_badges_and_art_explicitly_protected(self):
  edits=[e for s in self.plan['sources']for e in s['textures']if e.get('image_id')=='field_mainmenu_atlas'];self.assertEqual(len(edits),1);e=edits[0];self.assertEqual(e['alpha_encoding'],'adaptive-range');self.assertTrue(e['preserve_unchanged_blocks']);self.assertEqual({p['id']for p in e['protected_regions']},{'master_held','sid_and_arrow','hp_exp_lv_panel','blue_panel_art','menu_left_gutter'});self.assertTrue(all(x['blocks_preserved']for x in self.d['native_encoded_proof']['protected_regions']));self.assertTrue(any('卡蒙德盘'in a['translation']for a in self.d['terminology_anchors']))
  for row in self.d['entries']:
   for ref in row['label']['restoration'].values():
    if isinstance(ref,dict):self.assertEqual(hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest(),ref['sha256'])

if __name__=='__main__':unittest.main()
