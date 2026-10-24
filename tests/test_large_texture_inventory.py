import unittest,json,tempfile
from pathlib import Path
from unittest.mock import patch
from tools import texture_overlay as overlay,build_texture_overlay as builder,verify_resource_phase as phase
import test_texture_overlay as fixtures
from test_supplement_font import stored_decoder
class LargeTextureInventoryTests(unittest.TestCase):
 def test_finite_caps_cover_audited_union(self):
  self.assertEqual((overlay.MAX_TEXTURE_SOURCES,overlay.MAX_TEXT_LAYERS,overlay.MAX_TEXTURE_EDITS,phase.MAX_PACKET_RESOURCES),(512,2048,512,512))
 def test_sources_512_accepted_and_513_rejected(self):
  rows=[dict(path=f'{i}.xxx',discs=[1,2]) for i in range(512)];self.assertEqual(builder.select_sources(rows,2),rows)
  with self.assertRaisesRegex(ValueError,'source bound'):builder.select_sources(rows+[rows[0]],2)
 def test_129_edits_reach_duplicate_guard_not_old_bound(self):
  raw,_,_,e,l=fixtures.TextureOverlayTests().fixture()
  for n in [129,512]:
   with self.subTest(count=n),self.assertRaisesRegex(ValueError,'duplicate texture'):overlay.patch_package(raw,overlay.digest(raw),[e]*n,l,stored_decoder)
 def test_513_edits_rejected_before_package_parse(self):
  raw,_,_,e,l=fixtures.TextureOverlayTests().fixture()
  with self.assertRaisesRegex(ValueError,'edit bound'):overlay.patch_package(raw,overlay.digest(raw),[e]*513,l,stored_decoder)
 def test_1024_layers_build_with_owned_fixture_and_mocked_rasterizer(self):
  raw,_,_,e,l=fixtures.TextureOverlayTests().fixture();rgba=l['x'][1]
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'font').write_bytes(b'owned-font-fixture');(r/'source').write_bytes(raw);ref=lambda n:dict(path=n,sha256=overlay.digest((r/n).read_bytes()))
   p=dict(schema_version=1,kind='texture-text-overlay-plan',game_rendering_verified=False,rasterizer_versions=dict(Pillow='locked',fonttools='locked'),font=ref('font'),labels=[dict(id='x' if i==0 else f'x{i}',text='x',rect=[8,8,8,8],font_size=1) for i in range(1024)],sources=[dict(path='Game/Atlas.xxx',original=ref('source'),base=ref('source'),textures=[e])])
   with patch.object(builder.importlib.metadata,'version',return_value='locked'),patch.object(builder,'render_label',return_value=rgba):
    files,m,_=builder.prepare(p,r,stored_decoder)
   self.assertEqual(m['labels'],1024);self.assertIn('candidate/Game/Atlas.xxx',files)
 def test_2049_layers_rejected_before_inputs(self):
  p=dict(schema_version=1,kind='texture-text-overlay-plan',game_rendering_verified=False,rasterizer_versions=dict(Pillow='locked',fonttools='locked'),labels=[{}]*2049,sources=[{}])
  with patch.object(builder.importlib.metadata,'version',return_value='locked'),self.assertRaisesRegex(ValueError,'label/source bound'):builder.prepare(p,Path('.'),None)
 def test_512_raw_members_preserve_unrelated_bytes(self):
  from test_locale_comparison import inputs,raw_phase
  o,f,toc=inputs()
  for i in range(507):o[f'Extra/{i}.bin']=b'owned-unrelated'
  raw,_=raw_phase(o,f,toc,stored_decoder);self.assertEqual(len(raw),512);self.assertTrue(all(raw[f'Extra/{i}.bin']==b'owned-unrelated' for i in range(507)))
class TextAlignmentTests(unittest.TestCase):
 def test_default_position_exactly_retains_legacy_formula(self):
  for b in [(1,3,51,21),(-1,-3,47,15),(0,0,20,16)]:self.assertEqual(overlay.text_position(128,32,b),((128-(b[2]-b[0]))//2-b[0],(32-(b[3]-b[1]))//2-b[1]))
 def test_left_and_right_actual_ink_margin(self):
  b=(-2,3,48,21)
  for alignment,start in [('left',4),('right',74)]:
   x,y=overlay.text_position(128,32,b,alignment);self.assertEqual(x+b[0],start);self.assertEqual(y+b[1],7)
 def test_invalid_alignment_fails_closed(self):
  for v in [None,True,0,'LEFT','justify',[],{}]:
   with self.subTest(value=v),self.assertRaisesRegex(ValueError,'alignment'):overlay.text_position(128,32,(0,0,20,16),v)
 def test_alignment_does_not_relax_ink_fit(self):
  for alignment in ['left','center','right']:
   with self.subTest(align=alignment),self.assertRaisesRegex(ValueError,'does not fit'):overlay.text_position(32,32,(0,0,25,16),alignment)
 def test_invalid_ink_geometry_fails_closed(self):
  for w,h,b in [(True,32,(0,0,20,16)),(0,32,(0,0,20,16)),(128,32,(0,0,20,True)),(128,32,(0,0,0,16))]:
   with self.subTest(b=b),self.assertRaisesRegex(ValueError,'geometry'):overlay.text_position(w,h,b)

if __name__=='__main__':unittest.main()
