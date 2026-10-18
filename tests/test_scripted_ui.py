"""Self-authored bytecode/metadata fixtures only; no VM or game execution."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_function_metadata import FunctionFixture
from test_ui_style_graph import word
from tools.ue3_ui_styles import StyleGraph
from tools.ue3_function_metadata import parse_function_metadata
from tools.ue3_scripted_ui import decode_script, native_operator
from tools.inspect_function_metadata import main


def local(ref=22):return b'\x00'+word(ref)
def instance(ref=24):return b'\x01'+word(ref)
def boolean(value):return b'\x2d'+value
def member(prop,struct_,value,copy_=0,mod=0):return b'\x35'+word(prop,struct_)+bytes([copy_,mod])+value
def ret(value):return b'\x04'+value
def finish(body=b''):return body+ret(b'\x3a'+word(23))+b'\x53'


class ScriptFixture(FunctionFixture):
    def __init__(self):
        super().__init__();self.exports[21]['class_path']='Core.BoolProperty';self.exports[21]['class']=self.ref['BoolProperty']
        self.replace(22,self.declaration(23,0x80))
        for name,kind in [('Flag','BoolProperty'),('Owner','ObjectProperty')]:
            self.exports.append(dict(path='RendererClass.'+name,class_path='Core.'+kind,outer=1,super=0,archetype=0,
                object_flags='0000000000000000',serial_offset=0,serial_size=0,**{'class':self.ref[kind]}))
            self.replace(len(self.exports),self.declaration(0,0,1 if kind=='ObjectProperty' else None))
        self.code=finish(ret(boolean(local())));self.set_code(self.code)
        self.core=FunctionFixture();c=self.core;c.exports[0]['path']='Object';c.exports[0]['super']=0
        c.exports[20]['path']='Object.Or';c.exports[21]['class_path']='Core.BoolProperty';c.exports[21]['class']=c.ref['BoolProperty']
        c.exports[22]['path']='Object.Or.Second'
        c.exports.append(dict(c.exports[22],path='Object.Or.ReturnValue'));c.replace(24,c.declaration(0,0x580))
        c.replace(22,c.declaration(23,0x80));c.replace(23,c.declaration(24,0x280))
        c.script=b'\x29'+word(22)+b'\x29'+word(23)+b'\x0b\x53'
        body=c.function(flags=0x23401,friendly='||');offset=44+len(c.script)
        c.replace(21,body[:offset]+struct.pack('>H',132)+body[offset+2:])

    def set_code(self,code,**kwargs):
        self.code=code;self.replace(21,self.function(script=code,flags=0x00020003,**kwargs))
    def graph(self):return StyleGraph(dict(sample=self.ctx,core=self.core.ctx))
    def parsed(self):return parse_function_metadata(self.graph(),('sample',21),True)
    def native_or(self,a,b):return b'\x84'+a+b'\x18'+struct.pack('>H',len(b)+1)+b+b'\x16'


class ScriptedUiTests(unittest.TestCase):
    def test_return_local_and_compiler_returnnothing_tail(self):
        f=ScriptFixture();r=f.parsed();p=r['script_program']
        self.assertFalse(r['declared_native']);self.assertFalse(p['executed'])
        self.assertTrue(p['full_script_consumed']);self.assertEqual(p['syntactically_reachable_offsets'],[0])
        self.assertEqual(p['source_like_statements'][0],'0000: return NewFont')
        self.assertIn('ReturnNothing',p['source_like_statements'][1])
        for t in r['script_tokens']:
            self.assertEqual(t['logical_package_offset'],r['logical_script_offset']+t['script_offset'])

    def test_native_operator_bound_to_unique_core_declaration_and_skip_span(self):
        f=ScriptFixture();f.set_code(finish(ret(f.native_or(boolean(local()),boolean(instance())))))
        r=f.parsed();op=r['script_program']['statements'][0]['value']
        self.assertEqual(op['native_token'],132);self.assertEqual(op['friendly_name']['name'],'||')
        self.assertEqual(op['callee']['package'],'core');self.assertFalse(op['native_implementation_verified'])
        self.assertEqual(op['arguments'][1]['opcode'],'Skip')

    def test_missing_duplicate_and_wrong_operator_scope(self):
        f=ScriptFixture();g=f.graph();g.packages.pop('core')
        with self.assertRaisesRegex(ValueError,'Core reference'):native_operator(g,132)
        with self.assertRaisesRegex(ValueError,'missing/ambiguous'):native_operator(f.graph(),133)
        c=f.core;c.exports.append(copy.deepcopy(c.exports[20]))
        with self.assertRaisesRegex(ValueError,'missing/ambiguous'):native_operator(f.graph(),132)

    def test_operator_friendly_alias_does_not_relax_nonoperator_names(self):
        f=ScriptFixture();r=parse_function_metadata(f.graph(),('core',21))
        self.assertEqual(r['friendly_name']['name'],'||')
        f.replace(21,f.function(friendly='Wrong'))
        with self.assertRaisesRegex(ValueError,'friendly name'):parse_function_metadata(f.graph(),('sample',21))

    def test_scoped_instance_assignment_and_forward_control_flow(self):
        f=ScriptFixture();assign=b'\x14'+boolean(instance())+boolean(local())
        condition=boolean(instance());jump_start=len(assign);dest=jump_start+3+len(condition)+len(assign)
        code=assign+b'\x07'+struct.pack('>H',dest)+condition+assign+ret(boolean(instance()))+b'\x53'
        f.set_code(code);p=f.parsed()['script_program']
        self.assertEqual(p['statements'][0]['opcode'],'LetBool')
        self.assertIn(dict(source=jump_start,target=dest,kind='condition-false'),p['control_flow_edges'])
        self.assertIn('self.Flag = NewFont',p['source_like_statements'][0])

    def test_jump_into_operand_backwards_or_outside_is_rejected(self):
        for dest in [0,1,4,65535]:
            f=ScriptFixture();f.set_code(b'\x07'+struct.pack('>H',dest)+boolean(local())+ret(boolean(local()))+b'\x53')
            with self.subTest(dest=dest),self.assertRaises(ValueError):f.parsed()

    def test_struct_member_array_and_cast_references(self):
        f=ScriptFixture();f.exports[21]['class_path']='Core.ByteProperty';f.exports[21]['class']=f.ref['ByteProperty']
        f.replace(22,f.declaration(23,0x80,3))
        array=member(12,5,instance(16));element=b'\x1a\x38\x3a'+local()+array
        f.set_code(finish(b'\x0f'+element+local()+ret(b'\x27')))
        p=f.parsed()['script_program'];self.assertIn('self.TextStyleCustomization.Alignment[int(NewFont)] = NewFont',p['source_like_statements'][0])
        self.assertEqual(p['statements'][0]['target']['value_type']['array_dim'],1)

    def test_struct_owner_context_flags_and_array_dimension_mismatches(self):
        for prop_,struct_,copy_,mod in [(9,5,0,0),(12,4,0,0),(12,5,2,0),(12,5,0,2)]:
            f=ScriptFixture();f.set_code(finish(ret(boolean(member(prop_,struct_,instance(16),copy_,mod)))))
            with self.subTest(values=(prop_,struct_,copy_,mod)),self.assertRaises(ValueError):f.parsed()
        f=ScriptFixture();f.set_code(finish(ret(b'\x1a\x25'+instance())))
        with self.assertRaises(ValueError):f.parsed()

    def test_inherited_struct_member_owner_is_validated(self):
        f=ScriptFixture();f.exports[4]['super']=4
        raw=f.ctx['logical'][f.exports[4]['serial_offset']:f.exports[4]['serial_offset']+f.exports[4]['serial_size']]
        f.replace(5,raw[:12]+word(4)+raw[16:])
        value=member(8,5,instance(16));f.set_code(finish(ret(boolean(value))))
        self.assertIn('self.TextStyleCustomization.Bold',f.parsed()['script_program']['source_like_statements'][0])
        f.exports[3]['super']=5
        with self.assertRaisesRegex(ValueError,'ancestry'):f.parsed()

    def test_local_and_instance_references_cannot_cross_owners(self):
        for value in [local(24),local(0),instance(22),instance(8),instance(999999)]:
            f=ScriptFixture();f.set_code(finish(ret(boolean(value))))
            with self.subTest(value=value),self.assertRaises(ValueError):f.parsed()

    def test_bool_cast_assignment_and_return_types_are_checked(self):
        for value in [b'\x2d\x25',b'\x38\x3a'+local(),b'\x38\x3b'+local(),b'\x25']:
            f=ScriptFixture();f.set_code(finish(ret(value)))
            with self.subTest(value=value),self.assertRaises(ValueError):f.parsed()
        for code in [b'\x14\x27\x28',b'\x14'+boolean(instance())+b'\x25',b'\x0f'+instance()+b'\x25']:
            f=ScriptFixture();f.set_code(finish(code))
            with self.subTest(code=code),self.assertRaises(ValueError):f.parsed()

    def test_optional_default_span_and_header_order(self):
        f=ScriptFixture();f.replace(22,f.declaration(23,0x90))
        f.set_code(b'\x49\x00\x02\x27\x15'+finish(ret(boolean(local()))))
        p=f.parsed()['script_program'];self.assertEqual(p['source_like_statements'][0],'0000: default NewFont = true')
        for code in [f.code[5:],b'\x49\x00\x01\x27\x15'+f.code[5:],b'\x49\x00\x02\x27\x16'+f.code[5:],ret(boolean(local()))+f.code]:
            f.set_code(code)
            with self.subTest(code=code),self.assertRaises(ValueError):f.parsed()

    def test_direct_call_signature_without_callee_body_execution(self):
        f=ScriptFixture();f.set_code(finish(ret(b'\x1c'+word(21)+boolean(local())+b'\x16')))
        call=f.parsed()['script_program']['statements'][0]['value']
        self.assertFalse(call['callee_body_verified']);self.assertEqual(call['callee']['object_index'],21)
        for args in [b'',b'\x25',boolean(local())+boolean(local()),b'\x4a']:
            f.set_code(finish(ret(b'\x1c'+word(21)+args+b'\x16')))
            with self.subTest(args=args),self.assertRaises(ValueError):f.parsed()

    def test_out_and_skip_parameter_constraints(self):
        f=ScriptFixture();f.replace(22,f.declaration(23,0x180))
        f.set_code(finish(ret(b'\x1c'+word(21)+b'\x27\x16')))
        with self.assertRaisesRegex(ValueError,'out argument'):f.parsed()
        f=ScriptFixture();f.set_code(finish(ret(b'\x84'+boolean(local())+boolean(instance())+b'\x16')))
        with self.assertRaisesRegex(ValueError,'Skip argument'):f.parsed()

    def test_context_retains_unverified_skip_meaning(self):
        f=ScriptFixture();call=b'\x1c'+word(21)+boolean(local())+b'\x16'
        f.set_code(b'\x19'+instance(25)+b'\x00\x05\x00'+call+finish(ret(boolean(local()))))
        ctx=f.parsed()['script_program']['statements'][0]
        self.assertFalse(ctx['skip_vm_meaning_verified']);self.assertEqual(ctx['raw_skip_size'],5)
        for prefix in [b'\x19'+instance(25)+b'\x00\x05\x01',b'\x19'+boolean(local())+b'\x00\x05\x00']:
            f.set_code(prefix+call+finish(ret(boolean(local()))))
            with self.subTest(prefix=prefix),self.assertRaises(ValueError):f.parsed()

    def test_skip_size_terminator_and_missing_core_fail_closed(self):
        f=ScriptFixture();code=finish(ret(f.native_or(boolean(local()),boolean(instance()))))
        for size in [0,1,65535]:
            data=bytearray(code);pos=data.index(0x18);data[pos+1:pos+3]=struct.pack('>H',size);f.set_code(bytes(data))
            with self.subTest(size=size),self.assertRaisesRegex(ValueError,'Skip span'):f.parsed()
        f.set_code(code);g=f.graph();g.packages.pop('core')
        with self.assertRaises(ValueError):parse_function_metadata(g,('sample',21),True)

    def test_unknown_tokens_end_and_statement_placement_fail_closed(self):
        for code in [b'\x03'+finish(),finish()+b'\x00',finish()[:-1],b'\x53',b'\x27'+finish(),ret(ret(boolean(local())))+b'\x53',b'\x0b'+finish(),b'\x4a'+finish()]:
            f=ScriptFixture();f.set_code(code)
            with self.subTest(code=code),self.assertRaises(ValueError):f.parsed()

    def test_every_script_truncation_rejected(self):
        f=ScriptFixture();code=finish(ret(f.native_or(boolean(local()),boolean(instance()))))
        for n in range(len(code)):
            f.set_code(code[:n])
            with self.subTest(n=n),self.assertRaises(ValueError):f.parsed()

    def test_enum_assignment_identity_and_return_marker_placement(self):
        f=ScriptFixture();f.exports[21]['class_path']='Core.ByteProperty';f.exports[21]['class']=f.ref['ByteProperty']
        f.replace(22,f.declaration(23,0x80,0));element=b'\x1a\x25'+member(12,5,instance(16))
        f.set_code(finish(b'\x0f'+element+local()))
        with self.assertRaisesRegex(ValueError,'assignment'):f.parsed()
        f=ScriptFixture();f.set_code(finish(ret(f.native_or(b'\x3a'+word(23),boolean(instance())))))
        with self.assertRaisesRegex(ValueError,'return marker'):f.parsed()

    def test_primary_and_reference_hashes_precede_optional_decoder_loading(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=ScriptFixture();source=root/'sample.xxx';core=root/'Core.xxx'
            source.write_bytes(f.package());core.write_bytes(f.core.package())
            args=[str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),'--object','RendererClass.SetFont',
                '--reference-package','Core',str(core),hashlib.sha256(core.read_bytes()).hexdigest(),
                '--lzx-library',str(root/'never-load.dll'),'--output',str(root/'never-write.json')]
            for index in [2,8]:
                bad=args.copy();bad[index]='0'*64
                with self.subTest(index=index),patch('tools.inspect_function_metadata.LzxDecoder') as decoder:
                    self.assertEqual(main(bad),2);decoder.assert_not_called()

    def test_nesting_limit_and_nonzero_scripted_native_token(self):
        f=ScriptFixture();f.set_code(finish(ret(b'\x2d'*66+local())))
        with self.assertRaisesRegex(ValueError,'limit'):f.parsed()
        f=ScriptFixture();body=f.function(script=f.code,flags=0x20003);offset=44+len(f.code)
        f.replace(21,body[:offset]+b'\x00\x01'+body[offset+2:])
        with self.assertRaisesRegex(ValueError,'native token'):f.parsed()

    def test_local_declarations_reject_parameter_only_flags(self):
        for flags in [0x10,0x100,0x200,0x400,0x800]:
            f=ScriptFixture();f.replace(22,f.declaration(23,flags))
            with self.subTest(flags=flags),self.assertRaisesRegex(ValueError,'parameter-only flags'):f.parsed()

    def test_cli_scripted_opt_in_and_reference_hash_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=ScriptFixture();source=root/'sample.xxx';core=root/'Core.xxx'
            source.write_bytes(f.package());core.write_bytes(f.core.package());out=root/'report.json'
            args=[str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),'--object','RendererClass.SetFont',
                '--reference-package','Core',str(core),hashlib.sha256(core.read_bytes()).hexdigest(),'--output',str(out)]
            self.assertEqual(main(args),1);self.assertEqual(len(json.loads(out.read_text(encoding='utf8'))['unparsed']),1)
            args[-1]=str(root/'script.json');self.assertEqual(main(args+['--include-scripted']),0)
            r=json.loads(Path(args[-1]).read_text(encoding='utf8'));self.assertFalse(r['functions'][0]['script_program']['executed'])
            self.assertEqual(r['reference_sources'],[dict(package='core',sha256=hashlib.sha256(core.read_bytes()).hexdigest())])
            args[8]='0'*64;args[-1]=str(root/'bad-core.json');self.assertEqual(main(args+['--include-scripted']),2)
            self.assertFalse(Path(args[-1]).exists())


if __name__=='__main__':unittest.main()
