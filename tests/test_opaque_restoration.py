import hashlib
import struct
import unittest

from tools import texture_layout as layout, texture_overlay as overlay


class OpaqueRestorationTests(unittest.TestCase):
    def fixture(self):
        lo = layout.unit_layout(64, 16, 5)
        raw = bytearray(lo['storage_bytes'])
        # Noncanonical, entirely opaque black: re-encoding unchanged pixels
        # would discard these original index bits.
        block = struct.pack('<HHI', 0, 0, 0x55555555)
        native = b''.join(block[i:i+2][::-1] for i in range(0, 8, 2))
        for offset in lo['offsets']:
            raw[offset:offset+8] = native
        tx = dict(layout=lo, width=64, height=16, format=5, tiles=bytes(raw))
        source = overlay.rgba_crop(layout.decode_texture(tx), 64, [8, 4, 8, 8])
        label = dict(rect=[8, 4, 8, 8],
                     restoration=dict(source_rgba_sha256=hashlib.sha256(source).hexdigest()),
                     _repair_mask=bytes([255] + [0]*63),
                     _repair_pixels=bytes([180, 70, 30, 255]) + bytes(252))
        edit = dict(regions=['x'], image_id='owned-opaque-restoration', channel_mode='opaque-rgb',
                    profile=dict(kind=layout.PROFILE, format=5),
                    preserve_unchanged_blocks=True)
        return tx, edit, label

    def test_restoration_keeps_original_compressed_units_for_unchanged_pixels(self):
        tx, edit, label = self.fixture()
        out, proof = overlay.overlay_profile_regions(tx, edit, {'x': (label, bytes(256))})
        units = layout.rect_units(tx['layout'], label['rect'])
        self.assertNotEqual(out[units[0]:units[0]+8], tx['tiles'][units[0]:units[0]+8])
        for offset in units[1:]:
            self.assertEqual(out[offset:offset+8], tx['tiles'][offset:offset+8])
        self.assertEqual(proof['unchanged_region_blocks_preserved'], 3)
        self.assertEqual(proof['changed_blocks'], 1)
        pixels = layout.decode_texture(tx, out)
        self.assertTrue(all(a == 255 for a in pixels[3::4]))

    def test_transparent_repair_pixels_fail_closed(self):
        tx, edit, label = self.fixture()
        label['_repair_pixels'] = bytes([180, 70, 30, 0]) + bytes(252)
        with self.assertRaisesRegex(ValueError, 'opaque restoration'):
            overlay.overlay_profile_regions(tx, edit, {'x': (label, bytes(256))})

    def test_transparent_source_crop_fails_closed(self):
        tx, edit, label = self.fixture()
        raw = bytearray(tx['tiles'])
        offset = layout.rect_units(tx['layout'], label['rect'])[0]
        raw[offset:offset+8] = bytes([0, 0, 0, 0, 255, 255, 255, 255])
        tx['tiles'] = bytes(raw)
        source = overlay.rgba_crop(layout.decode_texture(tx), 64, label['rect'])
        label['restoration']['source_rgba_sha256'] = hashlib.sha256(source).hexdigest()
        with self.assertRaisesRegex(ValueError, 'opaque restoration'):
            overlay.overlay_profile_regions(tx, edit, {'x': (label, bytes(256))})

    def test_explicit_flag_is_boolean_and_requires_restored_rgb(self):
        tx, edit, label = self.fixture()
        for value in [1, 'yes', None]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'preserve unchanged'):
                overlay.overlay_profile_regions(tx, dict(edit, preserve_unchanged_blocks=value), {'x': (label, bytes(256))})
        for change in [dict(channel_mode='opaque-luma'), dict(channel_mode='rgba')]:
            with self.assertRaises(ValueError):
                overlay.overlay_profile_regions(tx, dict(edit, **change), {'x': (label, bytes(256))})
        label.pop('restoration')
        with self.assertRaisesRegex(ValueError, 'restor'):
            overlay.overlay_profile_regions(tx, edit, {'x': (label, bytes(256))})

    def test_default_legacy_rgb_reencodes_authorized_rectangle(self):
        tx, edit, label = self.fixture()
        edit.pop('preserve_unchanged_blocks')
        label.pop('restoration')
        out, proof = overlay.overlay_profile_regions(tx, edit, {'x': (label, bytes(256))})
        self.assertNotIn('unchanged_region_blocks_preserved', proof)
        self.assertEqual(proof['changed_blocks'], 4)


if __name__ == '__main__':
    unittest.main()
