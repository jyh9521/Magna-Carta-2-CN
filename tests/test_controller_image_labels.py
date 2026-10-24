import hashlib
import json
import struct
import unittest
from pathlib import Path
from tools import texture_layout as layout, texture_overlay as overlay
ROOT=Path(__file__).resolve().parents[1]

class RestoredBc3Tests(unittest.TestCase):
 def fixture(self):
  lo=layout.unit_layout(64,16,7);raw=bytearray(lo['storage_bytes']);block=bytes([128,128,0,0,0,0,0,0])+struct.pack('<HHI',0,0,0x55555555);native=b''.join(block[i:i+2][::-1]for i in range(0,16,2))
  for offset in lo['offsets']:raw[offset:offset+16]=native
  tx=dict(layout=lo,width=64,height=16,format=7,tiles=bytes(raw));crop=overlay.rgba_crop(layout.decode_texture(tx),64,[8,4,8,8]);label=dict(rect=[8,4,8,8],restoration=dict(source_rgba_sha256=overlay.digest(crop)),_repair_mask=bytes([255]+[0]*63),_repair_pixels=bytes([180,70,30,50])+bytes(252));edit=dict(regions=['x'],image_id='owned-restored-bc3',channel_mode='rgba',profile=dict(kind=layout.PROFILE,format=7),preserve_unchanged_blocks=True);return tx,edit,label
 def test_unchanged_bc3_units_and_translucent_alpha_are_preserved(self):
  tx,e,l=self.fixture();out,p=overlay.overlay_profile_regions(tx,e,{'x':(l,bytes(256))});units=layout.rect_units(tx['layout'],l['rect']);self.assertEqual(p['unchanged_region_blocks_preserved'],3);self.assertEqual(p['changed_blocks'],1)
  for o in units[1:]:self.assertEqual(out[o:o+16],tx['tiles'][o:o+16])
  source=overlay.rgba_crop(layout.decode_texture(tx),64,l['rect']);self.assertEqual(overlay.compose_restored_region(l,bytes(256),layout.decode_texture(tx),64)[3],50);rgba=layout.decode_texture(tx,out);self.assertLessEqual(abs(rgba[(4*64+8)*4+3]-50),18);self.assertEqual(rgba[3],128);self.assertNotIn('rgb_matte',p)
 def test_default_bc3_behavior_stays_legacy(self):
  tx,e,l=self.fixture();e.pop('preserve_unchanged_blocks');out,p=overlay.overlay_profile_regions(tx,e,{'x':(l,bytes(256))});self.assertNotIn('unchanged_region_blocks_preserved',p);self.assertEqual(p['changed_blocks'],4)
 def test_restoration_and_rgba_mode_are_mandatory(self):
  tx,e,l=self.fixture();bad=dict(l);bad.pop('restoration')
  with self.assertRaisesRegex(ValueError,'restoration'):overlay.overlay_profile_regions(tx,e,{'x':(bad,bytes(256))})
  with self.assertRaises(ValueError):overlay.overlay_profile_regions(tx,dict(e,channel_mode='opaque-rgb'),{'x':(l,bytes(256))})
 def test_source_hash_and_boolean_guard_remain_enforced(self):
  tx,e,l=self.fixture();bad=dict(l,restoration=dict(source_rgba_sha256='0'*64))
  with self.assertRaisesRegex(ValueError,'source crop hash'):overlay.overlay_profile_regions(tx,e,{'x':(bad,bytes(256))})
  for flag in[1,'yes',None]:
   with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,'boolean'):overlay.overlay_profile_regions(tx,dict(e,preserve_unchanged_blocks=flag),{'x':(l,bytes(256))})

class ControllerPlanTests(unittest.TestCase):
 def setUp(self):
  self.plan=json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());self.d=json.loads((ROOT/'locales/zh-Hans/candidate-decisions/controller-image-labels.json').read_bytes())
 def test_coherent14labels_and8_canonical_aliases(self):
  d=self.d;self.assertEqual((d['new_image_groups'],d['new_text_layers'],d['new_aliases']),(2,14,8));self.assertEqual(len(d['entries']),14);self.assertFalse(d['game_rendering_verified']);self.assertFalse(d['all_game_image_text_translated']);self.assertFalse(d['imagegen_donor_pixels_used']);self.assertTrue(d['controller_body_and_buttons_preserved']);self.assertEqual(sorted(a['disc']for a in d['all_source_aliases']),[1]*4+[2]*4);labels={l['id']:l for l in self.plan['labels']}
  for row in d['entries']:self.assertTrue(row['manual_review']);self.assertEqual(row['label'],labels[row['label']['id']])
 def test_prior1114_layers_are_byte_semantically_unchanged(self):
  raw=json.dumps(self.plan['labels'][:1114],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),'dd71ee30cd43647fe11bf7315a09dc12e80157735d0edceecb1be9933f1ad75f')
 def test_native_alpha_and_sparse_restoration_contract(self):
  from PIL import Image
  edits=[e for s in self.plan['sources']for e in s['textures']if e.get('image_id')in['controller_guide','controller_guide_title']];self.assertEqual(len(edits),4)
  for e in edits:
   self.assertEqual((e['profile']['format'],e['channel_mode']),(7,'rgba'));self.assertIs(e['preserve_unchanged_blocks'],True)
   if e['image_id']=='controller_guide':self.assertEqual(len(e['regions']),13);self.assertEqual(e['protected_regions'][0]['rect'],[280,120,476,296])
  for row in self.d['entries']:
   l=row['label'];repair=l['restoration'];self.assertNotIn('background_fill',l['style'])
   for k in['mask','patch']:self.assertEqual(hashlib.sha256((ROOT/repair[k]['path']).read_bytes()).hexdigest(),repair[k]['sha256'])
   with Image.open(ROOT/repair['mask']['path'])as m:mask=m.tobytes()
   with Image.open(ROOT/repair['patch']['path'])as p:pixels=p.tobytes()
   self.assertFalse(set(mask)-{0,255});self.assertGreater(sum(bool(v)for v in mask),0);self.assertLess(sum(bool(v)for v in mask),len(mask));self.assertTrue(all(v or pixels[i*4:i*4+4]==bytes(4)for i,v in enumerate(mask)))

if __name__=='__main__':unittest.main()
