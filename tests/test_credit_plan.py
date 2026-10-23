import json,unittest,hashlib
from pathlib import Path
from tools.texture_overlay import image_id,render_area
R=Path(__file__).resolve().parents[1]
class CreditPlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());c.d=json.loads((R/'locales/zh-Hans/candidate-decisions/credit-image-labels.json').read_bytes());c.l={l['id']:l for l in c.p['labels']};c.s=next(s for s in c.p['sources'] if s['path']=='MC2Game/CookedXenon/UI_Credit.xxx')
 def test_inventory(self):
  self.assertGreaterEqual(len(self.p['sources']),277);self.assertGreaterEqual(len(self.l),960);self.assertGreaterEqual(len({image_id(e) for s in self.p['sources'] for e in s['textures']}),520);self.assertEqual((self.d['image_groups'],self.d['logical_captions'],self.d['text_layers']),(13,112,113))
  for d,n in [(1,177),(2,234)]:self.assertGreaterEqual(sum(d in s['discs'] for s in self.p['sources']),n)
 def test_all_twenty_six_actual_aliases_are_enrolled(self):
  self.assertEqual(len(self.d['source_aliases']),26);self.assertEqual(self.s['discs'],[1,2]);self.assertEqual(len(self.s['textures']),13)
  for a in self.d['source_aliases']:
   e=next(e for e in self.s['textures'] if e['object']==a['path']);self.assertEqual(e['payload_sha256'],a['payload_sha256']);self.assertEqual(e['tiled_sha256'],a['tiled_sha256']);self.assertEqual(self.s['original']['sha256'],a['source_sha256'])
 def test_cells_and_real_complete_name_terms(self):
  for r in self.d['entries']:
   for c in r['cells']:
    l=self.l[f'img_ui_credit_{r["export"]}_{c["cell"]}'];self.assertEqual(l['text'],c['translation']);self.assertEqual(l['source_text_sha256'],hashlib.sha256(c['visual_reading'].encode()).hexdigest());self.assertEqual(l['rect'],c['rect'])
  self.assertEqual(self.l['img_ui_credit_67_90']['text'],'修恩扎伊特');self.assertEqual(self.l['img_ui_credit_67_94']['text'],'修亚伦');self.assertEqual(self.l['img_ui_credit_67_93']['text'],'克蕾尔');self.assertEqual(self.l['img_ui_credit_66_82']['text'],'朱特/艾尔加')
 def test_linked_caption_windows_are_complete_and_not_duplicated(self):
  w=self.d['linked_windows'];self.assertEqual(len(w),1);w=w[0];self.assertEqual(w['logical_caption'],21);self.assertEqual([r['export'] for r in w['pieces']],[61,62]);self.assertEqual(w['canvas'],[336,32]);self.assertEqual([p['window']['crop'] for p in w['pieces']],[[0,0,336,20],[0,20,336,12]])
 def test_source_contract_keeps_raw_legal_and_brand_exports(self):
  objects={e['object'] for e in self.s['textures']};self.assertNotIn('Tex.Credit_11',objects);self.assertNotIn('Tex.BlackBg',objects);self.assertEqual([r['index'] for r in self.d['retained_company_rows']],[59,67]);self.assertFalse(any(l['id'].endswith('_59') or l['id'].endswith('_67') for l in self.p['labels'] if l['id'].startswith('img_ui_credit_')))
 def test_rgb_contract_and_default_mask_are_not_confused(self):
  self.assertTrue(all(e['channel_mode']=='opaque-rgb' and e['profile']==dict(kind='xbox-inline-bc-v1',format=5) for e in self.s['textures']));old=next(e for s in self.p['sources'] for e in s['textures'] if e.get('image_id')=='img_ui_battle_08_jp_109');self.assertEqual(old['channel_mode'],'opaque-luma')
 def test_all_staff_protection_is_explicit_bounded_and_disjoint(self):
  from tools.texture_layout import unit_layout,rect_units
  for e in self.s['textures']:
   self.assertTrue(e['protected_regions']);self.assertLessEqual(len(e['protected_regions']),16);layout=unit_layout(*e['dimensions'],5);units=set()
   for k in e['regions']:
    q=set(rect_units(layout,self.l[k]['rect']));self.assertFalse(units&q);units|=q
   for p in e['protected_regions']:self.assertFalse(units&set(rect_units(layout,p['rect'])))
 def test_qa_and_brand_captions_are_real_language_changes(self):
  self.assertEqual(self.l['img_ui_credit_68_qa']['text'],'全体质量保证人员');self.assertEqual(self.l['img_ui_credit_72_0']['text'],'出品');self.assertEqual(self.l['img_ui_credit_73_0']['text'],'开发')
 def test_total_actual_canvas_area_stays_bounded(self):self.assertLessEqual(sum(render_area(l) for l in self.p['labels']),16*1024*1024)
if __name__=='__main__':unittest.main()
