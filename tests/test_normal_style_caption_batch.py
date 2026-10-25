import json,hashlib,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class NormalStyleCaptionBatchTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/normal-style-tree-captions.json').read_bytes());self.p=json.loads((R/self.d['plan']['path']).read_bytes());self.labels={r['id']:r for r in self.p['labels']}
 def test_whole21_batch_and_prior1323_layers(self):
  from tools.build_font_route_probe import encoded
  self.assertTrue(self.d['applied']);self.assertFalse(self.d['game_rendering_verified']);self.assertEqual((self.d['new_groups'],self.d['new_layers'],self.d['new_aliases']),(21,102,84));self.assertEqual(len(self.d['groups']),21);self.assertEqual(hashlib.sha256(encoded(self.p['labels'][:1323])).hexdigest(),self.d['prior1323_layers_canonical_sha256']);self.assertGreaterEqual(len(self.p['labels']),1425)
 def test_actual_consumer_uvs_and_current_skill_fields(self):
  count=0
  for g in self.d['groups']:
   self.assertTrue(g['assistant_visual_native_review'])
   for c in g['cells']:
    count+=1;l=self.labels[c['label_id']];self.assertEqual(l['text'],c['translation']);self.assertTrue(c['actual_consumers']);self.assertEqual(set(l['source_ids']),{b['source']['id']for b in c['current_field_bindings']})
    for b in c['current_field_bindings']:self.assertEqual(b['source']['source_sha256'],b['adopted']['source_sha256']);self.assertEqual(b['adopted']['translation'],l['text'])
  self.assertEqual(count,102)
 def test_original_coordinate_override_default_not_guessed(self):
  f=self.d['coordinate_defaults'];self.assertEqual(f['flag_name'],'bOverrideCoordinates');self.assertEqual(f['serialized_default'],0);self.assertTrue(f['complete_property_chain']);self.assertEqual(f['missing_default_slots'],[]);self.assertTrue(f['actual_archetype_and_flag_selected_CDO_chains_checked']);self.assertFalse(f['missing_values_assumed_zero']);self.assertEqual(len(f['engine_source_sha256']),64)
 def test_new_ink_fits_each_actual_native_sample(self):
  for g in self.d['groups']:
   for c in g['cells']:
    x,y,w,h=c['actual_sample_rect'];a,b,d,e=c['new_ink_bbox'];self.assertTrue(x<=a<d<=x+w and y<=b<e<=y+h)
 def test_all84_aliases_preserve_namespace_and_byte_locks(self):
  self.assertEqual(len(self.d['aliases']),84);self.assertEqual(len({(a['disc'],a['path'],a['object'])for a in self.d['aliases']}),84);groups={g['canonical_object']:g for g in self.d['groups']}
  for a in self.d['aliases']:self.assertEqual(a['canonical_namespace_guid'],self.d['canonical_namespace_guid']);self.assertEqual(a['rgba_sha256'],groups[a['canonical_object']]['original_native']);self.assertEqual(len(a['payload_sha256']),64);self.assertEqual(len(a['tiled_sha256']),64)
 def test_sparse_glyph_masks_and_unconsumed_originals_retained(self):
  from PIL import Image
  for lid,rect,old_height in [('normal_style_011_cell_067',[20,32,140,28],24),('normal_style_013_cell_078',[0,124,128,32],28)]:
   label=self.labels[lid];self.assertEqual(label['rect'],rect);mask=Image.open(R/label['restoration']['mask']['path']);self.assertGreater(sum(mask.crop((0,old_height,rect[2],rect[3])).tobytes()),0)
  audit=self.d['independent_full_sample_alpha_audit'];self.assertTrue(audit['all_102_full_original_alpha_masks_checked']);self.assertEqual(audit['uncovered_original_alpha_pixels'],0)
  for g in self.d['groups']:
   for c in g['cells']:
    l=self.labels[c['label_id']];r=l['restoration'];m=Image.open(R/r['mask']['path']);p=Image.open(R/r['patch']['path']);self.assertEqual(m.size,tuple(l['rect'][2:]));self.assertEqual(set(m.tobytes()),{0,255});self.assertEqual(set(p.tobytes()),{0})
  for s in self.p['sources']:
   for e in s['textures']:
    self.assertFalse((s['path'].endswith('/Style_Tree_Skill_Name_Jpn.xxx')and e['object']=='Ru_Skill_Sub1')or e['object']=='Style_Tree_Skill_Name_Jpn.Ru_Skill_Sub1')
  descriptor=json.loads((R/self.d['source_materialization']).read_bytes());self.assertEqual(len(descriptor['resources']),1);self.assertEqual(descriptor['resources'][0]['resource'],'MC2Game/CookedXenon/Style_Tree_Skill_Name_Jpn.xxx')
if __name__=='__main__':unittest.main()
