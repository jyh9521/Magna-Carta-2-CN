import copy
import importlib.metadata
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from tools.lettering_layers import source_ink,effects
from tools.rebuild_texture_titles import compose_island,build,rebuild_tiles
from tools.audit_texture_titles import audit,negative_space
from tools.texture_layout import unit_layout,overlay_rect,decode_texture
from tools.replace_texture_regions import selected,replace_tiles
from tools.patch_tagged_fields import digest
from tools.bc3_error_bound import refine
from tools.bc3_rgb_fit import encode_fitted_rgba_block
from tools.texture_overlay import encode_alpha_range
from tools.ue3_textures import decode_dxt5
from test_texture_layout import profile_fixture

FX=dict(outline_width=.25,outline_alpha=110,shadow_radius=.7,shadow_alpha=150,shadow_offset=[1,1],support_radius=3)

class TitleRebuildTests(unittest.TestCase):
    def font_layer(self):
        from test_texture_render_windows import owned_font
        from test_texture_appearance import AppearanceTests
        font=owned_font();label=AppearanceTests().label();label['id']='owned';ref=dict(path='font.otf',sha256=digest(font))
        return font,dict(id='owned',kind='font',font=ref,label=label,effects=FX.copy(),
                         anchor=dict(mode='right',target=148))

    def test_font_is_rendered_once_before_splitting_effects(self):
        font,layer=self.font_layer();assets={('font.otf',digest(font)):font}
        spec=dict(id='split',name='Split',rect=[0,0,160,64],background=dict(kind='transparent'),layers=[layer])
        original=Image.new('RGBA',(160,64),(0,0,0,200))
        whole,_,_=compose_island(original,spec,assets)
        joined=Image.new('RGBA',whole.size)
        for y in (0,32):
            part=copy.deepcopy(spec);part['rect']=[0,y,160,32];part['layers'][0]['crop']=[0,y,160,32]
            image,_,_=compose_island(original,part,assets);joined.paste(image,(0,y))
        self.assertEqual(joined.tobytes(),whole.tobytes())
        self.assertEqual(whole.getpixel((0,0))[3],0)

    def test_font_dependency_hash_checked_before_writing(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p,_=self.fixture(root);font,layer=self.font_layer();(root/'font.otf').write_bytes(font)
            layer['font']['sha256']='0'*64;p['resources'][0]['textures'][0]['islands'][0]['layers']=[layer]
            with self.assertRaisesRegex(ValueError,'SHA256'):build(p,root,root/'input',root/'out',None)
            self.assertFalse((root/'out').exists())

    def test_minimax_refinement_keeps_alpha_and_never_worsens_max_error(self):
        rgba=b''.join(bytes([v,v,v,255])for v in [0,45,150,220,255,45,150,220]*2)
        encoded=encode_alpha_range([255]*16)+encode_fitted_rgba_block(rgba)[8:]
        result=refine(rgba,encoded,20)
        error=lambda b:max(abs(x-y)for x,y in zip(rgba,decode_dxt5(b,4,4),strict=True))
        self.assertEqual(result[:8],encoded[:8])
        self.assertLessEqual(error(result),error(encoded))
        self.assertEqual(result,refine(rgba,encoded,20))
        self.assertEqual(encoded,refine(rgba,encoded,255))

    def image(self):
        im=Image.new('RGBA',(32,32))
        im.paste((0,0,0,150),(9,9,22,14))
        im.paste((160,120,80,200),(10,14,21,17))
        im.putpixel((14,15),(0,0,0,230))
        im.putpixel((1,22),(0,0,0,45))
        return im

    def spec(self):
        return dict(id='sample',name='Sample',rect=[0,0,32,24],background=dict(kind='transparent'),
                    layers=[dict(id='latin',kind='source-ink',core=[10,14,11,3],ink_floor=16,effects=FX.copy())],
                    max_alpha_delta=24,max_premultiplied_delta=48)

    def texture(self,im):
        layout=unit_layout(*im.size,7)
        raw,_=overlay_rect(bytes(layout['storage_bytes']),layout,[0,0,*im.size],im.tobytes(),
                           alpha_encoding='adaptive-range',rgb_encoding='weighted-fit-v1')
        return dict(layout=layout,tiles=raw,width=im.width,height=im.height,format=7)

    def test_no_original_dark_alpha_survives_even_inside_glyph_box(self):
        im=self.image();ink=source_ink(im,[10,14,11,3]);self.assertEqual(ink.getpixel((14,15))[3],0)
        self.assertEqual(ink.getpixel((10,12))[3],0)
        self.assertEqual(ink.getpixel((1,22))[3],0)
        self.assertEqual(ink.getpixel((10,14)),im.getpixel((10,14)))

    def test_arbitrary_neighbour_shadow_has_no_influence(self):
        im=self.image();clean=im.copy();clean.paste((0,0,0,0),(0,0,32,14))
        self.assertEqual(source_ink(im,[10,14,11,3]).tobytes(),source_ink(clean,[10,14,11,3]).tobytes())

    def test_weak_palette_bleed_between_letters_is_not_ink(self):
        im=Image.new('RGBA',(32,32));im.putpixel((5,15),(160,120,80,200))
        im.putpixel((20,15),(24,24,24,180))
        ink=source_ink(im,[4,12,24,8])
        self.assertEqual(ink.getpixel((20,15))[3],0)

    def test_unmatting_preserves_premultiplied_colour_and_sample_position(self):
        im=self.image();im.putpixel((12,14),(80,60,40,180));ink=source_ink(im,[10,14,11,3])
        p,q=im.getpixel((12,14)),ink.getpixel((12,14))
        self.assertEqual(q,(160,120,80,90))
        for c in range(3):self.assertEqual(p[c]*p[3],q[c]*q[3])

    def test_effects_have_finite_support_and_no_rectangle(self):
        ink=Image.new('RGBA',(32,32));ink.putpixel((15,15),(160,120,80,200))
        final,parts=effects(ink,FX)
        self.assertEqual(final.getpixel((0,0))[3],0)
        self.assertEqual(final.getpixel((15,11))[3],0)
        self.assertGreater(final.getpixel((16,16))[3],0)
        self.assertEqual(negative_space(final,Image.new('RGBA',final.size),[ink]),0)
        self.assertTrue(all(p[0]==p[1]==p[2]==0 for p in parts['shadow'].get_flattened_data()))

    def test_invalid_bounds_effects_and_unknown_layer_rejected(self):
        for rect in ([-1,0,4,4],[0,0,40,4]):
            with self.assertRaises(ValueError):source_ink(self.image(),rect)
        for bad in ({**FX,'support_radius':40},{**FX,'shadow_offset':[32,0]},{**FX,'shadow_alpha':256}):
            with self.assertRaises(ValueError):effects(self.image(),bad)
        spec=self.spec();spec['layers'][0]['kind']='keep-old-shadow'
        with self.assertRaises(ValueError):compose_island(self.image(),spec,{})

    def test_native_roundtrip_erases_orphan_and_builds_compact_shadow(self):
        tx=self.texture(self.image());raw,proofs=rebuild_tiles(tx,tx,[self.spec()],{})
        result=Image.frombytes('RGBA',(32,32),decode_texture(tx,raw))
        self.assertEqual(result.getpixel((10,9))[3],0)
        self.assertEqual(result.getpixel((1,22))[3],0)
        self.assertGreater(result.getpixel((10,17))[3],0)
        self.assertEqual(proofs[0]['layers'][0]['original_shadow_pixels_copied'],0)

    def test_overlap_rejected(self):
        tx=self.texture(self.image())
        with self.assertRaisesRegex(ValueError,'overlap'):rebuild_tiles(tx,tx,[self.spec(),self.spec()],{})

    def fixture(self,root):
        raw,spec,_=profile_fixture(width=32,height=32);tx=selected(raw,spec['object'],None)[3]
        tiles,_=overlay_rect(tx['tiles'],tx['layout'],[0,0,32,32],self.image().tobytes(),
                            alpha_encoding='adaptive-range',rgb_encoding='weighted-fit-v1')
        original,_=replace_tiles(raw,digest(raw),spec['object'],tiles,[[0,0,32,32]],None)
        original+=bytes((-len(original))%32768)
        (root/'original.xxx').write_bytes(original);(root/'input').mkdir();(root/'input/owned.xxx').write_bytes(original)
        profile=dict(schema_version=1,kind='clean-lettering-v1',rasterizer_versions={k:importlib.metadata.version(k)for k in ('Pillow','fonttools')},
            resources=[dict(path='owned.xxx',sha256=digest(original),original=dict(path='original.xxx',sha256=digest(original)),discs=[1,2],
                textures=[dict(object=spec['object'],profile=spec['profile'],tiled_sha256=digest(tiles),original_tiled_sha256=digest(tiles),islands=[self.spec()])])])
        return profile,original

    def test_real_package_sparse_copy_and_two_disc_manifest(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);profile,original=self.fixture(root);result=build(profile,root,root/'input',root/'output',None)
            self.assertEqual((root/'input/owned.xxx').read_bytes(),original);self.assertEqual((root/'original.xxx').read_bytes(),original)
            for disc in (1,2):
                m=json.loads((root/f'output/replacements-disc{disc}.json').read_bytes())
                self.assertEqual(m['resources'][0]['before_sha256'],digest(original))
            self.assertTrue(result['proofs'][0]['outside_blocks_preserved'])
            self.assertTrue(result['proofs'][0]['unselected_exports_preserved'])

    def test_source_texture_and_dependency_hash_guards(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p,_=self.fixture(root)
            for part in (p['resources'][0],p['resources'][0]['original'],p['resources'][0]['textures'][0]):
                field='sha256'if'sha256'in part else'tiled_sha256';old=part[field];part[field]='0'*64
                with self.assertRaisesRegex(ValueError,'SHA256'):build(p,root,root/'input',root/'output',None)
                part[field]=old;self.assertFalse((root/'output').exists())

    def test_disjoint_output_and_duplicates(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p,_=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'disjoint'):build(p,root,root/'input',root/'input/out',None)
            p['resources'].append(copy.deepcopy(p['resources'][0]))
            with self.assertRaisesRegex(ValueError,'duplicate'):build(p,root,root/'input',root/'out',None)

    def test_independent_negative_space_audit_catches_self_consistent_bad_reference(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p,_=self.fixture(root);ref=build(p,root,root/'input',root/'output',None)
            before=audit(p,root,root/'input',root/'input',ref,None)
            after=audit(p,root,root/'input',root/'output/candidate',ref,None)
            self.assertFalse(before['passed']);self.assertGreater(before['groups'][0]['negative_space_residue_pixels'],0)
            self.assertTrue(after['passed'])
            # A corrupt renderer could update its own reference digest. Independent
            # geometry must still reject this dark pixel, rather than agree with it.
            f=root/'output/candidate/owned.xxx';data=f.read_bytes();obj=p['resources'][0]['textures'][0]['object']
            tx=selected(data,obj,None)[3];im=Image.frombytes('RGBA',(32,32),decode_texture(tx));im.putpixel((1,22),(0,0,0,80))
            tile,_=overlay_rect(tx['tiles'],tx['layout'],[0,0,32,24],im.crop((0,0,32,24)).tobytes(),alpha_encoding='adaptive-range',rgb_encoding='weighted-fit-v1')
            changed,_=replace_tiles(data,digest(data),obj,tile,[[0,0,32,24]],None);f.write_bytes(changed)
            decoded=Image.frombytes('RGBA',(32,32),decode_texture(tx,tile)).crop((0,0,32,24))
            ref['proofs'][0]['islands'][0]['decoded_rgba_sha256']=digest(decoded.tobytes())
            bad=audit(p,root,root/'input',root/'output/candidate',ref,None)
            self.assertFalse(bad['passed']);self.assertTrue(bad['groups'][0]['native_identity'])

    def test_every_map_texture_and_latin_layer_covered(self):
        root=Path(__file__).resolve().parents[1]
        p=json.loads((root/'locales/zh-Hans/texture-overlays/map-lettering-v19.json').read_bytes())
        old=json.loads((root/'locales/zh-Hans/map-english-audit-v13.json').read_bytes())
        actual={(r['path'],t['object'])for r in p['resources']for t in r['textures']}
        self.assertEqual(actual,{(t['resource'],t['object'])for t in old['textures']})
        self.assertEqual(len(actual),82)
        islands=[s for r in p['resources']for t in r['textures']for s in t['islands']]
        latin=[l for s in islands for l in s['layers']if l['kind']=='source-ink'];self.assertEqual(len(latin),44)
        self.assertEqual(len(islands),257)
        high=[l for s in islands if s['name'].startswith('风息岛')for l in s['layers']if l['kind']=='font'and l['label']['text']=='风息岛']
        self.assertEqual(len(high),4)
        self.assertTrue(all(l['font']['path'].endswith('NotoSerifCJKsc-SemiBold.otf')for l in high))
        self.assertEqual(len({json.dumps(l['label']['appearance'],sort_keys=True)for l in high}),1)
        self.assertTrue(all(l['anchor']=={'mode':'right','target':192}for l in high))

if __name__=='__main__':unittest.main()
