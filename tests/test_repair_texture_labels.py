import copy
import importlib.metadata
import json
from pathlib import Path
import tempfile
import unittest
from tools import repair_texture_labels as repair
from tools.reface_font import sha
from tools.texture_overlay import render_label, patch_package
from tools.replace_texture_regions import selected, replace_tiles
from tools.texture_layout import decode_texture
from test_texture_layout import profile_fixture
import test_texture_appearance as appearance_fixtures
from test_texture_render_windows import owned_font
from test_supplement_font import stored_decoder


class LabelRepairTests(unittest.TestCase):
    def fixture(self,root):
        root=Path(root); font=owned_font(); (root/'font.ttf').write_bytes(font)
        label=appearance_fixtures.AppearanceTests().label()
        label.update(id='owned',text='AB',rect=[8,4,48,28],font_size=20,
                     font=dict(path='font.ttf',sha256=sha(font)))
        label['appearance'].update(ink_box=[2,4,44,19],align='left',outline_width=.6,
              gradient=[[0,[255,235,231,255]],[56,[150,130,120,255]],
                        [111,[255,235,206,255]],[500,[255,231,132,255]],[1000,[250,160,123,255]]])
        raw,edit,_=profile_fixture(width=64,height=32)
        edit['channel_mode']='rgba'
        baseline,_=patch_package(raw,sha(raw),[edit],{'x':(label,render_label(font,label))},stored_decoder)
        (root/'source.xxx').write_bytes(baseline)
        plan=dict(font=label['font'],labels=[label],
                  rasterizer_versions={p:importlib.metadata.version(p) for p in ('Pillow','fonttools')})
        plan_bytes=json.dumps(plan).encode();(root/'labels.json').write_bytes(plan_bytes)
        tx=selected(baseline,edit['object'],stored_decoder)[3]
        recipe=dict(schema_version=1,kind='bounded-label-rgb-repair-v1',
                    label_plan=dict(path='labels.json',sha256=sha(plan_bytes)),
                    source_tiled_sha256=sha(tx['tiles']),dimensions=[64,32],
                    labels=[dict(id='owned',remove_gradient_positions=[56])],
                    resources=[dict(path='art/source.xxx',object=edit['object'],
                                    input=dict(path='source.xxx',sha256=sha(baseline)))])
        return recipe,baseline,edit['object'],label

    def test_build_reopens_packages_preserves_alpha_shape_and_nonselected_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            recipe,baseline,obj,label=self.fixture(d)
            products,proof,png=repair.build(recipe,Path(d),stored_decoder)
            after=products['art/source.xxx'];before_tx=selected(baseline,obj,stored_decoder)[3]
            after_tx=selected(after,obj,stored_decoder)[3]
            self.assertEqual(decode_texture(before_tx)[3::4],decode_texture(after_tx)[3::4])
            self.assertEqual(Path(d,'source.xxx').read_bytes(),baseline)
            self.assertTrue(proof['resources'][0]['outside_blocks_preserved'])
            self.assertTrue(proof['resources'][0]['unselected_exports_preserved'])
            self.assertEqual(proof['resources'][0]['labels'][0]['before_gradient_valleys'],[56])
            self.assertEqual(proof['resources'][0]['labels'][0]['after_gradient_valleys'],[])
            self.assertTrue(png.startswith(b'\x89PNG'))
            self.assertEqual(products,repair.build(recipe,Path(d),stored_decoder)[0])
            restored,_=replace_tiles(after,sha(after),obj,before_tx['tiles'],[label['rect']],stored_decoder)
            self.assertEqual(restored,baseline)

    def test_revision_changes_only_explicit_gradient_samples(self):
        with tempfile.TemporaryDirectory() as d:
            _,_,_,label=self.fixture(d);before=copy.deepcopy(label)
            revised=repair.revise(label,[56]);self.assertEqual(label,before)
            gradient=revised['appearance'].pop('gradient')
            original=before['appearance'].pop('gradient')
            self.assertEqual(revised,before)
            self.assertEqual(gradient,[s for s in original if s[0]!=56])
            for bad in [[0],[1000],[54],[56,56],[True],None]:
                with self.assertRaises(ValueError):repair.revise(label,bad)

    def test_bad_identity_geometry_overlap_path_and_remaining_valley_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            recipe,_,_,_=self.fixture(d)
            variants=[]
            for key,value in [('source_tiled_sha256','0'*64),('dimensions',[32,32]),('extra',1)]:
                r=copy.deepcopy(recipe);r[key]=value;variants.append(r)
            for field,value in [('path','../escape.xxx'),('input',dict(path='source.xxx',sha256='0'*64))]:
                r=copy.deepcopy(recipe);r['resources'][0][field]=value;variants.append(r)
            r=copy.deepcopy(recipe);r['labels'][0]['remove_gradient_positions']=[];variants.append(r)
            r=copy.deepcopy(recipe);r['labels']*=2;variants.append(r)
            for variant in variants:
                with self.assertRaises(ValueError):repair.build(variant,Path(d),stored_decoder)
            self.assertFalse(Path(d,'art').exists())


if __name__=='__main__':unittest.main()
