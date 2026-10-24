import unittest,tempfile,io
from pathlib import Path
from unittest.mock import patch
from tools import texture_overlay as overlay,build_texture_overlay as builder
from test_texture_render_windows import owned_font
import test_texture_overlay as fixtures
from test_supplement_font import stored_decoder

class HudRenderBoundsTests(unittest.TestCase):
 def test_1044_and_2048_layers_build_owned_fixture(self):
  raw,_,_,edit,layers=fixtures.TextureOverlayTests().fixture();rgba=layers['x'][1]
  for count in [1044,2048]:
   with self.subTest(count=count),tempfile.TemporaryDirectory() as td:
    r=Path(td);(r/'font').write_bytes(b'owned-font-fixture');(r/'source').write_bytes(raw);ref=lambda n:dict(path=n,sha256=overlay.digest((r/n).read_bytes()))
    plan=dict(schema_version=1,kind='texture-text-overlay-plan',game_rendering_verified=False,rasterizer_versions=dict(Pillow='locked',fonttools='locked'),font=ref('font'),labels=[dict(id='x' if i==0 else f'x{i}',text='x',rect=[8,8,8,8],font_size=1) for i in range(count)],sources=[dict(path='Game/Atlas.xxx',original=ref('source'),base=ref('source'),textures=[edit])])
    with patch.object(builder.importlib.metadata,'version',return_value='locked'),patch.object(builder,'render_label',return_value=rgba):files,m,_=builder.prepare(plan,r,stored_decoder)
    self.assertEqual(m['labels'],count);self.assertIn('candidate/Game/Atlas.xxx',files)
 def test_2049_rejected_before_inputs(self):
  p=dict(schema_version=1,kind='texture-text-overlay-plan',game_rendering_verified=False,rasterizer_versions=dict(Pillow='locked',fonttools='locked'),labels=[{}]*2049,sources=[{}])
  with patch.object(builder.importlib.metadata,'version',return_value='locked'),self.assertRaisesRegex(ValueError,'label/source bound'):builder.prepare(p,Path('.'),None)
 def test_16Mi_canvas_budget_retained_after_expansion(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'font').write_bytes(b'owned-font-fixture');p=dict(schema_version=1,kind='texture-text-overlay-plan',game_rendering_verified=False,rasterizer_versions=dict(Pillow='locked',fonttools='locked'),font=dict(path='font',sha256=overlay.digest((r/'font').read_bytes())),labels=[dict(id=f'x{i}',rect=[0,0,4,4],render_window=dict(canvas=[2048,2048],crop=[0,0,4,4])) for i in range(5)],sources=[{}])
   with patch.object(builder.importlib.metadata,'version',return_value='locked'),self.assertRaisesRegex(ValueError,'text layer total bound'):builder.prepare(p,r,None)

if __name__=='__main__':unittest.main()
