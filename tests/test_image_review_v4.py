import copy
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image
from tools.texture_overlay import image_id, layer_ids, render_geometry, render_label
from tools.texture_appearance import validate
from tools.ue3_package import FormatError

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()

class ReviewFourthRoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=read('locales/zh-Hans/texture-overlays/ui-labels-reviewed-v3.json')
        cls.plan=read('locales/zh-Hans/texture-overlays/ui-labels-reviewed-v4.json')
        cls.decision=read('locales/zh-Hans/candidate-decisions/image-review-feedback-v3-20261026.json')
        cls.labels={l['id']:l for l in cls.plan['labels']}
        cls.edits={image_id(e):e for s in cls.plan['sources'] for e in s['textures']}

    def test_input_plan_and_exact_102_730_partition(self):
        d=self.decision
        self.assertEqual(d['input_csv_sha256'],'69a078d5b4ed05ec35a59d0850fd81f8a74018a5a2241960177101f4be71e1ac')
        self.assertEqual((d['review_round'],len(d['entries'])),(4,832))
        self.assertEqual(sum(bool(r['previous_feedback'].strip()) for r in d['entries']),102)
        self.assertEqual(sum(r['action']=='unchanged' for r in d['entries']),730)
        for key,name in [('baseline_plan_sha256','v3'),('review_plan_sha256','v4')]:
            self.assertEqual(d[key],sha((ROOT/f'locales/zh-Hans/texture-overlays/ui-labels-reviewed-{name}.json').read_bytes()))

    def test_730_unrequested_images_and_layers_are_unchanged(self):
        untouched={r['image_id'] for r in self.decision['entries'] if r['action']=='unchanged'}
        oldlabels={l['id']:l for l in self.old['labels']}
        for a,b in zip(self.old['sources'],self.plan['sources']):
            for key in ['path','original','base','discs']:self.assertEqual(a.get(key),b.get(key))
            for oe,ne in zip(a['textures'],b['textures']):
                if image_id(oe) in untouched:
                    self.assertEqual(oe,ne)
                    for lid in layer_ids(oe):self.assertEqual(oldlabels[lid],self.labels[lid])

    def test_all_material_hashes_modes_bounds_and_sparse_support(self):
        for l in self.plan['labels']:
            if 'appearance' in l:
                w,h,_=render_geometry(l);validate(l['appearance'],w,h)
            if 'restoration' not in l:continue
            rr=l['restoration']
            for key in ['mask','patch']:
                self.assertEqual(sha((ROOT/rr[key]['path']).read_bytes()),rr[key]['sha256'])
            with Image.open(ROOT/rr['mask']['path']) as im:
                self.assertEqual(list(im.size),l['rect'][2:]);self.assertEqual(im.mode,'L');mask=im.tobytes()
            with Image.open(ROOT/rr['patch']['path']) as im:patch=im.tobytes()
            self.assertTrue(set(mask)<={0,255})
            self.assertTrue(all(v or patch[i*4:i*4+4]==bytes(4) for i,v in enumerate(mask)))

    def test_background_donor_pixels_no_longer_cleared(self):
        # These native-coordinate blank pockets exhibited the exact rectangular
        # erasure. Assert the repair mask has no write support there.
        cases=[('ui_batch_899_guest',(0,0,24,16)),('ui_batch_961_guest',(0,0,16,8)),
               ('ui_boss_astaroth',(112,20,24,16)),('ui_batch_1089_instruction',(32,8,24,12))]
        old={l['id']:l for l in self.old['labels']}
        for lid,(x,y,w,h) in cases:
            oldmask=Image.open(ROOT/old[lid]['restoration']['mask']['path'])
            newmask=Image.open(ROOT/self.labels[lid]['restoration']['mask']['path'])
            self.assertTrue(any(oldmask.crop((x,y,x+w,y+h)).tobytes()))
            self.assertFalse(any(newmask.crop((x,y,x+w,y+h)).tobytes()),lid)

    def test_english_guard_and_original_digits(self):
        for iid,e in self.edits.items():
            if iid.startswith('normal_map_title') and any(r['image_id']==iid and r['action']!='unchanged' for r in self.decision['entries']) and iid!='normal_map_title_025':
                g=next(g for g in e['protected_regions'] if g['id']=='original_english_full_band')
                self.assertEqual(g['rect'],[0,44,256,20])
                self.assertEqual(self.labels[layer_ids(e)[0]]['rect'][3],44)
        for iid in ['ui_batch_1089','ui_batch_1090','ui_batch_1098','ui_batch_1099']:
            self.assertNotIn(iid+'_original_digit',self.labels)
            self.assertTrue(any(g['id']=='original_digit_and_backdrop' for g in self.edits[iid]['protected_regions']))

    def test_red_backdrop_halo_is_not_classified_as_old_glyphs(self):
        for n in [11,134,161,163,166,177,179,183,186]:
            for lid in layer_ids(self.edits['img_ui_name_jpn_'+str(n)]):
                with Image.open(ROOT/self.labels[lid]['restoration']['mask']['path']) as im:
                    self.assertIn(0,im.tobytes(),lid)
        with Image.open(ROOT/self.labels['img_ui_name_jpn_11_0']['restoration']['mask']['path']) as im:
            self.assertEqual(im.crop((64,0,192,4)).getbbox(),None)

    def test_requested_alignment_heights_and_source_variant_relationships(self):
        for suffix,align in [('18','left'),('19','right')]:
            a=[self.labels[i]['appearance'] for i in layer_ids(self.edits['img_hud_complete_'+suffix])]
            self.assertEqual({x['align'] for x in a},{align});self.assertEqual({x['ink_box'][3] for x in a},{14})
            self.assertTrue(all(x['italic']>=.2 for x in a))
        for iid in self.edits:
            if iid.startswith('ui_boss') or iid in ['ui_01elga','ui_02amon']:
                for lid in layer_ids(self.edits[iid]):self.assertEqual(self.labels[lid]['appearance']['italic'],0)
        for lid in ['hud_complete_23_00','hud_complete_26_00']:self.assertGreater(self.labels[lid]['appearance']['blur'],1)

    def test_all_guards_and_owned_rectangles_are_disjoint(self):
        def overlap(a,b):return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
        for e in self.edits.values():
            guards=e.get('protected_regions',[])
            for n,g in enumerate(guards):
                for other in guards[:n]:self.assertFalse(overlap(g['rect'],other['rect']),(image_id(e),g['id'],other['id']))
                for lid in layer_ids(e):self.assertFalse(overlap(self.labels[lid]['rect'],g['rect']),(lid,g['id']))

    def test_artwork_is_lettering_only_hash_locked_and_source_note_honest(self):
        arts=[l for l in self.plan['labels'] if 'glyph_mask' in l];self.assertEqual(len(arts),4)
        self.assertEqual(len({l['glyph_mask']['path'] for l in arts}),3)
        for l in arts:
            ref=l['glyph_mask'];self.assertEqual(sha((ROOT/ref['path']).read_bytes()),ref['sha256'])
            with Image.open(ROOT/ref['path']) as im:self.assertEqual(im.mode,'RGBA');self.assertEqual(im.getchannel('A').getextrema(),(0,255))
        self.assertNotIn('retained_semantic_hold',self.decision)
        self.assertEqual(self.decision['semantic_adoption']['translation'],'元帅之丘')
        self.assertTrue(self.decision['semantic_adoption']['source_ambiguity_retained_in_evidence'])

