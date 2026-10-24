import hashlib
import unittest
from tools import texture_overlay as overlay
from test_texture_render_windows import owned_font


class TextureLineLayoutTests(unittest.TestCase):
    def setUp(self):
        self.font = owned_font()
        self.label = dict(text='ABAB', rect=[0, 0, 64, 48], font_size=18,
                          ink_padding=dict(x=2, y=2), line_breaks=[2],
                          style=dict(fill=[255,255,255,255], stroke_fill=[0,0,0,255],
                                     shadow_fill=[0,0,0,0]))

    def test_layout_does_not_change_language_text_or_insert_engine_controls(self):
        self.assertEqual(overlay.render_text(self.label), 'AB\nAB')
        self.assertEqual(self.label['text'], 'ABAB')
        self.assertEqual(overlay.render_text(dict(text='AB')), 'AB')

    def test_bounded_strict_ordered_breaks(self):
        for breaks in [None, [], [True], [0], [4], [-1], [2, 2], [3, 1], '2', [1.0], [1, 2, 3, 4]]:
            with self.subTest(breaks=breaks), self.assertRaisesRegex(ValueError, 'line breaks'):
                overlay.render_label(self.font, dict(self.label, line_breaks=breaks))

    def test_legacy_owned_raster_is_byte_identical(self):
        label = dict(text='AB', rect=[0, 0, 64, 48], font_size=18)
        self.assertEqual(hashlib.sha256(overlay.render_label(self.font, label)).hexdigest(),
                         '864d30fe41c03329ac631fbedcf6e0e0b239c4d33056b28ae9714e6c84b7c2f6')

    def test_two_lines_and_original_glyph_control_guards(self):
        rgba = overlay.render_label(self.font, self.label)
        rows = [any(rgba[(y*64+x)*4+3] for x in range(64)) for y in range(48)]
        self.assertGreater(sum(rows), 15)
        self.assertTrue(any(not rows[y] and any(rows[:y]) and any(rows[y+1:]) for y in range(48)))
        with self.assertRaisesRegex(ValueError, 'missing glyphs'):
            overlay.render_label(self.font, dict(self.label, text='ABAC'))
        with self.assertRaisesRegex(ValueError, 'invalid text layer'):
            overlay.render_label(self.font, dict(self.label, text='AB\nB'))
        with self.assertRaisesRegex(ValueError, 'does not fit'):
            overlay.render_label(self.font, dict(self.label, rect=[0, 0, 64, 8]))

    def test_multiline_window_crops_stitch_without_extra_regions(self):
        whole = overlay.render_label(self.font, self.label)
        pieces = [overlay.render_label(self.font, dict(self.label, rect=[0, 0, 64, 24],
                  render_window=dict(canvas=[64, 48], crop=[0, y, 64, 24]))) for y in [0, 24]]
        self.assertEqual(b''.join(pieces), whole)
