"""Container and input-scope fixtures for source-identical movie prefixes."""
import copy
import struct
import unittest

from tools.bink_audio import inspect, strip_audio, replace_video_tail, audio_fingerprint, trim_silent_guard_frames
from tools.build_video_captions import encoding_first_frame, scratch_space_required, encoding_guard_frames
from test_bink_audio import fixture, field


class KeyframeTailTests(unittest.TestCase):
    def source(self):
        return fixture(videos=(b'abcd', b'efgh', b'ijkl', b'mnop'))

    def test_prefix_packets_and_all_audio_remain_byte_identical(self):
        original = self.source()
        tail = strip_audio(fixture(videos=(b'NEW1', b'NEW2')))
        result = inspect(replace_video_tail(original, tail, 2))
        source = inspect(original)
        self.assertEqual(result['header'], source['header'])
        self.assertEqual(result['frames'][:2], source['frames'][:2])
        self.assertEqual([f['video'] for f in result['frames'][2:]], [b'NEW1', b'NEW2'])
        self.assertEqual(audio_fingerprint(result), audio_fingerprint(source))
        self.assertTrue(result['frames'][2]['keyframe'])

    def test_silent_prefix_and_near_integer_encoder_rate_use_source_timing(self):
        original = strip_audio(fixture(videos=(b'xx',) * 4, numerator=10000000, denominator=333333))
        tail = strip_audio(fixture(videos=(b'yy',) * 2))
        result = inspect(replace_video_tail(original, tail, 2))
        self.assertEqual(result['header'], inspect(original)['header'])
        self.assertEqual(result['frames'][:2], inspect(original)['frames'][:2])

    def test_bad_bounds_geometry_audio_count_or_rate_fail(self):
        source = self.source()
        tail = strip_audio(fixture(videos=(b'xx', b'yy')))
        for first in (True, -1, 4, 2.0):
            with self.subTest(first=first), self.assertRaises(ValueError):
                replace_video_tail(source, tail, first)
        for bad in (field(tail, 20, 16), field(tail, 24, 12), field(tail, 28, 24),
                    fixture(videos=(b'xx', b'yy')), strip_audio(fixture(videos=(b'xx',)))):
            with self.subTest(tail=len(bad)), self.assertRaises(ValueError):
                replace_video_tail(source, bad, 2)

    def test_tail_without_independent_initial_keyframe_fails(self):
        tail = bytearray(strip_audio(fixture(videos=(b'xx', b'yy'))))
        struct.pack_into('<I', tail, 44, struct.unpack_from('<I', tail, 44)[0] & ~1)
        with self.assertRaisesRegex(ValueError, 'keyframe'):
            replace_video_tail(self.source(), tail, 2)

    def test_opt_in_requires_all_earlier_frames_to_be_inactive_and_repaired(self):
        entry = dict(encode_from_frame=2, captions=[dict(frame_alpha=[0, 0, 128, 255],
                     erase=dict(frame_repairs=dict(method='sparse-frame-rgba-v1', records=[])))])
        self.assertEqual(encoding_first_frame(entry, 4), 2)
        self.assertEqual(encoding_first_frame({}, 4), 0)
        for change in ('early-active', 'missing-repairs', 'missing-curve'):
            bad = copy.deepcopy(entry)
            if change == 'early-active':bad['captions'][0]['frame_alpha'][1] = 1
            if change == 'missing-repairs':bad['captions'][0]['erase'] = {}
            if change == 'missing-curve':del bad['captions'][0]['frame_alpha']
            with self.subTest(change=change), self.assertRaises(ValueError):
                encoding_first_frame(bad, 4)

    def test_explicit_scratch_budget_counts_only_encoded_tail(self):
        entry = dict(encode_from_frame=2, captions=[dict(frame_alpha=[0, 0, 255, 255],
                     erase=dict(frame_repairs={}))], scratch_reserve_bytes=0, minimum_start_free_bytes=0)
        self.assertEqual(scratch_space_required(dict(width=1280, height=720, frames=4), entry),
                         1280 * 720 * 3 * 2 + 128 * 1024 ** 2)

    def test_guard_trimming_retains_every_intended_packet_and_source_rate(self):
        encoded=strip_audio(fixture(videos=(b'aa',b'bb',b'cc',b'cc')))
        trimmed=inspect(trim_silent_guard_frames(encoded,3,1))
        self.assertEqual(trimmed['header']['frames'],3)
        self.assertEqual(trimmed['frames'],inspect(encoded)['frames'][:3])
        self.assertEqual(trim_silent_guard_frames(encoded,4,1),encoded)
        for expected,guard in [(5,1),(2,1),(3,0),(True,1),(3,True),(3,3)]:
            with self.subTest(expected=expected,guard=guard),self.assertRaises(ValueError):
                trim_silent_guard_frames(encoded,expected,guard)
        with self.assertRaises(ValueError):trim_silent_guard_frames(fixture(videos=(b'aa',)*4),3,1)

    def test_guard_opt_in_is_bounded_and_reserved_in_scratch_budget(self):
        self.assertEqual(encoding_guard_frames({},4),0)
        self.assertEqual(encoding_guard_frames(dict(encoder_guard_frames=1),4),1)
        for value in [True,-1,3,1.0]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                encoding_guard_frames(dict(encoder_guard_frames=value),4)
        with self.assertRaises(ValueError):encoding_guard_frames(dict(encoder_guard_frames=1),6144)
        entry=dict(encoder_guard_frames=1,scratch_reserve_bytes=0,minimum_start_free_bytes=0)
        self.assertEqual(scratch_space_required(dict(width=1280,height=720,frames=4),entry),
                         1280*720*3*5+128*1024**2)


if __name__ == '__main__':
    unittest.main()
