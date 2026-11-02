import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image

from tools.audit_ui_texture_polish import clean_block_differences, scaled_center
from tools.patch_tagged_fields import digest
from tools.texture_layout import overlay_rect, rect_units
from test_runtime_package import fixture, texture


class TexturePolishTests(unittest.TestCase):
    def test_visible_frame_excludes_the_asymmetric_bottom_shadow(self):
        center = scaled_center([3, 3, 125, 56], [128, 64], [96, 41])
        self.assertEqual(center, [48, 18.8984375])
        self.assertEqual(20.5-center[1], 1.6015625)
        self.assertNotEqual(center, [48, 20.5])

    def test_visible_frame_rejects_empty_and_out_of_texture_bounds(self):
        for box, size in [([0, 1, 0, 2], [128, 64]), ([0, 0, 129, 64], [128, 64]),
                          ([0, 0, 4, 4], [0, 64])]:
            with self.assertRaises(ValueError):
                scaled_center(box, size, [96, 41])

    def test_old_shadow_inside_a_text_cell_is_a_real_native_failure(self):
        _, _, _, tx = texture(fixture())
        label = dict(rect=[0, 0, 4, 4])
        clean = bytes([240, 220, 180, 255])*8 + bytes(4)*8
        clean_tiles, _ = overlay_rect(tx['tiles'], tx['layout'], label['rect'], clean,
                                     alpha_encoding='adaptive-range')
        actual = dict(tx, tiles=clean_tiles)
        with patch('tools.audit_ui_texture_polish.render_label', return_value=clean):
            self.assertEqual(clean_block_differences(actual, label, b'font'), 0)
            ghost = clean[:-4] + bytes([16, 16, 16, 190])
            dirty, _ = overlay_rect(clean_tiles, tx['layout'], label['rect'], ghost,
                                    alpha_encoding='adaptive-range')
            self.assertEqual(clean_block_differences(dict(tx, tiles=dirty), label, b'font'), 1)
            # An unrelated block must neither satisfy nor invalidate this cell.
            outside = rect_units(tx['layout'], [4, 0, 4, 4])[0]
            extra = bytearray(clean_tiles); extra[outside] ^= 1
            self.assertEqual(clean_block_differences(dict(tx, tiles=bytes(extra)), label, b'font'), 0)

    def test_invisible_rgb_and_equivalent_encodings_are_not_residue(self):
        _, _, _, tx = texture(fixture())
        label = dict(rect=[0, 0, 4, 4])
        invisible = bytes([240, 150, 100, 0])*16
        tiles, _ = overlay_rect(tx['tiles'], tx['layout'], label['rect'], invisible,
                                alpha_encoding='adaptive-range')
        with patch('tools.audit_ui_texture_polish.render_label', return_value=bytes(64)):
            self.assertEqual(clean_block_differences(dict(tx, tiles=tiles), label, b'font'), 0)

    def test_locale_revision_clears_only_the_two_owned_cells(self):
        root = Path(__file__).resolve().parents[1]
        path = root/'locales/zh-Hans/texture-overlays/ui-polish-v14.json'
        plan = json.loads(path.read_bytes())
        info = [r for r in plan['labels'] if r['id'].startswith('style_info_')]
        old = json.loads((root/'locales/zh-Hans/texture-overlays/save-slot-labels.json').read_bytes())
        self.assertEqual(len(info), 2)
        for a, b in zip(info, old['labels'], strict=True):
            a, b = copy.deepcopy(a), copy.deepcopy(b)
            new_restoration = a.pop('restoration'); old_restoration = b.pop('restoration')
            self.assertEqual(a, b)
            self.assertEqual(new_restoration['source_rgba_sha256'], old_restoration['source_rgba_sha256'])
            for key in ('mask', 'patch'):
                p = root/new_restoration[key]['path']
                self.assertEqual(digest(p.read_bytes()), new_restoration[key]['sha256'])
                with Image.open(p) as im:
                    self.assertEqual(im.size, (80, 16))
                    self.assertEqual(set(im.tobytes()), {255} if key == 'mask' else {0})
        for s in plan['sources']:
            for t in s['textures']:
                if 'Field_MainMenu_Info_Tex04' in t['object']:
                    self.assertTrue(t['preserve_unchanged_blocks'])
                    self.assertEqual(len(t['protected_regions']), 3)

    def test_only_the_equipment_label_shrinks_in_both_native_states(self):
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root/'locales/zh-Hans/texture-overlays/ui-polish-v14.json').read_bytes())
        old = json.loads((root/'locales/zh-Hans/texture-overlays/ui-labels-gameplay-v9.json').read_bytes())
        old = {r['id']: r for r in old['labels']}
        rows = [r for r in plan['labels'] if r['text'] == '辅助装备']
        self.assertEqual(len(rows), 2)
        for row in rows:
            expected = copy.deepcopy(old[row['id']])
            expected['appearance']['ink_box'][3] = 17
            self.assertEqual(row, expected)
        self.assertEqual(len(plan['labels']), 4)

    def test_equipment_retains_font_size_and_centers_in_the_sampled_window(self):
        target = scaled_center([3, 3, 125, 56], [128, 64], [87, 43])
        # Atlas row begins at 88; its consumer begins at V=90, not V=88.
        ink = [9, 7-2, 77, 24-2]
        old = [1+(ink[0]+ink[2])/2, 5+(ink[1]+ink[3])/2]
        new = [.5+(ink[0]+ink[2])/2, 6.3203125+(ink[1]+ink[3])/2]
        self.assertNotEqual(old, target)
        self.assertEqual(new, target)
        root = Path(__file__).resolve().parents[1]
        audit = json.loads((root/'locales/zh-Hans/ui-polish-audit-v14.json').read_bytes())
        spec = next(b for b in audit['buttons'] if b['name'] == '辅助装备')
        self.assertTrue(spec['verify_v'])
        self.assertEqual(spec['tolerance'], .01)
        self.assertEqual({tuple(s['uv']) for s in spec['states']}, {(0, 90, 88, 29)})

    def test_source_locked_profiles_have_only_requested_position_edits(self):
        root = Path(__file__).resolve().parents[1]
        for disc in (1, 2):
            profile = json.loads((root/f'locales/zh-Hans/ui-polish-revision-v14-disc{disc}.json').read_bytes())
            self.assertEqual(len(profile['sources']), 4)
            self.assertEqual(len(profile['transfers']), 6)
            self.assertFalse(profile['text_plans'] + profile['font_metrics'] + profile['alpha_filters'])
            for ref in [profile['overlay'], profile['field_plans'][0]['plan']]:
                self.assertEqual(digest((root/ref['path']).read_bytes()), ref['sha256'])
            fields = json.loads((root/profile['field_plans'][0]['plan']['path']).read_bytes())
            self.assertEqual(len(fields['objects']), 4)
            for obj in fields['objects'][:3]:
                self.assertEqual(len(obj['fields']), 1)
                field = obj['fields'][0]
                self.assertEqual(field['property_path'][-1], dict(name='Value', array_index=1))
                self.assertEqual(field['before']-field['after'], 1.6015625)
            equip = fields['objects'][3]
            self.assertTrue(equip['object_path'].endswith('CategoryBox_3.Category_3'))
            self.assertEqual([(f['before'], f['after']) for f in equip['fields']],
                             [(1, .5), (5, 6.3203125)])


if __name__ == '__main__':
    unittest.main()
