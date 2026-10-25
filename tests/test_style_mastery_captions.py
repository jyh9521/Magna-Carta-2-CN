import json,unittest,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class StyleMasteryCaptionTests(unittest.TestCase):
 def setUp(self):
  self.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.labels={l['id']:l for l in self.p['labels']}
 def test_three_master_marks_are_consistent_and_not_story_master(self):
  for key in ['field_menu_master','style_info_master','style_master_badge']:self.assertEqual(self.labels.get(key,{}).get('text'),'精通')
 def test_exact_style_menu_consumer_chain_is_retained(self):
  d=json.loads((R/'locales/zh-Hans/candidate-decisions/style-mastery-captions.json').read_bytes());self.assertTrue(d['applied']);self.assertFalse(d['game_rendering_verified']);links=d['evidence']['links']
  for side in ['Main','Sub']:
   start='UI_Field_2.Scenes.StyleMenu.StyleCategoryPanel.Style_List.'+side+'Panel.Master_'+side;at=start
   for prop in ['ImageComponent','ImageRef','ImageTexture']:
    match=[l for l in links if l['owner']==at and l['property']==prop];self.assertEqual(len(match),1);at=match[0]['target']
   self.assertEqual(at,'UI_Field.Textures.Field_MainMenu_Master')
 def test_new_regions_have_sparse_glyph_masks_not_filled_rectangles(self):
  from PIL import Image
  for key in ['field_menu_master','style_info_location','style_info_play_time','style_info_master','style_master_badge']:
   l=self.labels[key];r=l['restoration'];m=Image.open(R/r['mask']['path']);p=Image.open(R/r['patch']['path']);self.assertEqual(set(m.tobytes()),{0,255});self.assertEqual(set(p.tobytes()),{0});self.assertEqual(hashlib.sha256((R/r['mask']['path']).read_bytes()).hexdigest(),r['mask']['sha256'])
 def test_atlas_frame_bullets_sid_and_other_captions_protected(self):
  edits=[e for s in self.p['sources']for e in s['textures']if e.get('image_id')=='style_info_atlas'];self.assertEqual(len(edits),2)
  for e in edits:self.assertEqual({g['id']for g in e['protected_regions']},{'frame','bullets','SID','right_margin'});self.assertEqual(len(e['regions']),3)
 def test_old_skill_name_not_guessed(self):
  self.assertFalse(any(e['object'].lower().endswith('skill_zephi.skill_zephi_8')for s in self.p['sources']for e in s['textures']))
  d=json.loads((R/'locales/zh-Hans/candidate-decisions/original-only-legacy-ui-assets.json').read_bytes());self.assertFalse(d['apply_translation']);self.assertFalse(d['legacy_skill']['has_current_field_binding']);self.assertFalse(d['global_dynamic_unreachability_proven']);self.assertEqual(d['root_target_reference_table_presence'],[]);self.assertEqual(len(d['scope']),27)
  blocked={(r['resource'].lower(),r['object'].lower())for r in d['scope']}
  for source in self.p['sources']:
   for e in source['textures']:self.assertNotIn((source['path'].lower(),e['object'].lower()),blocked)
 def test_all_1212_baseline_layers_unchanged(self):
  d=json.loads((R/'locales/zh-Hans/candidate-decisions/tutorial-illustrations-original-policy.json').read_bytes());h=json.loads((R/d['historical_plan']['path']).read_bytes());self.assertEqual(self.p['labels'][:1212],h['labels'][:1212])
if __name__=='__main__':unittest.main()
