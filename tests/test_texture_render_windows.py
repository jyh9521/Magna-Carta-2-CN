import io,struct,unittest
from tools import texture_layout as layout
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from tools import texture_overlay as overlay
from tools.ue3_package import FormatError,parse_summary,parse_tables
from tools.supplement_font import decode_logical
from test_texture_layout import profile_fixture
from test_supplement_font import stored_decoder

def owned_font():
 f=FontBuilder(1000,isTTF=True);f.setupGlyphOrder(['.notdef','A','B']);f.setupCharacterMap({65:'A',66:'B'});glyphs={}
 for name in ['.notdef','A','B']:
  p=TTGlyphPen(None)
  if name!='.notdef':p.moveTo((50,0));p.lineTo((650,0));p.lineTo((650,700));p.lineTo((50,700));p.closePath()
  glyphs[name]=p.glyph()
 f.setupGlyf(glyphs);f.setupHorizontalMetrics({n:(750,0) for n in glyphs});f.setupHorizontalHeader(ascent=800,descent=-200);f.setupOS2(sTypoAscender=800,sTypoDescender=-200,usWinAscent=800,usWinDescent=200);f.setupNameTable({'familyName':'Owned window fixture','styleName':'Regular'});f.setupPost();f.setupMaxp();f.font['head'].created=f.font['head'].modified=2082844800;b=io.BytesIO();f.save(b);return b.getvalue()

class RenderWindowTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.font=owned_font();c.label=dict(text='AB',rect=[0,0,64,32],font_size=18,style=dict(fill=[255,150,70,255],stroke_fill=[60,20,5,255],shadow_fill=[0,0,0,0]))
 def test_two_linked_windows_stitch_exactly_to_whole_render(self):
  whole=overlay.render_label(self.font,self.label);parts=[]
  for y in [0,16]:parts.append(overlay.render_label(self.font,{**self.label,'rect':[0,0,64,16],'render_window':dict(canvas=[64,32],crop=[0,y,64,16])}))
  self.assertEqual(b''.join(parts),whole);self.assertNotEqual(parts[0],parts[1])
 def test_explicit_window_can_clear_a_tail_but_full_canvas_must_have_ink(self):
  label={**self.label,'rect':[0,0,64,4],'render_window':dict(canvas=[64,32],crop=[0,0,64,4])};self.assertFalse(any(overlay.render_label(self.font,label)[3::4]))
  with self.assertRaisesRegex(FormatError,'does not fit'):overlay.render_label(self.font,{**label,'render_window':dict(canvas=[64,4],crop=[0,0,64,4])})
 def test_actual_canvas_area_is_charged_not_tiny_output_crop(self):
  l={**self.label,'rect':[0,0,4,4],'render_window':dict(canvas=[2048,2048],crop=[0,0,4,4])};self.assertEqual(overlay.render_area(l),2048*2048);self.assertGreater(sum(overlay.render_area(l) for _ in range(5)),16*1024*1024)
 def test_invalid_views_rejected_without_silent_default(self):
  for view in [None,{},dict(canvas=[64,32]),dict(canvas=[True,32],crop=[0,0,64,32]),dict(canvas=[64,2049],crop=[0,0,64,32]),dict(canvas=[64,32],crop=[0,-1,64,32]),dict(canvas=[64,32],crop=[0,0,63,32]),dict(canvas=[64,32],crop=[0,1,64,32]),dict(canvas=[64,32],crop=[False,0,64,32]),dict(canvas=[64,32],crop=[0,0,64,32],extra=0)]:
   with self.subTest(view=view),self.assertRaises(FormatError):overlay.render_label(self.font,{**self.label,'render_window':view})
 def test_no_window_keeps_legacy_geometry_and_real_glyph_guard(self):
  self.assertEqual(overlay.render_geometry(self.label),(64,32,None));self.assertEqual(overlay.render_area(self.label),2048)
  with self.assertRaisesRegex(FormatError,'missing glyphs'):overlay.render_label(self.font,{**self.label,'text':'C','render_window':dict(canvas=[64,32],crop=[0,0,64,32])})

