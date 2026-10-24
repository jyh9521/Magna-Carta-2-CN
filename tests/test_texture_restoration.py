import unittest,hashlib
from tools import texture_overlay as t
class RestorationTests(unittest.TestCase):
 def fixture(self):
  source=bytes([20,40,60,200])*16;mask=bytes([255]+[0]*15);patch=bytes([80,90,100,170])+bytes(60)
  l=dict(rect=[0,0,4,4],restoration=dict(source_rgba_sha256=hashlib.sha256(source).hexdigest()),_repair_pixels=patch,_repair_mask=mask)
  return source,l
 def test_only_mask_is_reconstructed_and_transparent_glyph_preserves_background(self):
  source,l=self.fixture();out=t.compose_restored_region(l,bytes(64),source,4);self.assertEqual(out[:4],bytes([80,90,100,170]));self.assertEqual(out[4:],source[4:])
 def test_actual_source_hash_is_checked(self):
  source,l=self.fixture()
  with self.assertRaisesRegex(ValueError,'restoration source'):t.compose_restored_region(l,bytes(64),bytes(64),4)
 def test_alpha_composites_text_instead_of_replacing_gradient(self):
  source,l=self.fixture();glyph=bytes([255,255,255,255])+bytes(60);out=t.compose_restored_region(l,glyph,source,4);self.assertEqual(out[:4],glyph[:4]);self.assertEqual(out[4:],source[4:])
 def test_unresolved_or_nonbinary_mask_is_rejected(self):
  source,l=self.fixture()
  for bad in [dict(l,_repair_mask=bytes([1]*16)),{k:v for k,v in l.items() if k!='_repair_pixels'}]:
   with self.assertRaises(ValueError):t.compose_restored_region(bad,bytes(64),source,4)
 def test_legacy_layer_is_identical(self):
  source,l=self.fixture();self.assertEqual(t.compose_restored_region(dict(rect=[0,0,4,4]),source,bytes(64),4),source)

class RestorationBuilderTests(unittest.TestCase):
 def fixture(self,root):
  from PIL import Image
  from tools import build_texture_overlay as b
  import test_texture_overlay as f
  from unittest.mock import patch
  raw,logical,table,edit,layers=f.TextureOverlayTests().fixture();(root/'font').write_bytes(b'owned-font');(root/'source').write_bytes(raw)
  ex=table['exports'][1];payload=logical[ex['serial_offset']:ex['serial_offset']+ex['serial_size']];w,h,rgba=t.edit_pixels(payload,table['names'],ex['serial_offset'],edit,__import__('test_supplement_font').stored_decoder)
  crop=t.rgba_crop(rgba,w,[8,8,8,8]);Image.new('RGBA',(8,8),(0,0,0,0)).save(root/'patch.png');mask=Image.new('L',(8,8));mask.putpixel((0,0),255);mask.save(root/'mask.png')
  ref=lambda n:dict(path=n,sha256=t.digest((root/n).read_bytes()))
  label=dict(id='x',rect=[8,8,8,8],text='X',font_size=1,restoration=dict(patch=ref('patch.png'),mask=ref('mask.png'),source_rgba_sha256=t.digest(crop)))
  plan=dict(schema_version=1,kind='texture-text-overlay-plan',game_rendering_verified=False,rasterizer_versions=dict(Pillow='locked',fonttools='locked'),font=ref('font'),labels=[label],sources=[dict(path='Game/Atlas.xxx',original=ref('source'),base=ref('source'),textures=[edit])]);return plan
 def run_case(self,modify=None,match=None):
  import tempfile
  from pathlib import Path
  from unittest.mock import patch
  from tools import build_texture_overlay as b
  from test_supplement_font import stored_decoder
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);plan=self.fixture(root)
   if modify:modify(plan,root)
   with patch.object(b.importlib.metadata,'version',return_value='locked'),patch.object(b,'render_label',return_value=bytes(256)):
    if match:
     with self.assertRaisesRegex(ValueError,match):b.prepare(plan,root,stored_decoder)
    else:
     files,m,snap=b.prepare(plan,root,stored_decoder);self.assertEqual(m['labels'],1);self.assertGreaterEqual(len(snap),5)
 def test_hashed_pngs_reach_real_owned_package_writer(self):self.run_case()
 def test_wrong_patch_hash_rejected(self):self.run_case(lambda p,r:p['labels'][0]['restoration']['patch'].update(sha256='0'*64),'input hash mismatch')
 def test_patch_path_escape_rejected(self):self.run_case(lambda p,r:p['labels'][0]['restoration']['patch'].update(path='../outside.png'),'relative|path')
 def test_original_crop_identity_rejected(self):self.run_case(lambda p,r:p['labels'][0]['restoration'].update(source_rgba_sha256='0'*64),'restoration source')
 def test_raw_private_patch_in_plan_rejected(self):self.run_case(lambda p,r:p['labels'][0].update(_repair_pixels='injected'),'private restoration')
