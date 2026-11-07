import hashlib
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from tools.build_video_captions import load_mask_asset


def sha(data):return hashlib.sha256(data).hexdigest()


class MaskAssetTests(unittest.TestCase):
    def fixture(self, root):
        mask=np.zeros((8,12),bool);mask[2:6,2:10]=True
        p=root/'mask.png';Image.fromarray(mask.astype('uint8')*255).save(p)
        return mask,dict(path='mask.png',sha256=sha(p.read_bytes()),pixels_sha256=sha(mask.tobytes()),pixels=int(mask.sum()))

    def test_exact_binary_support_is_independent_of_scene_brightness(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mask,ref=self.fixture(root)
            actual=load_mask_asset(ref,[20,40,12,8],root)
            self.assertTrue(np.array_equal(actual,mask))

    def test_geometry_schema_hash_and_count_mismatches_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mask,ref=self.fixture(root)
            for change in [dict(sha256='0'*64),dict(pixels_sha256='0'*64),dict(pixels=True),
                           dict(pixels=mask.size),dict(unknown=0),dict(path='../mask.png')]:
                with self.subTest(change=change),self.assertRaises(ValueError):
                    load_mask_asset(dict(ref,**change),[20,40,12,8],root)
            with self.assertRaises(ValueError):load_mask_asset(ref,[0,0,16,8],root)

    def test_nonbinary_rgb_or_animated_png_is_not_a_mask(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mask,ref=self.fixture(root);p=root/'mask.png'
            variants=[Image.new('L',(12,8),127),Image.new('RGB',(12,8),'black')]
            for image in variants:
                image.save(p);ref['sha256']=sha(p.read_bytes())
                with self.assertRaises(ValueError):load_mask_asset(ref,[0,0,12,8],root)
            one=Image.fromarray(mask.astype('uint8')*255);two=Image.new('L',(12,8))
            one.save(p,save_all=True,append_images=[two],duration=100,loop=0)
            ref['sha256']=sha(p.read_bytes())
            with self.assertRaises(ValueError):load_mask_asset(ref,[0,0,12,8],root)


if __name__=='__main__':unittest.main()
