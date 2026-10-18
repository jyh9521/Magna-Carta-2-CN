"""Self-authored PPC words, image/table and metadata; never execute instructions."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools.xex_image import VirtualImage,digest
from tools.ppc_native_bindings import inspect_bindings,recover_stores,mask32
from tools.inspect_native_bindings import main


def D(op,t,a,imm):return op*2**26+t*2**21+a*2**16+(imm%65536)
def X(t,a,b,xo):return 31*2**26+t*2**21+a*2**16+b*2**11+xo*2
def MR(t,s):return X(s,t,s,444)
def ROT(t,s,sh,mb,me):return 21*2**26+s*2**21+t*2**16+sh*2**11+mb*2**6+me*2
def B(pc,target,link=0):return 18*2**26+((target-pc)%2**26)+link
def BC(pc,target,bo):return 16*2**26+bo*2**21+26*2**16+((target-pc)%65536)


class NativeFixture:
    def __init__(self):
        self.base=0x82000000;v=self.base;self.image=bytearray(65536)
        self.plan=dict(schema_version=1,profile='ppc-native-row12-cold-init-v1',image_base=v,code_ranges=[[v+0x100,v+0x1800]],
            string_range=[v+0x2000,v+0x2800],data_range=[v+0x3000,v+0x4000],table_address=v+0x3000,table_count=2,
            symbol_prefix='intUFixtureexec',engine_class='Fixture',engine_class_index=1,engine_source_sha256='d'*64,
            initializer_start=v+0x400,initializer_tail=v+0x700,lookup_start=v+0x100,lookup_prologue=v+0x300,
            lookup_comparator=v+0x320,lookup_epilogue=v+0x340,
            font_fields=dict(setter_method='SetFont',setter_alias_offset=0x28,setter_window_offset=0x88,
                disable_method='DisableCustomFont',disable_alias_offset=0x14,disable_window_offset=0x54,disable_skip_offset=0x78,conditional_helper=v+0xc00))
        functions=[];self.codes=[v+0x800,v+0xa00];ptr=v+0x2000
        for i,name in enumerate(['SetFont','DisableCustomFont']):
            encoded=('intUFixtureexec'+name+'\0').encode('utf-16-be');self.image[ptr-v:ptr-v+len(encoded)]=encoded
            self.put(v+0x3000+i*12,ptr);ptr+=len(encoded)+2
            owner=dict(package='engine',object_index=10+i,path='Fixture.'+name,class_path='Core.Function',source_sha256='d'*64)
            defining=dict(package='engine',object_index=1,path='Fixture',class_path='Class',source_sha256='d'*64)
            functions.append(dict(owner=owner,defining_class=defining,declared_native=True,native_token=0,
                script_kind='native-parameter-stub-only',function_flags_hex='00000400',return_declaration=None,
                parameters=[dict(kind='ObjectProperty',target=dict(path='engine.font'))] if i==0 else []))
        self.metadata=dict(source_sha256='d'*64,defining_class_scope='Fixture',functions=functions)
        words=[]
        for i,code in enumerate(self.codes+[0]):
            words += [D(15,11,0,(code+0x8000)>>16),D(14,11,11,code&65535),D(14,12,0,0),
                      D(36,11,1,-0x20),D(36,12,1,-0x1c),D(58,13,1,-0x20),D(15,14,0,0x8200),D(14,14,14,0x3000),D(62,13,14,4+12*i)]
        words.append(B(v+0x400+len(words)*4,v+0x700));self.words(v+0x400,words);self.plan['initializer_end']=v+0x400+len(words)*4
        s=v+0x100;t=v+0x3000
        lookup=[0x7d8802a6,B(s+4,v+0x300,1),D(37,1,1,-128),D(15,11,0,0x8200),MR(28,3),D(14,30,11,0x3000),D(14,31,0,0),D(32,11,11,0x3000),
            D(10,24,11,0),BC(s+36,s+100,12),MR(11,30),D(14,29,0,0),MR(3,28),D(32,4,11,0),B(s+56,v+0x320,1),D(11,24,3,0),
            BC(s+64,s+112,12),D(14,31,31,1),ROT(11,31,1,0,30),X(11,31,11,266),ROT(29,11,2,0,29),X(11,29,30,266),
            X(10,29,30,23),D(10,24,10,0),BC(s+96,s+48,4),D(14,3,0,0),D(14,1,1,128),B(s+108,v+0x340),D(14,11,30,4),X(3,29,11,266),D(14,1,1,128),B(s+124,v+0x340)]
        self.words(s,lookup);setter,disable=self.codes;self.put(setter+0x28,MR(30,3));self.put(disable+0x14,MR(31,3))
        self.words(setter+0x88,[D(32,9,30,0xe4),D(14,11,30,0xc4),D(32,10,1,0x50),D(32,8,30,0xd8),X(9,7,9,124),D(25,9,6,0x2000),X(5,8,10,40),ROT(4,7,3,31,31),D(36,6,30,0xe4),D(12,3,5,-1),D(36,10,30,0xd8)])
        dw=disable+0x54;self.words(dw,[D(32,10,31,0xe4),D(14,11,31,0xc4),ROT(9,10,3,31,31),ROT(8,10,0,3,1),D(11,24,9,0),D(36,8,31,0xe4),BC(dw+24,disable+0x78,12),MR(3,31),B(dw+32,v+0xc00,1)])
        self.refresh()
    def put(self,address,value):struct.pack_into('>I',self.image,address-self.base,value&0xffffffff)
    def words(self,address,words):
        for i,w in enumerate(words):self.put(address+4*i,w)
    def refresh(self):
        p=self.plan;self.metadata_raw=json.dumps(self.metadata,sort_keys=True).encode()
        p.update(image_sha256=digest(self.image),native_report_sha256=digest(self.metadata_raw),
            initializer_sha256=digest(self.image[p['initializer_start']-self.base:p['initializer_end']-self.base]),
            lookup_sha256=digest(self.image[p['lookup_start']-self.base:p['lookup_start']-self.base+128]))
    def run(self):return inspect_bindings(bytes(self.image),self.plan,self.metadata_raw,self.metadata)


class NativeBindingTests(unittest.TestCase):
    def test_complete_static_binding_and_paired_font_instruction_chains(self):
        f=NativeFixture();before=bytes(f.image);r=f.run()
        self.assertEqual([x['code_address'] for x in r['bindings']],f.codes)
        self.assertEqual(r['font_field_instruction_chains']['set_mask'],'20000000')
        self.assertEqual(r['font_field_instruction_chains']['clear_keep_mask'],'dfffffff')
        self.assertFalse(r['executed']);self.assertFalse(r['image_modified']);self.assertEqual(bytes(f.image),before)
        self.assertFalse(r['lookup']['comparator_semantics_verified']);self.assertFalse(r['engine_package_reread'])
        self.assertFalse(r['font_field_instruction_chains']['parameter_stack_producer_verified'])

    def test_symbolic_stack_reuse_retains_each_descriptor_provenance(self):
        f=NativeFixture();r=f.run()
        for i,row in enumerate(r['bindings']):
            evidence=row['initializer_evidence'];start=f.plan['initializer_start']+i*36
            self.assertIn(start,evidence['evidence_instructions']);self.assertIn(start+12,evidence['evidence_instructions'])
            self.assertEqual(evidence['store_instruction'],start+32);self.assertEqual(evidence['words'],[f.codes[i],0])

    def test_virtual_image_bounds_and_integer_types(self):
        v=VirtualImage(b'abc',0x1000);self.assertEqual(v.read(0x1000,3),b'abc')
        for addr,n in [(0xfff,1),(0x1000,4),(0x1000,-1),('x',1),(0x1000,True)]:
            with self.subTest(addr=addr,n=n),self.assertRaises(ValueError):v.read(addr,n)
        for base in [True,-1,0xffffffff]:
            with self.subTest(base=base),self.assertRaises(ValueError):VirtualImage(b'ab',base)

    def test_all_rotate_masks_against_independent_circular_bit_walk(self):
        for mb in range(32):
            for me in range(32):
                expected=0;i=mb
                while True:
                    expected|=1<<(31-i)
                    if i==me:break
                    i=(i+1)%32
                self.assertEqual(mask32(mb,me),expected)
        self.assertEqual(mask32(3,1)^0xffffffff,0x20000000)
        for value in [True,-1,32]:
            with self.assertRaises(ValueError):mask32(value,0)

    def test_image_metadata_and_code_hash_anchors_fail_closed(self):
        for key in ['image_sha256','native_report_sha256','initializer_sha256','lookup_sha256']:
            f=NativeFixture();f.plan[key]='0'*64
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_plan_profile_integer_ranges_and_overlaps(self):
        for key,value in [('schema_version',True),('profile','unknown'),('image_base',True),('table_count',0),('initializer_end',0),('lookup_prologue',0)]:
            f=NativeFixture();f.plan[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()
        for key in ['data_range','string_range']:
            f=NativeFixture();f.plan[key]=f.plan['code_ranges'][0]
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_cold_descriptor_sentinel_and_name_pointer_contract(self):
        for offset,value in [(4,1),(24,1),(0,0x82003000),(0,0x82002001)]:
            f=NativeFixture();f.put(f.plan['table_address']+offset,value);f.refresh()
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.run()

    def test_duplicate_wrong_prefix_and_unterminated_native_names(self):
        f=NativeFixture();f.put(f.plan['table_address']+12,f.plan['string_range'][0]);f.refresh()
        with self.assertRaises(ValueError):f.run()
        f=NativeFixture();f.plan['symbol_prefix']='Other'
        with self.assertRaises(ValueError):f.run()
        f=NativeFixture();f.image[0x2000:0x2800]=b'\x00A'*1024;f.refresh()
        with self.assertRaises(ValueError):f.run()

    def test_typed_engine_declarations_not_success_flags(self):
        for mutate in ['native','flags','class','scope','token','duplicate','methods','id','parameter']:
            f=NativeFixture();g=f.metadata['functions'][0]
            if mutate=='native':g['declared_native']=1
            elif mutate=='flags':g['function_flags_hex']='00000000'
            elif mutate=='class':g['defining_class']['object_index']=True
            elif mutate=='scope':g['owner']['path']='Other.SetFont'
            elif mutate=='token':g['native_token']=True
            elif mutate=='duplicate':f.metadata['functions'].append(copy.deepcopy(g))
            elif mutate=='methods':f.metadata['functions'].pop()
            elif mutate=='id':f.metadata['functions'][1]['owner']['object_index']=10
            else:g['parameters'][0]['target']['path']='engine.other'
            f.refresh()
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):f.run()

    def test_unknown_register_unwritten_stack_zero_base_and_ds_update(self):
        for index,word in [(3,D(36,31,1,-0x20)),(4,D(36,12,1,-0x18)),(3,D(36,11,0,-0x20)),(5,D(58,13,1,-0x20)|1)]:
            f=NativeFixture();f.put(f.plan['initializer_start']+index*4,word);f.refresh()
            with self.subTest(index=index,word=word),self.assertRaises(ValueError):f.run()

    def test_unsupported_control_flow_and_stack_base_updates(self):
        for index,word in [(0,D(14,1,1,1)),(3,B(0x8200040c,0x82000700)),(0,0x60000000)]:
            f=NativeFixture();f.put(f.plan['initializer_start']+index*4,word);f.refresh()
            with self.subTest(index=index),self.assertRaises(ValueError):f.run()

    def test_duplicate_missing_and_wrong_terminal_descriptor_stores(self):
        for where,word in [(17,D(62,13,14,4)),(26,D(14,13,0,0)),(27,B(0x8200046c,0x82000704))]:
            f=NativeFixture();f.put(f.plan['initializer_start']+where*4,word);f.refresh()
            with self.subTest(where=where),self.assertRaises(ValueError):f.run()

    def test_nonzero_sentinel_adjustor_and_noncode_targets(self):
        for where,value in [(2,D(14,12,0,1)),(1,D(14,11,11,0x2000)),(1,D(14,11,11,0x801)),(19,D(14,11,11,0x800))]:
            f=NativeFixture();f.put(f.plan['initializer_start']+where*4,value);f.refresh()
            with self.subTest(where=where,value=value),self.assertRaises(ValueError):f.run()

    def test_every_initializer_prefix_truncation(self):
        f=NativeFixture();p=f.plan;raw=bytes(f.image[p['initializer_start']-f.base:p['initializer_end']-f.base]);view=VirtualImage(bytes(f.image),f.base)
        slots=[p['table_address']+4+i*12 for i in range(3)]
        for n in range(len(raw)):
            with self.subTest(n=n),self.assertRaises(ValueError):recover_stores(view,raw[:n],p['initializer_start'],slots,p['initializer_tail'])

    def test_every_lookup_byte_mutation_fails_structural_check_even_with_new_hash(self):
        for i in range(128):
            f=NativeFixture();f.image[0x100+i]^=1;f.refresh()
            with self.subTest(i=i),self.assertRaises(ValueError):f.run()

    def test_every_font_chain_and_alias_byte_mutation_fails(self):
        for start,size in [(0x828,4),(0xa14,4),(0x888,44),(0xa54,36)]:
            for i in range(size):
                f=NativeFixture();f.image[start+i]^=1;f.refresh()
                with self.subTest(start=start,i=i),self.assertRaises(ValueError):f.run()

    def test_metadata_only_binding_can_omit_font_specific_profile(self):
        f=NativeFixture();f.plan['font_fields']=None;r=f.run()
        self.assertEqual(len(r['bindings']),2);self.assertIsNone(r['font_field_instruction_chains'])

    def test_cli_self_authored_image_plan_report_and_output_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=NativeFixture();image=root/'image.bin';plan=root/'plan.json';meta=root/'meta.json';out=root/'report.json'
            image.write_bytes(f.image);plan.write_text(json.dumps(f.plan));meta.write_bytes(f.metadata_raw)
            args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report',str(meta),'--output',str(out)]
            self.assertEqual(main(args),0);r=json.loads(out.read_text());self.assertFalse(r['executed']);self.assertEqual(len(r['bindings']),2)
            self.assertEqual(main(args),2);self.assertEqual(image.read_bytes(),f.image)
            for index in [2,6]:
                bad=args.copy();bad[index]='0'*64;bad[-1]=str(root/'never.json');self.assertEqual(main(bad),2);self.assertFalse(Path(bad[-1]).exists())

    def test_cli_ambiguous_json_and_source_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=NativeFixture();image=root/'image.bin';plan=root/'plan.json';meta=root/'meta.json';out=root/'report.json'
            image.write_bytes(f.image);meta.write_bytes(f.metadata_raw);plan.write_text(json.dumps(f.plan))
            args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report',str(meta),'--output',str(out)]
            raw=plan.read_bytes();plan.write_bytes(raw[:-1]+b',"profile":"duplicate"}');args[6]=digest(plan.read_bytes())
            self.assertEqual(main(args),2);self.assertFalse(out.exists());plan.write_bytes(raw);args[6]=digest(raw)
            def mutate(*a,**kw):
                result=inspect_bindings(*a,**kw);image.write_bytes(b'changed fixture');return result
            with patch('tools.inspect_native_bindings.inspect_bindings',side_effect=mutate):self.assertEqual(main(args),2)
            self.assertFalse(out.exists())

    def test_cli_byte_reopening_does_not_equate_false_and_zero(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=NativeFixture();image=root/'image.bin';plan=root/'plan.json';meta=root/'meta.json';out=root/'report.json'
            image.write_bytes(f.image);plan.write_text(json.dumps(f.plan));meta.write_bytes(f.metadata_raw)
            args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report',str(meta),'--output',str(out)]
            real=Path.read_bytes
            def altered(path):
                raw=real(path)
                return raw.replace(b'"executed": false',b'"executed": 0') if path==out else raw
            with patch.object(Path,'read_bytes',altered):self.assertEqual(main(args),2)


if __name__=='__main__':unittest.main()
