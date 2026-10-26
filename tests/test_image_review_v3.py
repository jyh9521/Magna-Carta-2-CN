import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from PIL import Image
from tools.texture_overlay import image_id, layer_ids, render_geometry
from tools.texture_appearance import validate

ROOT=Path(__file__).resolve().parents[1]
class ReviewThirdRoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels-reviewed-v3.json').read_bytes())
        cls.old=json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels-reviewed.json').read_bytes())
        cls.decision=json.loads((ROOT/'locales/zh-Hans/candidate-decisions/image-review-feedback-v2-20261026.json').read_bytes())
        cls.labels={l['id']:l for l in cls.plan['labels']}
    def test_feedback_identity_and_counts(self):
        d=self.decision
        self.assertEqual(d['input_csv_sha256'],'6e706ac12d5e329944ce1edcb7507c5cb9b4f6ac3774b36ed2ad60bf5a76f1a5')
        self.assertEqual(d['baseline_plan_sha256'],hashlib.sha256((ROOT/'locales/zh-Hans/texture-overlays/ui-labels-reviewed.json').read_bytes()).hexdigest())
        self.assertEqual((d['review_round'],len(d['entries'])),(3,832))
        self.assertEqual(sum(bool(r['previous_feedback'].strip()) for r in d['entries']),433)
        self.assertEqual(sum(r['action']=='unchanged' for r in d['entries']),399)
        self.assertEqual(d['review_plan_sha256'],hashlib.sha256((ROOT/'locales/zh-Hans/texture-overlays/ui-labels-reviewed-v3.json').read_bytes()).hexdigest())
    def test_review_round_rejects_wrong_types_before_publication(self):
        import tempfile
        from tools.build_image_review import build
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);plan=root/'plan.json';plan.write_bytes(b'{}')
            inventory=root/'inventory.json';inventory.write_bytes(b'{"items":[]}')
            for invalid in [True,1,100,'3',None]:
                decision=root/'decision.json'
                decision.write_text(json.dumps(dict(review_plan_sha256=hashlib.sha256(b'{}').hexdigest(),review_round=invalid)),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'review round'):
                    build(root,inventory,decision,plan,[],root/'review')
                self.assertFalse((root/'review').exists())
    def test_399_unrequested_images_are_exact(self):
        untouched={r['image_id'] for r in self.decision['entries'] if r['action']=='unchanged'}
        oldlabels={l['id']:l for l in self.old['labels']}
        for a,b in zip(self.old['sources'],self.plan['sources']):
            for k in ['path','original','base','discs']:self.assertEqual(a.get(k),b.get(k))
            for oe,ne in zip(a['textures'],b['textures']):
                if image_id(oe) in untouched:
                    self.assertEqual(oe,ne)
                    for i in layer_ids(oe):self.assertEqual(oldlabels[i],self.labels[i])
        text_changes={i for i,l in self.labels.items() if i in oldlabels and l['text']!=oldlabels[i]['text']}
        self.assertEqual(text_changes,{'ui_batch_1071_danger','ui_batch_1082_danger'})
        for i in text_changes:self.assertEqual(self.labels[i]['text'],'危险')
    def test_all_style_geometry_and_sparse_material_hashes(self):
        for l in self.plan['labels']:
            if 'appearance' in l:
                w,h,_=render_geometry(l);validate(l['appearance'],w,h)
            if 'restoration' not in l:continue
            rr=l['restoration']
            for k in ['mask','patch']:
                raw=(ROOT/rr[k]['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),rr[k]['sha256'])
            with Image.open(ROOT/rr['mask']['path']) as im:
                self.assertEqual(list(im.size),l['rect'][2:]);mask=im.tobytes();self.assertFalse(set(mask)-{0,255})
            with Image.open(ROOT/rr['patch']['path']) as im:patch=im.tobytes()
            self.assertTrue(all(v or patch[i*4:i*4+4]==bytes(4) for i,v in enumerate(mask)))
    def test_locked_colours_and_explicit_nonitalic_requests(self):
        old={l['id']:l for l in self.old['labels']}
        for row in self.decision['entries']:
            if row.get('colour_locked'):
                for i in row['labels']:self.assertEqual(old[i]['appearance']['gradient'],self.labels[i]['appearance']['gradient'])
        for i in ['hud_complete_11_00','hud_complete_14_00']:
            if i in self.labels:self.assertEqual(self.labels[i]['appearance']['italic'],0)
        for i in ['img_ui_name_jpn_15_0','img_ui_name_jpn_16_0']:
            self.assertEqual(self.labels[i]['appearance']['spans'],[{'start':0,'end':1,'scale':.7}])
    def test_guards_do_not_intersect_owned_rectangles(self):
        def overlap(a,b):return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
        for s in self.plan['sources']:
            for e in s['textures']:
                guards=e.get('protected_regions',[])
                for n,g in enumerate(guards):
                    for other in guards[:n]:self.assertFalse(overlap(g['rect'],other['rect']),(g['id'],other['id']))
                for lid in layer_ids(e):
                    for g in e.get('protected_regions',[]):self.assertFalse(overlap(self.labels[lid]['rect'],g['rect']),(lid,g['id']))
    def test_visible_duplicate_uses_existing_adopted_field(self):
        l=self.labels['normal_style_009_review_super_thunder'];anchor=self.labels['runtime_skill_104']
        self.assertEqual(l['text'],anchor['text']);self.assertEqual(l['source_ids'],anchor['source_ids'])
        self.assertEqual(l['rect'],[0,184,128,32])
        self.assertTrue(self.decision['added_visible_duplicate']['no_new_consumer_assertion'])
    def test_same_dialogue_group_uses_one_actual_ink_height(self):
        self.assertEqual(len(self.decision['uniform_dialogue_heights']),8)
        for group in self.decision['uniform_dialogue_heights']:
            heights={self.labels[lid]['appearance']['ink_box'][3] for lid in group['labels']}
            self.assertEqual(heights,{group['common_ink_height']})
        heights={l['appearance']['ink_box'][3] for l in self.plan['labels'] if l['id'].startswith('normal_room_senti_')}
        self.assertEqual(heights,{18})
    def test_explicit_glow_feedback_has_a_live_glow_layer(self):
        edits={image_id(e):e for s in self.plan['sources'] for e in s['textures']}
        for row in self.decision['entries']:
            if any(k in row['previous_feedback'] for k in ['发光','光晕','光圈']):
                self.assertTrue(any(self.labels[lid]['appearance']['glow'][3] and self.labels[lid]['appearance']['glow_radius']>0 for lid in layer_ids(edits[row['image_id']])),row['image_id'])
    def test_owned_glyph_contour_survives_actual_bc3_encoding(self):
        import copy
        from tools.texture_overlay import render_label,overlay_profile_regions
        from tools.texture_layout import unit_layout,decode_texture
        from test_texture_render_windows import owned_font
        counts=[];font=owned_font()
        for plan in [self.old,self.plan]:
            l=copy.deepcopy(next(x for x in plan['labels'] if x['id']=='img_ui_name_jpn_21'))
            l.pop('restoration',None);l.update(text='ABAB',font_size=24);a=l['appearance']
            a.update(ink_box=[4,4,120,22],align='center',gradient=[[0,[255,255,255,255]],[1000,[255,255,255,255]]],shadow=[0,0,0,0],glow=[0,0,0,0],motion=0,italic=0,weight=0,tracking=0)
            fg=render_label(font,l);plain=copy.deepcopy(l);plain['appearance']['outline_width']=0;fill=render_label(font,plain)
            layout=unit_layout(128,32,7);tx=dict(layout=layout,width=128,height=32,format=7,tiles=bytes(layout['storage_bytes']))
            edit=dict(regions=['owned'],image_id='owned',channel_mode='rgba',profile=dict(kind='xbox-inline-bc-v1',format=7))
            raw,_=overlay_profile_regions(tx,edit,{'owned':(l,fg)});native=decode_texture(tx,raw)
            counts.append(sum(fill[i*4+3]<4 and native[i*4+3]>200 and max(native[i*4:i*4+3])<80 for i in range(128*32)))
        self.assertLess(counts[0],8);self.assertGreaterEqual(counts[1],8)
    @unittest.skipUnless(shutil.which('node'),'Node.js is required')
    def test_round_three_keyboard_capture_and_feedback_namespace(self):
        env=dict(os.environ,REVIEW_ROUND='3')
        r=subprocess.run(['node',str(ROOT/'tests/review_navigation_test.cjs')],env=env,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

if __name__=='__main__':unittest.main()
