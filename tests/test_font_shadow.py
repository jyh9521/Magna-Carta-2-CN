"""Resource-only shadow regressions; no renderer or copyrighted fixture needed."""
import copy
import unittest

from tools import font_shadow as shadow
from tools import supplement_font
from test_supplement_font import package_fixture, plan


class FontShadowTests(unittest.TestCase):
    def fixture(self):
        spec = plan()
        alpha = bytes(255 if 4 <= x < 15 and 4 <= y < 17 else 0
                      for y in range(24) for x in range(24))
        raw = package_fixture()
        supplemented, _ = supplement_font.supplement_package(
            raw, shadow.digest(raw), 'General', spec, {ord('中'): alpha}, None,
            raw_atlas=True)
        return supplemented, spec

    def test_shadow_changes_only_selected_atlas_blocks_and_roundtrips(self):
        raw, spec = self.fixture()
        after, proof = shadow.apply_shadow(raw, shadow.digest(raw), 'General', spec)
        self.assertNotEqual(raw, after)
        self.assertEqual(len(raw), len(after))
        self.assertTrue(proof['foreground_pixels_preserved'])
        self.assertTrue(proof['font_metrics_preserved'])
        self.assertGreater(proof['added_shadow_pixels'], 0)
        self.assertEqual(shadow.restore_shadow(after, proof), raw)

    def test_hash_and_field_guards(self):
        raw, spec = self.fixture()
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            shadow.apply_shadow(raw, '0' * 64, 'General', spec)
        altered = copy.deepcopy(spec)
        altered['glyphs'][0]['x'] += 4
        with self.assertRaisesRegex(ValueError, 'placement'):
            shadow.apply_shadow(raw, shadow.digest(raw), 'General', altered)

    def test_foreign_rollback_rejected(self):
        raw, spec = self.fixture()
        after, proof = shadow.apply_shadow(raw, shadow.digest(raw), 'General', spec)
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            shadow.restore_shadow(after[:-1] + bytes([after[-1] ^ 1]), proof)

    def test_repeated_shadow_rejected(self):
        raw, spec = self.fixture()
        after, _ = shadow.apply_shadow(raw, shadow.digest(raw), 'General', spec)
        with self.assertRaisesRegex(ValueError, 'white'):
            shadow.apply_shadow(after, shadow.digest(after), 'General', spec)

    def test_shadow_never_expands_visible_metrics(self):
        rgba = bytes([255, 255, 255, 255] * 16)
        output, count, clipped = shadow.shadow_pixels(rgba, 4, 4, 3, 3)
        self.assertEqual(output, rgba)
        self.assertEqual(count, 0)
        self.assertEqual(clipped, 5)

    def test_invalid_delta_or_cell_is_rejected(self):
        for dx, dy in [(0, 0), (-1, 1), (4, 1), (True, 1)]:
            with self.subTest(delta=(dx, dy)), self.assertRaises(ValueError):
                shadow.shadow_pixels(bytes(64), 4, 4, 4, 4, dx, dy)


if __name__ == '__main__':
    unittest.main()
