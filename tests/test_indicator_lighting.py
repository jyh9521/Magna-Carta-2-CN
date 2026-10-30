import unittest
import numpy as np
from PIL import Image

from tools.video_native_indicator import NativeIndicator


class IndicatorLightingTests(unittest.TestCase):
    def fixture(self, method='harmonic-feathered-v1'):
        h, w = 40, 80
        y, x = np.indices((h, w))
        mask = np.zeros((h, w), bool)
        mask[5:35, 15:65] = True
        unknown = np.zeros_like(mask)
        unknown[10:30, 20:60] = True
        anchor = np.full((h, w, 3), 100, np.uint8)
        patch = np.zeros((h, w, 4), np.uint8)
        patch[unknown, :3] = 100
        patch[unknown, 3] = 255
        op = NativeIndicator((0, 0, w, h), mask, np.zeros_like(anchor), anchor,
                             Image.fromarray(patch), [Image.new('RGBA', (w, h))] * 3,
                             90, .9, unknown, temporal_lighting=method,
                             lighting_weight=mask.astype(np.uint8)*255 if method=='harmonic-feathered-v1' else None)
        # A smooth physical light field; nearest-donor cells create false facets.
        delta = (x / 3 + y / 4).astype(np.uint8)
        frame = anchor + delta[:, :, None]
        return op, frame, unknown

    def test_real_clean_path_has_no_nearest_donor_facets(self):
        op, frame, unknown = self.fixture()
        result = op.clean(frame)
        self.assertLessEqual(np.abs(result.astype(int) - frame)[unknown].max(), 1)
        self.assertTrue(np.array_equal(result[~op.mask], frame[~op.mask]))

    def test_old_mode_reproduces_the_reported_facets(self):
        op, frame, unknown = self.fixture('nearest-known-v1')
        self.assertGreater(np.abs(op.clean(frame).astype(int) - frame)[unknown].max(), 2)

    def test_caption_pixels_cannot_feed_the_lighting_estimate(self):
        op, frame, unknown = self.fixture()
        corrupted = frame.copy()
        corrupted[op.mask] = 255
        self.assertTrue(np.array_equal(op.clean(frame)[unknown], op.clean(corrupted)[unknown]))

    def test_bad_method_is_rejected(self):
        with self.assertRaises(ValueError):
            self.fixture('typo')

    def test_full_support_pulsing_letter_does_not_reappear(self):
        op, frame, _ = self.fixture()
        pulsing = frame.copy()
        pulsing[op.mask] = [255, 70, 20]
        clean = op.clean(pulsing)
        self.assertLessEqual(np.abs(clean.astype(int)-frame)[op.mask].max(), 1)

    def test_harmonic_solver_guards_and_no_input_mutation(self):
        from tools.video_screen_underlay import harmonic_lighting
        op, frame, _ = self.fixture()
        data=frame.astype(float)-100;original=data.copy()
        harmonic_lighting(data,op.mask)
        self.assertTrue(np.array_equal(data,original))
        for kw in ({'limit':0},{'limit':True},{'max_iterations':1},{'tolerance':float('nan')}):
            with self.assertRaises(ValueError):harmonic_lighting(data,op.mask,**kw)
        with self.assertRaises(ValueError):harmonic_lighting(data,np.ones_like(op.mask))

    def test_fft_light_field_is_linear_exact_and_interior_independent(self):
        from tools.video_screen_underlay import rectangular_lighting
        y,x=np.indices((19,37));expected=np.repeat((x*.6+y*.3-12)[:,:,None],3,axis=2)
        data=expected.copy();data[1:-1,1:-1]=255
        result=rectangular_lighting(data)
        self.assertLess(np.abs(result-expected).max(),1e-10)
        self.assertTrue(np.array_equal(data[1:-1,1:-1],np.full((17,35,3),255)))
        with self.assertRaises(ValueError):rectangular_lighting(data,limit=False)
        data[0,0]=float('nan')
        with self.assertRaises(ValueError):rectangular_lighting(data)

    def test_seam_audit_accepts_steep_smooth_light_but_rejects_donor_facets(self):
        from tools.audit_indicator_lighting import lighting_curvature,neighbor_jump
        y,x=np.indices((20,30));smooth=np.repeat((x*8.+y*4.)[:,:,None],3,axis=2)
        mask=np.ones((20,30),bool)
        self.assertEqual(neighbor_jump(smooth,mask),8)
        self.assertEqual(lighting_curvature(smooth,mask),0)
        faceted=smooth.copy();faceted[:,15:]+=30
        self.assertEqual(lighting_curvature(faceted,mask),30)
        with self.assertRaises(ValueError):lighting_curvature(smooth,np.zeros_like(mask))

    def test_v11_profiles_keep_all_fifteen_sources_and_non_indicator_captions(self):
        from pathlib import Path
        import json
        root=Path(__file__).resolve().parents[1]
        before=json.loads((root/'locales/zh-Hans/loading-captions-v10.json').read_bytes())
        after=json.loads((root/'locales/zh-Hans/loading-captions-v11.json').read_bytes())
        self.assertEqual(len(after['entries']),15)
        self.assertEqual(before['fonts'],after['fonts'])
        for a,b in zip(before['entries'],after['entries'],strict=True):
            self.assertEqual(a['source'],b['source'])
            self.assertEqual(a['captions'][:-1],b['captions'][:-1])
            spec=b['captions'][-1]['erase']['native_screen']
            self.assertEqual(spec['temporal_lighting'],'harmonic-feathered-v1')
            self.assertEqual(spec['core_patch'],a['captions'][-1]['erase']['native_screen']['core_patch'])
            self.assertEqual(spec['lighting_feather']['padding'][0],0)


if __name__ == '__main__':
    unittest.main()