class AuthoredGlyphTests(unittest.TestCase):
    def setUp(self):
        from test_texture_appearance import AppearanceTests
        fixture=AppearanceTests();fixture.setUp();self.label=fixture.label();self.font=fixture.font

    def test_authored_silhouette_reaches_actual_label_entrypoint(self):
        before=render_label(self.font,self.label)
        l=copy.deepcopy(self.label);l['glyph_mask']={'path':'owned.png','sha256':'0'*64}
        mask=Image.new('L',(9,9));mask.putpixel((4,4),255)
        l.update(_glyph_pixels=mask.tobytes(),_glyph_size=[9,9])
        after=render_label(self.font,l);self.assertNotEqual(before,after)
        self.assertEqual(Image.frombytes('RGBA',(160,64),after).getchannel('A').getbbox(),(60,8,100,48))

    def test_unresolved_invalid_and_empty_authored_masks_fail_closed(self):
        for kwargs in [{},{'_glyph_size':[True,1],'_glyph_pixels':bytes(1)},
                       {'_glyph_size':[2,2],'_glyph_pixels':bytes(4)},
                       {'_glyph_size':[1,1],'_glyph_pixels':bytes(2)}]:
            l={**self.label,'glyph_mask':{'path':'owned.png','sha256':'0'*64},**kwargs}
            with self.assertRaises(FormatError):render_label(self.font,l)

    def test_width_scale_has_unchanged_default_and_explicit_bounds(self):
        before=render_label(self.font,self.label);self.label['appearance']['width_scale']=1
        self.assertEqual(before,render_label(self.font,self.label))
        self.label['appearance']['width_scale']=.7;self.assertNotEqual(sha(before),sha(render_label(self.font,self.label)))
        for bad in [True,0,3.1,float('nan')]:
            self.label['appearance']['width_scale']=bad
            with self.assertRaises(FormatError):render_label(self.font,self.label)

