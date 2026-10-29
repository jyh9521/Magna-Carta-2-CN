import unittest
import numpy as np
from tools.verify_video_caption_regions import rectangle,intersection,metrics


class RegionMetricsTests(unittest.TestCase):
    def test_half_open_intersection_and_invalid_rectangle(self):
        self.assertFalse(intersection([0,0,4,4],[4,0,4,4]))
        self.assertTrue(intersection([0,0,4,4],[3,3,4,4]))
        self.assertEqual(rectangle('2,3,4,5'),[2,3,4,5])
        for value in ['1,2,3','-1,0,4,4','0,0,0,4']:
            with self.assertRaises(ValueError):rectangle(value)

    def test_metrics_only_use_explicit_mask_and_fail_empty(self):
        delta=np.zeros((3,4,3),dtype=np.int16);delta[0,0]=30;delta[1,1]=90
        mask=np.zeros((3,4),bool);mask[0,0]=True
        self.assertEqual(metrics(delta,mask),dict(mean=30.,p99=30.,maximum=30.))
        with self.assertRaises(ValueError):metrics(delta,np.zeros_like(mask))
