import copy,struct,unittest
from tools import texture_overlay as o,texture_layout as t

class PixelGuardTests(unittest.TestCase):
 def fixture(self,alpha=255):
  layout=t.unit_layout(64,16,7);rgb=o.encode_rgba_block(bytes([198,199,198,255,24,24,24,255])*8)[8:12];indices=sum((2 if i>=12 else i%2)<<(2*i)for i in range(16));linear=o.encode_alpha_range([alpha]*16)+rgb+struct.pack('<I',indices);native=b''.join(linear[i:i+2][::-1]for i in range(0,16,2));raw=bytearray(layout['storage_bytes'])
  for offset in layout['offsets']:raw[offset:offset+16]=native
  tx=dict(layout=layout,width=64,height=16,format=7,tiles=bytes(raw));before=t.decode_texture(tx);rect=[8,4,4,4];mask=bytes([255]*12+[0]*4);patch=bytes([120,120,120,alpha])*12+bytes(16);label=dict(rect=rect,restoration=dict(source_rgba_sha256=o.digest(o.rgba_crop(before,64,rect))),_repair_mask=mask,_repair_pixels=patch);guard=dict(id='numeric-row',rect=[8,7,4,1],rgba_sha256=o.digest(o.rgba_crop(before,64,[8,7,4,1])));edit=dict(regions=['x'],image_id='owned_pixel_guard',profile=dict(kind=t.PROFILE,format=7),channel_mode='rgba',preserve_unchanged_blocks=True,alpha_encoding='adaptive-range',protected_pixel_regions=[guard]);return tx,label,edit,before
 def draw(self,tx,l,e,rgba=None,cache=None):return o.overlay_profile_regions(tx,e,{'x':(l,rgba or bytes(64))},cache)
 def test_shared_numeric_row_does_not_requantize(self):
  tx,l,e,b=self.fixture();legacy=dict(e);legacy.pop('protected_pixel_regions');bad,_=self.draw(tx,l,legacy);good,p=self.draw(tx,l,e);rect=e['protected_pixel_regions'][0]['rect'];self.assertNotEqual(o.rgba_crop(t.decode_texture(tx,bad),64,rect),o.rgba_crop(b,64,rect));self.assertEqual(o.rgba_crop(t.decode_texture(tx,good),64,rect),o.rgba_crop(b,64,rect));self.assertTrue(p['protected_pixel_regions'][0]['pixels_preserved'])
 def test_source_palette_alpha_and_unrelated_units_stay_exact(self):
  tx,l,e,_=self.fixture();out,p=self.draw(tx,l,e);offset=t.rect_units(tx['layout'],l['rect'])[0];self.assertEqual(tx['tiles'][offset:offset+12],out[offset:offset+12]);self.assertEqual(tx['tiles'][:offset],out[:offset]);self.assertEqual(tx['tiles'][offset+16:],out[offset+16:]);self.assertEqual(p['protected_pixel_regions'][0]['source_palette_blocks'],1)
 def test_default_remains_independent_of_guarded_encoding_cache(self):
  tx,l,e,_=self.fixture();plain=dict(e);plain.pop('protected_pixel_regions');cache={};self.draw(tx,l,e,cache=cache);out,p=self.draw(tx,l,plain,cache=cache);fresh,fp=self.draw(tx,l,plain);self.assertEqual(out,fresh);self.assertEqual(p,fp);self.assertNotIn('protected_pixel_regions',p)
 def test_intended_glyph_cannot_overlap_guarded_pixels(self):
  tx,l,e,_=self.fixture()
  with self.assertRaises(ValueError):self.draw(tx,l,e,bytes([255,255,255,255])*16)
 def test_shared_translucent_blocks_are_rejected(self):
  tx,l,e,_=self.fixture(204)
  with self.assertRaises(ValueError):self.draw(tx,l,e)
 def test_wrong_modes_and_unrestored_inputs_are_rejected(self):
  tx,l,e,_=self.fixture()
  for changes in [dict(channel_mode='opaque-rgb'),dict(preserve_unchanged_blocks=False)]:
   with self.assertRaises(ValueError):self.draw(tx,l,dict(e,**changes))
  bare=dict(l);bare.pop('restoration')
  with self.assertRaises(ValueError):self.draw(tx,bare,e)
 def test_guard_schema_bounds_and_hashes_are_strict(self):
  tx,l,e,_=self.fixture();g=e['protected_pixel_regions'][0]
  for rows in [None,[],[g]*17,[g,g],[dict(g,rect=[True,7,4,1])],[dict(g,rect=[63,7,4,1])],[dict(g,rgba_sha256='0'*64)],[dict(g,extra=True)]]:
   with self.subTest(rows=rows):
    with self.assertRaises(ValueError):self.draw(tx,l,dict(e,protected_pixel_regions=rows))
 def test_palette_cannot_silently_drop_unrepresentable_colors(self):
  tx,l,e,_=self.fixture();l=dict(l,_repair_pixels=bytes([255,0,0,255])*12+bytes(16))
  with self.assertRaises(ValueError):self.draw(tx,l,e)
 def test_legacy_and_other_formats_do_not_ignore_pixel_guards(self):
  tx,l,e,_=self.fixture()
  with self.assertRaises(ValueError):o.overlay_regions(tx['tiles'],64,16,e,{'x':(l,bytes(64))})
  with self.assertRaises(ValueError):self.draw(dict(tx,format=5),l,dict(e,channel_mode='opaque-rgb'))
 def test_guard_outside_edit_is_checked_without_palette_rewrite(self):
  tx,l,e,b=self.fixture();rect=[32,8,4,1];e=copy.deepcopy(e);e['protected_pixel_regions'][0].update(rect=rect,rgba_sha256=o.digest(o.rgba_crop(b,64,rect)));out,p=self.draw(tx,l,e);self.assertEqual(o.rgba_crop(t.decode_texture(tx,out),64,rect),o.rgba_crop(b,64,rect));self.assertEqual(p['protected_pixel_regions'][0]['source_palette_blocks'],0)

if __name__=='__main__':unittest.main()
