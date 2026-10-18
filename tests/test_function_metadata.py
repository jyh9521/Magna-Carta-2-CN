"""Self-authored function metadata/stub packages; never execute game code."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from test_struct_defaults import StructFixture
from test_ui_style_graph import word
from tools.inspect_function_metadata import main
from tools.ue3_function_metadata import parse_function_metadata, native_parameter_stub


class FunctionFixture(StructFixture):
    def __init__(self):
        super().__init__();self.ref['Function']=-len(self.imports)-1
        self.imports.append(dict(path='Core.Function',class_name=dict(name='Class')))
        for path,kind,outer in [('RendererClass.SetFont','Core.Function',1),
                                ('RendererClass.SetFont.NewFont','Core.ObjectProperty',21),
                                ('RendererClass.SetFont.ReturnValue','Core.BoolProperty',21)]:
            self.exports.append(dict(path=path,class_path=kind,outer=outer,super=0,archetype=0,
                object_flags='0000000000000000',serial_offset=0,serial_size=0,**{'class':self.ref[kind.split('.')[-1]]}))
        self.replace(22,self.declaration(23,0x80,2));self.replace(23,self.declaration(0,0x580))
        self.script=b'\x29'+word(22)+b'\x0b\x53';self.replace(21,self.function())

    def declaration(self,next_,flags,target=None):
        raw=word(0)+self.f.props()+word(0,next_,1)+struct.pack('>Q',flags)+self.f.fname('None')+word(0)
        return raw+(word(target) if target is not None else b'')

    def function(self,script=None,flags=0x00020401,children=22,friendly='SetFont',size=None,super_=0,editor=(0,0,282,7250)):
        code=self.script if script is None else script;script_text,cpp_text,line,text=editor
        return (word(0)+self.f.props()+word(super_,0,script_text,children,cpp_text,line,text,len(code) if size is None else size)
                +code+bytes(3)+word(flags)+self.f.fname(friendly))

    def parsed(self):return parse_function_metadata(self.graph(),('sample',21))


class FunctionMetadataTests(unittest.TestCase):
    def test_native_declaration_exact_stub_and_source_offsets(self):
        f=FunctionFixture();r=f.parsed();e=f.exports[20]
        self.assertTrue(r['declared_native']);self.assertFalse(r['native_implementation_verified'])
        self.assertFalse(r['runtime_effective_values_resolved']);self.assertEqual(r['native_token'],0)
        self.assertEqual(r['header']['line'],282);self.assertEqual(r['header']['text_pos'],7250)
        self.assertEqual(r['logical_script_offset'],e['serial_offset']+44)
        self.assertEqual(r['logical_metadata_tail_offset'],e['serial_offset']+51)
        self.assertEqual(r['function_flags_hex'],'00020401')
        self.assertEqual([x['opcode'] for x in r['script_tokens']],['NativeParm','Nothing','EndOfScript'])
        self.assertEqual(r['parameters'][0]['target']['path'],'sample.fontclass')
        self.assertTrue(r['return_declaration']['parameter_flags']['returns'])
        for token in r['script_tokens']:
            expected=dict(NativeParm=0x29,Nothing=0x0b,EndOfScript=0x53)[token['opcode']]
            self.assertEqual(f.ctx['logical'][token['logical_package_offset']],expected)

    def test_void_no_parameter_stub_is_not_an_implementation(self):
        f=FunctionFixture();f.exports[21]['outer']=0;f.exports[22]['outer']=0
        f.replace(21,f.function(script=b'\x0b\x53',children=0));r=f.parsed()
        self.assertEqual(r['parameters'],[]);self.assertIsNone(r['return_declaration'])
        self.assertEqual(r['script_kind'],'native-parameter-stub-only')

    def test_optional_out_parameter_flags_and_return_not_nativeparm(self):
        f=FunctionFixture();f.replace(22,f.declaration(23,0x190,2));r=f.parsed()
        self.assertEqual(r['parameters'][0]['parameter_flags'],dict(optional=True,out=True,returns=False))
        self.assertEqual([x.get('reference') for x in r['script_tokens']],[22,None,None])

    def test_every_function_payload_truncation_is_rejected(self):
        original=FunctionFixture();e=original.exports[20];raw=original.ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        for n in range(len(raw)):
            f=FunctionFixture();f.replace(21,raw[:n])
            with self.subTest(n=n),self.assertRaises(ValueError):f.parsed()

    def test_size_limits_and_mismatched_declared_size(self):
        for size in [-1,0,1,6,8,10243]:
            f=FunctionFixture();f.replace(21,f.function(size=size))
            with self.subTest(size=size),self.assertRaises(ValueError):f.parsed()

    def test_non_native_networked_and_extra_tail_are_rejected(self):
        for flags in [0,0x00020401&~0x400,0x00020441]:
            f=FunctionFixture();f.replace(21,f.function(flags=flags))
            with self.subTest(flags=flags),self.assertRaises(ValueError):f.parsed()
        f=FunctionFixture();f.replace(21,f.function()+b'x')
        with self.assertRaisesRegex(ValueError,'trailing'):f.parsed()

    def test_friendly_fname_retained_and_must_match_export(self):
        f=FunctionFixture();f.replace(21,f.function(friendly='Wrong'))
        with self.assertRaisesRegex(ValueError,'friendly name'):f.parsed()
        f=FunctionFixture();f.replace(21,f.function()[:-4]+word(1))
        with self.assertRaisesRegex(ValueError,'friendly name'):f.parsed()

    def test_editor_profile_and_super_mismatch(self):
        for editor in [(1,0,282,7250),(0,1,282,7250),(0,0,-1,7250),(0,0,282,-1)]:
            f=FunctionFixture();f.replace(21,f.function(editor=editor))
            with self.subTest(editor=editor),self.assertRaises(ValueError):f.parsed()
        f=FunctionFixture();f.replace(21,f.function(super_=1))
        with self.assertRaisesRegex(ValueError,'super mismatch'):f.parsed()
        f.exports[20]['super']=1
        with self.assertRaisesRegex(ValueError,'wrong class'):f.parsed()

    def test_wrong_metadata_class_stack_cdo_and_nonempty_uobject(self):
        for mutate in ['class','stack','cdo','tags']:
            f=FunctionFixture()
            if mutate=='class':f.exports[20]['class_path']='Core.ScriptStruct'
            elif mutate=='stack':f.exports[20]['object_flags']='0200000000000000'
            elif mutate=='cdo':f.exports[20]['object_flags']='0000000000000200'
            else:f.replace(21,word(0)+f.f.props(f.f.prop('Flag','BoolProperty',boolean=1))+f.function()[12:])
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):f.parsed()

    def test_function_owner_is_a_scoped_class_not_leaf_match(self):
        for owner in [0,3,-1]:
            f=FunctionFixture();f.exports[20]['outer']=owner
            with self.subTest(owner=owner),self.assertRaises(ValueError):f.parsed()

    def test_parameter_chain_cycles_omissions_and_cross_owner(self):
        for mutate in ['cycle','omission','cross-owner','import']:
            f=FunctionFixture()
            if mutate=='cycle':f.replace(22,f.declaration(22,0x80,2))
            elif mutate=='omission':f.replace(21,f.function(children=23))
            elif mutate=='cross-owner':f.exports[21]['outer']=1
            else:f.replace(21,f.function(children=-1))
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):f.parsed()

    def test_non_parameter_and_multiple_returns_are_rejected(self):
        for flags in [0,0x580]:
            f=FunctionFixture();f.replace(22,f.declaration(23,flags,2))
            with self.subTest(flags=flags),self.assertRaises(ValueError):f.parsed()

    def test_nativeparm_references_are_exact_owned_order_not_any_export(self):
        for ref in [0,1,23,-1,999999]:
            f=FunctionFixture();f.replace(21,f.function(script=b'\x29'+word(ref)+b'\x0b\x53'))
            with self.subTest(ref=ref),self.assertRaises(ValueError):f.parsed()

    def test_unknown_tokens_and_all_stub_mutations_are_rejected(self):
        raw=b'\x29'+word(22)+b'\x0b\x53'
        for i in range(len(raw)):
            mutated=bytearray(raw);mutated[i]^=1
            with self.subTest(i=i),self.assertRaises(ValueError):native_parameter_stub(bytes(mutated),[22])
        for raw in [b'',b'\x0b',b'\x0b\x53\x00',b'\x53\x0b',b'\x00\x53']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):native_parameter_stub(raw,[])

    def test_multiple_parameter_order_is_chain_order_not_export_sort(self):
        f=FunctionFixture();f.replace(22,f.declaration(0,0x80,2));f.replace(23,f.declaration(22,0x80))
        f.replace(21,f.function(script=b'\x29'+word(23)+b'\x29'+word(22)+b'\x0b\x53',children=23))
        r=f.parsed();self.assertEqual([p['owner']['object_index'] for p in r['parameters']],[23,22])
        self.assertIsNone(r['return_declaration'])
        f.replace(21,f.function(script=b'\x29'+word(22)+b'\x29'+word(23)+b'\x0b\x53',children=23))
        with self.assertRaisesRegex(ValueError,'order mismatch'):f.parsed()

    def test_native_token_and_operator_bytes_are_retained_not_executed(self):
        f=FunctionFixture();body=f.function();offset=44+len(f.script)
        f.replace(21,body[:offset]+b'\x01\x23\x07'+body[offset+3:]);r=f.parsed()
        self.assertEqual(r['native_token'],0x123);self.assertEqual(r['operator_precedence'],7)
        self.assertFalse(r['native_implementation_verified'])

    def test_cli_class_scope_only_selects_immediate_functions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(FunctionFixture().package())
            out=root/'class.json';args=[str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),
                '--class','RendererClass','--output',str(out)]
            self.assertEqual(main(args),0);r=json.loads(out.read_text(encoding='utf8'))
            self.assertEqual(r['selected_objects'],['RendererClass.SetFont'])
            args[4]='FontClass';args[-1]=str(root/'empty.json');self.assertEqual(main(args),2)
            args[4]='Renderer';args[-1]=str(root/'non-class.json');self.assertEqual(main(args),2)

    def test_cli_real_self_authored_package_and_partial_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(FunctionFixture().package());original=source.read_bytes()
            out=root/'report.json';args=[str(source),'--sha256',hashlib.sha256(original).hexdigest(),'--object','RendererClass.SetFont','--output',str(out)]
            self.assertEqual(main(args),0);report=json.loads(out.read_text(encoding='utf8'))
            self.assertEqual(len(report['functions']),1);self.assertEqual(source.read_bytes(),original)
            self.assertEqual(main(args),2)
            args[-1]=str(root/'partial.json');self.assertEqual(main(args+['--object','Missing']),1)
            report=json.loads(Path(args[-1]).read_text(encoding='utf8'));self.assertEqual(len(report['unparsed']),1)
            args[2]='0'*64;args[-1]=str(root/'wrong.json');self.assertEqual(main(args),2);self.assertFalse(Path(args[-1]).exists())


if __name__=='__main__':unittest.main()
