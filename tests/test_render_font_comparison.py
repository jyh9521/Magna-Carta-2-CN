"""Font-preview regressions use a generated, redistributable two-glyph fixture."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

from tools import render_font_comparison as preview


def font_fixture(path):
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(['.notdef', 'A', 'B'])
    builder.setupCharacterMap({65: 'A', 66: 'B'})
    glyphs = {}
    for name in ('.notdef', 'A', 'B'):
        pen = TTGlyphPen(None)
        if name != '.notdef':
            pen.moveTo((40, 0))
            pen.lineTo((40, 680))
            pen.lineTo((400 if name == 'A' else 300, 680))
            pen.lineTo((400, 0))
            pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (500, 40) for name in glyphs})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable(dict(familyName='Preview Fixture', styleName='Regular',
                               psName='PreviewFixture-Regular', fullName='Preview Fixture Regular'))
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.save(path)


class FontComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'build').mkdir()
        self.font = self.root / 'build/fixture.ttf'
        font_fixture(self.font)
        self.face = dict(id='Fixture', label='Fixture', path='build/fixture.ttf',
                         sha256=preview.sha(self.font.read_bytes()), postscript_name='PreviewFixture-Regular',
                         release='fixture', download_url='https://example.invalid/font.ttf')
        self.text_ref = self.write_json('source.json', {'entries': [dict(id='line:1', translation='AB\\nBA')]})
        self.text_ref['entry_id'] = 'line:1'
        self.roles = []
        for size, height in [(15, 18), (22, 25), (27, 29)]:
            plan = dict(font_size=size, metric_height=height, ink_padding=dict(left=2, right=3),
                        wide_letter_advance=size+5)
            ref = self.write_json(f'role-{size}.json', plan)
            self.roles.append(dict(label=f'Size {size}', object=f'Fixture{size}',
                                   shadow=size == 27, effect_label='White', glyph_source=ref,
                                   canonical_sha256=preview.canonical(plan)))
        self.profile = dict(kind='dynamic-font-comparison', locale='en', fonts=[self.face],
                            roles=self.roles, label_font=self.face, text_source=self.text_ref,
                            overview_title='Font comparison', overview_note='1x specimen',
                            light_title='Light background', footer='Offline specimen',
                            source_label='Fixture text', comparison_link='Comparison')
        self.profile_path = self.root / 'profile.json'
        self.save_profile()

    def write_json(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding='utf-8')
        return dict(path=name, sha256=preview.sha(path.read_bytes()))

    def save_profile(self):
        self.profile_path.write_text(json.dumps(self.profile), encoding='utf-8')

    def test_confined_paths(self):
        self.assertEqual(preview.local(self.root, 'build/fixture.ttf'), self.font)
        for path in ('..', '../outside.ttf', '.', '', str(self.font)):
            with self.subTest(path=path), self.assertRaises(ValueError):
                preview.local(self.root, path)

    def test_input_hash_mismatch_is_rejected(self):
        bad = dict(self.face, sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            preview.locked(self.root, bad)

    def test_explicit_text_identity_accepts_crlf_and_lf_without_mutating_source(self):
        raw = b'{"entries": []}\n'
        path = self.root/'text.json'
        ref = dict(path='text.json', sha256=preview.sha(raw), identity_mode='utf8-lf')
        for data in (raw, raw.replace(b'\n', b'\r\n')):
            path.write_bytes(data)
            self.assertEqual(preview.locked(self.root, ref)[1], data)
            self.assertEqual(path.read_bytes(), data)
        path.write_bytes(b'{"entries": [1]}\n')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            preview.locked(self.root, ref)

    def test_unknown_identity_mode_and_bare_cr_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'identity mode'):
            preview.locked(self.root, dict(self.face, identity_mode='ignore-changes'))
        path = self.root/'text.json'
        path.write_bytes(b'line\rbreak')
        with self.assertRaisesRegex(ValueError, 'bare CR'):
            preview.locked(self.root, dict(path='text.json', sha256='0'*64, identity_mode='utf8-lf'))

    def test_source_text_keeps_content_and_decodes_only_linebreak(self):
        self.assertEqual(preview.source_text(self.root, self.text_ref), 'AB\nBA')
        self.assertEqual(json.loads((self.root/'source.json').read_bytes())['entries'][0]['translation'], 'AB\\nBA')

    def test_missing_or_duplicate_source_id_is_rejected(self):
        for entries in ([], [dict(id='x', translation='A')],
                        [dict(id='line:1', translation='A')]*2):
            ref = self.write_json('bad-text.json', dict(entries=entries))
            ref['entry_id'] = 'line:1'
            with self.subTest(entries=entries), self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
                preview.source_text(self.root, ref)

    def test_control_or_empty_text_is_rejected(self):
        for text in ('', ' ', 'A\tB', 'A'*1001):
            ref = self.write_json('bad-text.json', dict(entries=[dict(id='x', translation=text)]))
            ref['entry_id'] = 'x'
            with self.subTest(length=len(text)), self.assertRaises(ValueError):
                preview.source_text(self.root, ref)

    def test_roles_are_locked_to_three_distinct_sizes(self):
        specs = preview.role_specs(self.root, self.roles)
        self.assertEqual([s['font_size'] for s in specs], [15, 22, 27])
        with self.assertRaisesRegex(ValueError, 'distinct'):
            preview.role_specs(self.root, self.roles[:1]*3)
        changed = copy.deepcopy(self.roles)
        changed[0]['canonical_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'canonical'):
            preview.role_specs(self.root, changed)

    def test_real_rasterizer_cmap_baseline_and_shadow(self):
        specs = preview.role_specs(self.root, self.roles)
        for spec in specs:
            glyphs, proof = preview.raster_font(self.font, self.face, spec, 'AB\nBA')
            self.assertEqual(set(glyphs), {'A', 'B'})
            self.assertEqual(proof['missing_glyphs'], 0)
            self.assertFalse(proof['foreground_clipping'])
            self.assertEqual(len({r['cell_baseline'] for r in proof['raster_records']}), 1)
            self.assertEqual(proof['added_shadow_pixels'] > 0, spec['shadow'])

    def test_wrong_face_and_missing_glyph_are_rejected(self):
        spec = preview.role_specs(self.root, self.roles)[0]
        with self.assertRaisesRegex(ValueError, 'Wrong font face'):
            preview.raster_font(self.font, dict(self.face, postscript_name='WrongFace'), spec, 'A')
        with self.assertRaisesRegex(ValueError, 'cmap'):
            preview.raster_font(self.font, self.face, spec, '未')

    def test_opt_in_weight_strokes_outlines_but_preserves_metrics(self):
        spec = preview.role_specs(self.root, self.roles)[1]
        original, before = preview.raster_font(self.font, self.face, spec, 'A B')
        face = dict(self.face, embolden=dict(target_weight=500, stroke_em=0.006))
        bold, after = preview.raster_font(self.font, face, spec, 'A B')
        self.assertEqual(before['glyph_plan'], after['glyph_plan'])
        self.assertEqual(before['raster_records'], after['raster_records'])
        self.assertEqual([g.size for g in original.values()], [g.size for g in bold.values()])
        self.assertEqual(after['source_weight_class'], 400)
        self.assertEqual(after['requested_weight'], 500)
        self.assertTrue(after['synthetic_weight'])
        self.assertEqual(after['weight_method'], 'freetype-fractional-outline-stroke-v1')
        self.assertGreater(after['alpha_sum_after'], after['alpha_sum_before'])
        self.assertNotEqual(before['rgba_sha256'], after['rgba_sha256'])
        self.assertIsNone(bold[' '].getbbox())
        self.assertEqual(preview.sha(self.font.read_bytes()), self.face['sha256'])

    def test_weight_none_keeps_regular_pixels_identical(self):
        spec = preview.role_specs(self.root, self.roles)[2]
        _, before = preview.raster_font(self.font, self.face, spec, 'AB')
        _, after = preview.raster_font(self.font, dict(self.face, embolden=None), spec, 'AB')
        self.assertEqual(before['rgba_sha256'], after['rgba_sha256'])
        self.assertFalse(after['synthetic_weight'])
        self.assertEqual(after['source_weight_class'], after['requested_weight'])

    def test_synthetic_weight_requires_explicit_bounded_parameters(self):
        spec = preview.role_specs(self.root, self.roles)[0]
        for settings in ({}, {'target_weight': 500}, {'target_weight': 400, 'stroke_em': 0.006},
                         {'target_weight': 500, 'stroke_em': True},
                         {'target_weight': 500, 'stroke_em': 0},
                         {'target_weight': 500, 'stroke_em': float('nan')},
                         {'target_weight': 500, 'stroke_em': 0.03},
                         {'target_weight': 500, 'stroke_em': 0.006, 'blur': True}):
            with self.subTest(settings=settings), self.assertRaisesRegex(ValueError, 'synthetic weight'):
                preview.raster_font(self.font, dict(self.face, embolden=settings), spec, 'A')

    def test_outline_stroke_preserves_original_alpha_and_cell_bounds(self):
        spec = preview.role_specs(self.root, self.roles)[2]
        plan = preview.make_glyph_plan(self.font, spec, 'A')
        alphas, records = preview.rasterize_plan(self.font, self.face['sha256'], plan)
        font = preview.ImageFont.truetype(str(self.font), spec['font_size'])
        cell = plan['glyphs'][0]
        original = alphas[ord('A')]
        changed, report = preview.embolden_glyph(font, cell, records[0], original, spec['metric_height'], 0.006)
        self.assertEqual(len(changed), len(original))
        self.assertTrue(all(a <= b for a, b in zip(original, changed)))
        self.assertEqual(sum(changed)-sum(original), report['added_alpha'])
        for y in range(cell['height']):
            for x in range(cell['width']):
                if x >= cell['metric_width'] or y >= spec['metric_height']:
                    self.assertEqual(changed[y*cell['width']+x], original[y*cell['width']+x])

    def test_zero_outline_stroke_is_exact_identity(self):
        alpha = bytes(range(16))
        output, record = preview.embolden_glyph(None, {}, {'raster_bbox': None}, alpha, 4, 0)
        self.assertEqual(output, alpha)
        self.assertEqual(record, {'added_alpha': 0, 'boundary_samples': 0})

    def test_outline_stroke_invalid_amounts_rejected(self):
        for strength in (-1, True, float('nan'), float('inf'), 0.03, '0.006'):
            with self.subTest(strength=strength), self.assertRaises(ValueError):
                preview.embolden_glyph(None, {}, {}, bytes(16), 4, strength)

    def test_zhuque_profile_labels_synthetic_weight_without_replacing_font(self):
        root = Path(__file__).resolve().parents[1]
        profile = json.loads((root/'locales/zh-Hans/font-preview-zhuque-medium.json').read_bytes())
        regular, medium = profile['fonts']
        for key in ('path', 'sha256', 'postscript_name'):
            self.assertEqual(regular[key], medium[key])
        self.assertNotIn('embolden', regular)
        self.assertEqual(medium['embolden'], {'target_weight': 500, 'stroke_em': 0.006})
        self.assertIn('合成', medium['label'])

    def test_plan_never_implicitly_in_game_verified(self):
        spec = preview.role_specs(self.root, self.roles)[0]
        plan = preview.make_glyph_plan(self.font, spec, 'AB')
        self.assertIs(plan['in_game_verified'], False)
        self.assertTrue(all(g['width'] % 4 == g['height'] % 4 == 0 for g in plan['glyphs']))
        spaced = preview.make_glyph_plan(self.font, spec, 'A B')
        self.assertEqual(spaced['glyphs'][0]['layout'], 'blank-advance')
        glyphs, proof = preview.raster_font(self.font, self.face, spec, 'A B')
        self.assertIsNone(glyphs[' '].getbbox())
        self.assertFalse(proof['foreground_clipping'])
        with self.assertRaisesRegex(ValueError, 'control separator'):
            preview.make_glyph_plan(self.font, spec, 'A\tB')

    def test_linebreak_and_no_auto_shrink(self):
        glyph = Image.new('RGBA', (10, 18), '#ffffff')
        image, widths = preview.line_image({'A': glyph}, 'AA\nA', 18, 20)
        self.assertEqual(widths, [20, 10])
        self.assertEqual(image.size, (20, 50))
        with self.assertRaisesRegex(ValueError, 'never silently shrink'):
            preview.line_image({'A': glyph}, 'AAA', 18, 20)

    def test_bc3_white_and_shadow_preserve_black_white_pixels(self):
        alpha = bytes([255 if x == y == 1 else 0 for y in range(4) for x in range(4)])
        rgba = preview.bc3_white(alpha, 4, 4)
        self.assertEqual(rgba[20:24], b'\xff\xff\xff\xff')
        shaded, count, clipped = preview.shadow_pixels(rgba, 4, 4, 4, 4)
        result = preview.bc3_rgba(shaded, 4, 4)
        self.assertEqual((count, clipped), (1, 0))
        self.assertEqual(result[20:24], b'\xff\xff\xff\xff')
        self.assertEqual(result[40:44], b'\x00\x00\x00\xff')

    def test_existing_and_nonbuild_outputs_are_rejected(self):
        for destination in (self.root/'build', self.root/'dist/new', self.root/'../outside'):
            with self.subTest(path=destination), self.assertRaisesRegex(ValueError, 'new child'):
                preview.render(self.profile_path, self.root, destination)

    def test_render_reopens_images_checks_hashes_and_preserves_inputs(self):
        expected = preview.sha(self.font.read_bytes())
        report = preview.render(self.profile_path, self.root, self.root/'build/output')
        self.assertEqual(report['sizes'], [15, 22, 27])
        self.assertEqual(len(report['outputs']), 3)
        self.assertFalse(report['game_resources_written'])
        self.assertFalse(report['game_rendering_verified'])
        self.assertEqual(preview.sha(self.font.read_bytes()), expected)
        for result in report['outputs']:
            path = self.root/'build/output'/result['path']
            with Image.open(path) as image:
                image.load()
                self.assertEqual(list(image.size), result['size'])
            self.assertEqual(preview.sha(path.read_bytes()), result['sha256'])

    def test_duplicate_or_unsafe_ids_rejected_before_output(self):
        for faces in ([self.face, self.face], [dict(self.face, id='../unsafe')]):
            self.profile['fonts'] = faces
            self.save_profile()
            with self.assertRaises(ValueError):
                preview.render(self.profile_path, self.root, self.root/'build/output')
            self.assertFalse((self.root/'build/output').exists())

    def fetch_spec(self):
        return dict(path='build/download/font.ttf', sha256=preview.sha(b'font'),
                    download_url='https://example.invalid/font.ttf',
                    license_path='build/download/LICENSE', license_sha256=preview.sha(b'license'),
                    license_url='https://example.invalid/LICENSE')

    def test_fetch_is_hash_locked_and_never_installs(self):
        item = self.fetch_spec()
        with patch.object(preview.urllib.request, 'urlopen', side_effect=[io.BytesIO(b'font'), io.BytesIO(b'license')]):
            preview.fetch_fonts(dict(fonts=[item]), self.root)
        self.assertEqual((self.root/item['path']).read_bytes(), b'font')
        with patch.object(preview.urllib.request, 'urlopen') as network:
            preview.fetch_fonts(dict(fonts=[item]), self.root)
            network.assert_not_called()

    def test_fetch_mismatch_unsafe_path_and_http_rejected(self):
        item = self.fetch_spec()
        with patch.object(preview.urllib.request, 'urlopen', return_value=io.BytesIO(b'wrong')):
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                preview.fetch_fonts(dict(fonts=[item]), self.root)
        self.assertFalse((self.root/item['path']).exists())
        for changed in (dict(item, path='dist/font.ttf'),
                        dict(item, download_url='http://example.invalid/font.ttf')):
            with self.assertRaises(ValueError):
                preview.fetch_fonts(dict(fonts=[changed]), self.root)

    def test_archive_member_is_selected_without_extracting_other_files(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('nested/font.ttf', b'font')
            z.writestr('../do-not-extract.txt', b'other')
        item = dict(self.fetch_spec(), archive_sha256=preview.sha(archive.getvalue()))
        with patch.object(preview.urllib.request, 'urlopen', side_effect=[io.BytesIO(archive.getvalue()), io.BytesIO(b'license')]):
            preview.fetch_fonts(dict(fonts=[item]), self.root)
        self.assertEqual((self.root/item['path']).read_bytes(), b'font')
        self.assertFalse((self.root.parent/'do-not-extract.txt').exists())

    def test_repository_profile_has_user_selected_slab_variant_and_all_sizes(self):
        root = Path(__file__).resolve().parents[1]
        profile = json.loads((root/'locales/zh-Hans/font-preview-candidates.json').read_bytes())
        self.assertEqual([f['postscript_name'] for f in profile['fonts']],
                         ['LXGWZhenKaiSlabGB-Regular', 'LXGWWenKai-Medium',
                          'ZhuqueFangsong-Regular', 'LXGWNeoZhiSongPlus', 'LXGWNeoXiHeiPlus'])
        self.assertEqual([r['font_size'] for r in preview.role_specs(root, profile['roles'])], [15, 22, 27])
        self.assertIn('怪物兵器“哨兵”', preview.source_text(root, profile['text_source']))


if __name__ == '__main__':
    unittest.main()
