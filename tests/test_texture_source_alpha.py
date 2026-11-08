"""RGB-only restored BC3 artwork can explicitly retain native alpha bytes."""
import copy
import unittest

from tools.patch_tagged_fields import digest
from tools.texture_layout import unit_layout, overlay_rect, decode_texture
from tools.texture_overlay import overlay_profile_regions, compose_restored_region


class SourceAlphaEncodingTests(unittest.TestCase):
    def fixture(self):
        width = height = 32
        layout = unit_layout(width, height, 7)
        rgba = b''.join(bytes([100, 110, 120, (37, 71, 109, 143, 181, 217, 243, 255)[(x+y)%8]])
                        for y in range(height) for x in range(width))
        tiles, _ = overlay_rect(bytes(layout['storage_bytes']), layout, [0, 0, 32, 32], rgba,
                                alpha_encoding='adaptive-range')
        texture = dict(width=width, height=height, format=7, layout=layout, tiles=tiles)
        native = decode_texture(texture)
        mask = bytes([255] + [0]*(width*height-1))
        patch = bytes([220, 40, 70, native[3]]) + bytes((width*height-1)*4)
        label = dict(id='repair', rect=[0, 0, 32, 32],
                     restoration=dict(source_rgba_sha256=digest(native)),
                     _repair_pixels=patch, _repair_mask=mask)
        edit = dict(label='repair', profile=dict(kind='xbox-inline-bc-v1', format=7),
                    channel_mode='rgba', preserve_unchanged_blocks=True,
                    rgb_encoding='weighted-fit-v1', alpha_encoding='preserve-source')
        return texture, native, edit, label, bytes(width*height*4)

    def test_original_alpha_blocks_and_decoded_values_are_exact(self):
        t, native, edit, label, foreground = self.fixture()
        result, proof = overlay_profile_regions(t, edit, {'repair': (label, foreground)})
        self.assertNotEqual(result, t['tiles'])
        for offset in range(0, len(result), 16):
            self.assertEqual(result[offset:offset+8], t['tiles'][offset:offset+8])
        self.assertEqual(decode_texture(t, result)[3::4], native[3::4])
        self.assertEqual(proof['alpha_encoding'], 'preserve-source')
        self.assertTrue(proof['source_alpha_blocks_preserved'])

    def test_changed_repair_alpha_fails_instead_of_silently_reverting_it(self):
        t, _, edit, label, foreground = self.fixture()
        patch = label['_repair_pixels']
        label['_repair_pixels'] = patch[:3] + bytes([255]) + patch[4:]
        with self.assertRaisesRegex(ValueError, 'source alpha'):
            overlay_profile_regions(t, edit, {'repair': (label, foreground)})

    def test_foreground_alpha_change_also_fails(self):
        t, _, edit, label, foreground = self.fixture()
        foreground = bytes([1, 2, 3, 255]) + foreground[4:]
        with self.assertRaisesRegex(ValueError, 'source alpha'):
            overlay_profile_regions(t, edit, {'repair': (label, foreground)})

    def test_legacy_default_and_adaptive_encoding_stay_on_their_old_paths(self):
        for mode in (None, 'adaptive-range'):
            t, native, edit, label, foreground = self.fixture()
            if mode is None:
                del edit['alpha_encoding']
            else:
                edit['alpha_encoding'] = mode
            result, proof = overlay_profile_regions(t, edit, {'repair': (label, foreground)})
            composed = compose_restored_region(label, foreground, native, 32)
            expected, _ = overlay_rect(t['tiles'], t['layout'], label['rect'], composed,
                                       alpha_encoding=mode, rgb_encoding='weighted-fit-v1')
            # The existing unchanged-block preservation retains every other cell.
            offset = t['layout']['offsets'][0]
            self.assertEqual(result[offset:offset+16], expected[offset:offset+16])
            for other in t['layout']['offsets'][1:]:
                self.assertEqual(result[other:other+16], t['tiles'][other:other+16])
            self.assertNotIn('source_alpha_blocks_preserved', proof)

    def test_incompatible_profile_or_missing_preservation_rejects(self):
        t, _, edit, label, foreground = self.fixture()
        for key, value in (('preserve_unchanged_blocks', False), ('channel_mode', 'opaque-rgb')):
            bad = dict(edit, **{key: value})
            with self.subTest(field=key), self.assertRaises(ValueError):
                overlay_profile_regions(t, bad, {'repair': (label, foreground)})
        bad_t = copy.deepcopy(t); bad_t['format'] = 5
        with self.assertRaises(ValueError):
            overlay_profile_regions(bad_t, edit, {'repair': (label, foreground)})


if __name__ == '__main__':
    unittest.main()
