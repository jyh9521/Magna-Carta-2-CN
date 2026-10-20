"""Bounded count opt-in does not replace geometry or character validation."""
import unittest
from tools import supplement_font as s
from tools.prepare_text_sample import prepare
from test_supplement_font import plan, package_fixture, stored_decoder
import hashlib


def many(count, limit=None):
    p = plan()
    p['glyphs'] = [dict(p['glyphs'][0], character=chr(0x4e00+i)) for i in range(count)]
    if limit is not None:
        p['glyph_limit'] = limit
    return p


class GlyphCountOptinTests(unittest.TestCase):
    def test_default_stays_128(self):
        self.assertEqual(len(s.validate_plan(many(128))), 128)
        with self.assertRaisesRegex(ValueError, '1..128 glyphs'):
            s.validate_plan(many(129))

    def test_explicit_large_counts(self):
        for n in (2048, 2049, 2388, 2389, 4096):
            with self.subTest(n=n):
                self.assertEqual(len(s.validate_plan(many(n, n))), n)

    def test_bad_limits(self):
        for limit in (True, False, 0, -1, 4097, 1.5, '4096', None):
            with self.subTest(limit=limit), self.assertRaisesRegex(ValueError, 'glyph_limit'):
                s.validate_plan(many(1, limit) if limit is not None else dict(many(1), glyph_limit=None))

    def test_excess_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '1..4096 glyphs'):
            s.validate_plan(many(4097, 4096))

    def test_duplicate_in_large_plan_is_rejected(self):
        p = many(2389, 4096); p['glyphs'][-1]['character'] = p['glyphs'][0]['character']
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            s.validate_plan(p)

    def test_layout_and_control_are_still_rejected(self):
        for char in ('\t', '\u3000', '\n', '\U00020000', '\ud800'):
            p = many(2049, 4096); p['glyphs'][-1]['character'] = char
            with self.subTest(char=repr(char)), self.assertRaisesRegex(ValueError, 'printable BMP'):
                s.validate_plan(p)

    def test_count_does_not_bypass_placement_overlap(self):
        p = many(2049, 4096); b = package_fixture()
        with self.assertRaisesRegex(ValueError, 'overlap'):
            s.supplement_package(b, hashlib.sha256(b).hexdigest(), 'General', p, {}, stored_decoder)

    def test_prepare_accepts_count_but_checks_output(self):
        # Existing current directory is invalid; no file is read or written.
        with self.assertRaisesRegex(ValueError, 'output must be new'):
            prepare(None, None, '.', '.', None, '.', None, glyph_limit=4096)

    def test_prepare_rejects_invalid_limit_before_io(self):
        for limit in (True, 0, 4097):
            with self.subTest(limit=limit), self.assertRaisesRegex(ValueError, 'glyph_limit'):
                prepare(None, None, '.', '.', None, '.', None, glyph_limit=limit)
