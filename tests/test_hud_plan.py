import json,hashlib,unittest
from pathlib import Path
from tools.texture_overlay import image_id,render_area
R=Path(__file__).resolve().parents[1]
class HudCaptionPlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());c.d=json.loads((R/'locales/zh-Hans/candidate-decisions/hud-image-labels.json').read_bytes());c.labels={l['id']:l for l in c.p['labels']};c.sources={s['path']:s for s in c.p['sources']}
 def test_cohort_inventory_and_old_labels_preserved(self):
  self.assertGreaterEqual(len(self.p['sources']),330);self.assertGreaterEqual(len(self.labels),1043);self.assertGreaterEqual(len({image_id(e) for s in self.p['sources'] for e in s['textures']}),586);self.assertEqual((self.d['image_groups'],self.d['text_layers'],len(self.d['all_source_aliases'])),(38,55,140));self.assertEqual(hashlib.sha256(json.dumps(self.p['labels'][:988],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'20bdaaa772fa117ab79029188519298b2bc6ad830949d439ca0079d01f821dd0')
 def test_all_aliases_and_disc_provenance_enrolled(self):
  for dn in [1,2]:self.assertEqual(sum(a['disc']==dn for a in self.d['all_source_aliases']),70)
  for a in self.d['all_source_aliases']:
   s=self.sources[a['resource_path']];e=next(e for e in s['textures'] if e['object']==a['path']);self.assertIn(a['disc'],s['discs']);self.assertEqual(s['original']['sha256'],a['source_sha256']);self.assertEqual(e['payload_sha256'],a['payload_sha256']);self.assertEqual(e['tiled_sha256'],a['tiled_sha256']);self.assertEqual(e['profile'],dict(kind='xbox-inline-bc-v1',format=7))
 def test_visible_readings_and_optional_field_evidence(self):
  for g in self.d['entries']:
   for l,e in zip(g['labels'],g['source_group']['cells']):
    self.assertEqual(self.labels[l['id']],l);self.assertEqual(l['text'],e['candidate_translation']);self.assertEqual(l['source_text_sha256'],hashlib.sha256(e['visible_source'].encode()).hexdigest())
    if e.get('evidence'):self.assertEqual(l['source_ids'],[e['evidence']['source_id']]);self.assertEqual(e['evidence']['source_text_sha256'],hashlib.sha256(e['evidence']['source'].encode()).hexdigest())
 def test_masked_portraits_preserve_art_without_plaques(self):
  gs=[g for g in self.d['entries'] if g['source_group']['package'] in ['UI_Battle_Chain_JoinAttack','UI_Level_UP'] and 3<=g['source_group']['export']<=10];self.assertEqual(len(gs),16)
  for g in gs:
   l=g['labels'][0];self.assertFalse(g['plaque_authored']);self.assertTrue(g['original_art_reconstructed']);self.assertFalse(g['reconstruction_exact_original']);self.assertIn('restoration',l);self.assertIn('font',l);self.assertNotIn('background_fill',l.get('style',{}));self.assertTrue(g['aliases'][0]['complement_regions'])
 def test_sparse_restoration_assets_are_hash_locked_and_masked(self):
  from PIL import Image
  restored=[l for l in self.p['labels'] if 'restoration' in l];self.assertEqual(len(restored),17)
  for l in restored:
   r=l['restoration'];images={}
   for key,mode in [('patch','RGBA'),('mask','L')]:
    path=R/r[key]['path'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),r[key]['sha256']);self.assertLess(path.stat().st_size,65536);im=Image.open(path);self.assertEqual(im.mode,mode);self.assertEqual(list(im.size),l['rect'][2:]);images[key]=im.tobytes()
   mask=images['mask'];patch=images['patch'];self.assertFalse(set(mask)-{0,255});self.assertTrue(any(mask));self.assertTrue(all(patch[i*4:i*4+4]==bytes(4) for i,v in enumerate(mask) if not v))
 def test_rue_far_field_has_no_detached_old_letter_pixels(self):
  from PIL import Image
  l=self.labels['hud_complete_07_00'];x,y,w,h=l['rect'];im=Image.open(R/l['restoration']['patch']['path']);self.assertEqual(max(im.crop((380-x,0,392-x,h)).getchannel('A').get_flattened_data()),0)
 def test_boss_category_art_is_never_overlaid_and_gray_state_remains(self):
  self.assertNotIn('hud_complete_16_00',self.labels);self.assertEqual(len(self.d['retained_source_aliases']),4)
  self.assertTrue(any(g.get('retained_original_export') and g['image_id']=='img_hud_complete_16' for g in self.d['retained_entries']))
  boss_hashes={hashlib.sha256(t.encode()).hexdigest() for t in ['Boss','BOSS','boss','보스']}
  for l in self.labels.values():self.assertNotIn(l.get('source_text_sha256'),boss_hashes)
  for source in self.p['sources']:
   for e in source['textures']:self.assertFalse(e['object'].casefold().endswith('tex.battel_boss_ui'))
  for g in self.d['entries']:
   if g['source_group']['package']=='UI_Battle_Master' and g['source_group']['export']==42:
    for l in g['labels']:self.assertEqual(l['style']['fill'],[176,176,176,255])
 def test_user_boss_term_applies_to_tutorial_without_replacing_named_bosses(self):
  batch=json.loads((R/'locales/zh-Hans/batch-098.json').read_bytes());e=next(e for e in batch['entries']if e['id']=='coalesced:24de89d1c0630c042bda12275bbf17ca0b5e965fa7364a740879a717775e6899');self.assertIn('敌方Boss',e['translation']);self.assertNotIn('首领',e['translation'])
  terms=json.loads((R/'locales/zh-Hans/terms.json').read_bytes());term=next(e for e in terms['terms']if e['id']=='mc2-combat-boss-label');self.assertEqual((term['source'],term['target']),('보스','Boss'))
 def test_names_use_current_applied_spellings(self):
  names={l['text'] for g in self.d['entries'] if g['source_group']['package']=='UI_Battle_Master' and g['source_group']['export']==41 for l in g['labels']};self.assertEqual(names,{'朱特','洁菲','克罗塞尔','阿尔戈','塞蕾丝汀','露'})
 def test_small_rows_and_uv_annotations_remain_explicit(self):
  for g in self.d['entries']:
   if g['source_group']['package']=='UI_Battle_Master' and g['source_group']['export'] in [41,42]:self.assertEqual([(l['rect'][1],l['rect'][3]) for l in g['labels']],[(0,20),(20,20),(40,20),(60,24),(84,20),(104,24)])
   if g['source_group']['package']=='UI_Battle' and g['source_group']['export']==13:self.assertTrue(all(l['rect'][0]+l['rect'][2]<=152 for l in g['labels']))
 def test_hit_is_literal_not_claimed_proven_combo_binding(self):
  g=next(g for g in self.d['entries'] if g['source_group']['package']=='UI_Battle_Master' and g['source_group']['export']==4);self.assertEqual(g['labels'][0]['text'],'命中！');self.assertFalse(self.d['hit_exact_consumer_binding_verified']);self.assertEqual(self.d['hit_adoption_basis'],'High-confidence literal English correspondence;not a combo-mechanic inference')
 def test_finite_render_budget_and_manual_reviews(self):
  self.assertLessEqual(sum(render_area(l) for l in self.p['labels']),16*1024*1024);self.assertTrue(all(g['manual_review'] for g in self.d['entries']));self.assertTrue(self.d['all_4145_headers_rechecked']);self.assertFalse(self.d['game_rendering_verified']);self.assertEqual(self.d['INT_drafts_added'],0)
if __name__=='__main__':unittest.main()
