import unittest
import numpy as np
from tools.video_screen_underlay import (recover_underlay, screen_forward_error,
    extract_stationary_matte, inverse_screen, nearest_known_indices, extract_glyph_matte)


class ScreenUnderlayTests(unittest.TestCase):
    def fixture(self):
        base=np.zeros((9,17,3),dtype=np.uint8)
        base[:,5:11]=255  # A static bright leg edge must not be discarded as saturation.
        base[:,11:,0]=80;base[:,11:,1]=160;base[:,11:,2]=40
        fs=[];ys=[]
        for amount in (0,40,80,120,160,200):
            f=np.full(base.shape,amount,dtype=np.uint8)
            f[3:6,7:9]=255  # The original opaque letter core hides the native pixels.
            y=np.rint(f.astype(float)+(1-f.astype(float)/255)*base).astype(np.uint8)
            fs.append(f);ys.append(y)
        return base,fs,ys

    def test_sharp_native_edges_and_white_leg_survive_halo_removal(self):
        base,fs,ys=self.fixture();proof=recover_underlay(iter(fs),iter(ys))
        known=~proof['unknown'];self.assertEqual(int(proof['unknown'].sum()),6)
        self.assertLessEqual(np.abs(proof['underlay_rgb'][known].astype(int)-base[known]).max(),1)
        self.assertTrue(np.all(proof['underlay_rgb'][:,5:7]==255))
        error=screen_forward_error(iter(fs),iter(ys),proof['underlay_rgb'],known)
        self.assertLess(error['mean_absolute_error'],.25)
        self.assertEqual(error['frames'],6)

    def test_no_blur_or_spatial_cross_talk(self):
        base,fs,ys=self.fixture();first=recover_underlay(fs,ys)
        changed=[a.copy()for a in ys]
        for a in changed:a[0,0]=255
        second=recover_underlay(fs,changed)
        self.assertTrue(np.array_equal(first['underlay_rgb'][1:],second['underlay_rgb'][1:]))
        self.assertTrue(np.array_equal(first['underlay_rgb'][0,1:],second['underlay_rgb'][0,1:]))
        self.assertFalse(np.array_equal(first['underlay_rgb'][0,0],second['underlay_rgb'][0,0]))

    def test_any_opaque_channel_is_explicitly_unknown(self):
        f=np.zeros((2,3,3),np.uint8);f[:,1,0]=255
        y=np.full_like(f,120);y[:,1,0]=255
        p=recover_underlay([f],[y]);self.assertTrue(np.all(p['unknown'][:,1]))
        self.assertFalse(p['unknown'][:,0].any())
        self.assertEqual(p['frame_count'],1)

    def test_both_inputs_remain_unchanged(self):
        _,fs,ys=self.fixture();a=[f.copy()for f in fs];b=[y.copy()for y in ys]
        recover_underlay(fs,ys)
        self.assertTrue(all(np.array_equal(x,y)for x,y in zip(a,fs)))
        self.assertTrue(all(np.array_equal(x,y)for x,y in zip(b,ys)))

    def test_bad_counts_shapes_types_and_limits_fail_closed(self):
        _,fs,ys=self.fixture()
        for a,b in [([],[]),(fs,ys[:-1]),(fs[:-1],ys),([fs[0]], [ys[0][:,:-1]]),([fs[0].astype(float)],[ys[0]])]:
            with self.assertRaises(ValueError):recover_underlay(a,b)
        for kw in [{'minimum_transmittance':0},{'minimum_transmittance':1.1},{'minimum_transmittance':float('nan')},{'max_frames':2},{'max_pixels':1}]:
            with self.assertRaises(ValueError):recover_underlay(fs,ys,**kw)

    def test_forward_metrics_detect_wrong_alignment_or_model(self):
        _,fs,ys=self.fixture();p=recover_underlay(fs,ys);known=~p['unknown']
        correct=screen_forward_error(fs,ys,p['underlay_rgb'],known)
        wrong=screen_forward_error(fs,ys,np.roll(p['underlay_rgb'],3,axis=1),known)
        self.assertGreater(wrong['mean_absolute_error'],20)
        self.assertGreater(wrong['rms_error'],correct['rms_error'])
        self.assertGreater(wrong['p99_absolute_error_upper_bound'],20)

    def test_stationary_matte_is_minimum_only_inside_explicit_support(self):
        a=np.full((4,5,3),90,np.uint8);b=np.full_like(a,140)
        support=np.zeros((4,5),bool);support[1:3,1:4]=True
        p=extract_stationary_matte(iter([a,b]),support)
        self.assertEqual(p['frame_count'],2)
        self.assertTrue(np.all(p['matte_rgb'][support]==90))
        self.assertFalse(p['matte_rgb'][~support].any())
        self.assertTrue(p['minimum_haze_may_be_included'])

    def test_inverse_preserves_white_leg_and_rescreens_known_pixels(self):
        base,fs,ys=self.fixture();matte=fs[3]
        p=inverse_screen(ys[3],matte);known=~p['unknown']
        self.assertEqual(p['unknown_pixels'],6)
        self.assertTrue(np.all(p['clean_rgb'][:,5:7]==255))
        replay=np.rint(matte.astype(float)+(1-matte.astype(float)/255)*p['clean_rgb']).astype(np.uint8)
        self.assertTrue(np.array_equal(replay[known],ys[3][known]))
        self.assertEqual(p['maximum_rescreen_error_known'],0)

    def test_inverse_zero_matte_leaves_outside_pixels_byte_identical(self):
        base,_,_=self.fixture();p=inverse_screen(base,np.zeros_like(base))
        self.assertTrue(np.array_equal(p['clean_rgb'],base))
        self.assertFalse(p['unknown'].any())

    def test_inverse_reports_impossible_matte_instead_of_hiding_clipping(self):
        frame=np.full((2,3,3),70,np.uint8);matte=np.full_like(frame,100)
        p=inverse_screen(frame,matte)
        self.assertTrue(p['invalid_model'].all())
        self.assertFalse(p['unknown'].any())
        self.assertEqual(p['invalid_model_pixels'],6)
        self.assertEqual(p['maximum_rescreen_error_known'],30)

    def test_bounded_nearest_map_points_only_to_known_pixels(self):
        unknown=np.zeros((9,11),bool);unknown[3:7,4:8]=True
        indices=nearest_known_indices(unknown,max_radius=3)
        self.assertEqual(indices.shape,(2,9,11))
        self.assertFalse(unknown[indices[0],indices[1]].any())
        yy,xx=np.indices(unknown.shape)
        self.assertTrue(np.array_equal(indices[:,~unknown],np.stack((yy,xx))[:,~unknown]))
        for y,x in zip(*np.where(unknown)):
            nearest=((yy[~unknown]-y)**2+(xx[~unknown]-x)**2).min()
            self.assertEqual(int(((indices[:,y,x]-[y,x])**2).sum()),int(nearest))
        with self.assertRaises(ValueError):nearest_known_indices(unknown,max_radius=1)
        with self.assertRaises(ValueError):nearest_known_indices(np.ones((2,2),bool))

    def test_new_helpers_reject_bad_inputs(self):
        rgb=np.zeros((2,3,3),np.uint8);mask=np.ones((2,3),bool)
        for frames,support,kwargs in [([],mask,{}),([rgb],mask.astype(np.uint8),{}),
                ([rgb],np.ones((2,4),bool),{}),([rgb,rgb],mask,{'max_frames':1})]:
            with self.assertRaises(ValueError):extract_stationary_matte(frames,support,**kwargs)
        with self.assertRaises(ValueError):inverse_screen(rgb,rgb[:,:2])
        with self.assertRaises(ValueError):inverse_screen(rgb,rgb,minimum_transmittance=0)
        with self.assertRaises(ValueError):nearest_known_indices(~mask,max_pixels=4194305)

    def test_glyph_matte_does_not_remove_native_haze_as_a_rectangle(self):
        haze=np.full((16,28,3),[34,20,15],np.uint8)
        glyph=np.zeros_like(haze);glyph[5:10,7:9]=255;glyph[8:10,9:14]=255
        reference=np.rint(glyph.astype(float)+(1-glyph.astype(float)/255)*haze).astype(np.uint8)
        support=np.zeros((16,28),bool);support[3:13,4:19]=True
        p=extract_glyph_matte([reference,reference],support)
        self.assertTrue(np.array_equal(p['matte_rgb'],glyph))
        self.assertTrue(np.array_equal(p['background_estimate_rgb'],haze))
        art=np.zeros_like(haze);art[:,20:]=255
        target=np.rint(reference.astype(float)+(1-reference.astype(float)/255)*art).astype(np.uint8)
        clean=inverse_screen(target,p['matte_rgb']);known=~clean['unknown']
        expected=np.rint(haze.astype(float)+(1-haze.astype(float)/255)*art).astype(np.uint8)
        self.assertTrue(np.array_equal(clean['clean_rgb'][known],expected[known]))
        self.assertFalse(p['target_art_spatial_filter_applied'])
        self.assertTrue(p['reference_fx_reconstructed'])
        self.assertFalse(p['original_fx_exact'])

    def test_glyph_matte_requires_native_context_around_ink(self):
        frame=np.zeros((5,6,3),np.uint8);support=np.ones((5,6),bool)
        with self.assertRaises(ValueError):extract_glyph_matte([frame],support)


if __name__=='__main__':unittest.main()
