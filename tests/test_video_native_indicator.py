import unittest
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from tools.video_native_indicator import NativeIndicator


class NativeIndicatorTests(unittest.TestCase):
    def setup_case(self):
        clean=np.zeros((8,12,3),np.uint8);clean[:,:6]=[220,180,130];clean[:,6:]=[12,19,33]
        matte=np.zeros_like(clean);matte[3:5,3:9]=255
        observed=np.rint(matte+(1-matte/255)*clean).astype(np.uint8)
        mask=np.zeros((8,12),bool);mask[3:5,3:9]=True
        patch=np.zeros((8,12,4),np.uint8);patch[mask,:3]=clean[mask];patch[mask,3]=255
        letters=[Image.new('RGBA',(12,8))for _ in range(3)]
        return clean,observed,mask,matte,patch,letters

    def test_opaque_detail_is_explicit_and_not_averaged_across_sharp_edge(self):
        clean,observed,mask,matte,patch,letters=self.setup_case()
        r=NativeIndicator((0,0,12,8),mask,matte,observed,Image.fromarray(patch),letters,90)
        self.assertTrue(np.array_equal(r.clean(observed),clean))
        self.assertEqual(r.proof()['known_pixels_spatially_filtered'],0)
        self.assertTrue(np.array_equal(np.asarray(r.apply(Image.fromarray(observed),0)),clean))

    def test_letter_support_cannot_change_foreign_pixels(self):
        clean,observed,mask,matte,patch,letters=self.setup_case()
        r=NativeIndicator((4,2,12,8),mask,matte,observed,Image.fromarray(patch),letters,90)
        frame=np.full((12,20,3),37,np.uint8);frame[2:10,4:16]=observed
        got=np.asarray(r.apply(Image.fromarray(frame),89));expected=frame.copy();expected[2:10,4:16]=clean
        self.assertTrue(np.array_equal(got,expected))
        for bad in (-1,90,False):
            with self.assertRaises(ValueError):r.apply(Image.fromarray(frame),bad)

    def test_unknown_pixel_mask_and_hidden_rgb_are_fail_closed(self):
        _,observed,mask,matte,patch,letters=self.setup_case()
        bad=patch.copy();bad[0,0]=[3,0,0,0]
        with self.assertRaises(ValueError):NativeIndicator((0,0,12,8),mask,matte,observed,Image.fromarray(bad),letters,90)
        bad=patch.copy();bad[3,3,3]=0
        with self.assertRaises(ValueError):NativeIndicator((0,0,12,8),mask,matte,observed,Image.fromarray(bad),letters,90)

    def test_three_letter_states_and_temporal_light_only_on_repair(self):
        clean,observed,mask,matte,patch,letters=self.setup_case()
        for i in range(3):letters[i].putpixel((11,7),(80*(i+1),0,0,255))
        r=NativeIndicator((0,0,12,8),mask,matte,observed,Image.fromarray(patch),letters,90)
        values=[np.asarray(r.apply(Image.fromarray(observed),i))[7,11,0]for i in (0,30,60)]
        self.assertTrue(values[0]<values[1]<values[2])
        later=np.minimum(255,observed.astype(int)+5).astype(np.uint8)
        fixed=r.clean(later)
        self.assertTrue(np.array_equal(fixed[~mask],later[~mask]))
        self.assertTrue(np.array_equal(fixed[mask],clean[mask]+5))

    def test_model_invalid_pixel_is_explicit_reconstruction_not_native_recovery(self):
        _,observed,mask,matte,patch,letters=self.setup_case()
        invalid=np.zeros_like(mask);invalid[2,3]=True;mask[2,3]=True
        patch[2,3]=[80,90,100,255]
        r=NativeIndicator((0,0,12,8),mask,matte,observed,Image.fromarray(patch),letters,90,invalid_mask=invalid)
        self.assertEqual(r.proof()['reconstructed_glyph_pixels'],13)
        self.assertEqual(r.clean(observed)[2,3].tolist(),[80,90,100])

    def test_native_composite_never_calls_target_background_interpolation(self):
        from tools.build_video_captions import composite
        from unittest.mock import patch as mock_patch
        clean,observed,mask,matte,patch,letters=self.setup_case()
        r=NativeIndicator((0,0,12,8),mask,matte,observed,Image.fromarray(patch),letters,90)
        with mock_patch('tools.build_video_captions.restore_masked',side_effect=AssertionError('target art filtered')):
            result=composite(Image.fromarray(observed),[r],Image.new('RGBA',(12,8)),mask,45)
        self.assertTrue(np.array_equal(np.array(result),clean))

    def test_regional_verifier_preserves_native_operation_when_rebasing(self):
        from tools.verify_video_caption_regions import local_layers
        from unittest.mock import patch as mock_patch
        _,observed,mask,matte,patch,letters=self.setup_case()
        r=NativeIndicator((4,2,12,8),mask,matte,observed,Image.fromarray(patch),letters,90)
        changed=np.zeros((12,20),bool);changed[2:10,4:16]=mask
        entry={'captions':[{'role':'indicator','style':{'rect':[4,2,12,8]}}]}
        result=(None,b'',{'width':20,'height':12},[r],Image.new('RGBA',(20,12)),changed,[])
        with mock_patch('tools.verify_video_caption_regions.prepare_layers',return_value=result):
            data=local_layers({},entry,'indicator',None,None,None,[1,1,18,10])
        self.assertIsInstance(data[3][0],NativeIndicator)
        self.assertEqual(data[3][0].rect,(3,1,12,8));self.assertEqual(r.rect,(4,2,12,8))


