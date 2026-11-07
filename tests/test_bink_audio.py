"""Synthetic BIKi packet fixtures; no proprietary media or audio codecs needed."""
import copy
import hashlib
import struct
import unittest

import numpy as np
from PIL import Image

from tools.bink_audio import inspect, strip_audio, replace_video, audio_fingerprint
from tools.video_caption import bink_header
from tools.worldmap_caption import temporal_static_mask


def fixture(*, videos=(b'abcd', b'123456'), tracks=2, numerator=30, denominator=1):
    count = len(videos)
    metadata = (struct.pack('<'+'I'*tracks, *([64]*tracks))
        + b''.join(struct.pack('<HH', 48000, 0x5000) for _ in range(tracks))
        + struct.pack('<'+'I'*tracks, *range(tracks)))
    payloads = []
    for index, video in enumerate(videos):
        audio = [struct.pack('<I', 6) + struct.pack('<I', 64) + bytes([index & 255, track]) for track in range(tracks)]
        payloads.append(b''.join(audio) + video)
    offsets = [44+12*tracks+4*(count+1)]
    for payload in payloads:
        offsets.append(offsets[-1]+len(payload))
    header = b'BIKi'+struct.pack('<10I', offsets[-1]-8, count, max(map(len, payloads)), count,
                                8, 6, numerator, denominator, 0, tracks)
    return header+metadata+struct.pack('<'+'I'*(count+1), *[x | int(i<count) for i, x in enumerate(offsets)])+b''.join(payloads)


def field(data, offset, value):
    result=bytearray(data)
    struct.pack_into('<I', result, offset, value)
    return bytes(result)


class BinkAudioTests(unittest.TestCase):
    def test_reads_audio_and_video_packets_without_decoding(self):
        parsed=inspect(fixture())
        self.assertEqual(parsed['header']['audio_tracks'], 2)
        self.assertEqual([f['video'] for f in parsed['frames']], [b'abcd', b'123456'])
        self.assertEqual(parsed['frames'][1]['audio'][1], struct.pack('<II', 6, 64)+b'\1\1')

    def test_source_identity_strip_remux_is_byte_exact(self):
        source=fixture()
        silent=strip_audio(source)
        self.assertEqual(bink_header(silent)['audio_tracks'], 0)
        self.assertEqual(replace_video(source, silent), source)
        self.assertEqual(strip_audio(silent), silent)

    def test_replacement_keeps_all_audio_metadata_and_each_frame_packet(self):
        source=fixture()
        replacement=fixture(videos=(b'VIDEO!',b'FRAMES!!'), tracks=0)
        result=inspect(replace_video(source,replacement))
        self.assertEqual(audio_fingerprint(result), audio_fingerprint(inspect(source)))
        self.assertEqual([f['video'] for f in result['frames']], [b'VIDEO!',b'FRAMES!!'])
        self.assertEqual(strip_audio(replace_video(source,replacement)),replacement)

    def test_rejects_geometry_timing_frame_count_or_audio_in_replacement(self):
        source=fixture()
        candidates=[fixture(tracks=1), fixture(tracks=0,numerator=60),
                    fixture(tracks=0,videos=(b'xx',)), field(fixture(tracks=0),20,9)]
        for candidate in candidates:
            with self.subTest(candidate=candidate[:44]),self.assertRaises(ValueError):
                replace_video(source,candidate)

    def test_rejects_unknown_revision_audio_count_and_flags(self):
        good=fixture()
        for candidate in (b'BIKk'+good[4:], good[:45], field(good,36,1), field(good,40,9),
                          field(good,8,601),field(good,4,len(good)-7)):
            with self.subTest(header=candidate[:44]),self.assertRaises(ValueError):
                inspect(candidate)

    def test_rejects_corrupt_frame_tables_and_audio_lengths(self):
        good=fixture()
        table=44+24
        first=struct.unpack_from('<I',good,table)[0]&~1
        for candidate in (field(good,table,2),field(good,table+4,first),
                          field(good,first,len(good)),field(good,12,1)):
            with self.subTest(header=candidate[:44]),self.assertRaises(ValueError):
                inspect(candidate)

    def test_rejects_metadata_rate_flags_and_duplicate_track_ids(self):
        good=fixture()
        for offset,value in ((44,0),(52,0),(52,(0x8000<<16)|48000),(64,0)):
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                inspect(field(good,offset,value))

    def test_eight_audio_tracks_are_supported(self):
        source=fixture(tracks=8)
        self.assertEqual(inspect(source)['header']['audio_tracks'],8)
        self.assertEqual(replace_video(source,strip_audio(source)),source)


class TemporalStaticMaskTests(unittest.TestCase):
    def frames(self):
        result=[]
        for n in (0,20,40):
            array=np.full((12,16,3),n,dtype=np.uint8)
            array[4:7,5:8]=[220,170,50]  # Native tinted glyph, not neutral white.
            result.append(Image.fromarray(array))
        return result

    def specification(self):
        mask=np.zeros((8,12),bool)
        mask[2:5,3:6]=True
        return dict(minimum_brightness=110,maximum_range=28,dilation=0,
                    mask_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),pixels=9)

    def test_keeps_static_coloured_glyphs_and_excludes_moving_background(self):
        mask=temporal_static_mask(self.frames(),[2,2,12,8],self.specification(),3)
        self.assertEqual(int(mask.sum()),9)
        self.assertTrue(mask[2:5,3:6].all())

    def test_rejects_short_extra_frame_sequences_and_geometry(self):
        for frames,rect,count in ((self.frames()[:2],[2,2,12,8],3),
                (self.frames(),[2,2,12,8],2),(self.frames(),[12,2,12,8],3)):
            with self.assertRaises(ValueError):
                temporal_static_mask(frames,rect,self.specification(),count)

    def test_exact_mask_hash_and_pixel_count_are_guarded(self):
        for key,value in (('mask_sha256','0'*64),('pixels',8),('dilation',9),('unknown',1)):
            spec=self.specification();spec[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                temporal_static_mask(self.frames(),[2,2,12,8],spec,3)


if __name__=='__main__':unittest.main()
