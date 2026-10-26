"""Fourth-feedback contracts, separate from human artwork/game acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image
from tools.texture_appearance import validate
from tools.texture_overlay import image_id, layer_ids, render_geometry, render_label

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_bytes())
def sha(data):
    return hashlib.sha256(data).hexdigest()


class FourthFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = read('locales/zh-Hans/texture-overlays/ui-labels-reviewed-v4.json')
        cls.plan = read('locales/zh-Hans/texture-overlays/ui-labels-reviewed-v5.json')
        cls.decision = read('locales/zh-Hans/candidate-decisions/image-review-feedback-v4-20261026.json')
        cls.labels = {l['id']: l for l in cls.plan['labels']}
        cls.oldlabels = {l['id']: l for l in cls.old['labels']}
        cls.edits = {image_id(e): e for s in cls.plan['sources'] for e in s['textures']}

    def test_exact_feedback_and_plan_identities(self):
        d = self.decision
        self.assertEqual(d['input_csv_sha256'], '0eeeb8d915e37e154b08494ce2f7380bb4adbfbd088dbce4ee79fcedced1298e')
        self.assertEqual((d['review_round'], len(d['entries'])), (5, 832))
        self.assertEqual(sum(bool(r['previous_feedback'].strip()) for r in d['entries']), 88)
        self.assertEqual(sum(r['action'] == 'unchanged' for r in d['entries']), 744)
        for key, version in [('baseline_plan_sha256', 4), ('review_plan_sha256', 5)]:
            self.assertEqual(d[key], sha((ROOT / f'locales/zh-Hans/texture-overlays/ui-labels-reviewed-v{version}.json').read_bytes()))

    def test_unrequested_images_and_all_their_labels_are_unchanged(self):
        untouched = {r['image_id'] for r in self.decision['entries'] if r['action'] == 'unchanged'}
        for old, new in zip(self.old['sources'], self.plan['sources']):
            for key in ['path', 'original', 'base', 'discs']:
                self.assertEqual(old.get(key), new.get(key))
            for a, b in zip(old['textures'], new['textures']):
                if image_id(a) in untouched:
                    self.assertEqual(a, b)
                    for lid in layer_ids(a):
                        self.assertEqual(self.oldlabels[lid], self.labels[lid])

    def test_all_feedback_records_have_actions_without_claiming_acceptance(self):
        self.assertFalse(self.decision['game_rendering_verified'])
        for row in self.decision['entries']:
            self.assertEqual(bool(row['changes']), bool(row['previous_feedback'].strip()))
            self.assertNotEqual(row['action'], 'approved')

    def test_only_background_changes_for_explicit_background_only_requests(self):
        for n in [161, 166, 186]:
            for lid in layer_ids(self.edits[f'img_ui_name_jpn_{n}']):
                a = {k: v for k, v in self.oldlabels[lid].items() if k != 'restoration'}
                b = {k: v for k, v in self.labels[lid].items() if k != 'restoration'}
                self.assertEqual(a, b, lid)

    def test_restoration_materials_are_hash_locked_bounded_and_sparse(self):
        for l in self.plan['labels']:
            if 'appearance' in l:
                w, h, _ = render_geometry(l)
                validate(l['appearance'], w, h)
            r = l.get('restoration')
            if not r:
                continue
            for key in ['mask', 'patch']:
                self.assertEqual(sha((ROOT / r[key]['path']).read_bytes()), r[key]['sha256'])
            with Image.open(ROOT / r['mask']['path']) as im:
                self.assertEqual(im.mode, 'L')
                self.assertEqual(list(im.size), l['rect'][2:])
                mask = im.tobytes()
            with Image.open(ROOT / r['patch']['path']) as im:
                self.assertEqual(im.mode, 'RGBA')
                patch = im.tobytes()
            self.assertTrue(set(mask) <= {0, 255})
            self.assertTrue(all(v or patch[4*i:4*i+4] == bytes(4) for i, v in enumerate(mask)))

    def test_32_titles_retain_geometry_but_gain_visible_directional_shadow(self):
        rows = [r for r in self.decision['entries'] if r['previous_feedback'] == '原图文字有阴影，稍微有点立体感，参考原图修改']
        self.assertEqual(len(rows), 32)
        for row in rows:
            for lid in layer_ids(self.edits[row['image_id']]):
                a, b = self.oldlabels[lid]['appearance'], self.labels[lid]['appearance']
                for key in ['ink_box', 'gradient', 'align', 'tracking', 'italic']:
                    self.assertEqual(a[key], b[key])
                self.assertGreater(b['shadow'][3], a['shadow'][3])
                self.assertEqual(b['shadow_offset'], [2, 3])
                self.assertGreaterEqual(b['outline_width'], .75)

    def test_start_states_share_all_geometry_except_color(self):
        a = self.labels['img_ui_battle_08_jp_108_0']
        b = self.labels['img_ui_battle_08_jp_109_0']
        for key in ['font', 'font_size', 'rect', 'text']:
            self.assertEqual(a[key], b[key])
        self.assertEqual({k: v for k, v in a['appearance'].items() if k != 'gradient'},
                         {k: v for k, v in b['appearance'].items() if k != 'gradient'})

    def test_reverse_states_reuse_identical_text_layer(self):
        a = self.labels['img_ui_name_jpn_176_0']
        b = self.labels['img_ui_name_jpn_177_0']
        for key in ['text', 'rect', 'font', 'font_size', 'appearance']:
            self.assertEqual(a[key], b[key])

    def test_referenced_skill_fonts_and_effects_match(self):
        ref = self.labels['img_ui_name_jpn_145_0']
        for n in [146, 147, 148, 149, 153, 154]:
            for lid in layer_ids(self.edits[f'img_ui_name_jpn_{n}']):
                l = self.labels[lid]
                self.assertEqual(l['font'], ref['font'])
                for key in ['outline_width', 'shadow', 'glow', 'tracking', 'weight']:
                    self.assertEqual(l['appearance'][key], ref['appearance'][key])

    def test_two_map_halves_use_same_full_canvas_style(self):
        a = self.labels['normal_map_terrain_map_view_abazet_1_10']
        b = self.labels['normal_map_terrain_map_view_abazet_2_00']
        for key in ['text', 'font', 'font_size', 'appearance']:
            self.assertEqual(a[key], b[key])
        self.assertEqual(a['render_window']['canvas'], b['render_window']['canvas'])
        self.assertEqual(a['render_window']['crop'][1], 0)
        self.assertEqual(b['render_window']['crop'][1], 16)

    def test_menu_rows_use_41_pixel_pitch_and_shared_selected_geometry(self):
        positions = []
        for n in range(4):
            a = self.labels[f'img_ui_name_jpn_190_{n}']
            b = self.labels[f'img_ui_name_jpn_191_{n}']
            self.assertEqual(a['rect'], b['rect'])
            self.assertEqual(a['appearance']['ink_box'], b['appearance']['ink_box'])
            self.assertEqual(a['font'], b['font'])
            positions.append(a['rect'][1] + a['appearance']['ink_box'][1])
        self.assertEqual(positions, [12, 53, 94, 135])

    def test_map_title_english_is_not_moved_to_fake_the_gap(self):
        rows = [r for r in self.decision['entries'] if r['previous_feedback'] and r['image_id'].startswith('normal_map_title_')]
        self.assertEqual(len(rows), 19)
        for row in rows:
            lid = layer_ids(self.edits[row['image_id']])[0]
            self.assertGreater(self.labels[lid]['appearance']['ink_box'][1], self.oldlabels[lid]['appearance']['ink_box'][1])
            oldedit = next(e for s in self.old['sources'] for e in s['textures'] if image_id(e) == row['image_id'])
            self.assertEqual(oldedit['protected_regions'], self.edits[row['image_id']]['protected_regions'])

    def test_small_menu_pair_shares_size_and_center(self):
        a, b = (self.labels[f'img_ui_name_jpn_182_{n}'] for n in range(2))
        self.assertEqual(a['font_size'], b['font_size'])
        for l in [a, b]:
            self.assertEqual(l['appearance']['align'], 'center')
            self.assertEqual(l['appearance']['ink_box'][2:], [48, 19])

    def test_minigame_white_dot_and_black_bars_are_native_guards(self):
        for n in [1071, 1082]:
            guards = {g['id']: g['rect'] for g in self.edits[f'ui_batch_{n}']['protected_regions']}
            self.assertEqual(guards['original_danger_white_dot'], [460, 116, 20, 36])
            self.assertEqual(guards['original_black_bar_below_danger'], [332, 152, 148, 20])
            self.assertEqual(guards['original_lower_right_black_bar'], [340, 456, 172, 56])
            l = self.labels[f'ui_batch_{n}_prize']
            with Image.open(ROOT / l['restoration']['patch']['path']) as im:
                self.assertIsNone(im.getbbox())

    def test_counter_center_uses_the_box_not_texture_width(self):
        a = self.labels['ui_batch_1075_time']['appearance']
        self.assertEqual((a['align'], a['ink_box']), ('center', [0, 1, 90, 13]))

    def test_digits_share_style_without_changing_values_or_buttons(self):
        for n, value in [(1089, '1'), (1090, '2'), (1098, '1'), (1099, '3')]:
            l = self.labels[f'ui_batch_{n}_styled_digit']
            ref = self.labels[f'ui_batch_{n}_instruction']
            self.assertEqual(l['text'], value)
            for key in ['outline', 'outline_width', 'shadow', 'shadow_offset', 'shadow_radius', 'gradient']:
                self.assertEqual(l['appearance'][key], ref['appearance'][key])
            self.assertTrue(any(g['rect'] == [220, 0, 36, 32] for g in self.edits[f'ui_batch_{n}']['protected_regions']))

    def test_all_guards_and_owned_rectangles_are_disjoint(self):
        def overlap(a, b):
            return a[0] < b[0]+b[2] and b[0] < a[0]+a[2] and a[1] < b[1]+b[3] and b[1] < a[1]+a[3]
        for edit in self.edits.values():
            guards = edit.get('protected_regions', [])
            for n, g in enumerate(guards):
                for previous in guards[:n]:
                    self.assertFalse(overlap(g['rect'], previous['rect']))
                for lid in layer_ids(edit):
                    self.assertFalse(overlap(g['rect'], self.labels[lid]['rect']), (image_id(edit), lid, g['id']))


if __name__ == '__main__':
    unittest.main()
