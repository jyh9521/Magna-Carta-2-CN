import io,struct,unittest
from pathlib import Path
from tools import texture_layout as layout,texture_overlay as overlay
from tools.ue3_package import Reader,parse_summary,parse_tables,FormatError
from tools.ue3_fonts import read_properties,unique_properties
from tools.supplement_font import decode_logical,repack_append_only,parse_atlas_payload
from tools.lzx_stored import wrap_ue3_chunk
import test_texture_overlay as fixtures
from test_supplement_font import stored_decoder

def profile_fixture(fmt=7,width=64,height=16,compressed=False,package_compressed=False):
    raw,logical,table,oldedit,_=fixtures.TextureOverlayTests().fixture(package_compressed,compressed)
    ex=table['exports'][1];off=ex['serial_offset'];payload=logical[off:off+ex['serial_size']]
    r=Reader(payload);r.i32();props=unique_properties(read_properties(r,table['names']));source=r.pos
    t=parse_atlas_payload(payload,table['names'],off);bulk=t['mips'][0]['bulk'];po=bulk['payload_offset'];bo=bulk['header_offset']
    target=(len(logical)+3)&~3;data=bytes(layout.unit_layout(width,height,fmt)['storage_bytes'])
    stored=wrap_ue3_chunk(data) if compressed else data
    p=bytearray(payload[:po]);struct.pack_into('>I',p,props['SizeX']['value_offset'],width);struct.pack_into('>I',p,props['SizeY']['value_offset'],height);p[props['Format']['value_offset']]=fmt
    struct.pack_into('>I',p,source+12,target+source+16);struct.pack_into('>IIII',p,bo,64 if compressed else 0,len(data),len(stored),target+po);p+=stored+struct.pack('>II',width,height)
    new=bytearray(logical);new+=bytes(target-len(new))+p;struct.pack_into('>II',new,ex['table_offset']+32,len(p),target)
    summary=parse_summary(raw,len(raw));out,_=repack_append_only(raw,summary,logical,bytes(new))
    edit=dict(object=oldedit['object'],payload_sha256=overlay.digest(bytes(p)),tiled_sha256=overlay.digest(data),dimensions=[width,height],regions=['x'],image_id='owned-profile',profile=dict(kind=layout.PROFILE,format=fmt))
    if fmt==5:edit['channel_mode']='opaque-luma'
    layers={'x':(dict(rect=[8,4,8,8]),bytes([240,240,240,255])*64)}
    return out,edit,layers

