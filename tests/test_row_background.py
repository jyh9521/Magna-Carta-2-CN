"""Exact native row transport rejects textured or contradictory donors."""
import copy
import unittest

import numpy as np

from tools.row_background import restore_rows


class NativeRowBackgroundTests(unittest.TestCase):
    def fixture(self):
        rgb = np.zeros((8, 32, 3), np.uint8)
        for y in range(8):
            rgb[y] = (10+y, 20+y*2, 30+y*3)
        rect = [12, 2, 8, 4]
        mask = np.zeros((4, 8), dtype=bool)
        mask[1:3, 2:6] = True
        original = rgb.copy()
        rgb[2:6, 12:20][mask] = (245, 220, 190)
        return rgb, rect, mask, [[0, 10], [22, 32]], original

    def test_only_owned_glyph_pixels_use_native_rows(self):
        rgb, rect, mask, bands, expected = self.fixture()
        before = rgb.copy()
        actual, proof = restore_rows(rgb, rect, mask, bands)
        np.testing.assert_array_equal(actual, expected)
        np.testing.assert_array_equal(rgb, before)
        self.assertFalse(np.shares_memory(actual, rgb))
        self.assertEqual(proof['owned_pixels'], 8)
        self.assertEqual(proof['donor_maximum_difference'], 0)
        self.assertTrue(proof['hidden_background_is_inferred'])

    def test_disagreeing_separated_donors_fail(self):
        rgb, rect, mask, bands, _ = self.fixture()
        rgb[3, 22:32, 0] += 1
        with self.assertRaisesRegex(ValueError, 'invariant'):
            restore_rows(rgb, rect, mask, bands)

    def test_one_textured_native_sample_fails(self):
        rgb, rect, mask, bands, _ = self.fixture()
        rgb[4, 3, 2] += 1
        with self.assertRaisesRegex(ValueError, 'invariant'):
            restore_rows(rgb, rect, mask, bands)

    def test_bands_must_be_wide_separated_and_outside_owned_rectangle(self):
        rgb, rect, mask, _, _ = self.fixture()
        for bands in ([[[1, 3], [22, 32]]], [[0, 13], [22, 32]],
                      [[0, 10], [19, 32]], [[0, 10], [22, 33]],
                      [[0, 10]], [[0, 10], [22, 29]]):
            with self.subTest(bands=bands), self.assertRaises(ValueError):
                restore_rows(rgb, rect, mask, bands)

    def test_empty_full_nonbinary_or_wrong_shape_masks_fail(self):
        rgb, rect, mask, bands, _ = self.fixture()
        for invalid in (np.zeros_like(mask), np.ones_like(mask),
                        mask.astype('uint8'), np.ones((3, 8), bool)):
            with self.subTest(shape=invalid.shape), self.assertRaises(ValueError):
                restore_rows(rgb, rect, invalid, bands)

    def test_native_geometry_and_type_are_bounded(self):
        rgb, rect, mask, bands, _ = self.fixture()
        for invalid in ([12, -1, 8, 4], [12, 2, 21, 4], [12, 2, 8, 9],
                        [12, 2, 8.0, 4], [12, 2, 0, 4]):
            with self.subTest(rect=invalid), self.assertRaises(ValueError):
                restore_rows(rgb, invalid, mask, bands)
        for invalid in (rgb.astype('int16'), rgb[:, :, :2], rgb.tolist()):
            with self.assertRaises(ValueError):
                restore_rows(invalid, rect, mask, bands)

    def test_unowned_native_detail_is_not_filled_or_normalized(self):
        rgb, rect, mask, bands, _ = self.fixture()
        rgb[2, 12] = (41, 15, 200)
        rgb[7, 18] = (111, 222, 33)
        actual, _ = restore_rows(rgb, rect, mask, bands)
        np.testing.assert_array_equal(actual[2, 12], rgb[2, 12])
        np.testing.assert_array_equal(actual[7, 18], rgb[7, 18])

    def test_proof_does_not_share_mutable_donor_bands(self):
        rgb, rect, mask, bands, _ = self.fixture()
        saved = copy.deepcopy(bands)
        _, proof = restore_rows(rgb, rect, mask, bands)
        proof['donor_bands'][0][0] = 999
        self.assertEqual(bands, saved)


if __name__ == '__main__':
    unittest.main()
