import unittest

from tools.font_shadow import outline_pixels, _outline_block
from tools.texture_overlay import encode_rgba_block
from tools.ue3_textures import decode_dxt5


class DigitOutlineTests(unittest.TestCase):
    def test_outline_extends_both_axes_and_preserves_visible_samples(self):
        data = bytearray(64)
        data[20:24] = bytes((255, 255, 255, 255))
        data[40:44] = bytes((0, 0, 0, 255))
        original = encode_rgba_block(bytes(data))
        before = decode_dxt5(original, 4, 4)
        requested, added, clipped = outline_pixels(before, 4, 4, 4, 4)
        actual = decode_dxt5(_outline_block(before, requested, original), 4, 4)
        self.assertEqual((added, clipped), (7, 0))
        for i in (1, 4, 6, 9):
            self.assertEqual(actual[i*4:i*4+4], bytes((0, 0, 0, 255)))
        for i in (5, 10):
            self.assertEqual(actual[i*4:i*4+4], before[i*4:i*4+4])

    def test_bounds_and_clipping(self):
        data = bytes((255, 255, 255, 255)) + bytes(12)
        self.assertEqual(outline_pixels(data, 2, 2, 2, 2)[1:], (3, 5))
        with self.assertRaises(ValueError):
            outline_pixels(data, 2, 2, 3, 2)
