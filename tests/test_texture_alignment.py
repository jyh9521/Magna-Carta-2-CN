import copy
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from tools.audit_texture_alignment import anchor, foreground_span
from tools.translate_texture_regions import shift_pixels, translate_tiles, build
from tools.texture_layout import unit_layout, overlay_rect, decode_texture, rect_units
from tools.patch_tagged_fields import digest
from tools.replace_texture_regions import replace_tiles, selected
from test_texture_layout import profile_fixture


class TextureAlignmentTests(unittest.TestCase):
    def image(self):
        im = Image.new('RGBA', (32, 16))
        for y in range(4, 12):
            for x in range(8, 16):
                im.putpixel((x, y), (240, 210, 120, 255))
        return im

    def texture(self):
        im = self.image()
        layout = unit_layout(32, 16, 7)
        tiles, _ = overlay_rect(bytes(layout['storage_bytes']), layout, [0, 0, 32, 16], im.tobytes(),
                                alpha_encoding='adaptive-range', rgb_encoding='weighted-fit-v1')
        return dict(layout=layout, tiles=tiles, width=32, height=16, format=7)

    def test_pixel_translation_is_integer_copy_not_resize_or_wrap(self):
        im = self.image()
        out = shift_pixels(im.tobytes(), 32, 16, [5, 0])
        check = Image.frombytes('RGBA', im.size, out)
        self.assertEqual(check.crop((13, 4, 21, 12)).tobytes(), im.crop((8, 4, 16, 12)).tobytes())
        self.assertEqual(check.getchannel('A').getbbox(), (13, 4, 21, 12))

    def test_clipping_even_faint_alpha_is_rejected(self):
        im = self.image()
        im.putpixel((31, 0), (0, 0, 0, 1))
        with self.assertRaisesRegex(ValueError, 'clip'):
            shift_pixels(im.tobytes(), 32, 16, [1, 0])

    def test_invalid_offset_and_pixel_inputs_are_rejected(self):
        for offset in ([True, 0], [0, 0], [32, 0], [1.5, 0], [1], 'x'):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                shift_pixels(self.image().tobytes(), 32, 16, offset)
        with self.assertRaises(ValueError):
            shift_pixels(b'', 32, 16, [1, 0])

    def test_block_aligned_move_is_lossless_and_outside_blocks_stay_exact(self):
        t = self.texture()
        out, proof = translate_tiles(t, [4, 0, 24, 16], [4, 0], 0, 0)
        before = Image.frombytes('RGBA', (32, 16), decode_texture(t))
        after = Image.frombytes('RGBA', (32, 16), decode_texture(t, out))
        self.assertEqual(after.crop((12, 4, 20, 12)).tobytes(), before.crop((8, 4, 16, 12)).tobytes())
        self.assertEqual(proof['alpha_max_delta'], 0)
        self.assertTrue(proof['native_block_copy'])
        for off in rect_units(t['layout'], [0, 0, 4, 16]):
            self.assertEqual(out[off:off+16], t['tiles'][off:off+16])

    def test_sub_block_move_keeps_shape_and_reports_quantization(self):
        t = self.texture()
        out, proof = translate_tiles(t, [4, 0, 24, 16], [5, 0], 24, 48)
        after = Image.frombytes('RGBA', (32, 16), decode_texture(t, out))
        self.assertEqual(after.getchannel('A').getbbox(), (13, 4, 21, 12))
        self.assertFalse(proof['native_block_copy'])

    def test_span_uses_visible_ink_and_excludes_dark_backplate(self):
        im = Image.new('RGBA', (32, 16), (0, 0, 0, 255))
        im.paste(self.image(), (0, 0), self.image())
        self.assertEqual(foreground_span(im, [0, 0, 32, 16], 160, 128), [8, 16])
        self.assertEqual(anchor([8, 17], 'center'), 12.5)
        for mode in ('x', None):
            with self.assertRaises(ValueError):
                anchor([8, 17], mode)
        with self.assertRaises(ValueError):
            foreground_span(im, [-1, 0, 32, 16], 160, 128)

    def test_source_hash_and_new_disjoint_output_guard(self):
        profile = dict(schema_version=1, kind='native-texture-translation-v1', resources=[
            dict(path='a.xxx', sha256='0'*64, discs=[1], textures=[dict(object='x',
                 tiled_sha256='0'*64, operations=[dict(kind='translate',rect=[0,0,4,4],offset=[1,0],
                 max_alpha_delta=24,max_premultiplied_delta=48)])])])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'input'; source.mkdir(); (source/'a.xxx').write_bytes(b'x')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                build(profile, source, root/'output')
            self.assertFalse((root/'output').exists())
            with self.assertRaisesRegex(ValueError, 'disjoint'):
                build(profile, source, source/'output')

    def package(self):
        raw, spec, _ = profile_fixture(width=32, height=16)
        tx = selected(raw, spec['object'], None)[3]
        tiles, _ = overlay_rect(tx['tiles'], tx['layout'], [0, 0, 32, 16], self.image().tobytes(),
                                alpha_encoding='adaptive-range', rgb_encoding='weighted-fit-v1')
        raw, _ = replace_tiles(raw, digest(raw), spec['object'], tiles, [[0, 0, 32, 16]], None)
        raw += bytes((-len(raw)) % 32768)
        op = dict(kind='translate', rect=[4, 0, 24, 16], offset=[5, 0],
                  max_alpha_delta=24, max_premultiplied_delta=48)
        profile = dict(schema_version=1, kind='native-texture-translation-v1', resources=[
            dict(path='owned.xxx', sha256=digest(raw), discs=[1, 2], textures=[
                dict(object=spec['object'], tiled_sha256=digest(tiles), operations=[op])])])
        return raw, profile

    def test_build_reopens_candidate_keeps_input_and_two_disc_identities(self):
        raw, profile = self.package()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'input'; source.mkdir()
            (source/'owned.xxx').write_bytes(raw)
            out = root/'output'; result = build(profile, source, out)
            data = (out/'candidate/owned.xxx').read_bytes()
            self.assertEqual((source/'owned.xxx').read_bytes(), raw)
            self.assertEqual(digest(data), result['resources'][0]['sha256'])
            for disc in (1, 2):
                replacement = json.loads((out/f'replacements-disc{disc}.json').read_bytes())
                self.assertEqual(replacement['disc'], disc)
                self.assertEqual(replacement['resources'][0]['before_sha256'], digest(raw))
            self.assertTrue(result['operations'][0]['proof']['unselected_exports_preserved'])
            self.assertNotEqual(data, raw)

    def test_texture_hash_mismatch_is_rejected_before_publication(self):
        raw, profile = self.package()
        profile['resources'][0]['textures'][0]['tiled_sha256'] = '0'*64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'input'; source.mkdir()
            (source/'owned.xxx').write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'texture SHA256'):
                build(profile, source, root/'output')
            self.assertFalse((root/'output').exists())

    def test_unknown_operation_and_overlaps_are_rejected(self):
        raw, profile = self.package()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'input'; source.mkdir()
            (source/'owned.xxx').write_bytes(raw)
            bad = copy.deepcopy(profile)
            bad['resources'][0]['textures'][0]['operations'][0]['kind'] = 'guess'
            with self.assertRaisesRegex(ValueError, 'unknown'):
                build(bad, source, root/'output')
            bad = copy.deepcopy(profile)
            ops = bad['resources'][0]['textures'][0]['operations']
            ops.append(copy.deepcopy(ops[0]))
            with self.assertRaisesRegex(ValueError, 'overlapping'):
                build(bad, source, root/'output')
            self.assertFalse((root/'output').exists())

    def test_translated_latin_subtitle_pixels_stay_outside_native_write_set(self):
        t = self.texture()
        out, _ = translate_tiles(t, [4, 0, 24, 12], [4, 0], 0, 0)
        before = decode_texture(t); after = decode_texture(t, out)
        self.assertEqual(before[12*32*4:], after[12*32*4:])

    def test_locale_contract_covers_all_original_maps_and_split_title(self):
        root = Path(__file__).resolve().parents[1]
        p = json.loads((root/'locales/zh-Hans/texture-alignment-audit-v17.json').read_bytes())
        self.assertEqual((p['reviewed_map_groups'], p['reviewed_map_textures']), (49, 82))
        self.assertEqual(len(p['groups']), 41)
        self.assertEqual(len(p['inline_groups']), 3)
        self.assertEqual(len(p['gaps']), 2)
        highwind = [g for g in p['groups'] if 'highwind' in g['id']]
        self.assertEqual(len(highwind), 2)
        self.assertTrue(all(g['alignment']=='right' and len(g['upper'])==2 for g in highwind))
        self.assertEqual({g['alignment'] for g in p['groups']}, {'left','center','right'})


if __name__ == '__main__':
    unittest.main()
