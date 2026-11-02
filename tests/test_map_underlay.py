import unittest
from PIL import Image
from tools.map_underlay import retained_art, scanline_art


class MapUnderlayTests(unittest.TestCase):
    def fixture(self):
        im = Image.new('RGBA', (24,24))
        im.paste((120,130,140,200), (16,2,24,3))
        im.paste((120,130,140,200), (12,21,24,22))
        im.paste((255,255,255,255), (0,3,24,21))
        return im, dict(kind='scanline-map-art-v1', top=[2,16,24],
                       bottom=[21,12,24], preserve_rects=[])

    def test_old_ink_and_shadow_inside_strip_have_no_influence(self):
        im, spec = self.fixture()
        a = scanline_art(im, [0,2,24,20], spec)
        im.paste((0,0,0,255), (0,3,24,21))
        b = scanline_art(im, [0,2,24,20], spec)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.getpixel((3,12)),(0,0,0,0))
        self.assertEqual(a.getpixel((20,12)),(120,130,140,200))

    def test_reviewed_visible_art_preserved_exactly(self):
        im, spec = self.fixture();spec['preserve_rects']=[[22,0,2,20]]
        out=scanline_art(im,[0,2,24,20],spec)
        self.assertEqual(out.crop((22,0,24,20)).tobytes(),im.crop((22,2,24,22)).tobytes())

    def test_residual_in_reused_repair_does_not_become_background(self):
        im=Image.new('RGBA',(24,24));im.putpixel((3,12),(0,0,0,50))
        im.putpixel((22,12),(160,160,160,255))
        out=retained_art(im,[[20,0,4,24]])
        self.assertEqual(out.getpixel((3,12)),(0,0,0,0))
        self.assertEqual(out.getpixel((22,12)),im.getpixel((22,12)))

    def test_donors_must_be_outside_occluded_strip(self):
        im,spec=self.fixture();spec['top'][0]=5
        with self.assertRaisesRegex(ValueError,'bracket'):scanline_art(im,[0,2,24,20],spec)
        spec['top']=[-1,16,24]
        with self.assertRaisesRegex(ValueError,'bounds'):scanline_art(im,[0,2,24,20],spec)
        with self.assertRaises(ValueError):retained_art(im,[[23,0,3,24]])

    def test_unlisted_fields_rejected(self):
        im,spec=self.fixture();spec['unverified']='sample'
        with self.assertRaisesRegex(ValueError,'fields'):scanline_art(im,[0,2,24,20],spec)
