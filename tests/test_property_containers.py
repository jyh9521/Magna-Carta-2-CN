"""Self-authored container declarations; native sizes/values never inferred."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import test_struct_defaults as fixtures
from test_ui_style_graph import word
from tools.ue3_struct_defaults import property_declaration,validate_values
from tools.property_declaration_audit import property_tree,class_properties
from tools.inspect_property_declarations import main


class ContainerFixture(fixtures.StructFixture):
    def __init__(self):
        super().__init__()
        for kind in ['ArrayProperty','MapProperty']:
            self.ref[kind]=-len(self.imports)-1;self.imports.append(dict(path='Core.'+kind,class_name={'name':'Class'}))
        self.add('ContainerClass','Class',0)
        self.add('ContainerClass.List','ArrayProperty',21)
        self.add('ContainerClass.List.Element','StructProperty',22)
        self.add('ContainerClass.Lookup','MapProperty',21)
        self.add('ContainerClass.Count','IntProperty',21)
        self.replace(22,self.decl(24,[23]));self.replace(23,self.decl(0,[5]));self.replace(24,self.decl(25,[0,0],0x1002));self.replace(25,self.decl(0,[]))

    def add(self,path,kind,outer):
        self.exports.append(dict(path=path,class_path='Class' if kind=='Class' else 'Core.'+kind,outer=outer,
            super=self.ref['Object'] if kind=='Class' else 0,archetype=0,object_flags='0000000000000000',
            serial_offset=0,serial_size=0,**{'class':0 if kind=='Class' else self.ref[kind]}))
        return len(self.exports)

    def decl(self,next_,refs,flags=0):
        return word(0)+self.f.props()+word(0,next_,1)+struct.pack('>Q',flags)+self.f.fname('None')+word(0,*refs)

    def typed_map(self):
        key=self.add('ContainerClass.Lookup.Key','IntProperty',24);value=self.add('ContainerClass.Lookup.Value','ObjectProperty',24)
        self.replace(key,self.decl(0,[]));self.replace(value,self.decl(0,[2]));self.replace(24,self.decl(25,[key,value]));return key,value


class ContainerDeclarationTests(unittest.TestCase):
    def test_array_inner_struct_schema_and_opaque_map_are_distinct(self):
        f=ContainerFixture();r=class_properties(f.graph(),('sample',21),True)
        self.assertEqual(r['local_property_count'],3);self.assertFalse(r['serialized_type_trees_complete'])
        array,map_,scalar=r['properties'];self.assertEqual(array['children'][0]['declaration']['target']['class_name'],'ScriptStruct')
        self.assertIn('struct_definition',array['children'][0]);self.assertFalse(map_['serialized_type_tree_complete'])
        self.assertIsNone(map_['declaration']['container']['key']);self.assertFalse(r['native_layout_verified'])
        self.assertNotIn('container',scalar['declaration'])

    def test_typed_map_keeps_both_local_property_definitions(self):
        f=ContainerFixture();key,value=f.typed_map();r=property_tree(f.graph(),('sample',24))
        self.assertEqual([c['declaration']['owner']['object_index'] for c in r['children']],[key,value])
        self.assertTrue(r['serialized_type_tree_complete']);self.assertFalse(r['container_values_decoded'])

    def test_array_requires_nonnull_local_owned_exact_property(self):
        for ref,change in [(0,None),(-1,None),(9999,None),(23,'owner'),(23,'kind')]:
            f=ContainerFixture();f.replace(22,f.decl(24,[ref]))
            if change=='owner':f.exports[22]['outer']=21
            elif change=='kind':f.exports[22]['class_path']='Other.StructProperty'
            with self.subTest(ref=ref,change=change),self.assertRaises(ValueError):property_declaration(f.graph(),('sample',22))

    def test_map_half_null_duplicates_and_unreferenced_children_fail(self):
        for refs in [[0,25],[25,0],[25,25]]:
            f=ContainerFixture();f.replace(24,f.decl(25,refs))
            with self.subTest(refs=refs),self.assertRaises(ValueError):property_declaration(f.graph(),('sample',24))
        f=ContainerFixture();f.typed_map();f.replace(24,f.decl(25,[0,0]))
        with self.assertRaisesRegex(ValueError,'omit local'):property_declaration(f.graph(),('sample',24))

    def test_all_container_payload_truncations_rejected(self):
        for index in [22,24]:
            original=ContainerFixture();e=original.exports[index-1];body=original.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
            for size in range(len(body)):
                f=ContainerFixture();f.replace(index,body[:size])
                with self.subTest(index=index,size=size),self.assertRaises(ValueError):property_declaration(f.graph(),('sample',index))

    def test_trailing_container_bytes_and_unknown_kinds_fail_closed(self):
        f=ContainerFixture();f.replace(22,f.decl(24,[23])+b'x')
        with self.assertRaisesRegex(ValueError,'trailing'):property_declaration(f.graph(),('sample',22))
        f=ContainerFixture();f.exports[21]['class_path']='Core.UnknownProperty'
        with self.assertRaisesRegex(ValueError,'unsupported'):property_declaration(f.graph(),('sample',22))

    def test_recursive_container_cycle_and_depth_are_bounded(self):
        f=ContainerFixture();f.exports[21]['outer']=23;f.exports[22].update(class_path='Core.ArrayProperty',**{'class':f.ref['ArrayProperty']})
        f.replace(23,f.decl(0,[22]))
        with self.assertRaisesRegex(ValueError,'cyclic'):property_tree(f.graph(),('sample',22))
        f=ContainerFixture();current=22
        for i in range(17):
            child=f.add('Deep'+str(i),'ArrayProperty',current);f.replace(current,f.decl(0,[child]));current=child
        inner=f.add('Last','IntProperty',current);f.replace(current,f.decl(0,[inner]));f.replace(inner,f.decl(0,[]))
        # Remove the original, now unreferenced inner from this test's ownership.
        f.exports[22]['outer']=0
        with self.assertRaisesRegex(ValueError,'overlong'):property_tree(f.graph(),('sample',22))

    def test_local_next_runs_preserve_nonproperty_boundary(self):
        f=ContainerFixture();boundary=f.add('ContainerClass.Record','ScriptStruct',21);f.replace(25,f.decl(boundary,[]))
        r=class_properties(f.graph(),('sample',21));run,=r['local_next_runs']
        self.assertEqual([x['path'].rsplit('.',1)[-1] for x in run['properties']],['List','Lookup','Count'])
        self.assertEqual(run['boundary']['object_index'],boundary);self.assertFalse(r['class_children_header_decoded'])

    def test_local_next_cycles_cross_owners_and_ambiguous_predecessors_fail(self):
        for change in ['cycle','cross','ambiguous']:
            f=ContainerFixture()
            if change=='cycle':f.replace(25,f.decl(22,[]))
            elif change=='cross':f.replace(25,f.decl(4,[]))
            else:f.replace(22,f.decl(25,[23]))
            with self.subTest(change=change),self.assertRaises(ValueError):class_properties(f.graph(),('sample',21))

    def test_container_default_bytes_not_accepted_as_validated_values(self):
        f=ContainerFixture();d=property_declaration(f.graph(),('sample',22))
        with self.assertRaisesRegex(ValueError,'separate typed value decoder'):
            validate_values(f.graph(),'sample',[dict(name='List',array_index=0,type='ArrayProperty',raw=bytes(4))],[d],{})

    def test_scalar_declaration_shape_and_flags_remain_unchanged(self):
        f=ContainerFixture();d=property_declaration(f.graph(),('sample',25));self.assertNotIn('container',d)
        m=property_declaration(f.graph(),('sample',24));self.assertEqual(m['flags_hex'],'0000000000001002')
        self.assertEqual(m['container']['type_visibility'],'opaque-null-type-references')

    def cli(self,root):
        f=ContainerFixture();source=root/'sample.xxx';source.write_bytes(f.package());out=root/'report.json'
        args=[str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),'--class','ContainerClass','--bind-structs','--output',str(out)]
        return source,out,args

    def test_cli_source_locked_inventory_reopens_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as d:
            source,out,args=self.cli(Path(d));original=source.read_bytes();self.assertEqual(main(args),0)
            r=json.loads(out.read_text());self.assertEqual(r['declarations'][0]['local_property_count'],3)
            self.assertFalse(r['native_layout_verified']);self.assertEqual(source.read_bytes(),original);self.assertEqual(main(args),2)

    def test_cli_missing_selection_and_bad_source_are_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            source,out,args=self.cli(Path(d));args[4]='Missing';self.assertEqual(main(args),1)
            self.assertEqual(len(json.loads(out.read_text())['unparsed']),1)
            args[2]='0'*64;args[-1]=str(Path(d)/'bad.json');self.assertEqual(main(args),2)
            adapter=Path(d)/'adapter.bin';adapter.write_bytes(b'self-authored placeholder')
            with patch('tools.inspect_property_declarations.LzxDecoder') as load:
                self.assertEqual(main(args+['--lzx-library',str(adapter)]),2);load.assert_not_called()

    def test_cli_late_input_change_removes_only_own_output(self):
        with tempfile.TemporaryDirectory() as d:
            source,out,args=self.cli(Path(d));read=Path.read_bytes
            def changed(path):
                data=read(path)
                if path==out:source.write_bytes(b'changed self-authored input')
                return data
            with patch.object(Path,'read_bytes',changed):self.assertEqual(main(args),2)
            self.assertFalse(out.exists())

    def test_cli_external_output_change_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            source,out,args=self.cli(Path(d));read=Path.read_bytes
            def changed(path):
                data=read(path)
                if path==out:out.write_bytes(b'external changed bytes')
                return data
            with patch.object(Path,'read_bytes',changed):self.assertEqual(main(args),2)
            self.assertEqual(out.read_bytes(),b'external changed bytes')


if __name__=='__main__':unittest.main()
