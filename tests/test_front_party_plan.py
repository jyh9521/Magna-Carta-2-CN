import json
from pathlib import Path
import unittest
from tools.texture_overlay import image_id,layer_ids,region_offsets
R=Path(__file__).resolve().parents[1]
class FrontPartyPlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());cls.d=json.loads((R/'locales/zh-Hans/candidate-decisions/front-party-image-labels.json').read_bytes());cls.labels={x['id']:x for x in cls.p['labels']}
 def test_cumulative_image_layer_and_alias_counts(self):
  self.assertGreaterEqual(len(self.p['labels']),92);self.assertGreaterEqual(len({image_id(e) for s in self.p['sources'] for e in s['textures']}),78);self.assertEqual(len(self.d['source_aliases']),52)
 def test_complete_dual_disc_five_resource_enrollment(self):
  for d in [1,2]:
   rows=[a for a in self.d['source_aliases'] if a['disc']==d];self.assertEqual(len(rows),26);self.assertEqual(len({a['resource_path'] for a in rows}),5)
   for a in rows:
    s=next(s for s in self.p['sources'] if s['path']==a['resource_path']);self.assertIn(d,s['discs']);e=next(e for e in s['textures'] if e['object']==a['path']);self.assertEqual(e['payload_sha256'],a['payload_sha256']);self.assertEqual(e['tiled_sha256'],a['tiled_sha256'])
 def test_two_states_complete_four_adopted_character_names(self):
  for name,text in [('argo','阿尔戈'),('celestin','塞蕾丝汀'),('juto','朱特'),('zephi','洁菲')]:
   for suffix in ['', '_red']:self.assertEqual(self.labels['ui_character_name_'+name+suffix]['text'],text)
 def test_controller_identifier_retained(self):
  self.assertEqual(self.labels['ui_press_start_1_0']['text'],'按START键')
 def test_menu_copyright_and_disc_upper_masks_are_disjoint(self):
  seen=set()
  for s in self.p['sources']:
   for e in s['textures']:
    if image_id(e) not in ['ui_menu_tex','ui_disc_01','ui_disc_02']:continue
    seen.add(image_id(e));w,h=e['dimensions'];ed=set()
    for n in layer_ids(e):ed|=region_offsets(w,h,self.labels[n]['rect'])
    protected=e['protected_regions'];self.assertEqual(len(protected),1);r=protected[0];self.assertFalse(ed & region_offsets(w,h,r['rect']));self.assertEqual(len(r['rgba_sha256']),64)
  self.assertEqual(len(seen),3)
 def test_guest_and_final_brand_do_not_regress(self):
  self.assertEqual(self.labels['ui_guest_icon']['text'],'临时');self.assertEqual(self.labels['ui_menu_tex_title']['text'],'真名法典2');self.assertEqual(self.labels['ui_menu_tex_5_normal']['text'],'语音剧')
if __name__=='__main__':unittest.main()
