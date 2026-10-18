"""Entirely self-authored 446/25 metadata/default fixtures; no game execution."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from test_ui_style_graph import Fixture,word
from tools.ue3_ui_styles import StyleGraph
from tools.ue3_struct_defaults import parse_struct_defaults,audit_struct_property
from tools.inspect_struct_defaults import main as inspect_main
from tools.inspect_ui_fonts import main as ui_main


class StructFixture:
    def __init__(self):
        self.f=Fixture();f=self.f
        kinds=['Object','ScriptStruct','BoolProperty','ObjectProperty','ByteProperty','FloatProperty','StructProperty','IntProperty','Enum']
        self.imports=[dict(path='Core.'+k,class_name=dict(name='Class')) for k in kinds]
        self.ref={k:-i for i,k in enumerate(kinds,1)}
        specs=[('RendererClass','Class',0),('FontClass','Class',0),('Enum','Core.Enum',0),
               ('UITextAttributes','Core.ScriptStruct',0),('UITextStyleOverride','Core.ScriptStruct',0),
               ('STYLE_ID','Core.ScriptStruct',0),('Guid','Core.ScriptStruct',0),
               ('UITextAttributes.Bold','Core.BoolProperty',4),('Guid.A','Core.IntProperty',7),
               ('UITextStyleOverride.Flag','Core.BoolProperty',5),('UITextStyleOverride.DrawFont','Core.ObjectProperty',5),
               ('UITextStyleOverride.Alignment','Core.ByteProperty',5),('UITextStyleOverride.Opacity','Core.FloatProperty',5),
               ('UITextStyleOverride.Attributes','Core.StructProperty',5),('UITextStyleOverride.ID','Core.StructProperty',5),
               ('RendererClass.TextStyleCustomization','Core.StructProperty',1),('Renderer','RendererClass',0),
               ('Guid.B','Core.IntProperty',7),('Guid.C','Core.IntProperty',7),('Guid.D','Core.IntProperty',7)]
        self.exports=[];self.ctx=dict(logical=b'',sha256='self-authored',tables=dict(names=f.names,imports=self.imports,exports=self.exports))
        for name,kind,outer in specs:
            cls=0 if kind=='Class' else 1 if kind=='RendererClass' else self.ref[kind.split('.')[-1]]
            self.exports.append(dict(path=name,class_path=kind,outer=outer,super=self.ref['Object'] if kind=='Class' else 0,
                                    archetype=0,object_flags='0000000000000000',serial_offset=0,serial_size=0,**{'class':cls}))
        self.exports[5]['super']=7
        self.replace(3,word(0)+f.props()+word(0,0,3)+f.fname('Left')+f.fname('Center')+f.fname('Max'))
        self.attr=f.props(f.prop('Bold','BoolProperty',boolean=0));self.guid=f.props(*(f.prop(k,'IntProperty',word(0)) for k in 'ABCD'))
        self.defaults=f.props(f.prop('Flag','BoolProperty',boolean=0),f.prop('DrawFont','ObjectProperty',word(0)),
            f.prop('Alignment','ByteProperty',b'\0'),f.prop('Alignment','ByteProperty',b'\0',index=1),
            f.prop('Opacity','FloatProperty',struct.pack('>f',0)),
            f.prop('Attributes','StructProperty',self.attr,'UITextAttributes'),
            f.prop('ID','StructProperty',self.guid,'STYLE_ID'))
        self.replace(4,self.struct(8,self.attr));self.replace(5,self.struct(15,self.defaults));self.replace(6,self.struct(0,f.props(),7));self.replace(7,self.struct(20,self.guid))
        for index,next_,dim,target in [(8,0,1,None),(9,0,1,None),(10,0,1,None),(11,10,1,2),(12,11,2,3),
                                       (13,12,1,None),(14,13,1,4),(15,14,1,6),(16,0,1,5),
                                       (18,9,1,None),(19,18,1,None),(20,19,1,None)]:
            raw=word(0)+f.props()+word(0,next_,dim)+bytes(8)+f.fname('None')+word(0)
            if target is not None:raw+=word(target)
            self.replace(index,raw)
        instance=f.props(f.prop('Flag','BoolProperty',boolean=1))
        self.replace(17,word(1)+f.props(f.prop('TextStyleCustomization','StructProperty',instance,'UITextStyleOverride')))

    def struct(self,children,defaults,parent=0):
        return word(0)+self.f.props()+word(parent,0,0,children,0,0,0,0,1)+defaults

    def replace(self,index,body):
        e=self.exports[index-1];e['serial_offset']=len(self.ctx['logical']);e['serial_size']=len(body);self.ctx['logical']+=body

    def graph(self):return StyleGraph(dict(sample=self.ctx))

    def package(self):
        f=self.f
        for value in ['Core','Class','Package',*self.ref,*[e['path'].rsplit('.',1)[-1] for e in self.exports]]:f.fname(value)
        string=lambda s:word(len(s)+1)+s.encode()+b'\0'
        names=b''.join(string(s)+bytes(8) for s in f.names)
        imports=f.fname('Core')+f.fname('Package')+word(0)+f.fname('Core')
        for name in self.ref:imports+=f.fname('Core')+f.fname('Class')+word(-1)+f.fname(name)
        # Add a package import before the fixture's Class imports.
        offset=101+len(names)+len(imports);head=offset+68*len(self.exports);exports=b''
        for e in self.exports:
            cls=e['class']-1 if e['class']<0 else e['class'];sup=e['super']-1 if e['super']<0 else e['super']
            exports+=word(cls,sup,e['outer'])+f.fname(e['path'].rsplit('.',1)[-1])+word(0)+bytes(8)
            exports+=word(e['serial_size'],head+e['serial_offset'],0,0,0)+bytes(16)
        summary=b'\x9e\x2a\x83\xc1'+word((25<<16)|446,head)+string('None')
        summary+=word(0,len(f.names),101,len(self.exports),offset,len(self.ref)+1,101+len(names),0)+bytes(16)
        summary+=word(1,len(self.exports),len(f.names),0,3004,42,0,0)
        return summary+names+imports+exports+self.ctx['logical']


class StructDefaultTests(unittest.TestCase):
    def test_complete_declarations_values_and_inherited_guid_schema(self):
        f=StructFixture();r=parse_struct_defaults(f.graph(),('sample',5))
        self.assertEqual(len(r['declarations']),6);self.assertEqual(r['missing_default_slots'],[])
        self.assertFalse(r['native_initialization_verified']);self.assertFalse(r['runtime_effective_values_resolved'])
        guid=parse_struct_defaults(f.graph(),('sample',6))
        self.assertEqual(guid['own_declaration_count'],0);self.assertEqual({d['name'] for d in guid['missing_default_slots']},set('ABCD'))
        self.assertEqual(guid['super_defaults'][0]['fields'][0]['value'],0)

    def test_binding_uses_class_outer_and_type_reference_not_leaf_guess(self):
        f=StructFixture();r=audit_struct_property(f.graph(),('sample',17),'TextStyleCustomization')
        self.assertEqual(r['declaration']['owner']['object_index'],16)
        self.assertEqual(r['struct_defaults']['owner']['object_index'],5)
        self.assertFalse(r['runtime_effective_values_resolved'])

    def test_bool_header_offset_points_at_actual_word_not_empty_payload(self):
        f=StructFixture();g=f.graph();r=g.one(('sample',17),['TextStyleCustomization','Flag']);raw=f.ctx['logical']
        self.assertEqual(raw[r['logical_package_offset']:r['logical_package_offset']+4],word(1))
        self.assertEqual(r['logical_payload_offset'],r['logical_package_offset']+4)
        defaults=parse_struct_defaults(g,('sample',5));p=next(p for p in defaults['fields'] if p['property_path'][0]['name']=='Flag')
        self.assertEqual(raw[p['logical_package_offset']:p['logical_package_offset']+4],word(0))

    def test_missing_default_is_reported_not_assumed_zero(self):
        f=StructFixture();f.replace(5,f.struct(15,f.f.props()))
        r=parse_struct_defaults(f.graph(),('sample',5));self.assertEqual(r['fields'],[])
        self.assertEqual(len(r['missing_default_slots']),7);self.assertFalse(r['missing_values_assumed_zero'])

    def test_field_chain_cycles_omissions_and_cross_owner_rejected(self):
        for mode in ('cycle','omission','owner'):
            f=StructFixture();e=f.exports[9];raw=bytearray(f.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']])
            if mode=='cycle':raw[16:20]=word(10)
            elif mode=='omission':raw[16:20]=word(8)
            else:e['outer']=4
            f.replace(10,bytes(raw))
            with self.subTest(mode=mode),self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',5))

    def test_struct_header_profile_flags_and_trailing_guards(self):
        for field in ('script','stack','trailing','super'):
            f=StructFixture();e=f.exports[4];raw=bytearray(f.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']])
            if field=='script':raw[40:44]=word(1)
            elif field=='stack':e['object_flags']='0200000000000000'
            elif field=='trailing':raw+=b'x'
            else:raw[12:16]=word(7)
            f.replace(5,bytes(raw))
            with self.subTest(field=field),self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',5))

    def test_property_dimensions_flags_type_targets_and_sizes_guarded(self):
        for mode in ('dimension','network','target','trailing'):
            f=StructFixture();e=f.exports[10];raw=bytearray(f.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']])
            if mode=='dimension':raw[20:24]=word(0x10001)
            elif mode=='network':raw[24:32]=struct.pack('>Q',0x20)
            elif mode=='target':raw[-4:]=word(3)
            else:raw+=b'x'
            f.replace(11,bytes(raw))
            with self.subTest(mode=mode),self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',5))

    def test_default_unknown_duplicate_index_and_type_mismatch_rejected(self):
        for mode in ('unknown','duplicate','index','type','struct'):
            f=StructFixture();p=f.f
            if mode=='unknown':raw=p.props(p.prop('Unknown','IntProperty',word(0)))
            elif mode=='duplicate':raw=p.props(p.prop('Flag','BoolProperty',boolean=0),p.prop('Flag','BoolProperty',boolean=0))
            elif mode=='index':raw=p.props(p.prop('Alignment','ByteProperty',b'\0',index=2))
            elif mode=='type':raw=p.props(p.prop('Flag','IntProperty',word(0)))
            else:raw=p.props(p.prop('Attributes','StructProperty',f.attr,'UIStyleReference'))
            f.replace(5,f.struct(15,raw))
            with self.subTest(mode=mode),self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',5))

    def test_nested_defaults_validate_against_actual_member_declarations(self):
        f=StructFixture();p=f.f;inner=p.props(p.prop('Bogus','BoolProperty',boolean=0))
        f.replace(5,f.struct(15,p.props(p.prop('Attributes','StructProperty',inner,'UITextAttributes'))))
        with self.assertRaisesRegex(ValueError,'slot'):parse_struct_defaults(f.graph(),('sample',5))
        f=StructFixture();p=f.f
        f.replace(7,f.struct(20,p.props(p.prop('Bogus','IntProperty',word(0)))))
        with self.assertRaisesRegex(ValueError,'slot'):parse_struct_defaults(f.graph(),('sample',6))

    def test_super_cycle_and_missing_import_are_unresolved_not_zero(self):
        f=StructFixture();f.exports[6]['super']=6;f.replace(7,f.struct(20,f.guid,6))
        with self.assertRaisesRegex(ValueError,'super chain'):parse_struct_defaults(f.graph(),('sample',6))
        f=StructFixture();f.exports[5]['super']=-2;f.replace(6,f.struct(0,f.f.props(),-2))
        with self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',6))

    def test_float_bits_nonfinite_and_scalar_sizes(self):
        f=StructFixture();p=f.f
        f.replace(5,f.struct(15,p.props(p.prop('Opacity','FloatProperty',bytes.fromhex('7fc00000')))))
        r=parse_struct_defaults(f.graph(),('sample',5))['fields'][0]
        self.assertTrue(r['non_finite']);self.assertEqual(r['value_bits'],'7fc00000');self.assertNotIn('value',r)
        f.replace(5,f.struct(15,p.props(p.prop('Opacity','FloatProperty',bytes(5)))))
        with self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',5))

    def test_class_interface_name_and_string_declarations(self):
        for kind in ('ClassProperty','InterfaceProperty','NameProperty','StrProperty'):
            f=StructFixture();p=f.f;f.imports.append(dict(path='Core.'+kind,class_name=dict(name='Class')))
            e=f.exports[9];e['class_path']='Core.'+kind;e['class']=-len(f.imports)
            body=word(0)+p.props()+word(0,0,1)+bytes(8)+p.fname('None')+word(0)
            if kind in ('ClassProperty','InterfaceProperty'):body+=word(2)
            if kind=='ClassProperty':body+=word(2)
            f.replace(10,body)
            tag='ObjectProperty' if kind=='ClassProperty' else kind
            value=p.fname('None') if kind=='NameProperty' else word(0)
            f.replace(5,f.struct(15,p.props(p.prop('Flag',tag,value))))
            with self.subTest(kind=kind):
                r=parse_struct_defaults(f.graph(),('sample',5));self.assertEqual(r['fields'][0]['type'],tag)

    def test_enum_catalog_slot_and_outside_byte_value_are_not_guessed(self):
        f=StructFixture();p=f.f
        f.replace(5,f.struct(15,p.props(p.prop('Alignment','ByteProperty',b'\1'),p.prop('Alignment','ByteProperty',b'\xff',index=1))))
        fields=parse_struct_defaults(f.graph(),('sample',5))['fields']
        self.assertEqual(fields[0]['enum_slot_name']['name'],'Center');self.assertIsNone(fields[1]['enum_slot_name'])
        e=f.exports[2];raw=f.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']];f.replace(3,raw+b'x')
        with self.assertRaisesRegex(ValueError,'enum catalog'):parse_struct_defaults(f.graph(),('sample',5))

    def test_duplicate_scoped_declaration_and_inherited_class_binding(self):
        f=StructFixture();f.exports.append(copy.deepcopy(f.exports[15]))
        with self.assertRaisesRegex(ValueError,'ambiguous'):audit_struct_property(f.graph(),('sample',17),'TextStyleCustomization')
        f=StructFixture();f.exports[1]['super']=1;f.exports[16]['class']=2
        r=audit_struct_property(f.graph(),('sample',17),'TextStyleCustomization');self.assertEqual(len(r['class_search']),2)

    def test_every_struct_payload_truncation_is_rejected(self):
        original=StructFixture();e=original.exports[4];raw=original.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        for n in range(len(raw)):
            f=StructFixture();f.replace(5,raw[:n])
            with self.subTest(n=n),self.assertRaises(ValueError):parse_struct_defaults(f.graph(),('sample',5))

    def test_cli_real_self_authored_package_and_mode_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(StructFixture().package())
            from tools.font_binding_plan import digest
            out=root/'report.json';args=[str(source),'--sha256',digest(source.read_bytes()),'--object','UITextStyleOverride','--output',str(out)]
            self.assertEqual(inspect_main(args),0);r=json.loads(out.read_text(encoding='utf8'));self.assertEqual(len(r['structs']),1)
            self.assertEqual(inspect_main(args),2)
            args[2]='0'*64;args[-1]=str(root/'wrong.json');self.assertEqual(inspect_main(args),2)
            self.assertEqual(ui_main(['missing','--sha256','0'*64,'--audit-struct-defaults','--output',str(root/'ui.json')]),2)


if __name__=='__main__':unittest.main()
