import json,unittest
from pathlib import Path
from tools import texture_overlay as overlay
import test_texture_overlay as fixtures
from test_supplement_font import stored_decoder
R=Path(__file__).resolve().parents[1]

class LargerRegionInventoryTests(unittest.TestCase):
 def test_actual_seventeen_cell_atlas_and_finite_bound(self):
  self.assertEqual(overlay.MAX_TEXTURE_REGIONS,32)
  self.assertEqual(len(overlay.layer_ids(dict(regions=[f'x{i}' for i in range(17)],image_id='atlas'))),17)
 def fixture(self,n):
  raw,_,_,e,_=fixtures.TextureOverlayTests().fixture();e.pop('label');e.update(regions=[f'x{i}' for i in range(n)],image_id='owned-atlas')
  layers={f'x{i}':(dict(rect=[(i%16)*8,(i//16)*8,4,4]),bytes([240,180,80,255])*16) for i in range(n)}
  return raw,e,layers
 def test_thirty_two_disjoint_regions_rebuild_and_preserve_other_blocks(self):
  raw,e,l=self.fixture(32);out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder);proof=p['textures'][0]
  self.assertNotEqual(out,raw);self.assertEqual(len(proof['regions']),32);self.assertEqual(proof['authorized_blocks'],32);self.assertTrue(proof['untouched_blocks_preserved']);self.assertTrue(proof['alignment_padding_preserved']);self.assertEqual(p['nonselected_exports_preserved'],2)
 def test_thirty_three_unique_regions_rejected(self):
  raw,e,l=self.fixture(33)
  with self.assertRaisesRegex(ValueError,'region labels'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
 def test_larger_inventory_still_rejects_overlaps(self):
  raw,e,l=self.fixture(32);l['x31']=l['x0']
  with self.assertRaisesRegex(ValueError,'overlap'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
 def test_protected_region_bound_not_expanded(self):
  raw,e,l=fixtures.MultiRegionTextureTests().fixture();e['protected_regions']*=17
  with self.assertRaisesRegex(ValueError,'protected region bound'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)

class RemainingUiNamePlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());cls.d=json.loads((R/'locales/zh-Hans/candidate-decisions/remaining-ui-name-image-labels.json').read_bytes());cls.labels={l['id']:l for l in cls.p['labels']};cls.rows={r['export']:r for r in cls.d['entries']}
 def test_exact_current_inventory_and_complete_ui_name_package(self):
  self.assertGreaterEqual(len(self.p['sources']),273);self.assertGreaterEqual(len(self.labels),708);self.assertGreaterEqual(len({overlay.image_id(e) for s in self.p['sources'] for e in s['textures']}),461)
  self.assertEqual(len(self.rows),56);self.assertEqual(sum(len(r['cells']) for r in self.rows.values()),274);self.assertEqual(len(next(s for s in self.p['sources'] if s['path']=='MC2Game/CookedXenon/UI_Name_Jpn.xxx')['textures']),184)
  for d,n in [(1,173),(2,230)]:self.assertGreaterEqual(sum(d in s['discs'] for s in self.p['sources']),n)
 def test_all_204_aliases_enrolled_with_exact_expected_payload(self):
  self.assertEqual(len(self.d['source_aliases']),204)
  for d in [1,2]:self.assertEqual(sum(a['disc']==d for a in self.d['source_aliases']),102)
  for a in self.d['source_aliases']:
   s=next(s for s in self.p['sources'] if s['path']==a['resource_path']);self.assertIn(a['disc'],s['discs']);e=next(e for e in s['textures'] if e['object']==a['object']);self.assertEqual(e['payload_sha256'],a['payload_sha256']);self.assertEqual(e['tiled_sha256'],a['tiled_sha256'])
 def test_every_cell_is_real_label_with_visible_source_hash(self):
  for r in self.rows.values():
   for c in r['cells']:
    l=self.labels[f'img_ui_name_jpn_{r["export"]}_{c["cell"]}'];self.assertEqual(l['text'],c['translation']);self.assertEqual(l['source_text_sha256'],overlay.digest(c['visual_reading'].encode()));self.assertEqual(l['rect'],c['rect']);self.assertEqual(l['font_size'],c['font_size'])
 def test_unchanged_menu_state_pairs_have_identical_translations(self):
  for a,b in [(11,12),(134,135),(161,162),(163,164),(166,167),(176,177),(178,179),(183,184),(186,187),(190,191)]:
   self.assertEqual([(c['visual_reading'],c['translation'],c['rect']) for c in self.rows[a]['cells']],[(c['visual_reading'],c['translation'],c['rect']) for c in self.rows[b]['cells']])
 def test_source_semantics_not_english_leaf_or_unrelated_field(self):
  for n in [134,135,136]:self.assertEqual(next(c['translation'] for c in self.rows[n]['cells'] if c['visual_reading']=='로드'),'读取')
  self.assertEqual(next(c['translation'] for c in self.rows[170]['cells'] if c['visual_reading']=='초기화'),'恢复默认')
  self.assertEqual(self.labels['img_ui_name_jpn_188_10']['text'],'当前成员');self.assertEqual(self.labels['img_ui_name_jpn_142_0']['text'],'里空进枪');self.assertEqual(self.labels['img_ui_name_jpn_140_6']['text'],'秘奥义·一击必杀')
 def test_narrow_email_and_equipment_labels_use_readable_equivalents(self):
  for n,text in [('165_3','致'),('165_4','来自'),('157_6','辅助'),('170_4','辅助'),('188_13','辅助')]:
   l=self.labels['img_ui_name_jpn_'+n];self.assertEqual(l['text'],text);self.assertGreaterEqual(l['font_size'],16)
 def test_seventeen_regions_protections_and_nonoverlap(self):
  groups={f'img_ui_name_jpn_{n}' for n in self.rows};maximum=0
  for s in self.p['sources']:
   for e in s['textures']:
    if overlay.image_id(e) not in groups:continue
    ids=overlay.layer_ids(e);maximum=max(maximum,len(ids));w,h=e['dimensions'];allowed=set()
    for n in ids:
     blocks=overlay.region_offsets(w,h,self.labels[n]['rect']);self.assertFalse(allowed & blocks);allowed|=blocks
    for p in e.get('protected_regions',[]):self.assertFalse(allowed & overlay.region_offsets(w,h,p['rect']))
  self.assertEqual(maximum,17)
 def test_new_startup_font_base_is_not_replaced_with_original(self):
  s=next(s for s in self.p['sources'] if s['path']=='MC2Game/CookedXenon/Startup_int.xxx');self.assertNotEqual(s['base']['sha256'],s['original']['sha256']);self.assertIn('phase-285-verification/route-probe/candidate/',s['base']['path'])
 def test_actual_kamond_rows_are_thirty_two_pixels_apart(self):
  for n in [186,187]:
   self.assertEqual([c['rect'] for c in self.rows[n]['cells']],[[0,i*32,128,32] for i in range(4)])
 def test_gray_option_normal_states_remain_distinct_from_selected(self):
  for n in [176,178]:
   for c in self.rows[n]['cells']:self.assertEqual(c['style']['fill'],[183,183,183,255])
  for n in [177,179]:
   for c in self.rows[n]['cells']:self.assertNotEqual(c['style']['fill'],[183,183,183,255]);self.assertEqual(c['style']['shadow_fill'],[230,45,15,200])

if __name__=='__main__':unittest.main()
