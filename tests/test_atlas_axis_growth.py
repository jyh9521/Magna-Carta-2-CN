"""Synthetic package/block tests for explicitly bounded width retile."""
import hashlib
import unittest

from tools import supplement_font as s
from tools.ue3_package import parse_tables
from test_supplement_font import package_fixture, plan, stored_decoder, NAMES


def build(p, compressed=False, raw=True):
    source = package_fixture(texture_compressed=compressed)
    output, report = s.supplement_package(source, hashlib.sha256(source).hexdigest(), 'General', p,
        {ord(g['character']): bytes([255]) * g['width'] * g['height'] for g in p['glyphs']},
        stored_decoder, raw_atlas=raw)
    return source, output, report


def atlas(data):
    tables = parse_tables(data); e = tables['exports'][1]
    payload = data[e['serial_offset']:e['serial_offset'] + e['serial_size']]
    return payload, s.parse_atlas_payload(payload, NAMES, e['serial_offset'])


def serial_offset(texture):
    b = texture['source_art']
    return b['data_offset'] - b['payload_offset']


class AtlasAxisGrowthTests(unittest.TestCase):
    def test_width_only_package_growth_preserves_old_records(self):
        p = plan(); p['atlas_width'] = 256; p['glyphs'][0]['x'] = 136
        original, output, r = build(p)
        _, tex = atlas(output)
        self.assertEqual((tex['width'], tex['height']), (256, 128))
        self.assertTrue(r['original_glyphs_and_remap_preserved'])
        self.assertTrue(r['original_glyph_rect_pixels_identical'])

    def test_two_axes_have_honest_block_relocation_report(self):
        p = plan(); p.update(atlas_width=256, atlas_height=256)
        p['glyphs'][0].update(x=136, y=136)
        _, _, r = build(p)
        self.assertFalse(r['atlas_growth']['original_tiled_bytes_retained'])
        self.assertTrue(r['atlas_growth']['original_block_values_relocated'])
        self.assertTrue(r['atlas_growth']['original_decoded_rectangle_identical'])

    def test_compressed_original_atlas_is_supported_without_pixel_reencoding(self):
        p = plan(); p['atlas_width'] = 256; p['glyphs'][0]['x'] = 136
        _, _, r = build(p, compressed=True)
        self.assertTrue(r['all_pixels_outside_selected_cells_identical'])
        self.assertTrue(r['original_glyph_rect_pixels_identical'])

    def test_tagged_native_dimensions_and_bulk_size_agree(self):
        p = plan(); p.update(atlas_width=256, atlas_height=256)
        _, output, _ = build(p); _, tex = atlas(output)
        self.assertEqual((tex['mips'][0]['width'], tex['mips'][0]['height']), (256, 256))
        self.assertEqual(tex['mips'][0]['bulk']['element_count'], 256 * 256)
        self.assertEqual(tex['mips'][0]['bulk']['size_on_disk'], 256 * 256)

    def test_original_padding_blocks_keep_exact_values_at_new_addresses(self):
        source = package_fixture(); raw, tex = atlas(source)
        old = s.atlas_tiles(raw, tex, stored_decoder)
        changed, parsed = s.grow_atlas_axes(raw, NAMES, serial_offset(tex), tex, 256, 256, stored_decoder)
        new = s.atlas_tiles(changed, parsed, stored_decoder)
        for y in range(32):
            for x in range(32):
                a = s.xbox_tiled_block_offset(x, y, 32) * 16
                b = s.xbox_tiled_block_offset(x, y, 64) * 16
                self.assertEqual(old[a:a + 16], new[b:b + 16])

    def test_invalid_widths_and_bool_are_rejected(self):
        for w in [False, 0, 64, 192, 4096]:
            p = plan(); p['atlas_width'] = w
            with self.subTest(width=w), self.assertRaises(ValueError): build(p)

    def test_implicit_raw_and_no_growth_are_rejected(self):
        p = plan(); p['atlas_width'] = 256
        with self.assertRaisesRegex(ValueError, 'explicit raw_atlas'): build(p, raw=False)
        p['atlas_width'] = 128
        with self.assertRaisesRegex(ValueError, 'nonshrinking'): build(p)

    def test_shrink_is_rejected_at_primitive_boundary(self):
        raw, tex = atlas(package_fixture())
        for w, h in [(64, 256), (256, 64), (128, 128), (True, 256)]:
            with self.subTest(size=(w, h)), self.assertRaises(ValueError):
                s.grow_atlas_axes(raw, NAMES, serial_offset(tex), tex, w, h, stored_decoder)

    def test_old_vertical_path_keeps_identical_package_bytes(self):
        p = plan(); p['atlas_height'] = 256; p['glyphs'][0]['y'] = 136
        _, old, _ = build(p)
        p['atlas_width'] = 128
        _, new, _ = build(p)
        self.assertEqual(old, new)

    def test_repeated_width_growth_is_deterministic(self):
        p = plan(); p['atlas_width'] = 256; p['glyphs'][0]['x'] = 136
        original, one, _ = build(p); _, two, _ = build(p)
        self.assertEqual(one, two); self.assertEqual(original, package_fixture())

    def test_noop_height_is_allowed_when_only_width_grows(self):
        raw, tex = atlas(package_fixture())
        changed, parsed = s.grow_atlas_axes(raw, NAMES, serial_offset(tex), tex, 256, 128, stored_decoder)
        self.assertEqual((parsed['width'], parsed['height']), (256, 128))
        self.assertNotEqual(raw, changed)


if __name__ == '__main__':
    unittest.main()
