"""Owned thin-stroke fixture reproduces dark breaks in the legacy BC3 fit."""
import random
import unittest
from tools.bc3_rgb_fit import encode_fitted_rgba_block
from tools.texture_overlay import encode_rgba_block, overlay_profile_regions, overlay_regions
from tools.texture_layout import unit_layout, overlay_rect, decode_texture
from tools.ue3_textures import decode_dxt5
from tools.ue3_package import FormatError


def strokes():
    colors = [(255,235,220), (255,231,132), (255,207,123), (250,160,123)]
    return bytes(v for y in range(4) for x in range(4)
                 for v in (colors[y]+(255,) if x in (1,2) else (8,8,10,245)))


def error(source, block):
    decoded = decode_dxt5(block,4,4)
    return sum(source[i+3]**2 * sum((source[i+k]-decoded[i+k])**2 for k in range(3))
               for i in range(0,64,4))


class FittedRGBTests(unittest.TestCase):
    def test_thin_strokes_do_not_drop_into_the_dark_palette_entry(self):
        source=strokes(); old=encode_rgba_block(source); new=encode_fitted_rgba_block(source)
        a=decode_dxt5(old,4,4); b=decode_dxt5(new,4,4)
        foreground=[(y*4+x)*4 for y in range(4) for x in (1,2)]
        self.assertLess(min(a[i] for i in foreground),220)  # red-capable baseline
        self.assertGreaterEqual(min(b[i] for i in foreground),220)
        self.assertLess(error(source,new),error(source,old)*.5)
        self.assertEqual(new[:8],old[:8])

    def test_deterministic_never_worse_and_alpha_unchanged(self):
        rng=random.Random(329)
        samples=[bytes(64),bytes([19,45,87,63])*16,bytes([255])*64]
        samples += [bytes(rng.randrange(256) for _ in range(64)) for _ in range(24)]
        for source in samples:
            old=encode_rgba_block(source); new=encode_fitted_rgba_block(source)
            self.assertEqual(new,encode_fitted_rgba_block(source))
            self.assertEqual(new[:8],old[:8])
            self.assertLessEqual(error(source,new),error(source,old))

    def test_native_opt_in_cache_and_outside_blocks(self):
        layout=unit_layout(32,32,7); raw=bytes(layout['storage_bytes']); cache={}
        old,_=overlay_rect(raw,layout,[8,4,4,4],strokes(),cache)
        new,proof=overlay_rect(raw,layout,[8,4,4,4],strokes(),cache,
                              rgb_encoding='weighted-fit-v1')
        self.assertNotEqual(old,new); self.assertEqual(len(cache),2)
        self.assertEqual(old,overlay_rect(raw,layout,[8,4,4,4],strokes(),cache)[0])
        self.assertTrue(proof['untouched_blocks_preserved'])
        tx=dict(layout=layout,width=32,height=32,format=7,tiles=new)
        b=decode_texture(tx)
        self.assertGreaterEqual(min(b[((y+4)*32+x+8)*4] for y in range(4) for x in (1,2)),220)

    def test_invalid_samples_and_profiles_fail_closed(self):
        for sample in [None,'a',bytes(63),bytearray(64)]:
            with self.assertRaises(FormatError):encode_fitted_rgba_block(sample)
        for fmt,mode in [(7,'unknown'),(7,True),(5,'weighted-fit-v1')]:
            layout=unit_layout(32,32,fmt)
            with self.assertRaises(FormatError):
                overlay_rect(bytes(layout['storage_bytes']),layout,[0,0,4,4],strokes(),rgb_encoding=mode)

    def test_explicit_overlay_profile_uses_fit_and_legacy_profile_rejects_it(self):
        layout=unit_layout(32,32,7); raw=bytes(layout['storage_bytes'])
        texture=dict(layout=layout,width=32,height=32,format=7,tiles=raw)
        edit=dict(regions=['line'],image_id='owned',channel_mode='rgba',
                  profile=dict(kind='xbox-inline-bc-v1',format=7),rgb_encoding='weighted-fit-v1')
        layers={'line':(dict(rect=[8,4,4,4]),strokes())}
        output,proof=overlay_profile_regions(texture,edit,layers)
        expected,_=overlay_rect(raw,layout,[8,4,4,4],strokes(),rgb_encoding='weighted-fit-v1')
        self.assertEqual(output,expected); self.assertEqual(proof['rgb_encoding'],'weighted-fit-v1')
        with self.assertRaises(FormatError):overlay_regions(raw,32,32,edit,layers)
        for bad in [None,True,'unknown']:
            with self.assertRaises(FormatError):overlay_profile_regions(texture,{**edit,'rgb_encoding':bad},layers)


if __name__=='__main__':unittest.main()
