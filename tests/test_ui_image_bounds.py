import unittest

from tools.audit_ui_image_bounds import ink_points, measure, center_delta


class NativeImageBoundsTests(unittest.TestCase):
    def test_native_bottom_row_is_detected_even_when_whole_texture_is_intact(self):
        points = [(3, y) for y in range(3, 17)]
        before = measure(points, [87, 19, 78, 16], [0, 0, 78, 16])
        after = measure(points, [87, 19, 78, 20], [0, 0, 78, 20])
        self.assertEqual(before['clipped_pixels'], 1)
        self.assertEqual(after['clipped_pixels'], 0)
        self.assertEqual(before['screen_bounds'], after['screen_bounds'])
        self.assertEqual(after['scale'], [1, 1])

    def test_frame_center_uses_native_border_not_label_texture_padding(self):
        label = measure([(3, 38), (79, 56)], [271, -11, 160, 32], [0, 32, 160, 32])
        frame = measure([(5, 18), (211, 53)], [234, -15, 216, 50], [0, 14, 216, 50])
        self.assertEqual(center_delta(label, frame), [-30, -2.5])
        fixed = measure([(3, 38), (79, 56)], [301, -8.5, 160, 32], [0, 32, 160, 32])
        self.assertEqual(center_delta(fixed, frame), [0, 0])

    def test_threshold_excludes_shadow_but_retains_visible_character(self):
        pixels = bytes([0, 0, 0, 255, 240, 220, 160, 255])
        self.assertEqual(ink_points(pixels, (2, 1), [0, 0, 2, 1], [100, 80, 50, 160]), [(1, 0)])

    def test_invalid_or_empty_windows_are_rejected(self):
        for region in [[-1, 0, 2, 1], [0, 0, 0, 1], [0, 0, 3, 1]]:
            with self.assertRaises(ValueError):
                ink_points(bytes(8), (2, 1), region, [100]*4)
        with self.assertRaisesRegex(ValueError, 'empty'):
            ink_points(bytes(8), (2, 1), [0, 0, 2, 1], [100]*4)


if __name__ == '__main__':
    unittest.main()
