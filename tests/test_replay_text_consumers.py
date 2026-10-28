import unittest
from tools.replay_text_consumers import advances, line_case, property_value
from tools.ue3_fonts import parse_font_payload
from test_supplement_font import font_payload, NAMES


class TextConsumerTests(unittest.TestCase):
    def setUp(self):
        self.font = parse_font_payload(font_payload(), NAMES)

    def test_glyph_width_not_string_length(self):
        self.assertEqual(advances(self.font, 'AAA'), [4, 4, 4])
        self.assertFalse(line_case('AAA', self.font, 8)['passed'])
        self.assertTrue(line_case('AA\\nA', self.font, 8, 2)['passed'])

    def test_physical_newline_and_unmapped_glyph_rejected(self):
        with self.assertRaisesRegex(ValueError, 'physical'):
            line_case('A\nA', self.font, 8)
        with self.assertRaisesRegex(ValueError, 'exact glyph'):
            advances(self.font, 'B')

    def test_wrong_line_count_is_red(self):
        self.assertFalse(line_case('A', self.font, 8, 2)['passed'])

    def test_missing_consumer_field_rejected(self):
        with self.assertRaisesRegex(ValueError, 'field missing'):
            property_value(font_payload(), NAMES, 4, [('Absent', 0)])


if __name__ == '__main__':
    unittest.main()