class TextureLayoutTests(unittest.TestCase):
    def test_packed_origins_and_legacy_zero_origin(self):
        for w,h,origin in [(64,16,[0,4]),(128,16,[0,4]),(16,128,[4,0]),(16,16,[4,0]),(128,32,[0,0])]:
            for fmt in [5,7]:self.assertEqual(layout.unit_layout(w,h,fmt)['origin_blocks'],origin)
    def test_profile_format_geometry_and_finite_bounds(self):
        for args in [(64,16,2),(True,16,7),(63,16,7),(64,0,7),(16384,16,7),(8192,8192,7)]:
            with self.subTest(args=args),self.assertRaises(FormatError):layout.unit_layout(*args)
        for p in [None,{},dict(kind=layout.PROFILE,format=True),dict(kind=layout.PROFILE,format=2),dict(kind='other',format=7),dict(kind=layout.PROFILE,format=7,extra=1)]:
            with self.assertRaises(FormatError):layout.validate_profile(p)
    def test_owned_packages_all_bc_bulk_and_package_compression_profiles(self):
        for fmt in [5,7]:
            for bulk in [False,True]:
                for package in [False,True]:
                    with self.subTest(fmt=fmt,bulk=bulk,package=package):
                        raw,e,l=profile_fixture(fmt,compressed=bulk,package_compressed=package);out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
                        self.assertNotEqual(out,raw);self.assertEqual(p['nonselected_exports_preserved'],2);self.assertEqual(p['textures'][0]['storage_origin_blocks'],[0,4]);self.assertTrue(p['textures'][0]['untouched_blocks_preserved']);self.assertTrue(p['textures'][0]['alignment_padding_preserved'])
    def test_without_explicit_profile_legacy_small_or_bc1_is_rejected(self):
        for fmt in [5,7]:
            raw,e,l=profile_fixture(fmt);e.pop('profile');e.pop('channel_mode',None)
            with self.assertRaises(FormatError):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
    def test_actual_reopening_pixels_and_source_bytes_unchanged(self):
        raw,e,l=profile_fixture();original=bytes(raw);out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder);s=parse_summary(out);logical=decode_logical(out,s,stored_decoder);t=parse_tables(logical,s,len(logical));x=t['exports'][1];payload=logical[x['serial_offset']:x['serial_offset']+x['serial_size']]
        w,h,rgba=overlay.edit_pixels(payload,t['names'],x['serial_offset'],e,stored_decoder)
        self.assertEqual((w,h),(64,16));self.assertEqual(overlay.digest(rgba),p['textures'][0]['decoded_rgba_sha256']);self.assertEqual(raw,original)
    def test_extract_identity_and_only_authorized_physical_units_change(self):
        for fmt in [5,7]:
            l=layout.unit_layout(64,16,fmt);raw=bytes(l['storage_bytes']);out,p=layout.overlay_rect(raw,l,[8,4,8,8],bytes([220,220,220,255])*64);bs=l['unit_bytes'];changed={i for i in range(0,len(raw),bs) if raw[i:i+bs]!=out[i:i+bs]}
            self.assertTrue(changed);self.assertLessEqual(changed,set(layout.rect_units(l,[8,4,8,8])));self.assertEqual(p['authorized_blocks'],4)
    def test_region_and_encoding_cache_fail_closed(self):
        l=layout.unit_layout(64,16,7);raw=bytes(l['storage_bytes']);rgba=bytes([255]*256);cache={};a,p=layout.overlay_rect(raw,l,[8,4,8,8],rgba,cache);b,q=layout.overlay_rect(raw,l,[8,4,8,8],rgba,cache);self.assertEqual((a,p),(b,q))
        for rect in [[1,0,4,4],[0,0,0,4],[60,0,8,4],[0,16,4,4],[False,0,4,4]]:
            with self.assertRaises(FormatError):layout.rect_units(l,rect)
        with self.assertRaises(FormatError):layout.overlay_rect(raw,l,[8,4,8,8],b'x')
        cache[('xbox-bc',7,8,8,rgba)]=b'x'
        with self.assertRaisesRegex(FormatError,'cache'):layout.overlay_rect(raw,l,[8,4,8,8],rgba,cache)
    def test_bc1_requires_opaque_pixels_and_channel_contract(self):
        l=layout.unit_layout(64,16,5)
        with self.assertRaisesRegex(FormatError,'opaque'):layout.overlay_rect(bytes(l['storage_bytes']),l,[0,0,4,4],bytes(64))
        raw,e,layers=profile_fixture(5)
        for mode in ['rgba',None,'mask','alpha']:
            with self.assertRaisesRegex(FormatError,'channel mode'):overlay.patch_package(raw,overlay.digest(raw),[{**e,'channel_mode':mode}],layers,stored_decoder)
    def test_protected_crop_and_unit_hashes_are_enforced(self):
        for fmt in [5,7]:
            raw,e,l=profile_fixture(fmt);s=parse_summary(raw);log=decode_logical(raw,s,stored_decoder);t=parse_tables(log,s,len(log));x=t['exports'][1];w,h,rgba=overlay.edit_pixels(log[x['serial_offset']:x['serial_offset']+x['serial_size']],t['names'],x['serial_offset'],e,stored_decoder)
            e['protected_regions']=[dict(id='symbol',rect=[0,0,4,16],rgba_sha256=overlay.digest(overlay.rgba_crop(rgba,w,[0,0,4,16])))];out,p=overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder);self.assertTrue(p['textures'][0]['protected_regions'][0]['blocks_preserved'])
            e['protected_regions'][0]['rgba_sha256']='0'*64
            with self.assertRaisesRegex(FormatError,'hash mismatch'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
    def test_hash_dimensions_and_overlap_guards_remain(self):
        raw,e,l=profile_fixture()
        for change in [dict(payload_sha256='0'*64),dict(tiled_sha256='0'*64),dict(dimensions=[32,16]),dict(profile=None)]:
            with self.assertRaises(FormatError):overlay.patch_package(raw,overlay.digest(raw),[{**e,**change}],l,stored_decoder)
        e['regions']=['x','y'];l['y']=l['x']
        with self.assertRaisesRegex(FormatError,'overlap'):overlay.patch_package(raw,overlay.digest(raw),[e],l,stored_decoder)
    def test_inline_header_and_export_termination_guards(self):
        raw,e,_=profile_fixture();s=parse_summary(raw);log=decode_logical(raw,s,stored_decoder);t=parse_tables(log,s,len(log));x=t['exports'][1];off=x['serial_offset'];p=log[off:off+x['serial_size']];tx=layout.read_texture(p,t['names'],off,e['profile'],stored_decoder)
        for at,value in [(tx['source_offset'],1),(tx['source_offset']+16,2),(tx['bulk_offset'],128),(tx['bulk_offset']+4,1),(tx['bulk_offset']+12,0),(len(p)-4,32)]:
            b=bytearray(p);struct.pack_into('>I',b,at,value)
            with self.subTest(at=at),self.assertRaises(FormatError):layout.read_texture(bytes(b),t['names'],off,e['profile'],stored_decoder)
        with self.assertRaises(FormatError):layout.read_texture(p+b'x',t['names'],off,e['profile'],stored_decoder)
    def test_opaque_profile_rejects_transparent_source_not_only_new_layer(self):
        l=layout.unit_layout(64,16,5);raw=bytearray(l['storage_bytes']);block=struct.pack('<HHI',0,0,0xffffffff);o=l['offsets'][0];raw[o:o+8]=b''.join(block[i:i+2][::-1] for i in range(0,8,2));t=dict(layout=l,width=64,height=16,format=5,tiles=bytes(raw))
        edit=dict(regions=['x'],image_id='opaque',channel_mode='opaque-luma');layers={'x':(dict(rect=[8,4,8,8]),bytes([255]*256))}
        with self.assertRaisesRegex(FormatError,'source has transparent'):overlay.overlay_profile_regions(t,edit,layers)

class ExplicitInkPaddingTests(unittest.TestCase):
    def test_default_and_explicit_four_pixel_position_are_identical(self):
        for b in [(-1,3,40,21),(0,0,20,16)]:
            for a in ['left','center','right']:self.assertEqual(overlay.text_position(128,32,b,a),overlay.text_position(128,32,b,a,dict(x=4,y=4)))
    def test_small_padding_is_bounded_not_a_logical_size_change(self):
        self.assertEqual(overlay.text_position(64,16,(-1,3,21,17),'center',dict(x=4,y=1)),(22,-2))
        with self.assertRaisesRegex(FormatError,'does not fit'):overlay.text_position(64,16,(-1,3,21,17))
    def test_invalid_explicit_padding_rejected(self):
        for p in [{},{'x':1},{'x':True,'y':1},{'x':4,'y':-1},{'x':4,'y':17},{'x':4,'y':1,'z':0},[],0]:
            with self.assertRaisesRegex(FormatError,'padding'):overlay.text_position(64,16,(0,0,20,14),padding=p)
    def test_padding_cannot_make_oversized_ink_fit(self):
        with self.assertRaisesRegex(FormatError,'does not fit'):overlay.text_position(64,16,(0,0,65,14),padding=dict(x=0,y=0))

class FontCodepointCacheTests(unittest.TestCase):
    def tearDown(self):overlay.font_codepoints.cache_clear()
    def test_identical_bytes_reuse_one_immutable_cmap_and_close_font(self):
        from unittest.mock import patch,Mock
        overlay.font_codepoints.cache_clear();font=Mock();font.getBestCmap.return_value={65:'a'}
        with patch('fontTools.ttLib.TTFont',return_value=font) as ctor:
            a=overlay.font_codepoints(b'owned-one');b=overlay.font_codepoints(bytes(bytearray(b'owned-one')))
            self.assertIs(a,b);self.assertEqual(a,frozenset({65}));self.assertEqual(ctor.call_count,1);font.close.assert_called_once();self.assertEqual(overlay.font_codepoints.cache_info().hits,1)
    def test_changed_bytes_do_not_reuse_glyph_validation_and_cache_is_bounded(self):
        from unittest.mock import patch,Mock
        overlay.font_codepoints.cache_clear();a=Mock();a.getBestCmap.return_value={65:'a'};b=Mock();b.getBestCmap.return_value={66:'b'}
        with patch('fontTools.ttLib.TTFont',side_effect=[a,b,a]) as ctor:
            self.assertEqual(overlay.font_codepoints(b'font-A'),frozenset({65}));self.assertEqual(overlay.font_codepoints(b'font-B'),frozenset({66}));self.assertEqual(overlay.font_codepoints(b'font-A'),frozenset({65}));self.assertEqual(ctor.call_count,3);self.assertEqual(overlay.font_codepoints.cache_info().maxsize,1);self.assertEqual(overlay.font_codepoints.cache_info().currsize,1)
    def test_empty_or_nonbytes_font_rejected(self):
        for value in [b'',None,'font']:
            with self.assertRaisesRegex(FormatError,'font bytes bound'):overlay.font_codepoints(value)

if __name__=='__main__':unittest.main()
