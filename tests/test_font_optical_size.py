import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from tools.audit_font_optical_size import Sampler, ink_box, measure
from tools import reface_font as ref
from test_render_font_comparison import font_fixture
from test_supplement_font import package_fixture


class OpticalFontTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.face = Path(self.temp.name)/'face.ttf'
        font_fixture(self.face)
        self.sha = ref.sha(self.face.read_bytes())
        self.spec = dict(font_size=15, metric_height=24, wide_advance=20,
                         texture_index=0, stroke_em=.006, shadow=False,
                         codepoints=[65])

    def test_explicit_baseline_offset_changes_only_vertical_placement(self):
        old = ref.raster_cells(self.face, self.sha, self.spec, [65], {65:15})[0]
        spec = dict(self.spec, baseline_offset=-1)
        new = ref.raster_cells(self.face, self.sha, spec, [65], {65:15})[0]
        self.assertEqual(new['baseline'], old['baseline']-1)
        self.assertEqual(new['metric_width'], old['metric_width'])
        self.assertEqual(new['metric_height'], old['metric_height'])
        self.assertEqual(new['outline_growth']['boundary_samples'], 0)

    def test_zero_offset_preserves_default_bytes(self):
        a = ref.raster_cells(self.face, self.sha, self.spec, [65], {65:15})
        b = ref.raster_cells(self.face, self.sha, dict(self.spec, baseline_offset=0), [65], {65:15})
        self.assertEqual(a, b)

    def test_out_of_bounds_baseline_is_rejected(self):
        for offset in [True, .5, -100, 100, -20, 10]:
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                ref.raster_cells(self.face, self.sha, dict(self.spec, baseline_offset=offset), [65], {65:15})

    def test_native_sampler_matches_rebuilt_glyph(self):
        data = package_fixture()
        new, proof = ref.reface(data, ref.sha(data), 'General', self.face, self.sha, self.spec)
        sampled = Sampler(new, 'General').glyph(65)
        self.assertEqual(sampled.size, (proof['glyphs'][0]['metric_width'], 24))
        self.assertIsNotNone(ink_box(sampled))
        with self.assertRaisesRegex(ValueError, 'missing mapped'):
            Sampler(new, 'General').glyph(66)

    def test_white_foreground_measurement_excludes_shadow(self):
        im = Image.new('RGBA', (8, 24))
        im.paste((255, 255, 255, 255), (2, 3, 6, 13))
        im.paste((0, 0, 0, 255), (2, 13, 6, 22))
        self.assertEqual(ink_box(im), (2, 3, 6, 13))

    def test_small_digits_fail_then_proportional_digits_pass(self):
        class Fixture:
            def __init__(self, height): self.height = height
            def glyph(self, cp):
                im = Image.new('RGBA', (20, 24))
                im.paste('white', (2, 2, 10, 2+(20 if cp == ord('R') else self.height)))
                return im
        self.assertFalse(measure(Fixture(10), '2', 'R', .85, 1.1)[0]['passed'])
        self.assertTrue(measure(Fixture(19), '2', 'R', .85, 1.1)[0]['passed'])

    def test_equal_height_with_wrong_baseline_fails(self):
        class Fixture:
            def glyph(self, cp):
                im = Image.new('RGBA', (20, 24))
                y = 1 if cp == ord('R') else 5
                im.paste('white', (2, y, 10, y+18))
                return im
        self.assertTrue(measure(Fixture(), '2', 'R', .85, 1.1)[0]['passed'])
        self.assertFalse(measure(Fixture(), '2', 'R', .85, 1.1, 1)[0]['passed'])

    def test_locale_plan_only_selects_numerals_in_all_seven_aliases(self):
        root = Path(__file__).resolve().parents[1]
        p = json.loads((root/'locales/zh-Hans/dynamic-font-numerals-v9.json').read_bytes())
        self.assertEqual(sum(len(s['fonts']) for s in p['sources']), 7)
        for r in p['roles']:
            self.assertEqual(r['codepoints'], list(range(48, 58))+[0xff11])
            self.assertEqual(r['glyph_aliases'], {'１':'1'})
            self.assertEqual(r['stroke_em'], .006)
        self.assertEqual(p['font']['sha256'], '558c62730844fe54ba220146ed62f859d4e2880188d92d985f8921c6e3743bc4')


if __name__ == '__main__':
    unittest.main()