class NativeIndicatorProfileTests(unittest.TestCase):
    root=Path(__file__).resolve().parents[1]

    def read(self,path):return json.loads((self.root/path).read_bytes())

    def test_hash_bound_source_profiles_are_canonical_lf(self):
        paths=['locales/zh-Hans/loading-captions-v10.json',
               'locales/zh-Hans/voice-drama-punctuation-v10.json',
               'locales/zh-Hans/texture-overlays/voice-drama-headings-v10.json',
               'locales/zh-Hans/texture-overlays/voice-drama-region-update-v10.json',
               'locales/zh-Hans/texture-overlays/voice-drama-heading-contracts-v10.json']
        for path in paths:self.assertFalse(b'\r\n' in (self.root/path).read_bytes(),path)

    def test_all_fifteen_movies_change_only_indicator_recipe(self):
        before=self.read('locales/zh-Hans/loading-captions-v9.json')
        after=self.read('locales/zh-Hans/loading-captions-v10.json')
        self.assertEqual(len(after['entries']),15)
        self.assertEqual(after['rasterizer_versions'],before['rasterizer_versions'])
        for old,new in zip(before['entries'],after['entries'],strict=True):
            self.assertEqual(new['id'],old['id']);self.assertEqual(new['source'],old['source'])
            self.assertEqual([c for c in old['captions'] if c['role']!='indicator'],
                             [c for c in new['captions'] if c['role']!='indicator'])
            indicator=[c for c in new['captions'] if c['role']=='indicator'];self.assertEqual(len(indicator),1)
            c=indicator[0];s=c['erase']['native_screen']
            self.assertEqual(s['method'],'boundary-compensated-screen-v1')
            self.assertEqual(s['minimum_transmittance'],.9) # bounded 1.111x inversion, not 8.33x noise/ghosts
            self.assertEqual(s['invalid_tolerance'],4)
            self.assertEqual(s['text_states'],['正在载入.','正在载入..','正在载入...'])
            self.assertEqual(c['font'],'indicator');self.assertEqual(c['style']['font_size'],22)

    def test_authored_assets_are_sparse_hash_locked_and_include_no_full_backdrop(self):
        p=self.read('locales/zh-Hans/loading-captions-v10.json')
        provenance=self.read('locales/zh-Hans/loading-restoration-v10/PROVENANCE.json')
        records={r['id']:r for r in provenance['resources']}
        self.assertFalse(provenance['complete_original_asset_included'])
        for entry in p['entries']:
            spec=next(c for c in entry['captions']if c['role']=='indicator')['erase']['native_screen']
            asset=spec['core_patch'];raw=(self.root/asset['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),asset['sha256'])
            im=Image.open(self.root/asset['path']);self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(192,40))
            rgba=np.array(im);mask=rgba[:,:,3]>0
            self.assertTrue(np.isin(rgba[:,:,3],[0,255]).all());self.assertTrue((rgba[~mask]==0).all())
            self.assertEqual(hashlib.sha256(mask.tobytes()).hexdigest(),spec['repair_mask_sha256'])
            self.assertLess(mask.sum(),6000);self.assertEqual(int(mask.sum()),records[entry['id']]['reconstructed_glyph_pixels'])


if __name__=='__main__':unittest.main()
