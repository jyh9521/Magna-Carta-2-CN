import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import unittest
from PIL import Image
from tools.texture_overlay import image_id,layer_ids
from tools.texture_appearance import validate

ROOT=Path(__file__).resolve().parents[1]


class ReviewRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels-reviewed.json').read_bytes())
        cls.baseline=json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes())
        cls.decision=json.loads((ROOT/'locales/zh-Hans/candidate-decisions/image-review-feedback-20261026.json').read_bytes())
        cls.labels={l['id']:l for l in cls.plan['labels']}

    def test_every_feedback_row_is_bound_once(self):
        d=self.decision;self.assertEqual(len(d['entries']),832)
        self.assertEqual(len({e['image_id'] for e in d['entries']}),832)
        self.assertEqual(sum(bool(e['previous_feedback']) for e in d['entries']),757)
        self.assertEqual(sum(e['action']=='restore-original' for e in d['entries']),2)
        self.assertEqual(sum(e['action']=='unchanged' for e in d['entries']),75)
        self.assertEqual(d['review_plan_sha256'],hashlib.sha256((ROOT/'locales/zh-Hans/texture-overlays/ui-labels-reviewed.json').read_bytes()).hexdigest())
        self.assertFalse(d['game_rendering_verified'])

    def test_unrequested_images_and_source_bytes_remain_exact(self):
        unchanged={e['image_id'] for e in self.decision['entries'] if e['action']=='unchanged'}
        baseline={l['id']:l for l in self.baseline['labels']}
        self.assertEqual(len(self.plan['sources']),len(self.baseline['sources']))
        for old,new in zip(self.baseline['sources'],self.plan['sources']):
            for key in ['original','base','path','discs']:self.assertEqual(old.get(key),new.get(key))
            for a,b in zip(old['textures'],new['textures']):
                if image_id(a) in unchanged:
                    self.assertEqual(a,b)
                    for lid in layer_ids(a):self.assertEqual(baseline[lid],self.labels[lid])

    def test_explicit_wording_and_protected_tokens(self):
        l=self.labels
        self.assertEqual(l['controller_move_dash']['text'],'移动角色（按下）冲刺')
        self.assertEqual(l['controller_camera']['text'],'移动镜头（按下）重置镜头')
        self.assertEqual(l['tutorial_complete_08']['text'],'队员（临时同伴）加入')
        self.assertEqual(l['tutorial_complete_20']['text'],'捕捉怪物‘蓬蓬’')
        self.assertIn('首先',l['img_ui_battle_08_jp_166_0']['text'])
        self.assertEqual(l['ui_guest_icon']['text'],'临时同伴')
        self.assertEqual(l['ui_press_start_1_0']['text'],'按 START 键')
        for prefix in ['ui_batch_1071','ui_batch_1082']:
            for x in l.values():
                if x['id'].startswith(prefix+'_points'):self.assertEqual(x['text'],'点')
        for name in ['field_menu_sid','style_info_sid','ui_batch_958_sid']:self.assertEqual(l[name]['text'],'SID')
        self.assertEqual(l['normal_style_018_review_all_cure']['text'],'全体疗愈术')
        self.assertEqual(l['normal_style_018_review_holy_platina']['text'],'神圣白金')

    def test_style_geometry_fonts_gradients_and_sparse_materials(self):
        from tools.texture_overlay import render_geometry
        for label in self.plan['labels']:
            if 'appearance' not in label:continue
            w,h,_=render_geometry(label);validate(label['appearance'],w,h)
            if label['appearance']['kind']=='source-style-v1' and label['id'].startswith('runtime_skill'):
                self.assertGreater(label['appearance']['italic'],0)
            if 'restoration' not in label:
                users=[e for s in self.plan['sources'] for e in s['textures'] if label['id'] in layer_ids(e)]
                self.assertTrue(users)
                self.assertTrue(all(e.get('channel_mode')=='opaque-luma' and not e.get('preserve_unchanged_blocks') for e in users))
                continue
            r=label['restoration']
            for key in ['patch','mask']:
                raw=(ROOT/r[key]['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),r[key]['sha256'])
            with Image.open(ROOT/r['mask']['path']) as im:
                mask=im.tobytes();self.assertFalse(set(mask)-{0,255});self.assertTrue(any(mask))
            with Image.open(ROOT/r['patch']['path']) as im:
                patch=im.tobytes();self.assertEqual(list(im.size),label['rect'][2:])
            self.assertTrue(all(v or patch[i*4:i*4+4]==bytes(4) for i,v in enumerate(mask)))

    @unittest.skipUnless(shutil.which('node'),'Node.js is required for browser-script harness')
    def test_actual_page_script_navigation(self):
        r=subprocess.run(['node',str(ROOT/'tests/review_navigation_test.cjs')],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_cross_sprite_words_keep_one_joined_raster(self):
        old={l['id']:l for l in self.baseline['labels']}
        for lid in ['normal_map_terrain_map_view_abazet_1_10','normal_map_terrain_map_view_abazet_1_11']:
            self.assertEqual(self.labels[lid],old[lid])
        names=['normal_map_terrain_map_highwind_down_01','normal_map_terrain_map_highwind_up_03','normal_map_terrain_map_highwind_up_cave_03']
        self.assertEqual(self.labels[names[0]]['appearance'],self.labels[names[1]]['appearance'])
        self.assertEqual(self.labels[names[1]]['appearance'],self.labels[names[2]]['appearance'])

    def test_native_channel_and_protection_preflight(self):
        def overlaps(a,b):return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
        for source in self.plan['sources']:
            for edit in source['textures']:
                if edit.get('preserve_unchanged_blocks'):
                    self.assertIn((edit['profile']['format'],edit['channel_mode']),[(7,'rgba'),(5,'opaque-rgb')])
                for lid in layer_ids(edit):
                    for guard in edit.get('protected_regions',[]):self.assertFalse(overlaps(self.labels[lid]['rect'],guard['rect']))

    def test_original_orange_divider_is_not_part_of_a_text_rectangle(self):
        for lid in ['ui_menu_tex_1_normal','ui_menu_tex_1_hover']:
            self.assertEqual(self.labels[lid]['rect'][1::2],[28,24])
        for source in self.plan['sources']:
            for edit in source['textures']:
                if edit.get('image_id')=='ui_menu_tex':
                    guards=[g for g in edit['protected_regions'] if g['id']=='original_orange_menu_divider']
                    self.assertEqual(len(guards),1);self.assertEqual(guards[0]['rect'],[0,52,176,8])
        self.assertGreater(self.labels['ui_menu_tex_back_0_normal']['appearance']['weight'],0)


if __name__=='__main__':unittest.main()
