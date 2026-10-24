import unittest,struct
from tools.texture_overlay import digest,encode_rgba_block,overlay_tiles,patch_package,label_style
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
  from tools.texture_overlay import select_texture_export
  from tools.build_texture_overlay import select_texture_export as preview_selector
  self.assertIs(preview_selector,select_texture_export)
  tex=dict(path='Fixture',class_path='Engine.Texture2D');pkg=dict(path='Fixture',class_path='Core.Package')
  self.assertIs(select_texture_export(dict(exports=[pkg,tex]),'fixture'),tex)
  for exports in [[pkg],[tex,dict(tex)],[]]:
   with self.subTest(exports=exports),self.assertRaises(FormatError):select_texture_export(dict(exports=exports),'Fixture')
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


class TextureLabelStyleTests(unittest.TestCase):
 def test_default_palette_retains_original_overlay(self):
  self.assertEqual(label_style({}),dict(fill=(236,236,236,255),stroke_fill=(25,25,25,230),shadow_fill=(0,0,0,180)))
 def test_partial_style_is_generic_and_does_not_mutate_input(self):
  p={'style':{'fill':[252,215,160,255]}};self.assertEqual(label_style(p)['fill'],(252,215,160,255));self.assertEqual(p['style'],{'fill':[252,215,160,255]});self.assertEqual(label_style(p)['stroke_fill'],(25,25,25,230))
 def test_unknown_palette_fields_rejected(self):
  for style in [None,[],{'color':[1,2,3,4]}]:
   with self.subTest(style=style),self.assertRaises(FormatError):label_style({'style':style})
 def test_invalid_rgba_bytes_rejected(self):
  for value in [[0,0,0],[-1,0,0,0],[256,0,0,0],[True,0,0,0],['0',0,0,0],None]:
   with self.subTest(value=value),self.assertRaises(FormatError):label_style({'style':{'fill':value}})


class TextureDiscSelectionTests(unittest.TestCase):
 def test_legacy_sources_require_no_disc_and_keep_all(self):
  from tools.build_texture_overlay import select_sources
  sources=[{'path':'a'},{'path':'b'}];self.assertEqual(select_sources(sources),sources);self.assertEqual(select_sources(sources,2),sources)
 def test_explicit_disc_inventory_selects_exact_subset(self):
  from tools.build_texture_overlay import select_sources
  a={'path':'a','discs':[1]};b={'path':'b','discs':[2]};c={'path':'c','discs':[1,2]}
  self.assertEqual(select_sources([a,b,c],1),[a,c]);self.assertEqual(select_sources([a,b,c],2),[b,c]);self.assertEqual(a['discs'],[1])
 def test_scoped_sources_reject_implicit_or_invalid_disc(self):
  from tools.build_texture_overlay import select_sources
  for disc in [None,True,0,3,'1']:
   with self.subTest(disc=disc),self.assertRaises(ValueError):select_sources([{'discs':[1]}],disc)
 def test_disc_declaration_bounds_and_empty_selection(self):
  from tools.build_texture_overlay import select_sources
  for discs in [[],[True],[1,1],[3],'1']:
   with self.subTest(discs=discs),self.assertRaises(ValueError):select_sources([{'discs':discs}],1)
  for sources in [[],[{}]*513,[{'discs':[2]}]]:
   with self.subTest(sources=len(sources)),self.assertRaises(ValueError):select_sources(sources,1)

class TextureEncodingCacheTests(unittest.TestCase):
 def test_cache_keeps_encoded_output_and_block_proofs_identical(self):
  tiles=bytes(range(256))*64;rgba=bytes([236,236,236,255])*64;cache={};a,p=overlay_tiles(tiles,128,128,[8,8,8,8],rgba);b,q=overlay_tiles(tiles,128,128,[8,8,8,8],rgba,cache);c,r=overlay_tiles(tiles,128,128,[8,8,8,8],rgba,cache)
  self.assertEqual((a,p),(b,q));self.assertEqual((a,p),(c,r));self.assertEqual(len(cache),1)
 def test_malformed_cached_bytes_rejected(self):
  rgba=bytes(256)
  with self.assertRaisesRegex(FormatError,'cached'):overlay_tiles(bytes(16384),128,128,[8,8,8,8],rgba,{(8,8,rgba):b'x'})

