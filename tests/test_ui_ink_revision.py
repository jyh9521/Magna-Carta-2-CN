import unittest
import random

from PIL import Image

from tools.ui_ink_revision import alpha_palette, clear_block_alpha, right_ink_width, clean_alpha
from tools.audit_ui_ink_revision import core_box, visible_right, runtime_value


class InkRevisionTests(unittest.TestCase):
    def test_right_bearing_trims_only_empty_or_explicit_faint_black_shadow(self):
        cell = Image.new('RGBA', (14, 18))
        for y in range(2, 16):
            for x in range(3, 11):
                cell.putpixel((x, y), (255, 255, 255, 255))
        cell.putpixel((13, 11), (0, 0, 0, 21))
        self.assertEqual(right_ink_width(cell, 2, 32), 13)
        with self.assertRaises(ValueError):
            right_ink_width(cell, 2, 0)
        cell.putpixel((13, 11), (100, 100, 100, 21))
        with self.assertRaises(ValueError):
            right_ink_width(cell, 2, 32)

    def test_right_bearing_rejects_blank_and_growth(self):
        with self.assertRaises(ValueError):
            right_ink_width(Image.new('RGBA', (8, 8)), 2, 32)
        with self.assertRaises(ValueError):
            right_ink_width(Image.new('RGBA', (8, 8), 'white'), 2, 32)

    def test_alpha_clear_preserves_rgb_and_retained_samples(self):
        indices = sum((i % 8) << (3 * i) for i in range(16))
        block = bytes([255, 0]) + indices.to_bytes(6, 'little') + bytes(range(8))
        out, delta = clear_block_alpha(block, [True] + [False] * 15)
        self.assertEqual(out[8:], block[8:])
        self.assertEqual(delta, 0)
        pal = alpha_palette(out[:2])
        ids = int.from_bytes(out[2:8], 'little')
        self.assertEqual(pal[ids & 7], 0)
        self.assertEqual(ids >> 3, indices >> 3)

    def test_zero_mask_is_exact_noop_and_all_clear_is_transparent(self):
        block = bytes([240, 100]) + bytes(6) + bytes(range(8))
        self.assertEqual(clear_block_alpha(block, [False] * 16), (block, 0))
        out, delta = clear_block_alpha(block, [True] * 16)
        self.assertEqual(out[:8], bytes(8))
        self.assertEqual(out[8:], block[8:])
        self.assertEqual(delta, 0)

    def test_alpha_clear_reports_quantization_when_zero_missing(self):
        block = bytes([240, 100]) + bytes(6) + bytes(range(8))
        out, delta = clear_block_alpha(block, [True] + [False] * 15)
        self.assertEqual(out[8:], block[8:])
        self.assertEqual(delta, 0)  # all retained samples are the same endpoint

    def test_invalid_inputs_rejected(self):
        for block, mask in [(bytes(15), [False] * 16), (bytes(16), []),
                            (bytes(16), [1] * 16)]:
            with self.assertRaises(ValueError):
                clear_block_alpha(block, mask)

    def test_alpha_palette_modes_fuzz_preserves_rgb_and_clears_exactly(self):
        rng = random.Random(340)
        for _ in range(256):
            block = rng.randbytes(16)
            mask = [rng.choice([True, False]) for _ in range(16)]
            result, reported = clear_block_alpha(block, mask)
            self.assertEqual(result[8:], block[8:])
            old = alpha_palette(block[:2]); new = alpha_palette(result[:2])
            before = int.from_bytes(block[2:8], 'little')
            after = int.from_bytes(result[2:8], 'little')
            errors = []
            for i in range(16):
                a, b = old[(before >> (3*i)) & 7], new[(after >> (3*i)) & 7]
                if mask[i]:
                    self.assertEqual(b, 0)
                else:
                    errors.append(abs(a-b))
            self.assertEqual(reported, max(errors, default=0))

    def test_regions_and_error_budget_rejected_before_package_read(self):
        for regions, ceiling, delta in [([], 32, 24), ([[0, 0, 4, 4]], 128, 24),
                                         ([[0, 0, 4, 4]], 32, -1), ([[0, 0, 4, 4]], 32, 33)]:
            with self.assertRaises(ValueError):
                clean_alpha(b'', 'x', regions, ceiling, delta)

    def test_right_edge_uses_ink_not_advance_and_right_bearing(self):
        one = dict(advance=10, box=[3, 2, 8, 16])
        self.assertEqual(visible_right(203, 26, 2, one), 227)
        self.assertEqual(visible_right(203, 26, 0, one), 211)
        with self.assertRaises(ValueError):
            visible_right(0, 9, 2, one)

    def test_core_box_excludes_chromatic_glow_and_allows_half_pixel_centers(self):
        im = Image.new('RGBA', (10, 8), (255, 0, 0, 255))
        for y in range(2, 6):
            for x in range(3, 6):
                im.putpixel((x, y), (220, 220, 220, 255))
        self.assertEqual(core_box(im), [3, 2, 6, 6])
        self.assertEqual(runtime_value('" "'), ' ')
        self.assertEqual(runtime_value('  value  '), 'value')

    def test_texture_selector_ignores_same_named_package_export(self):
        from unittest.mock import patch
        from tools.replace_texture_regions import selected
        from test_texture_layout import profile_fixture
        from tools.build_font_supplement import context
        raw, spec, _ = profile_fixture()
        c = context(raw, None)
        c['tables']['exports'].append(dict(path=spec['object'], class_path='Core.Package'))
        with patch('tools.replace_texture_regions.context', return_value=c):
            self.assertEqual(selected(raw, spec['object'], None)[1]['class_path'], 'Engine.Texture2D')


if __name__ == '__main__':
    unittest.main()
