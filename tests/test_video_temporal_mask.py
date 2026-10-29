import unittest
import numpy as np
from PIL import Image

from tools.video_caption import temporal_ink_mask


class TemporalMaskTests(unittest.TestCase):
    def test_union_covers_later_visible_glyph_without_touching_unrelated_area(self):
        frames=[]
        for x in (4,10):
            im=Image.new('RGB',(20,16));im.putpixel((x,7),(255,255,255));frames.append(im)
        result=temporal_ink_mask(iter(frames),[2,2,14,12],200,1,2)
        self.assertEqual(int(result.sum()),18)
        self.assertTrue(result[5,2]);self.assertTrue(result[5,8])
        self.assertFalse(result[0,0])

    def test_count_and_geometry_mismatch_rejected(self):
        frame=Image.new('RGB',(20,16),'white')
        for frames,count in [([frame],2),([frame,frame],1),([],1)]:
            with self.assertRaises(ValueError):temporal_ink_mask(iter(frames),[2,2,14,12],200,1,count)
        with self.assertRaises(ValueError):temporal_ink_mask(iter([frame]),[2,2,14,12],200,1,601)

    def test_input_untouched(self):
        im=Image.new('RGB',(20,16),'white');before=im.tobytes()
        temporal_ink_mask(iter([im]),[2,2,14,12],200,1,1)
        self.assertEqual(im.tobytes(),before)
