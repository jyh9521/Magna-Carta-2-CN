import json
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile

from PIL import Image

from tools.audit_font_optical_size import Sampler
from tools.audit_mixed_text_layout import center_error, span, visible_gap
from tools.audit_ui_residency import scan
from tools.build_metric_revision import build
from tools.patch_tagged_fields import digest


class MixedLayoutTests(unittest.TestCase):
    def test_visible_gap_includes_both_cell_bearings(self):
        left = dict(advance=27, box=(2, 1, 23, 21))
        right = dict(advance=12, box=(3, 2, 8, 16))
        self.assertEqual(visible_gap(left, right, 17), 24)
        self.assertEqual(visible_gap(left, right, 0), 7)

    def test_fullwidth_padding_is_measured_in_both_directions(self):
        cjk = dict(advance=26, box=(2, 1, 23, 21))
        wide = dict(advance=27, box=(9, 4, 17, 21))
        tight = dict(advance=15, box=(3, 4, 11, 21))
        self.assertEqual(visible_gap(cjk, wide), 12)
        self.assertEqual(visible_gap(wide, cjk), 12)
        self.assertEqual(visible_gap(cjk, tight), 6)
        self.assertEqual(visible_gap(tight, cjk), 6)

    def test_widget_center_is_not_ink_center(self):
        metrics = dict(height=25, box=(2, 1, 23, 21))
        self.assertAlmostEqual(center_error(metrics, -1.1 + 3, 26, 30), -1.6)
        self.assertAlmostEqual(center_error(metrics, -1.1 + 4.6, 26, 30), 0)

    def test_vertical_clipping_rejected(self):
        with self.assertRaisesRegex(ValueError, 'clips'):
            center_error(dict(height=25), 0, 24, 30)

    def test_native_span_uses_advances_and_visible_union(self):
        class Fixture:
            def glyph(self, cp):
                im = Image.new('RGBA', (20, 25))
                im.paste('white', (3, 1, 17, 21))
                return im
        result = span(Fixture(), 'AB')
        self.assertEqual(result, dict(advance=40, height=25, box=(3, 1, 37, 21)))
        with self.assertRaises(ValueError):
            span(Fixture(), '')

    def test_nonremapped_font_uses_native_identity_not_empty_remap(self):
        ctx = dict(tables=dict(exports=[dict(path='Native', class_path='Engine.Font',
                                             serial_offset=0, serial_size=0)], names=[]))
        with patch('tools.audit_font_optical_size.context', return_value=ctx), \
             patch('tools.audit_font_optical_size.parse_font_payload',
                   return_value=dict(is_remapped=False, remap=[], characters=[{}] * 64)):
            sample = Sampler(b'', 'Native')
        self.assertEqual(sample.mapping[49], 49)
        self.assertNotIn(64, sample.mapping)

    def test_remapped_font_keeps_explicit_mapping(self):
        ctx = dict(tables=dict(exports=[dict(path='Mapped', class_path='Engine.Font',
                                             serial_offset=0, serial_size=0)], names=[]))
        with patch('tools.audit_font_optical_size.context', return_value=ctx), \
             patch('tools.audit_font_optical_size.parse_font_payload',
                   return_value=dict(is_remapped=True, remap=[dict(codepoint=65, glyph_index=0)], characters=[{}])):
            sample = Sampler(b'', 'Mapped')
        self.assertEqual(sample.mapping, {65: 0})

    def test_locale_contract_covers_all_hud_consumers_and_font_copies(self):
        root = Path(__file__).resolve().parents[1] / 'locales/zh-Hans'
        plan = json.loads((root / 'mixed-text-layout-v12.json').read_bytes())
        fields = json.loads((root / 'hud-mixed-fields-v12.json').read_bytes())
        font = json.loads((root / 'mixed-font-padding-v12.json').read_bytes())
        text = json.loads((root / 'mixed-text-v12.json').read_bytes())
        self.assertEqual(len(plan['fonts']), 7)
        self.assertEqual(len(plan['vertical_roles']), 7)
        self.assertEqual(sum(len(r['shadows']) for r in plan['vertical_roles']), 28)
        self.assertEqual(len(fields['objects']), 45)
        self.assertEqual(len(font['codepoints']), 2374)
        self.assertTrue(set(range(48, 58)) | {0xff11} <= set(font['codepoints']))
        self.assertEqual(plan['center_tolerance'], 1.01)
        self.assertEqual(len(text['entries']), 20)
        self.assertEqual(plan['vertical_roles'][-1]['style'], 'names')
        self.assertEqual(plan['styles']['numbers']['states'], 6)

    def test_ui_inventory_finds_shortened_resident_path(self):
        ctx = dict(tables=dict(exports=[dict(path='Scenes.Scene_ButtonA.TextA')]))
        spec = dict(pattern=r'(?:^|\.)Scenes\.Scene_Button[ABX](?:\.|$)', expected={'primary': 1})
        with patch('tools.audit_ui_residency.context', return_value=ctx):
            self.assertTrue(scan([('primary', b'a')], None, spec)['passed'])
            self.assertFalse(scan([('primary', b'a'), ('other', b'a')], None, spec)['passed'])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                scan([('primary', b'a'), ('primary', b'a')], None, spec)

    def test_revision_rejects_unknown_profile_and_source_overlap(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            profile = root / 'plan.json'
            profile.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                build(profile, '0' * 64, root, root / 'source', root / 'out')
            with self.assertRaisesRegex(ValueError, 'unsupported'):
                build(profile, digest(profile.read_bytes()), root, root / 'source', root / 'out')
            profile.write_text(json.dumps(dict(schema_version=1, kind='native-metric-revision')))
            with self.assertRaisesRegex(ValueError, 'disjoint'):
                build(profile, digest(profile.read_bytes()), root, root / 'source', root / 'source/out')


if __name__ == '__main__':
    unittest.main()
