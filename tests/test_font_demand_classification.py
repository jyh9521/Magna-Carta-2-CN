"""Synthetic demand classification; no glyph bytes, normalization or layout guesses."""
import copy
import unittest

from tools.prepare_text_sample import classify_font_demand


def font(remap=(32, 65)):
    return dict(is_remapped=True, remap=[dict(codepoint=cp, glyph_index=i)
                                       for i, cp in enumerate(remap)], characters=[{}] * len(remap))


class FontDemandClassificationTests(unittest.TestCase):
    def test_explicit_remaps_preserve_requested_set(self):
        f = font(); original = copy.deepcopy(f)
        r = classify_font_demand(f, [65, 66, 0x4e00])
        self.assertEqual(r['drawable_additions'], [66, 0x4e00])
        self.assertEqual(r['requested_codepoints'], [65, 66, 0x4e00]); self.assertEqual(f, original)

    def test_identity_conversion_does_not_treat_ascii_as_missing(self):
        f = dict(is_remapped=False, remap=[], characters=[{}] * 256)
        r = classify_font_demand(f, [9, 32, 65, 0x4e00])
        self.assertEqual(r['missing_codepoints'], [0x4e00])
        self.assertEqual(r['mapping_model'], '256-glyph-identity-conversion')

    def test_other_nonremapped_shapes_are_not_guessed(self):
        with self.assertRaisesRegex(ValueError, '256-glyph'):
            classify_font_demand(dict(is_remapped=False, remap=[], characters=[]), [65])

    def test_layout_controls_are_retained_but_not_drawable(self):
        r = classify_font_demand(font(), [9, 32, 0x3000, 0x4e00])
        self.assertEqual(r['layout_or_control_additions'], [9, 0x3000])
        self.assertEqual(r['drawable_additions'], [0x4e00])
        self.assertIn(9, r['required_additions']); self.assertIn(0x3000, r['requested_codepoints'])

    def test_transparent_repair_is_counted_once(self):
        r = classify_font_demand(font(), [65, 66], [65, 65])
        self.assertEqual(r['transparent_repairs'], [65]); self.assertEqual(r['drawable_additions'], [65, 66])
        with self.assertRaisesRegex(ValueError, 'already mapped'):
            classify_font_demand(font(), [65, 66], [66])

    def test_outside_bmp_is_preserved_as_separate_gate(self):
        r = classify_font_demand(font(), [0x20000])
        self.assertEqual(r['outside_bmp_additions'], [0x20000]); self.assertEqual(r['drawable_additions'], [])

    def test_invalid_scalars_and_bool_are_rejected(self):
        for values in [[1, True], [-1], [0x110000], [0xd800]]:
            with self.assertRaises(ValueError): classify_font_demand(font(), values)

    def test_total_demand_and_new_glyph_count_are_distinct(self):
        r = classify_font_demand(font(range(2048)), range(2451))
        self.assertEqual(len(r['requested_codepoints']), 2451)
        self.assertEqual(len(r['missing_codepoints']), 403)
        self.assertEqual(set(r['required_additions']),
                         set(r['drawable_additions']) | set(r['layout_or_control_additions'])
                         | set(r['outside_bmp_additions']))


if __name__ == '__main__':
    unittest.main()
