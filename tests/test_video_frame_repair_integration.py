"""Synthetic codec-free integration of source-style titles and sparse repairs."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from tools.build_video_captions import (composite,frame_repair_metadata,
    prepare_frame_repairs,prepare_layers,render_caption_layer)
from tools.video_frame_repairs import VideoFrameRepairs
from tools.video_title_caption import VideoTitleCaption,render_title_layer
from test_texture_render_windows import owned_font
from test_video_caption import bink_fixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class VideoFrameRepairIntegrationTests(unittest.TestCase):
    def fixture(self,root,alpha=None):
        canvas=(128,80);rect=[40,30,48,24]
        mask=np.zeros((24,48),bool);mask[4:20,9:12]=True;mask[10:13,9:34]=True
        yy,xx=np.indices((80,128));frames=[];clean=[];records=[]
        alpha=[0,128,255,0] if alpha is None else alpha
        folder=root/'patches';folder.mkdir(exist_ok=True)
        for index in range(4):
            grid=((xx+index)//2+yy//2)%2
            native=np.stack((25+100*grid,40+100*grid,60+100*grid),axis=2).astype('uint8')
            clean.append(Image.fromarray(native))
            burned=native.copy();burned[30:54,40:88][mask]=(245,245,245)
            frames.append(Image.fromarray(burned))
            if alpha[index]:
                rgba=np.zeros((24,48,4),'uint8')
                rgba[:,:,:3][mask]=native[30:54,40:88][mask];rgba[:,:,3][mask]=255
                path=folder/(str(index)+'.png');Image.fromarray(rgba).save(path)
                records.append(dict(index=index,source_crop_sha256=sha(burned[30:54,40:88].tobytes()),
                    patch=dict(path=path.relative_to(root).as_posix(),sha256=sha(path.read_bytes()))))
        font=owned_font();font_path=root/'owned.ttf';font_path.write_bytes(font)
        source_root=root/'sources';source_root.mkdir(exist_ok=True)
        raw=bink_fixture(payloads=(b'xx',)*4,width=128,height=80,numerator=30,denominator=1)
        (source_root/'owned.bik').write_bytes(raw)
        appearance=dict(kind='source-style-v1',ink_box=[24,25,80,20],align='center',
            gradient=[[0,[220,141,142,255]],[1000,[255,250,224,255]]],
            outline=[8,5,5,245],outline_width=.75,glow=[0,0,0,0],glow_radius=0,
            shadow=[0,0,0,210],shadow_offset=[1,1],shadow_radius=.5,
            italic=0,tracking=3,weight=0,motion=0)
        caption=dict(text='AB',font='owned',font_size=18,appearance=appearance,frame_alpha=alpha,
            erase=dict(rect=rect,threshold=200,radius=0,
                frame_repairs=dict(method='sparse-frame-rgba-v1',records=records)))
        entry=dict(id='owned',source=dict(file='owned.bik',sha256=sha(raw),size=len(raw),
            first_rgb_sha256=sha(frames[0].tobytes())),captions=[caption])
        plan=dict(fonts=dict(owned=dict(path='owned.ttf',sha256=sha(font))))
        return dict(plan=plan,entry=entry,caption=caption,root=root,source_root=source_root,
                    frames=frames,clean=clean,mask=mask,font=font,canvas=canvas)

    def prepare(self,fixture):
        with patch('tools.build_video_captions.first_frame',return_value=fixture['frames'][0]):
            return prepare_layers(fixture['plan'],fixture['entry'],fixture['root'],fixture['source_root'],'UNUSED')

    def rewrite_patch(self,fixture,record_index,image,format='PNG',**options):
        record=fixture['caption']['erase']['frame_repairs']['records'][record_index]
        path=fixture['root']/record['patch']['path'];image.save(path,format=format,**options)
        record['patch']['sha256']=sha(path.read_bytes())

    def test_prepare_and_composite_use_source_style_and_explicit_repairs(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));source,raw,header,operations,layer,changed,proofs=self.prepare(fixture)
            self.assertEqual(header['frames'],4)
            self.assertEqual(source,(fixture['source_root']/'owned.bik').resolve())
            self.assertEqual(raw,source.read_bytes())
            self.assertIsNone(layer.getbbox())
            operation=operations[0]
            self.assertIsInstance(operation,VideoTitleCaption)
            self.assertIsInstance(operation.repairs,VideoFrameRepairs)
            self.assertTrue(np.array_equal(operation.mask,fixture['mask']))
            rendered,expected_proof=render_title_layer(fixture['font'],'AB',fixture['canvas'],font_size=18,
                appearance=fixture['caption']['appearance'])
            self.assertEqual(operation.layer.tobytes(),rendered.tobytes())
            self.assertEqual(proofs[0]['rgba_sha256'],expected_proof['rgba_sha256'])
            self.assertEqual(proofs[0]['render_method'],'source-style-v1')
            self.assertEqual(proofs[0]['timed_caption']['background_method'],'sparse-frame-rgba-v1')
            self.assertIs(proofs[0]['timed_caption']['frame_repairs']['artistic_acceptance'],False)
            with patch('tools.video_caption.restore_masked',side_effect=AssertionError('legacy restoration used')):
                for index,frame in enumerate(fixture['frames']):
                    before=frame.tobytes();alpha=fixture['caption']['frame_alpha'][index]
                    result=composite(frame,operations,layer,changed,index)
                    if alpha:
                        title=rendered.copy()
                        title.putalpha(title.getchannel('A').point(lambda value:round(value*alpha/255)))
                        expected=Image.alpha_composite(fixture['clean'][index].convert('RGBA'),title).convert('RGB')
                    else:expected=frame
                    self.assertEqual(result.tobytes(),expected.tobytes())
                    self.assertEqual(frame.tobytes(),before)
                    self.assertTrue(np.array_equal(np.asarray(result)[~changed],np.asarray(frame)[~changed]))

    def test_all_frames_may_be_explicitly_active_without_implicit_static_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory),[255]*4)
            _,_,_,operations,layer,changed,_=self.prepare(fixture)
            self.assertEqual(operations[0].repairs.active_frames,(0,1,2,3))
            for index,frame in enumerate(fixture['frames']):
                result=composite(frame,operations,layer,changed,index)
                self.assertNotEqual(result.tobytes(),frame.tobytes())

    def test_bad_source_crop_hash_rejects_at_composite_without_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory))
            fixture['caption']['erase']['frame_repairs']['records'][0]['source_crop_sha256']='0'*64
            _,_,_,operations,layer,changed,_=self.prepare(fixture)
            frame=fixture['frames'][1];before=frame.tobytes()
            with patch('tools.video_caption.restore_masked',side_effect=AssertionError('fallback')):
                with self.assertRaisesRegex(ValueError,'source crop SHA-256 mismatch'):
                    composite(frame,operations,layer,changed,1)
            self.assertEqual(frame.tobytes(),before)

    def test_frame_repair_contract_must_match_title_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));operation=self.prepare(fixture)[3][0]
            mask=operation.mask.copy();mask[0,0]=True
            cases=[dict(rect=[41,30,48,24]),dict(mask=mask),dict(layer=Image.new('RGBA',(129,80))),
                   dict(frame_alpha=[255,128,255,0]),dict(frame_alpha=[0,128,255,0,0],expected_frames=5),
                   dict(repairs=object())]
            for case in cases:
                args=dict(rect=operation.rect,mask=operation.mask,layer=operation.layer,
                          frame_alpha=[0,128,255,0],expected_frames=4,repairs=operation.repairs)
                args.update(case)
                with self.subTest(case=list(case)),self.assertRaises(ValueError):
                    VideoTitleCaption(**args)

    def test_background_only_repairs_outlive_the_visible_caption(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory))
            fixture['caption']['frame_alpha']=[0,255,0,0]
            _,_,_,operations,layer,changed,proofs=self.prepare(fixture)
            operation=operations[0]
            self.assertEqual(operation.repairs.active_frames,(1,2))
            self.assertEqual(composite(fixture['frames'][2],operations,layer,changed,2).tobytes(),
                             fixture['clean'][2].tobytes())
            for index in (0,3):
                self.assertEqual(composite(fixture['frames'][index],operations,layer,changed,index).tobytes(),
                                 fixture['frames'][index].tobytes())
            proof=proofs[0]['timed_caption']
            self.assertEqual(proof['active_frames'],2)
            self.assertEqual(proof['text_active_frames'],1)
            self.assertEqual(proof['background_only_frames'],1)
            self.assertEqual(proof['last_active_frame_exclusive'],3)
            self.assertEqual(proof['last_text_active_frame_exclusive'],2)

    def test_repair_superset_still_requires_every_positive_caption_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory))
            caption=copy.deepcopy(fixture['caption'])
            caption['erase']['frame_repairs']['records'][1]['index']=3
            with (patch('tools.build_video_captions.locked_file',side_effect=AssertionError('asset read')),
                    patch('PIL.Image.open',side_effect=AssertionError('PNG opened')),
                    self.assertRaisesRegex(ValueError,'every active text frame')):
                frame_repair_metadata(caption,4,fixture['canvas'],fixture['root'])

    def test_missing_frame_alpha_rejects_before_frame_decode_or_png_open(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));del fixture['caption']['frame_alpha']
            with (patch('tools.build_video_captions.first_frame',side_effect=AssertionError('decoder called')),
                    patch('PIL.Image.open',side_effect=AssertionError('PNG opened'))):
                with self.assertRaisesRegex(ValueError,'explicit frame_alpha'):
                    prepare_layers(fixture['plan'],fixture['entry'],fixture['root'],fixture['source_root'],'UNUSED')

    def test_missing_or_ambiguous_typography_fields_never_choose_legacy_silently(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));caption=fixture['caption']
            cases=[{k:v for k,v in caption.items() if k!='appearance'},
                   {k:v for k,v in caption.items() if k!='font_size'},
                   {**caption,'style':{}},{**caption,'font_size':True},{**caption,'appearance':None}]
            for value in cases:
                with self.subTest(keys=list(value)),self.assertRaises(ValueError):
                    render_caption_layer(value,fixture['font'],fixture['canvas'])

    def test_legacy_title_renderer_and_research_background_remain_explicit(self):
        from tools.video_caption import render_layer
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));caption=fixture['caption']
            del caption['appearance'];del caption['font_size'];del caption['erase']['frame_repairs']
            caption['style']=dict(rect=[24,25,80,20],font_size=18,line_height=20,align='center',
                gradient=[[0,[220,141,142,255]],[1000,[255,250,224,255]]],outline=[0,0,0,255],
                outline_width=1,shadow=[0,0,0,0],shadow_offset=[0,0],shadow_radius=0,glow=[0,0,0,0],glow_radius=0)
            expected,_=render_layer('AB',fixture['font'],fixture['canvas'],caption['style'])
            _,_,_,operations,_,_,proofs=self.prepare(fixture)
            self.assertEqual(operations[0].layer.tobytes(),expected.tobytes())
            self.assertIsNone(operations[0].repairs)
            self.assertEqual(proofs[0]['timed_caption']['background_method'],'legacy-harmonic-rgb-v1')

    def test_schema_indices_paths_and_hashes_preflight_all_records_before_png_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));base=fixture['caption']
            def altered(change):
                result=copy.deepcopy(base);change(result['erase']['frame_repairs']);return result
            cases=[altered(lambda spec:spec.update(method='unknown')),
                   altered(lambda spec:spec.update(extra=True)),altered(lambda spec:spec.pop('method')),
                   altered(lambda spec:spec.update(records=None)),altered(lambda spec:spec.update(records=[])),
                   altered(lambda spec:spec['records'][1].update(index=1)),
                   altered(lambda spec:spec['records'][1].update(index=0)),
                   altered(lambda spec:spec['records'][1].update(index=True)),
                   altered(lambda spec:spec['records'][1].update(index=2.0)),
                   altered(lambda spec:spec['records'][1].update(extra=True)),
                   altered(lambda spec:spec['records'][1].pop('source_crop_sha256')),
                   altered(lambda spec:spec['records'][1].update(source_crop_sha256='x'*64)),
                   altered(lambda spec:spec['records'][1]['patch'].update(sha256='0'*63)),
                   altered(lambda spec:spec['records'][1]['patch'].update(extra=True)),
                   altered(lambda spec:spec['records'][1].update(patch=None)),
                   altered(lambda spec:spec['records'][1]['patch'].update(path='../outside.png')),
                   altered(lambda spec:spec['records'][1]['patch'].update(path='patches\\2.png')),
                   altered(lambda spec:spec['records'][1]['patch'].update(path='patches/./2.png')),
                   altered(lambda spec:spec['records'][1]['patch'].update(path='patches/2.jpg')),
                   altered(lambda spec:spec['records'][1]['patch'].update(path='patches/1.png')),
                   altered(lambda spec:spec['records'][1]['patch'].update(path='PATCHES/1.PNG'))]
            for caption in cases:
                with (self.subTest(spec=repr(caption['erase']['frame_repairs'])[:180]),
                        patch('tools.build_video_captions.locked_file',side_effect=AssertionError('PNG read')),
                        patch('PIL.Image.open',side_effect=AssertionError('PNG opened')),
                        self.assertRaises(ValueError)):
                    frame_repair_metadata(caption,4,fixture['canvas'],fixture['root'])

    def test_repeated_crop_and_patch_content_hashes_are_valid_at_distinct_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));records=fixture['caption']['erase']['frame_repairs']['records']
            records[1]['source_crop_sha256']=records[0]['source_crop_sha256']
            first=(fixture['root']/records[0]['patch']['path']).read_bytes()
            (fixture['root']/records[1]['patch']['path']).write_bytes(first)
            records[1]['patch']['sha256']=records[0]['patch']['sha256']
            metadata=frame_repair_metadata(fixture['caption'],4,fixture['canvas'],fixture['root'])
            repairs=prepare_frame_repairs(metadata,fixture['caption'],fixture['mask'],4,fixture['canvas'])
            self.assertEqual(repairs.apply(fixture['frames'][1],1).tobytes(),
                             repairs.apply(fixture['frames'][1],2).tobytes())

    def test_aggregate_patch_size_and_record_count_reject_before_any_file_read(self):
        for count in (129,6145):
            caption=dict(frame_alpha=[255]*count,erase=dict(rect=[0,0,512,512],frame_repairs=dict(
                method='sparse-frame-rgba-v1',records=[dict(index=i,source_crop_sha256='0'*64,
                    patch=dict(path=str(i)+'.png',sha256='0'*64)) for i in range(count)])))
            with (self.subTest(count=count),patch('PIL.Image.open',side_effect=AssertionError('opened')),
                    self.assertRaises(ValueError)):
                frame_repair_metadata(caption,count,(512,512),Path.cwd())

    def test_png_hash_tampering_rejects_without_any_reconstruction(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));record=fixture['caption']['erase']['frame_repairs']['records'][0]
            path=fixture['root']/record['patch']['path'];path.write_bytes(path.read_bytes()+b'changed')
            with patch('tools.video_caption.restore_masked',side_effect=AssertionError('fallback')):
                with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
                    self.prepare(fixture)

    def test_png_format_mode_geometry_and_animation_are_not_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory))
            cases=[(Image.new('RGB',(48,24)),'PNG',{}),(Image.new('RGBA',(49,24)),'PNG',{}),
                   (Image.new('RGBA',(48,24)),'BMP',{}),
                   (Image.new('RGBA',(48,24)),'PNG',dict(save_all=True,
                       append_images=[Image.new('RGBA',(48,24),(1,2,3,255))],duration=100,loop=0))]
            for image,format,options in cases:
                self.rewrite_patch(fixture,0,image,format,**options)
                with (self.subTest(mode=image.mode,size=image.size,format=format,animated=bool(options)),
                        self.assertRaisesRegex(ValueError,'RGBA PNG')):
                    self.prepare(fixture)

    def test_png_hidden_rgb_and_inexact_alpha_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));record=fixture['caption']['erase']['frame_repairs']['records'][0]
            with Image.open(fixture['root']/record['patch']['path']) as image:original=np.asarray(image).copy()
            for position,channel,value in (((0,0),0,1),((0,0),3,1),((9,4),3,254)):
                rgba=original.copy();x,y=position;rgba[y,x,channel]=value
                self.rewrite_patch(fixture,0,Image.fromarray(rgba))
                with self.subTest(position=position,channel=channel),self.assertRaisesRegex(ValueError,'owned mask'):
                    self.prepare(fixture)

    def test_oversized_encoded_png_rejects_during_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=self.fixture(Path(directory));record=fixture['caption']['erase']['frame_repairs']['records'][0]
            path=fixture['root']/record['patch']['path'];path.write_bytes(b'x'*(48*24*4+64*1024+1))
            record['patch']['sha256']=sha(path.read_bytes())
            with patch('PIL.Image.open',side_effect=AssertionError('PNG opened')):
                with self.assertRaisesRegex(ValueError,'file size bound'):
                    frame_repair_metadata(fixture['caption'],4,fixture['canvas'],fixture['root'])

    def test_repair_path_cannot_resolve_outside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            project=root/'project';project.mkdir();fixture=self.fixture(project)
            outside=root/'outside.png';outside.write_bytes(b'owned')
            alias=project/'outside-link.png';original_resolve=Path.resolve
            # Model a symlink/junction resolution without requiring Windows'
            # optional symlink privilege in this otherwise codec-free fixture.
            def resolve(path,*args,**kwargs):
                return original_resolve(outside if path==alias else path,*args,**kwargs)
            fixture['caption']['erase']['frame_repairs']['records'][0]['patch']['path']='outside-link.png'
            with patch.object(Path,'resolve',autospec=True,side_effect=resolve):
                with self.assertRaisesRegex(ValueError,'escapes root'):
                    frame_repair_metadata(fixture['caption'],4,fixture['canvas'],project)


if __name__=='__main__':unittest.main()
