import unittest,struct
from tools.texture_overlay import digest,encode_rgba_block,overlay_tiles,patch_package
from tools.ue3_package import FormatError,parse_summary,parse_tables
from tools.supplement_font import decode_logical,parse_atlas_payload,atlas_tiles
from tools.ue3_textures import decode_dxt5
from test_supplement_font import package_fixture,stored_decoder

class TextureOverlayTests(unittest.TestCase):
 def fixture(self,c=False,t=False):
  raw=package_fixture(c,t);s=parse_summary(raw,len(raw));logical=decode_logical(raw,s,stored_decoder);table=parse_tables(logical,s,len(logical));e=table['exports'][1];payload=logical[e['serial_offset']:e['serial_offset']+e['serial_size']];tex=parse_atlas_payload(payload,table['names'],e['serial_offset']);tiles=atlas_tiles(payload,tex,stored_decoder)
  edit=dict(object='General.Atlas',payload_sha256=digest(payload),tiled_sha256=digest(tiles),dimensions=[128,128],label='x')
  return raw,logical,table,edit,{'x':(dict(rect=[8,8,8,8]),bytes([230,230,230,255])*64)}
 def test_rgba_codec_deterministic_and_alpha_error_bounded(self):
  samples=b''.join(bytes([200,180,160,a]) for a in range(0,256,17));block=encode_rgba_block(samples);self.assertEqual(block,encode_rgba_block(samples));pixels=decode_dxt5(block,4,4)
  self.assertLessEqual(max(abs(a-b) for a,b in zip(samples[3::4],pixels[3::4])),18)
 def test_block_input_rejected(self):
  for data in [b'',bytes(63),bytearray(64),None]:
   with self.subTest(data=type(data)),self.assertRaises(FormatError):encode_rgba_block(data)
 def test_all_package_and_bulk_compression_profiles(self):
  for c in [False,True]:
   for t in [False,True]:
    with self.subTest(c=c,t=t):
     raw,logical,table,edit,layers=self.fixture(c,t);out,proof=patch_package(raw,digest(raw),[edit],layers,stored_decoder);self.assertNotEqual(out,raw);self.assertEqual(proof['nonselected_exports_preserved'],2);self.assertTrue(proof['textures'][0]['untouched_blocks_preserved']);self.assertEqual(proof['textures'][0]['authorized_blocks'],4)
     new=decode_logical(out,parse_summary(out,len(out)),stored_decoder);nt=parse_tables(new,parse_summary(out,len(out)),len(new))
     for i in [0,2]:
      a=table['exports'][i];b=nt['exports'][i];self.assertEqual(a,b);self.assertEqual(logical[a['serial_offset']:a['serial_offset']+a['serial_size']],new[b['serial_offset']:b['serial_offset']+b['serial_size']])
     e=nt['exports'][1];p=new[e['serial_offset']:e['serial_offset']+e['serial_size']];tex=parse_atlas_payload(p,nt['names'],e['serial_offset'])
     for header in [tex['source_art'],tex['mips'][0]['bulk']]:self.assertEqual(struct.unpack_from('>I',p,header['data_offset_field_offset'])[0],e['serial_offset']+header['payload_offset'])
     self.assertEqual(raw,package_fixture(c,t))
 def test_identity_and_selection_guards(self):
  raw,_,_,edit,layers=self.fixture()
  with self.assertRaisesRegex(FormatError,'base SHA'):patch_package(raw,'0'*64,[edit],layers,stored_decoder)
  for key,value in [('object','Other'),('payload_sha256','0'*64),('tiled_sha256','0'*64),('dimensions',[64,128])]:
   with self.subTest(key=key),self.assertRaises(FormatError):patch_package(raw,digest(raw),[{**edit,key:value}],layers,stored_decoder)
  with self.assertRaisesRegex(FormatError,'duplicate'):patch_package(raw,digest(raw),[edit,edit],layers,stored_decoder)
  with self.assertRaises(FormatError):patch_package(raw,digest(raw),[],layers,stored_decoder)
 def test_rectangles_fail_closed(self):
  for rect in [[1,0,4,4],[0,0,0,4],[-4,0,4,4],[124,0,8,4],[0,0,True,4]]:
   with self.subTest(rect=rect),self.assertRaises(FormatError):overlay_tiles(bytes(16384),128,128,rect,bytes(64))
 def test_untouched_blocks_and_padding_exact(self):
  raw=bytes(range(256))*64;out,p=overlay_tiles(raw,128,128,[8,8,8,8],bytes([250,250,250,255])*64)
  self.assertEqual(len(out),len(raw));self.assertEqual(sum(raw[i:i+16]!=out[i:i+16] for i in range(0,len(raw),16)),4);self.assertTrue(p['alignment_padding_preserved'])

if __name__=='__main__':unittest.main()
