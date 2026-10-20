"""Explicit blank separators do not grant control-character or alias bypasses."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch
from tools import supplement_font as s
from tools.ue3_package import parse_tables
from tools.ue3_fonts import parse_font_payload
from test_supplement_font import plan, package_fixture, stored_decoder, NAMES


def blank(char='\u3000'):
    p = plan(); p['metric_height'] = 23
    p['glyphs'][0].update(character=char, layout='blank-advance', metric_width=22)
    return p


def build(p, alpha=bytes(24*24)):
    b = package_fixture()
    return s.supplement_package(b, s.sha256(b), 'General', p,
        {ord(p['glyphs'][0]['character']): alpha}, stored_decoder)


class BlankAdvanceTests(unittest.TestCase):
    def test_default_rejects_space(self):
        p = blank(); del p['glyphs'][0]['layout']
        with self.assertRaisesRegex(ValueError, 'printable BMP'):s.validate_plan(p)

    def test_only_explicit_zs_separators(self):
        for char in ('\u3000', '\u2002', '\u00a0', ' '):
            with self.subTest(char=repr(char)):self.assertEqual(len(s.validate_plan(blank(char))), 1)

    def test_controls_and_line_separators_rejected(self):
        for char in ('\t', '\n', '\r', '\u200b', '\u2028', '\u2029', '\ud800', '\U00020000'):
            with self.subTest(char=repr(char)), self.assertRaises(ValueError):s.validate_plan(blank(char))

    def test_visible_character_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Zs separator'):s.validate_plan(blank('中'))

    def test_metric_width_required(self):
        p = blank(); del p['glyphs'][0]['metric_width']
        with self.assertRaisesRegex(ValueError, 'explicit metric_width'):s.validate_plan(p)

    def test_metric_width_bounded(self):
        for width in (0, 25, True):
            p = blank(); p['glyphs'][0]['metric_width'] = width
            with self.subTest(width=width), self.assertRaises(ValueError):s.validate_plan(p)

    def test_unknown_layout_rejected(self):
        for layout in (None, True, 'blank', 'alias'):
            p = blank(); p['glyphs'][0]['layout'] = layout
            with self.subTest(layout=layout), self.assertRaisesRegex(ValueError, 'explicit glyph layout'):s.validate_plan(p)

    def test_existing_mapping_replacement_rejected(self):
        p = blank(); p['replace_blank_codepoints'] = [0x3000]
        with self.assertRaisesRegex(ValueError, 'cannot replace'):s.validate_plan(p)

    def test_nonzero_alpha_rejected(self):
        with self.assertRaisesRegex(ValueError, 'all-zero alpha'):build(blank(), bytes([1])+bytes(575))

    def test_alpha_length_still_checked(self):
        with self.assertRaisesRegex(ValueError, 'alpha length'):build(blank(), bytes(575))

    def test_package_records_and_exact_zero_alpha(self):
        output, report = build(blank()); tables = parse_tables(output)
        e = tables['exports'][0]; f = parse_font_payload(output[e['serial_offset']:e['serial_offset']+e['serial_size']], NAMES)
        self.assertEqual(f['remap'][-1]['codepoint'], 0x3000)
        self.assertEqual(f['characters'][-1]['USize'], 22)
        self.assertEqual(f['characters'][-1]['VSize'], 23)
        self.assertTrue(report['original_glyphs_and_remap_preserved'])
        self.assertTrue(report['original_glyph_rect_pixels_identical'])
        self.assertEqual(report['maximum_new_glyph_alpha_error'], 0)
        self.assertEqual(report['explicit_layout_glyphs'], [dict(codepoint=12288,
            metric_width=22, kind='blank-advance', decoded_alpha_zero=True)])
        self.assertFalse(report['runtime_rendering_verified'])

    def test_overlap_still_rejected(self):
        p = blank(); p['glyphs'][0].update(x=0,y=0)
        with self.assertRaisesRegex(ValueError, 'overlap'):build(p)

    def test_mixed_plan_uses_distinct_records_not_space_alias(self):
        p = plan(); p['metric_height'] = 23
        p['glyphs'].append(dict(blank()['glyphs'][0], x=36))
        b = package_fixture()
        _, report = s.supplement_package(b, s.sha256(b), 'General', p,
            {0x4e2d: bytes([255])*(24*23)+bytes(24), 0x3000: bytes(576)}, stored_decoder)
        self.assertEqual(report['added_codepoints'], [0x4e2d,0x3000])
        self.assertEqual(len(report['explicit_layout_glyphs']), 1)

    @unittest.skipUnless(importlib.util.find_spec('PIL') and importlib.util.find_spec('fontTools'), 'optional raster dependencies')
    def test_blank_raster_never_draws_or_requires_separator_cmap(self):
        # Source font identity is still verified; no fabricated ink or cmap alias.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'font'; p.write_bytes(b'fixture')
            for height in (23, 20):
                gp = blank(); gp['metric_height'] = height
                with patch('fontTools.ttLib.TTFont') as tt, patch('PIL.ImageFont.truetype'), patch('PIL.ImageDraw.Draw') as draw:
                    tt.return_value.__enter__.return_value.getBestCmap.return_value = {65:'A'}
                    alphas, reports = s.rasterize_plan(p, s.sha256(b'fixture'), gp)
                    draw.assert_not_called(); self.assertEqual(alphas[12288], bytes(576))
                    self.assertIsNone(reports[0]['raster_bbox'])
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                s.rasterize_plan(p, '0'*64, blank())
