"""Serialized consumers, resident aliases and native ink must agree together."""
import json
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from test_tagged_fields import Fixture
from tools.audit_ui_geometry import audit


def fixture(x=94,override=1):
    f=Fixture()
    f.names += ['ImageComponent','ObjectProperty','ImageRef','ImageTexture',
                'StyleCustomization','Coordinates','U','V','UL','VL','bOverrideCoordinates']
    scalar=lambda n,v:f.tag(n,'FloatProperty',struct.pack('>f',v))
    nested=lambda n,b:f.tag(n,'StructProperty',b+f.name('None'),structure='UIBounds')
    ref=lambda n,i:f.tag(n,'ObjectProperty',struct.pack('>i',i))
    position=b''.join(f.tag('Value','FloatProperty',struct.pack('>f',n),i)
                      for i,n in enumerate([x,10,6,4]))
    uv=b''.join(scalar(n,v) for n,v in zip(('U','V','UL','VL'),(2,0,6,4)))
    objects=[('Label','Image',b'\0'*4+ref('ImageComponent',2)+nested('Position',position)),
             ('Component','Engine.UIComp_DrawImage',b'\0'*8+ref('ImageRef',3)+nested('StyleCustomization',nested('Coordinates',uv)+f.tag('bOverrideCoordinates','BoolProperty',b'',boolean=override))),
             ('Surface','Engine.UITexture',b'\0'*4+ref('ImageTexture',-1))]
    data=b'';exports=[]
    for path,cls,payload in objects:
        payload+=f.name('None')
        exports.append(dict(path=path,class_path=cls,serial_offset=len(data),serial_size=len(payload)))
        data+=payload
    return data,dict(logical=data,tables=dict(names=f.names,exports=exports,imports=[dict(path='Atlas.Labels')]))


class NativeLabelGeometryTests(unittest.TestCase):
    def setUp(self):
        self.data,self.ctx=fixture()
        self.pixels=bytearray(8*4*4)
        for y in (1,2):
            for x in (4,5):self.pixels[(y*8+x)*4:(y*8+x)*4+4]=bytes([250,220,150,255])
        self.case=dict(name='slot',package='scene',object='Label',texture_import='Atlas.Labels',
                       textures=[dict(package='atlas',object='Labels')],ink_region=[4,0,4,4],
                       rgba_min=[100,80,0,128],scale=[1,1],expected=dict(right=98,height=2,bottom=3))
        self.plan=dict(schema_version=1,kind='ui-geometry-contracts',packages=dict(scene='scene.xxx',atlas='atlas.xxx'),
                       anchors=[],image_labels=[self.case])

    def run_audit(self,contexts=None):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for p in self.plan['packages'].values():(root/p).write_bytes(self.data)
            with patch('tools.audit_ui_geometry.context',side_effect=contexts or [self.ctx]*len(self.plan['packages'])), \
                 patch('tools.audit_ui_geometry.selected',return_value=(None,None,None,dict(width=8,height=4))), \
                 patch('tools.audit_ui_geometry.decode_texture',return_value=bytes(self.pixels)):
                return audit(root,self.plan)

    def test_native_label_and_independent_resident_alias(self):
        self.assertTrue(self.run_audit()['passed'])
        self.plan['packages']['title']='title.xxx'
        self.plan['image_labels'].append(dict(self.case,package='title',name='title slot'))
        _,bad=fixture(93)
        result=self.run_audit([self.ctx,self.ctx,bad])
        self.assertEqual([r['passed'] for r in result['checks']],[True,False])

    def test_same_anchor_does_not_hide_wrong_size_or_texture(self):
        self.case['expected']['height']=3
        self.assertFalse(self.run_audit()['passed'])

    def test_disabled_coordinate_override_does_not_validate_dead_uv(self):
        _,disabled=fixture(override=0)
        self.assertFalse(self.run_audit([disabled,self.ctx])['passed'])
        self.case['expected']['height']=2;self.case['texture_import']='Different.Labels'
        self.assertFalse(self.run_audit()['passed'])

    def test_uv_clipping_and_empty_ink_fail_closed(self):
        self.case['ink_region']=[4,0,5,4]
        with self.assertRaisesRegex(ValueError,'UV'):self.run_audit()
        self.case['ink_region']=[4,0,4,4];self.pixels=bytearray(len(self.pixels))
        with self.assertRaisesRegex(ValueError,'empty'):self.run_audit()

    def test_equal_numeric_fields_and_override_flags(self):
        term=dict(package='scene',object='Label',field=[['Position',0],['Value',0]])
        self.plan['equal_fields']=[dict(name='equal',terms=[term,term])]
        self.assertTrue(self.run_audit()['passed'])
        self.plan['equal_fields'][0]['terms'][1]=dict(term,field=[['Position',0],['Value',2]])
        self.assertFalse(self.run_audit()['passed'])

    def test_locale_contract_covers_both_scene_packages_and_all_slots(self):
        root=Path(__file__).resolve().parents[1]
        plan=json.loads((root/'locales/zh-Hans/save-slot-geometry.json').read_bytes())
        self.assertEqual(len(plan['image_labels']),18)
        self.assertEqual({r['package'] for r in plan['image_labels']},{'title','save'})
        self.assertTrue(all(len(r['textures'])==2 for r in plan['image_labels']))
        for slot in range(3):
            self.assertEqual(sum(f'BoxPanel_{slot}.' in r['object'] for r in plan['image_labels']),6)
        labels=json.loads((root/'locales/zh-Hans/texture-overlays/save-slot-labels.json').read_bytes())['labels']
        self.assertEqual({r['text'] for r in labels},{'游戏时间','SID'})
        self.assertEqual({r['appearance']['font_scale_reference'] for r in labels},{'游戏时间'})
        self.assertEqual(len({(r['font_size'],r['font']['sha256']) for r in labels}),1)
        texture=json.loads((root/'locales/zh-Hans/save-slot-textures.json').read_bytes())
        ref=texture['overlay_plan']
        self.assertEqual(hashlib.sha256((root/ref['path']).read_bytes()).hexdigest(),ref['sha256'])


if __name__=='__main__':unittest.main()
