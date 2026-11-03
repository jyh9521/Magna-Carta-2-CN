"""Menu title aliases share a style without erasing their icon or other rows."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.audit_texture_alignment import audit
from tools.patch_tagged_fields import digest
from tools.replace_texture_regions import replace_tiles, selected
from tools.texture_layout import decode_texture, overlay_rect
from tools.texture_overlay import render_label
from tools.ui_ink_revision import clean_alpha
from test_texture_layout import profile_fixture
from test_texture_render_windows import owned_font


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_bytes())


class MenuTitleRevisionTests(unittest.TestCase):
    def test_option_inherits_entire_sibling_style_except_original_placement(self):
        old = read('locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json')
        labels = {l['id']: l for l in old['labels']}
        new = read('locales/zh-Hans/texture-overlays/menu-title-style-v21.json')
        self.assertEqual(len(new['labels']), 1)
        target = new['labels'][0]
        reference = labels['img_ui_name_jpn_159_5']
        for key in ('font', 'font_size', 'style'):
            self.assertEqual(target[key], reference[key])
        expected = copy.deepcopy(reference['appearance'])
        expected['ink_box'] = copy.deepcopy(labels[target['id']]['appearance']['ink_box'])
        expected['ink_box'][0] = reference['rect'][0] + reference['appearance']['ink_box'][0] - target['rect'][0]
        self.assertEqual(target['appearance'], expected)
        for key in ('text', 'rect', 'restoration'):
            self.assertEqual(target[key], labels[target['id']][key])
        self.assertNotEqual(target['font'], labels[target['id']]['font'])
        self.assertEqual(target['appearance']['ink_box'][0], 5)

    def test_full_atlas_family_and_both_physical_aliases_are_bound(self):
        p = read('locales/zh-Hans/texture-overlays/menu-title-cleanup-v21.json')
        self.assertEqual(len(p['resources']), 2)
        for r in p['resources']:
            self.assertEqual(r['discs'], [1, 2])
            self.assertEqual(len(r['textures']), 1)
            op = r['textures'][0]['operations'][0]
            self.assertEqual(op['rectangles'], [[32, 36, 4, 216]])
            self.assertEqual(op['rgb_ceiling'], 96)
        a = read('locales/zh-Hans/menu-title-audit-v21.json')
        self.assertEqual(len(a['gaps']), 14)
        self.assertEqual({g['rect'][1] for g in a['gaps']}, set(range(0, 252, 36)))

    def test_style_revision_is_single_bounded_label_on_each_alias(self):
        p = read('locales/zh-Hans/texture-overlays/menu-title-style-v21.json')
        update = read('locales/zh-Hans/texture-overlays/menu-title-style-update-v21.json')
        self.assertEqual(digest((ROOT / update['overlay_plan']['path']).read_bytes()),
                         update['overlay_plan']['sha256'])
        self.assertEqual(len(p['sources']), 2)
        for s, r in zip(p['sources'], update['resources'], strict=True):
            self.assertEqual(s['path'], r['path'])
            self.assertEqual(s['discs'], [1, 2])
            self.assertEqual(len(s['textures']), 1)
            self.assertTrue(s['textures'][0]['object'].endswith('Big_Title1'))
            self.assertEqual(s['textures'][0]['regions'], ['img_ui_name_jpn_160_0'])
            self.assertEqual(r['rectangles'], [[32, 0, 224, 36]])

    def test_style_mutation_changes_actual_raster_not_only_metadata(self):
        p = read('locales/zh-Hans/texture-overlays/menu-title-style-v21.json')
        target = copy.deepcopy(p['labels'][0]); target['text'] = 'AB'
        expected = render_label(owned_font(), target)
        old = read('locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json')
        old = next(l for l in old['labels'] if l['id'] == target['id'])
        target['appearance'] = old['appearance']
        self.assertNotEqual(expected, render_label(owned_font(), target))

    def test_native_gap_audit_goes_red_green_without_removing_coloured_icon(self):
        raw, spec, _ = profile_fixture(width=64, height=64)
        tx = selected(raw, spec['object'], None)[3]
        im = Image.new('RGBA', (64, 64))
        # A coloured icon fringe and a neighbouring old, dark glyph shadow
        # occupy the same BC3 block, just as in the physical atlas.
        for y in range(36, 56):
            im.putpixel((32, y), (255, 150, 40, 100))
            for x in range(33, 36):
                im.putpixel((x, y), (0, 0, 0, 70))
        tiles, _ = overlay_rect(tx['tiles'], tx['layout'], [0, 0, 64, 64],
                                im.tobytes(), alpha_encoding='adaptive-range',
                                rgb_encoding='weighted-fit-v1')
        raw, _ = replace_tiles(raw, digest(raw), spec['object'], tiles,
                               [[0, 0, 64, 64]], None)
        new, proof = clean_alpha(raw, spec['object'], [[32, 36, 4, 24]], 96, 3)
        contract = dict(schema_version=1, kind='native-texture-alignment-audit',
                        groups=[], protected=[], gaps=[dict(resource='owned.xxx',
                        object=spec['object'], rect=[33, 36, 3, 24], rgb_ceiling=96)])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root / 'owned.xxx'; path.write_bytes(raw)
            self.assertFalse(audit(root, root, contract)['passed'])
            path.write_bytes(new)
            self.assertTrue(audit(root, root, contract)['passed'])
        self.assertTrue(proof['native_rgb_byte_identical'])
        actual = Image.frombytes('RGBA', (64, 64), decode_texture(selected(new, spec['object'], None)[3]))
        self.assertTrue(all(actual.getpixel((32, y))[3] > 0 for y in range(36, 56)))


if __name__ == '__main__':
    unittest.main()