class OpaqueRgbTests(unittest.TestCase):
 def pixels(self,out,e):
  s=parse_summary(out);log=decode_logical(out,s,stored_decoder);t=parse_tables(log,s,len(log));x=t['exports'][1];return overlay.edit_pixels(log[x['serial_offset']:x['serial_offset']+x['serial_size']],t['names'],x['serial_offset'],e,stored_decoder)[2]
 def test_rgb_over_black_not_alpha_luma_and_alpha_stays_opaque(self):
  raw,e,l=profile_fixture(5);e['channel_mode']='opaque-rgb';l['x']=(l['x'][0],bytes([255,0,0,128])*64);out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder);rgba=self.pixels(out,e);i=(4*64+8)*4;r,g,b,a=rgba[i:i+4];self.assertLess(abs(r-128),9);self.assertLess(g,9);self.assertLess(b,9);self.assertEqual(a,255);self.assertTrue(all(a==255 for a in rgba[3::4]));self.assertEqual(p['nonselected_exports_preserved'],2)
 def test_transparent_colored_pixels_become_black_not_hidden_rgb(self):
  raw,e,l=profile_fixture(5);e['channel_mode']='opaque-rgb';l['x']=(l['x'][0],bytes([255,100,60,0])*64)
  # Source is already black: resulting no-op is correctly rejected.
  with self.assertRaisesRegex(FormatError,'no-op'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
 def test_explicit_rgb_matte_accepts_mixed_source_alpha_only_in_owned_edit(self):
  raw,e,l=profile_fixture(5);summary=parse_summary(raw);logical=decode_logical(raw,summary,stored_decoder);tables=parse_tables(logical,summary,len(logical));ex=tables['exports'][1];off=ex['serial_offset'];payload=bytearray(logical[off:off+ex['serial_size']]);tx=layout.read_texture(bytes(payload),tables['names'],off,e['profile'],stored_decoder);tiles=bytearray(tx['tiles']);block=struct.pack('<HHI',0,0,0xffffffff);word=b''.join(block[i:i+2][::-1] for i in range(0,8,2))
  for o in [tx['layout']['offsets'][0],layout.rect_units(tx['layout'],[8,4,4,4])[0]]:tiles[o:o+8]=word
  payload[tx['payload_offset']:tx['payload_offset']+len(tiles)]=tiles;modified=bytearray(raw);modified[off:off+len(payload)]=payload;raw=bytes(modified);e['payload_sha256']=overlay.digest(bytes(payload));e['tiled_sha256']=overlay.digest(bytes(tiles));e['channel_mode']='opaque-rgb';l['x']=(l['x'][0],bytes([240,100,60,255])*64);out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder);rgba=self.pixels(out,e);self.assertEqual(rgba[3],0);self.assertEqual(rgba[(4*64+8)*4+3],255);self.assertEqual(p['textures'][0]['source_transparent_pixels'],32)
  with self.assertRaisesRegex(FormatError,'source has transparent'):overlay.patch_package(raw,overlay.digest(raw),[{**e,'channel_mode':'opaque-luma'}],l,stored_decoder)
 def test_nonmatching_profile_or_channel_still_rejected(self):
  raw,e,l=profile_fixture(7);e['channel_mode']='opaque-rgb'
  with self.assertRaisesRegex(FormatError,'channel mode'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
 def test_input_rgba_length_checked_before_any_channel_transform(self):
  for mode in ['opaque-luma','opaque-rgb']:
   raw,e,l=profile_fixture(5);e['channel_mode']=mode
   for value in [bytes([255]*259),bytearray([255]*256),bytes(255)]:
    with self.subTest(mode=mode),self.assertRaisesRegex(FormatError,'RGBA region length'):overlay.patch_package(raw,overlay.digest(raw),[e],{'x':(l['x'][0],value)},stored_decoder)
 def test_protected_rgb_blocks_and_crops_remain_exact(self):
  raw,e,l=profile_fixture(5);e['channel_mode']='opaque-rgb';e['protected_regions']=[dict(id='name',rect=[0,0,4,16],rgba_sha256=overlay.digest(bytes([0,0,0,255])*64))];l['x']=(l['x'][0],bytes([230,100,60,255])*64);out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder);q=p['textures'][0]['protected_regions'][0];self.assertTrue(q['blocks_preserved']);self.assertEqual(q['before_rgba_sha256'],q['after_rgba_sha256'])
if __name__=='__main__':unittest.main()
