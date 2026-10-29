import unittest
from tools.build_video_captions import verify_report_fields


class VideoReportReplayTests(unittest.TestCase):
    def test_pillow_tuple_bounds_roundtrip_as_json_arrays(self):
        verify_report_fields({'captions':[{'alpha_bbox':[1,2,3,4]}]},
                             {'captions':[{'alpha_bbox':(1,2,3,4)}]},['captions'])

    def test_value_drift_is_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'captions'):
            verify_report_fields({'captions':[{'alpha_bbox':[1,2,3,4]}]},
                                 {'captions':[{'alpha_bbox':(1,2,3,5)}]},['captions'])

    def test_missing_proof_field_is_not_ignored(self):
        with self.assertRaises(KeyError):verify_report_fields({}, {'frames':[]},['frames'])
