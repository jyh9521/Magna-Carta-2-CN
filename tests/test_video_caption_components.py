import copy
import unittest
from PIL import Image, ImageDraw
import numpy as np
from tools.video_caption import component_ink_mask, restore_masked
from tools.build_video_captions import avi_transport_rate


class ComponentCaptionTests(unittest.TestCase):
    def fixture(self):
        im=Image.new('RGB',(40,24),(30,30,30));d=ImageDraw.Draw(im)
        d.rectangle((3,5,5,15),fill='white')
        d.rectangle((17,2,39,22),fill=(220,220,220))
        selection={'roi':[0,0,40,24],'threshold':175,'chroma':35,'min_area':5,'boxes':[[3,5,6,16]]}
        return im,selection

    def test_bright_artwork_excluded(self):
        im,s=self.fixture();mask=component_ink_mask(im,[0,0,40,24],s,2)
        self.assertFalse(mask[:,17:].any())
        self.assertTrue(mask[5:16,3:6].all())
        repaired,_=restore_masked(im,[0,0,40,24],mask)
        np.testing.assert_array_equal(np.array(im)[:,17:],np.array(repaired)[:,17:])

    def test_exact_component_required(self):
        im,s=self.fixture();s['boxes']=[[3,5,7,16]]
        with self.assertRaisesRegex(ValueError,'components changed'):
            component_ink_mask(im,[0,0,40,24],s,2)

    def test_duplicate_component_rejected(self):
        im,s=self.fixture();s['boxes']*=2
        with self.assertRaises(ValueError):component_ink_mask(im,[0,0,40,24],s,2)

    def test_changed_backdrop_not_silently_accepted_as_glyph(self):
        im,s=self.fixture();ImageDraw.Draw(im).rectangle((6,5,17,15),fill='white')
        with self.assertRaises(ValueError):component_ink_mask(im,[0,0,40,24],s,2)

    def test_source_and_outside_mask_unchanged(self):
        im,s=self.fixture();before=im.tobytes();mask=component_ink_mask(im,[0,0,40,24],s,1)
        repaired,_=restore_masked(im,[0,0,40,24],mask)
        self.assertEqual(before,im.tobytes())
        np.testing.assert_array_equal(np.array(im)[~mask],np.array(repaired)[~mask])

    def test_roi_bounds(self):
        im,s=self.fixture()
        for roi in [[-1,0,40,24],[0,0,41,24],[0,0,0,24]]:
            bad=copy.deepcopy(s);bad['roi']=roi
            with self.assertRaises(ValueError):component_ink_mask(im,[0,0,40,24],bad,1)

    def test_avi_transport_uses_exact_integer_without_frame_drop(self):
        self.assertEqual(30,avi_transport_rate({'numerator':10000000,'denominator':333333}))
        self.assertEqual(24,avi_transport_rate({'numerator':24,'denominator':1}))

    def test_untested_fractional_transport_rejected(self):
        with self.assertRaises(ValueError):avi_transport_rate({'numerator':30000,'denominator':1001})


if __name__=='__main__':unittest.main()
