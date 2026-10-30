import unittest
from tools.texture_overlay import compose_restored_region, digest


class BackgroundClipTests(unittest.TestCase):
    def test_only_owned_background_clips_not_glyph_or_unmasked_art(self):
        source=bytes([1,2,3,255])*16
        mask=bytes([0]+[255]*15)
        patch=bytes(4)+bytes([255,0,0,180])*15
        glyph=bytes(4)*15+bytes([255,255,255,255])
        label=dict(rect=[0,0,4,4],restoration=dict(source_rgba_sha256=digest(source),clip=[1,1,2,2]),
                   _repair_mask=mask,_repair_pixels=patch)
        out=compose_restored_region(label,glyph,source,4)
        self.assertEqual(out[:4],source[:4])
        self.assertEqual(out[4:8],bytes(4))
        self.assertEqual(out[20:24],bytes([255,0,0,180]))
        self.assertEqual(out[-4:],bytes([255,255,255,255]))
    def test_invalid_clip_rejected(self):
        source=bytes(64)
        for clip in ([-1,0,2,2],[0,0,5,4],[0,0,0,4],[True,0,2,2],'all'):
            label=dict(rect=[0,0,4,4],restoration=dict(source_rgba_sha256=digest(source),clip=clip),
                       _repair_mask=bytes([255])*16,_repair_pixels=source)
            with self.subTest(clip=clip),self.assertRaises(ValueError):
                compose_restored_region(label,source,source,4)
    def test_background_feather_stays_inside_clip(self):
        source=bytes(256);patch=bytes([255,0,0,200])*64
        label=dict(rect=[0,0,8,8],restoration=dict(source_rgba_sha256=digest(source),clip=[1,1,6,6],clip_feather=2),
                   _repair_mask=bytes([255])*64,_repair_pixels=patch)
        out=compose_restored_region(label,source,source,8)
        self.assertEqual(out[(1*8+1)*4+3],0)
        self.assertEqual(out[(2*8+2)*4+3],100)
        self.assertEqual(out[(3*8+3)*4+3],200)