class AuthoredGlyphBuilderTests(unittest.TestCase):
    def run_case(self,modify=None,error=None):
        import tempfile
        from unittest.mock import patch
        from test_texture_restoration import RestorationBuilderTests
        from test_supplement_font import stored_decoder
        from tools import build_texture_overlay as b
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan=RestorationBuilderTests().fixture(root)
            file=root/'glyph.png';Image.new('L',(4,4),255).save(file)
            plan['labels'][0]['glyph_mask']=dict(path='glyph.png',sha256=sha(file.read_bytes()))
            if modify:modify(plan,root)
            seen=[]
            def render(font,label):
                seen.append(label)
                self.assertEqual(label['_glyph_size'],[4,4]);self.assertEqual(label['_glyph_pixels'],bytes([255])*16)
                return bytes(256)
            with patch.object(b.importlib.metadata,'version',return_value='locked'),patch.object(b,'render_label',side_effect=render):
                if error:
                    with self.assertRaisesRegex(ValueError,error):b.prepare(plan,root,stored_decoder)
                else:
                    _,_,snapshots=b.prepare(plan,root,stored_decoder)
                    self.assertTrue(seen)
                    # prepare() records resolved paths, including expanded Windows
                    # 8.3 TEMP aliases; compare the same path identity and hash.
                    self.assertIn((file.resolve(),sha(file.read_bytes())),snapshots)

    def test_builder_resolves_and_snapshots_glyph_bytes(self):self.run_case()
    def test_builder_rejects_wrong_glyph_hash(self):
        self.run_case(lambda p,r:p['labels'][0]['glyph_mask'].update(sha256='0'*64),'input hash mismatch')
    def test_builder_rejects_glyph_path_escape(self):
        self.run_case(lambda p,r:p['labels'][0]['glyph_mask'].update(path='../glyph.png'),'relative|path')
    def test_builder_rejects_private_glyph_injection(self):
        self.run_case(lambda p,r:p['labels'][0].update(_glyph_pixels='injected'),'private restoration/glyph')
    def test_builder_rejects_rgb_and_oversized_glyph_geometry(self):
        for mode,size in [('RGB',(4,4)),('L',(4097,1))]:
            def change(p,r):
                file=r/'glyph.png';Image.new(mode,size).save(file);p['labels'][0]['glyph_mask']['sha256']=sha(file.read_bytes())
            self.run_case(change,'geometry/mode')

if __name__=='__main__':unittest.main()
