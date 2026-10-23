import json,unittest,hashlib
from pathlib import Path
from tools.texture_overlay import image_id,layer_ids
R=Path(__file__).resolve().parents[1]
class BattleTutorialPlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());c.d=json.loads((R/'locales/zh-Hans/candidate-decisions/battle-tutorial-image-labels.json').read_bytes());c.labels={l['id']:l for l in c.p['labels']};c.rows={(r['package'],r['export']):r for r in c.d['entries']}
 def test_exact_inventory(self):
  self.assertEqual((len(self.p['sources']),len(self.labels),len({image_id(e) for s in self.p['sources'] for e in s['textures']})),(276,847,507));self.assertEqual(len(self.rows),46);self.assertEqual(sum(len(r['cells']) for r in self.rows.values()),139)
  for d,n in [(1,176),(2,233)]:self.assertEqual(sum(d in s['discs'] for s in self.p['sources']),n)
 def test_aliases_originals_and_fields(self):
  self.assertEqual(len(self.d['source_aliases']),92)
  for a in self.d['source_aliases']:
   s=next(s for s in self.p['sources'] if s['path']==a['resource_path']);e=next(e for e in s['textures'] if e['object']==a['path']);self.assertIn(a['disc'],s['discs']);self.assertEqual(s['original']['sha256'],a['source_sha256']);self.assertEqual(e['payload_sha256'],a['payload_sha256']);self.assertEqual(e['tiled_sha256'],a['tiled_sha256']);self.assertEqual(e['dimensions'],[a['width'],a['height']])
 def test_actual_text_cells_and_source_hashes(self):
  for r in self.rows.values():
   for c in r['cells']:
    l=self.labels[f'img_{r["package"].lower()}_{r["export"]}_{c["cell"]}'];self.assertEqual(l['text'],c['translation']);self.assertEqual(l['source_text_sha256'],hashlib.sha256(c['visual_reading'].encode()).hexdigest());self.assertEqual(l['rect'],c['rect']);self.assertEqual(l['font_size'],c['font_size'])
 def test_packed_feedback_has_real_ten_pixel_font_and_explicit_padding(self):
  for n in [68,69,189,190]:
   l=self.labels[f'img_ui_battle_08_jp_{n}_0'];self.assertEqual(l['font_size'],10);self.assertEqual(l['ink_padding'],dict(x=4,y=1));self.assertEqual(l['rect'][3],16)
 def test_paired_start_opaque_mask_and_protected_button(self):
  edits={image_id(e):e for s in self.p['sources'] for e in s['textures']}
  a,b=[self.labels[f'img_ui_battle_08_jp_{n}_0'] for n in [108,109]];self.assertEqual(a['text'],b['text']);self.assertEqual(a['rect'],b['rect']);e=edits['img_ui_battle_08_jp_109'];self.assertEqual(e['profile'],dict(kind='xbox-inline-bc-v1',format=5));self.assertEqual(e['channel_mode'],'opaque-luma');self.assertTrue(e['protected_regions']);self.assertFalse(self.d['mask_shader_consumer_verified'])
 def test_tutorial_namespaces_are_not_collapsed(self):
  rs=[r for r in self.rows.values() if r['package'].startswith('Tutorial')];self.assertEqual(len(rs),3);self.assertEqual(len({r['resource'] for r in rs}),3);self.assertEqual([r['export'] for r in rs],[28,32,27]);self.assertEqual(rs[1]['rgba_sha256'],rs[2]['rgba_sha256'])
 def test_max_retention_is_not_patched(self):
  self.assertEqual(len(self.d['retained_MAX']),2);self.assertNotIn('img_ui_battle_08_jp_119',{image_id(e) for s in self.p['sources'] for e in s['textures']});self.assertEqual(self.d['language_layers'],138);self.assertEqual(self.d['derived_mask_layers'],1)
 def test_effect_last_line_is_not_plain_kick(self):
  c=self.rows['UI_Battle_08_Jp',160]['cells'][6];self.assertEqual(c['visual_reading'],'『氷の媒質』破壊');self.assertEqual(c['translation'],'破坏冰之媒质');self.assertEqual(self.labels['img_ui_battle_08_jp_156_6']['text'],'踢击')
 def test_native_review_state_and_sentence_reflow(self):
  self.assertEqual(self.labels['img_ui_battle_08_jp_87_0']['style']['stroke_fill'],[255,20,65,255]);self.assertEqual(''.join(self.labels[f'img_ui_battle_08_jp_172_{i}']['text'] for i in range(3)),'需要塞蕾丝汀的“冰之大炼换阵”才行。');self.assertTrue(all(self.labels[f'img_ui_battle_08_jp_172_{i}']['font_size']>=14 for i in range(3)))
if __name__=='__main__':unittest.main()
