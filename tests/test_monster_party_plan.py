import json,collections,unittest
from pathlib import Path
from tools.texture_overlay import image_id,layer_ids,region_offsets
R=Path(__file__).resolve().parents[1]
class MonsterPartyPlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());cls.d=json.loads((R/'locales/zh-Hans/candidate-decisions/monster-party-image-labels.json').read_bytes());cls.labels={l['id']:l for l in cls.p['labels']}
 def test_complete_cumulative_source_and_layer_counts(self):
  self.assertEqual((len(self.p['sources']),len(self.p['labels'])),(270,434));self.assertEqual(len({image_id(e) for s in self.p['sources'] for e in s['textures']}),405);self.assertEqual(len(self.d['entries']),327);self.assertEqual(len(self.d['source_aliases']),1400)
  for disc,count in [(1,171),(2,228)]:self.assertEqual(sum(disc in s['discs'] for s in self.p['sources']),count)
 def test_every_declared_alias_is_actually_enrolled(self):
  for a in self.d['source_aliases']:
   s=next(s for s in self.p['sources'] if s['path']==a['resource_path']);self.assertIn(a['disc'],s['discs']);self.assertTrue(any(e['object']==a['object'] for e in s['textures']));self.assertNotIn('fx_pattern',a['canonical_path']);self.assertNotIn('north_crowd',a['canonical_path'])
 def test_actual_pixel_identity_implies_same_source_and_translation(self):
  groups=collections.defaultdict(set)
  for r in self.d['entries']:
   if r.get('translation'):groups[(tuple(r['dimensions']),r['rgba_sha256'])].add((''.join(r['visual_reading'].split()),r['translation']))
  self.assertTrue(all(len(v)==1 for v in groups.values()))
 def test_source_glyph_corrections_and_misleading_leaf(self):
  by={(r['package'],r['export']):r for r in self.d['entries']}
  for key,source,text in [(('UI_Name_Jpn',132),'로얄가드','皇家卫兵'),(('UI_Name_Jpn',120),'데스발리스타','死亡弩炮'),(('UI_Name_Jpn',27),'휴아렌의 팔','修亚伦的手臂'),(('UI_Name_Jpn',67),'겔피쉬','格尔鱼'),(('UI_Monster_Name_Jpn',68),'푸 르 손','普尔森')]:
   r=by[key];self.assertEqual(''.join(r['visual_reading'].split()),''.join(source.split()));self.assertEqual(r['translation'],text)
 def test_party_states_and_source_alignment(self):
  self.assertEqual(len([x for x in self.labels if x.startswith('img_ui_name_jpn_174_')]),12);self.assertEqual(len([x for x in self.labels if x.startswith('img_ui_name_jpn_175_')]),5)
  self.assertEqual(self.labels['img_ui_name_jpn_171']['align'],'center')
  for n in ['8','9','10','173_0']:self.assertEqual(self.labels['img_ui_name_jpn_'+n]['align'],'left')
  for n in [8,9,10]:self.assertGreater(self.labels['img_ui_name_jpn_'+str(n)]['style']['fill'][1],self.labels['img_ui_name_jpn_'+str(n)]['style']['fill'][2])
 def test_ornament_protections_are_disjoint_from_text_blocks(self):
  seen=set()
  for s in self.p['sources']:
   for e in s['textures']:
    group=image_id(e)
    if not group.startswith('img_') or not e.get('protected_regions'):continue
    seen.add(group);w,h=e['dimensions'];ed=set()
    for n in layer_ids(e):ed|=region_offsets(w,h,self.labels[n]['rect'])
    for p in e['protected_regions']:self.assertFalse(ed & region_offsets(w,h,p['rect']));self.assertEqual(len(p['rgba_sha256']),64)
  self.assertTrue({'img_ui_name_jpn_'+str(n) for n in [137,155,180,174,175]}<=seen);self.assertEqual(len(seen),17)
if __name__=='__main__':unittest.main()
