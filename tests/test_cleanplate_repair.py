import copy
import unittest

from tools.cleanplate_repair import reconcile_rgba


class CleanplateRepairTests(unittest.TestCase):
    def test_owned_texture_survives_boundary_color_correction(self):
        import numpy as np
        width=height=11
        guide=np.array([[[30+(x%2)*40,50+(y%2)*30,70,180] for x in range(width)] for y in range(height)],dtype=np.uint8)
        original=guide.copy();original[:,:,:3]+=10
        mask=np.zeros((height,width),dtype=np.uint8);mask[3:8,3:8]=255
        damaged=original.copy();damaged[mask>0]=[255,255,255,255]
        result=reconcile_rgba(damaged.tobytes(),guide.tobytes(),width,height,mask.tobytes(),1000,'interpolate-source-alpha-v1')
        actual=np.frombuffer(result,dtype=np.uint8).reshape(height,width,4)
        self.assertTrue(np.array_equal(actual[:,:,:3],original[:,:,:3]))
        self.assertTrue(np.array_equal(actual[:,:,3],original[:,:,3]))
        self.assertTrue(np.array_equal(actual[mask==0],damaged[mask==0]))
        self.assertEqual(result,reconcile_rgba(damaged.tobytes(),guide.tobytes(),width,height,mask.tobytes(),1000,'interpolate-source-alpha-v1'))

    def test_invisible_guide_rgb_never_becomes_visible_after_native_alpha_repair(self):
        import numpy as np
        source=np.full((9,9,4),[30,50,70,200],dtype=np.uint8)
        mask=np.zeros((9,9),dtype=np.uint8);mask[3:6,3:6]=255
        source[mask>0]=[240,230,230,255]
        black=np.zeros_like(source)
        white=black.copy();white[:,:,:3]=255
        args=(9,9,mask.tobytes(),1000,'interpolate-source-alpha-v1')
        a=reconcile_rgba(source.tobytes(),black.tobytes(),*args)
        b=reconcile_rgba(source.tobytes(),white.tobytes(),*args)
        self.assertEqual(a,b)
        self.assertEqual(np.frombuffer(a,dtype=np.uint8).reshape(9,9,4)[4,4].tolist(),[30,50,70,200])
        white[4,4,3]=1
        near_transparent=np.frombuffer(reconcile_rgba(source.tobytes(),white.tobytes(),*args),dtype=np.uint8).reshape(9,9,4)
        self.assertLess(int(near_transparent[4,4,:3].max()),75)

    def test_explicit_guided_alpha_clears_old_letter_support_outside_silhouette(self):
        import numpy as np
        source=np.zeros((9,9,4),dtype=np.uint8)
        plate=np.zeros_like(source)
        mask=np.zeros((9,9),dtype=np.uint8);mask[3:6,3:6]=255
        source[mask>0]=[240,230,230,255]
        preserved=np.frombuffer(reconcile_rgba(source.tobytes(),plate.tobytes(),9,9,mask.tobytes(),64),dtype=np.uint8).reshape(9,9,4)
        self.assertTrue((preserved[mask>0,3]==255).all())
        restored=np.frombuffer(reconcile_rgba(source.tobytes(),plate.tobytes(),9,9,mask.tobytes(),64,'guided-source-envelope-v1'),dtype=np.uint8).reshape(9,9,4)
        self.assertTrue((restored[mask>0]==0).all())
        self.assertTrue(np.array_equal(restored[mask==0],source[mask==0]))

    def test_native_alpha_continuation_preserves_artist_brush_when_guide_omits_it(self):
        import numpy as np
        source=np.zeros((9,9,4),dtype=np.uint8);source[:,:,3]=160
        plate=np.zeros_like(source)
        mask=np.zeros((9,9),dtype=np.uint8);mask[3:6,3:6]=255
        source[mask>0]=[240,230,230,255]
        restored=np.frombuffer(reconcile_rgba(source.tobytes(),plate.tobytes(),9,9,mask.tobytes(),1000,'interpolate-source-alpha-v1'),dtype=np.uint8).reshape(9,9,4)
        self.assertTrue((restored[:,:,3]==160).all())
        self.assertTrue(np.array_equal(restored[mask==0],source[mask==0]))

    def test_rejects_empty_whole_nonbinary_and_unbounded_inputs(self):
        for mask in (bytes(9),bytes([255])*9,bytes([1])+bytes(8),bytes(8)):
            with self.subTest(mask=mask),self.assertRaises(ValueError):
                reconcile_rgba(bytes(36),bytes(36),3,3,mask)
        mask=bytes([0]*4+[255]+[0]*4)
        for iterations,mode in ((-1,'preserve-source'),(2049,'preserve-source'),(True,'preserve-source'),(64,'unknown')):
            with self.subTest(iterations=iterations,mode=mode),self.assertRaises(ValueError):
                reconcile_rgba(bytes(36),bytes(36),3,3,mask,iterations,mode)