class MultiRegionTextureTests(unittest.TestCase):
 def fixture(self,c=False,t=False):
  from tools.texture_overlay import rgba_crop
  raw,logical,table,edit,layers=TextureOverlayTests().fixture(c,t);e=table['exports'][1];p=logical[e['serial_offset']:e['serial_offset']+e['serial_size']];tx=parse_atlas_payload(p,table['names'],e['serial_offset']);tiles=atlas_tiles(p,tx,stored_decoder);rgba=decode_dxt5(__import__('tools.ue3_textures',fromlist=['untile_dxt5']).untile_dxt5(tiles,128,128),128,128)
  edit={k:v for k,v in edit.items() if k!='label'};edit.update(regions=['x','y'],image_id='caption',protected_regions=[dict(id='symbol',rect=[32,0,16,32],rgba_sha256=digest(rgba_crop(rgba,128,[32,0,16,32])))])
  layers['y']=(dict(rect=[64,8,8,8]),bytes([255,100,40,255])*64)
  return raw,edit,layers
 def test_two_regions_all_compression_profiles_preserve_symbol(self):
  for c in [False,True]:
   for t in [False,True]:
    with self.subTest(c=c,t=t):
     raw,edit,layers=self.fixture(c,t);out,proof=patch_package(raw,digest(raw),[edit],layers,stored_decoder);p=proof['textures'][0];self.assertEqual(p['authorized_blocks'],8);self.assertEqual(len(p['regions']),2);self.assertEqual(p['protected_regions'][0]['before_rgba_sha256'],p['protected_regions'][0]['after_rgba_sha256']);self.assertTrue(p['protected_regions'][0]['blocks_preserved']);self.assertNotEqual(out,raw)
 def test_single_region_legacy_proof_unchanged(self):
  from tools.texture_overlay import overlay_regions
  raw,logical,t,e,l=TextureOverlayTests().fixture();p=l['x'];tiles=bytes(range(256))*64
  self.assertEqual(overlay_regions(tiles,128,128,e,l),overlay_tiles(tiles,128,128,p[0]['rect'],p[1]))
 def test_ambiguous_region_modes_rejected(self):
  from tools.texture_overlay import layer_ids
  for edit in [{},{'label':'x','regions':['x'],'image_id':'a'}]:
   with self.subTest(edit=edit),self.assertRaises(FormatError):layer_ids(edit)
 def test_invalid_region_ids_and_group_rejected(self):
  from tools.texture_overlay import layer_ids
  for regions in [[],['x']*2,['x']*17,'x',[None],['']]:
   with self.subTest(regions=regions),self.assertRaises(FormatError):layer_ids(dict(regions=regions,image_id='a'))
  for group in [None,True,'']:
   with self.subTest(group=group),self.assertRaises(FormatError):layer_ids(dict(regions=['x'],image_id=group))
 def test_missing_layer_rejected(self):
  raw,e,l=self.fixture();del l['y']
  with self.assertRaisesRegex(FormatError,'missing'):patch_package(raw,digest(raw),[e],l,stored_decoder)
 def test_edit_regions_overlap_rejected(self):
  raw,e,l=self.fixture();l['y']=(dict(rect=[8,8,8,8]),l['y'][1])
  with self.assertRaisesRegex(FormatError,'overlap'):patch_package(raw,digest(raw),[e],l,stored_decoder)
 def test_protected_region_overlap_rejected(self):
  raw,e,l=self.fixture();e['protected_regions'][0]['rect']=[8,8,8,8]
  with self.assertRaisesRegex(FormatError,'overlap'):patch_package(raw,digest(raw),[e],l,stored_decoder)
 def test_protected_original_hash_required_and_source_kept(self):
  raw,e,l=self.fixture();old=bytes(raw);e['protected_regions'][0]['rgba_sha256']='0'*64
  with self.assertRaisesRegex(FormatError,'hash mismatch'):patch_package(raw,digest(raw),[e],l,stored_decoder)
  self.assertEqual(raw,old)
 def test_protection_metadata_bound_and_duplicates(self):
  for change in [lambda e:e.update(protected_regions=None),lambda e:e.update(protected_regions=e['protected_regions']*17),lambda e:e.update(protected_regions=e['protected_regions']*2),lambda e:e['protected_regions'][0].update(extra=True)]:
   raw,e,l=self.fixture();change(e)
   with self.subTest(change=change),self.assertRaises(FormatError):patch_package(raw,digest(raw),[e],l,stored_decoder)
 def test_protected_rectangles_fail_closed(self):
  for rect in [[1,0,4,4],[0,0,True,4],[-4,0,4,4],[128,0,4,4],[0,0,0,4]]:
   raw,e,l=self.fixture();e['protected_regions'][0]['rect']=rect
   with self.subTest(rect=rect),self.assertRaises(FormatError):patch_package(raw,digest(raw),[e],l,stored_decoder)

if __name__=='__main__':unittest.main()
