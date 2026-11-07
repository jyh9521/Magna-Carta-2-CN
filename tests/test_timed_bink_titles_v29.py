"""Self-authored pixel and container fixtures for frame-indexed movie captions."""
import copy
import unittest

import numpy as np
from PIL import Image

from tools.bink_audio import inspect,replace_video,strip_audio
from tools.build_video_captions import composite,frame_count_limit,encoded_size_limit,encoder_time_limit,scratch_space_required
from tools.video_caption import bink_header,preserve_timing
from tools.video_title_caption import VideoTitleCaption,reference_window
from test_video_caption import bink_fixture
from test_bink_audio import fixture


class TimedCaptionTests(unittest.TestCase):
    def operation(self, alpha=None):
        mask=np.zeros((6,8),bool);mask[2:4,2:5]=True
        layer=Image.new('RGBA',(20,14));layer.paste((220,90,70,255),(6,5,8,7))
        return VideoTitleCaption([3,2,8,6],mask,layer,alpha or [0,128,255,0],4)

    def source(self):
        frame=Image.new('RGB',(20,14),(15,30,45))
        frame.paste((240,240,240),(5,4,8,6))
        return frame

    def test_inactive_frames_are_byte_identical_and_input_is_never_mutated(self):
        op=self.operation();source=self.source();before=source.tobytes()
        for index in (0,3):
            result=op.apply(source,index)
            self.assertEqual(result.tobytes(),before)
            self.assertIsNot(result,source)
        op.apply(source,2)
        self.assertEqual(source.tobytes(),before)

    def test_explicit_per_frame_alpha_controls_the_fade_without_shifting_the_clip(self):
        op=self.operation();source=self.source()
        half=op.apply(source,1);full=op.apply(source,2)
        self.assertEqual(full.getpixel((6,5)),(220,90,70))
        self.assertEqual(half.getpixel((6,5)),(118,60,58))
        self.assertEqual(op.proof()['first_active_frame'],1)
        self.assertEqual(op.proof()['last_active_frame_exclusive'],3)
        self.assertEqual(op.proof()['active_frames'],2)

    def test_native_wings_and_all_pixels_outside_declared_support_are_unchanged(self):
        op=self.operation();source=self.source();before=np.asarray(source)
        result=np.asarray(op.apply(source,2));support=np.zeros((14,20),bool)
        support[2:8,3:11]=op.mask;support|=np.asarray(op.layer.getchannel('A'))>0
        self.assertTrue(np.array_equal(before[~support],result[~support]))
        self.assertEqual(op.apply(source,2).getpixel((2,4)),source.getpixel((2,4)))

    def test_shared_compositor_dispatches_timed_operation_and_preserves_inactive_source(self):
        op=self.operation();source=self.source();support=np.zeros((14,20),bool)
        support[2:8,3:11]=op.mask;support|=np.asarray(op.layer.getchannel('A'))>0
        empty=Image.new('RGBA',source.size)
        self.assertEqual(composite(source,[op],empty,support,0).tobytes(),source.tobytes())
        self.assertEqual(composite(source,[op],empty,support,2).tobytes(),op.apply(source,2).tobytes())

    def test_bad_curves_indices_and_canvas_are_rejected(self):
        for alpha in ([0,0,0,0],[255], [0,1.0,255,0], [0,True,255,0], [0,-1,255,0], [0,256,255,0]):
            with self.subTest(alpha=alpha),self.assertRaises(ValueError):
                self.operation(alpha)
        op=self.operation()
        for index in (-1,4,True,1.0):
            with self.subTest(index=index),self.assertRaises(ValueError):
                op.apply(self.source(),index)
        with self.assertRaises(ValueError):op.apply(Image.new('RGB',(21,14)),1)

    def test_empty_glyph_layers_and_mask_geometry_mismatches_fail(self):
        mask=np.ones((6,8),bool)
        with self.assertRaises(ValueError):VideoTitleCaption([3,2,8,6],mask,Image.new('RGBA',(20,14)),[0,1],2)
        with self.assertRaises(ValueError):VideoTitleCaption([3,2,8,6],mask.astype('uint8'),Image.new('RGBA',(20,14)),[0,1],2)

    def test_reference_windows_are_exact_and_bounded(self):
        self.assertEqual(reference_window({},354),[0,354])
        self.assertEqual(reference_window(dict(reference_window=[210,255]),354),[210,255])
        for window in (None,[0,0],[-1,20],[20,10],[0,355],[True,20],[0,1.0],'0:20'):
            with self.subTest(window=window),self.assertRaises(ValueError):
                reference_window(dict(reference_window=window),354)


class LongMovieOptInTests(unittest.TestCase):
    def test_legacy_silent_limit_stays_600_and_long_clip_requires_an_explicit_limit(self):
        long=bink_fixture(payloads=(b'xx',)*601)
        with self.assertRaises(ValueError):bink_header(long)
        self.assertEqual(bink_header(long,maximum_frames=601)['frames'],601)
        self.assertEqual(preserve_timing(long,long,maximum_frames=601),long)
        self.assertEqual(frame_count_limit({}),600)
        self.assertEqual(frame_count_limit(dict(maximum_frames=6144)),6144)
        for value in (False,0,-1,6145,600.0):
            with self.subTest(value=value),self.assertRaises(ValueError):
                frame_count_limit(dict(maximum_frames=value))

    def test_long_sound_container_round_trip_retains_each_original_audio_packet(self):
        original=fixture(videos=(b'xx',)*601)
        self.assertEqual(inspect(original)['header']['frames'],601)
        self.assertEqual(replace_video(original,strip_audio(original)),original)

    def test_long_movie_size_cap_is_explicit_and_finite(self):
        self.assertEqual(encoded_size_limit({}),64*1024*1024)
        self.assertEqual(encoded_size_limit(dict(maximum_encoded_bytes=512*1024*1024)),512*1024*1024)
        with self.assertRaises(ValueError):encoded_size_limit(dict(maximum_encoded_bytes=512*1024*1024+1))

    def test_long_encoder_timeout_is_explicit_and_bounded(self):
        self.assertEqual(encoder_time_limit({}),180)
        self.assertEqual(encoder_time_limit(dict(encoder_timeout_seconds=600)),600)
        for value in (False,0,-1,1801):
            with self.subTest(value=value),self.assertRaises(ValueError):
                encoder_time_limit(dict(encoder_timeout_seconds=value))

    def test_raw_avi_bytes_plus_headroom_are_reserved_before_long_clip_writes(self):
        header=dict(width=1280,height=720,frames=2032)
        self.assertEqual(scratch_space_required(header,{}),8*1024**3)
        policy=dict(scratch_reserve_bytes=8*1024**3,minimum_start_free_bytes=16*1024**3)
        self.assertEqual(scratch_space_required(header,policy),16*1024**3)
        policy['minimum_start_free_bytes']=0
        self.assertEqual(scratch_space_required(header,policy),1280*720*3*2032+128*1024**2+8*1024**3)
        with self.assertRaises(ValueError):scratch_space_required(header,dict(scratch_reserve_bytes=False))


if __name__=='__main__':unittest.main()