class CleanplateReplayTests(unittest.TestCase):
    def fixture(self,root):
        import io
        from pathlib import Path
        from PIL import Image
        from tools.build_font_supplement import context
        from tools.patch_tagged_fields import digest
        from tools.texture_layout import read_texture,decode_texture
        from tools.texture_overlay import select_texture_export,rgba_crop
        from test_texture_layout import profile_fixture
        from test_supplement_font import stored_decoder
        import importlib.metadata
        data,edit,_=profile_fixture(7)
        (root/'source.xxx').write_bytes(data)
        c=context(data,stored_decoder);e=select_texture_export(c['tables'],edit['object'])
        payload=c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        texture=read_texture(payload,c['tables']['names'],e['serial_offset'],edit['profile'],stored_decoder)
        width,height=texture['width'],texture['height'];native=decode_texture(texture)
        plate=Image.frombytes('RGBA',(width,height),native);plate.save(root/'plate.png')
        rect=[8,8,8,8];mask=Image.new('L',(8,8));mask.putpixel((3,3),255);mask.save(root/'mask.png')
        sparse=bytes(8*8*4);stream=io.BytesIO();Image.frombytes('RGBA',(8,8),sparse).save(stream,format='PNG')
        ref=lambda name:dict(path=name,sha256=digest((root/name).read_bytes()))
        case=dict(id='owned',source=ref('source.xxx'),object=edit['object'],profile=edit['profile'],
                  dimensions=[width,height],tiled_sha256=digest(texture['tiles']),rect=rect,
                  source_rgba_sha256=digest(rgba_crop(native,width,rect)),mask=ref('mask.png'),
                  plate=ref('plate.png'),plate_size=[width,height],iterations=8,
                  alpha_mode='preserve-source',patch=dict(path='restorations/patch.png',sha256=digest(stream.getvalue())))
        recipe=dict(schema_version=1,kind='texture-cleanplate-repair-v1',method='premultiplied-harmonic-boundary-v1',
                    hidden_artwork='reconstruction-not-original',rasterizer_versions={k:importlib.metadata.version(k)for k in ['Pillow','numpy']},cases=[case])
        return recipe,stored_decoder

    def test_native_source_and_plate_identity_fail_closed_before_output(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.build_texture_cleanplates import build
        with TemporaryDirectory() as temp:
            root=Path(temp);recipe,decoder=self.fixture(root)
            # Fixture's selected native atlas is transparent; exact patch replay
            # is zero RGBA and still uses the real native decoder and crop hash.
            result=build(recipe,root,root/'replay',decoder)
            self.assertEqual(len(result['cases']),1)
            for field in ('source','mask','plate'):
                bad=copy.deepcopy(recipe);bad['cases'][0][field]['sha256']='0'*64
                out=root/('bad-'+field)
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'SHA256'):
                    build(bad,root,out,decoder)
                self.assertFalse(out.exists())
            for field,value in (('source_rgba_sha256','0'*64),('tiled_sha256','0'*64),('dimensions',[64,64]),('plate_size',[64,64])):
                bad=copy.deepcopy(recipe);bad['cases'][0][field]=value;out=root/('bad-'+field)
                with self.subTest(field=field),self.assertRaises(ValueError):build(bad,root,out,decoder)
                self.assertFalse(out.exists())

    def test_reserved_casefold_and_ancestor_outputs_are_rejected_before_publication(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.build_texture_cleanplates import build
        with TemporaryDirectory() as temp:
            root=Path(temp);recipe,decoder=self.fixture(root)
            for names in (['manifest.json'],['Manifest.json'],['manifest.json/x.png'],
                          ['a.png','A.PNG'],['a.png','a.png/b.png'],['a.PNG/b.png','A.png'],
                          ['a.png','a.png+z.png','a.png/b.png']):
                bad=copy.deepcopy(recipe);base=bad['cases'][0];bad['cases']=[]
                for i,name in enumerate(names):
                    case=copy.deepcopy(base);case['id']=str(i);case['patch']['path']=name;bad['cases'].append(case)
                out=root/'rejected'
                with self.subTest(names=names),self.assertRaises(ValueError):build(bad,root,out,decoder)
                self.assertFalse(out.exists())

    def test_same_output_preflight_protects_sparse_interpolation_replay(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.build_sparse_texture_repairs import build
        with TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ('manifest.json','Manifest.json','manifest.json/patch.png','bad?.png','AUX.png'):
                recipe=dict(schema_version=1,kind='sparse-texture-repair-v1',
                            method='premultiplied-front-laplace-v1',hidden_artwork='reconstruction-not-original',
                            cases=[dict(patch=dict(path=name,sha256='0'*64))])
                out=root/'rejected'
                with self.subTest(name=name),self.assertRaisesRegex(ValueError,'output path'):
                    build(recipe,root,out,None)
                self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
