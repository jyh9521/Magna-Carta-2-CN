"""Self-authored initialized rows, scope reports and PE records; no execution."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import test_native_style_selection as fixtures
from tools.initialized_native_tables import inspect_tables
from tools.inspect_initialized_natives import main
from tools.xex_image import digest


class InitializedFixture:
    def __init__(self):
        old=fixtures.StyleFixture();self.image=old.image;self.base=v=old.base;self.put=old.put
        self.plan=dict(schema_version=1,profile='ppc-initialized-native-row8-v1',image_base=v,
            code_ranges=old.plan['code_ranges'],string_range=[v+0x3ff0,v+0x4800],data_range=[v+0x3000,v+0x3400],
            engine_source_sha256='2'*64,tables=[dict(label='Demo',engine_class='DemoClass',engine_class_index=3,
                table_address=v+0x3000,table_count=2,symbol_prefix='intUDemoClassexec')])
        cls=dict(package='engine',path='DemoClass',object_index=3,class_path='Class',source_sha256='2'*64)
        def record(name,index,native,token):
            return dict(owner=dict(package='engine',path='DemoClass.'+name,object_index=index,class_path='Core.Function',source_sha256='2'*64),
                defining_class=copy.deepcopy(cls),declared_native=native,native_token=token,function_flags_hex='00000400' if native else '00000000')
        records=[record('One',5,True,0),record('Two',6,True,470),record('Script',7,False,0)]
        self.meta=dict(schema_version=1,profile='446/25-big-retained-editor-fields-and-friendly-name',source_sha256='2'*64,
            defining_class_scope='DemoClass',include_scripted=False,unparsed=[],selected_objects=['DemoClass.One','DemoClass.Two'],
            functions=[dict(copy.deepcopy(row),script_kind='native-parameter-stub-only') for row in records[:2]],
            native_filter=dict(mode='declared-native-only',class_function_count=3,omitted_non_native_count=1,
                               inventory=records,omitted_scripts_decoded=False))
        for index,(name,target) in enumerate([('One',v+0x800),('Two',v+0xa00)]):
            at=0x4000+index*0x100;encoded=('intUDemoClassexec'+name+'\0').encode('utf-16-be')
            self.image[at:at+len(encoded)]=encoded;self.put(v+0x3000+index*8,v+at);self.put(v+0x3004+index*8,target)
        self.image[0x3010:0x3018]=bytes(8);self.refresh()

    def refresh(self):
        raw=json.dumps(self.meta).encode();self.metadata={'Demo':raw};t=self.plan['tables'][0]
        t['metadata_sha256']=digest(raw);t['table_sha256']=digest(self.image[0x3000:0x3018]);self.plan['image_sha256']=digest(self.image)

    def run(self):return inspect_tables(bytes(self.image),self.plan,self.metadata)


class InitializedNativeTests(unittest.TestCase):
    def test_complete_initialized_rows_preserve_zero_and_indexed_tokens(self):
        f=InitializedFixture();before=bytes(f.image);r=f.run();t,=r['tables']
        self.assertEqual(t['row_size'],8);self.assertEqual([x['native_token'] for x in t['bindings']],[0,470])
        self.assertEqual(t['metadata_coverage']['class_functions'],3);self.assertEqual(t['metadata_coverage']['omitted_non_native'],1)
        self.assertEqual([x['code_address'] for x in t['bindings']],[f.base+0x800,f.base+0xa00])
        self.assertEqual(bytes(f.image),before)

    def test_runtime_and_code_semantics_remain_unverified(self):
        r=InitializedFixture().run()
        for key in ['executed','image_modified','active_font_verified','runtime_registration_verified',
                    'engine_package_reread','code_body_semantics_verified','native_token_dispatch_semantics_verified']:
            self.assertIs(r[key],False)
        self.assertTrue(r['native_tokens_preserved']);self.assertTrue(r['static_name_code_association_verified'])

    def test_image_metadata_and_table_hashes_guard_inputs_independently(self):
        for target in ['image','metadata','table']:
            f=InitializedFixture()
            if target=='image':f.plan['image_sha256']='0'*64
            elif target=='metadata':f.plan['tables'][0]['metadata_sha256']='0'*64
            else:f.plan['tables'][0]['table_sha256']='0'*64
            with self.subTest(target=target),self.assertRaises(ValueError):f.run()

    def test_full_zero_sentinel_and_initialized_code_words_required(self):
        for offset,value in [(0x3010,1),(0x3014,1),(0x3004,0),(0x300c,0)]:
            f=InitializedFixture();f.put(f.base+offset,value);f.refresh()
            with self.subTest(offset=offset),self.assertRaises(ValueError):f.run()

    def test_symbol_full_boundary_termination_prefix_and_method_set(self):
        for change in ['boundary','unaligned','outside','wrong-prefix','duplicate','unterminated']:
            f=InitializedFixture()
            if change=='boundary':f.image[0x3fff]=1
            elif change=='unaligned':f.put(f.base+0x3000,f.base+0x4001)
            elif change=='outside':f.put(f.base+0x3000,f.base+0x3000)
            elif change=='wrong-prefix':f.plan['tables'][0]['symbol_prefix']='other'
            elif change=='duplicate':f.put(f.base+0x3008,f.base+0x4000)
            else:f.image[0x4000:0x4402]=b'A'*0x402
            f.refresh()
            with self.subTest(change=change),self.assertRaises(ValueError):f.run()

    def test_code_alignment_range_and_exact_pdata_not_neighbor_extent(self):
        for address in [0x82000801,0x82003000,0x82000804]:
            f=InitializedFixture();f.put(f.base+0x3004,address);f.refresh()
            with self.subTest(address=address),self.assertRaises(ValueError):f.run()

    def test_valid_code_alias_is_retained_not_invented_semantic_equality(self):
        f=InitializedFixture();f.put(f.base+0x300c,f.base+0x800);f.refresh();rows=f.run()['tables'][0]['bindings']
        self.assertEqual(rows[0]['code_address'],rows[1]['code_address']);self.assertNotEqual(rows[0]['method'],rows[1]['method'])
        self.assertFalse(rows[1]['function_semantics_verified'])

    def test_multiple_table_copies_retained_but_overlapping_windows_rejected(self):
        f=InitializedFixture();f.image[0x3100:0x3118]=f.image[0x3000:0x3018];f.refresh()
        alias=copy.deepcopy(f.plan['tables'][0]);alias.update(label='Alias',table_address=f.base+0x3100)
        f.plan['tables'].append(alias);f.metadata['Alias']=f.metadata['Demo']
        r=f.run();self.assertEqual([t['label'] for t in r['tables']],['Demo','Alias'])
        alias['table_address']=f.base+0x3000
        with self.assertRaisesRegex(ValueError,'windows overlap'):f.run()

    def test_profile_fields_types_ranges_and_overlap_guards(self):
        for key,value in [('profile','ppc-native-row12-cold-init-v1'),('schema_version',True),('image_base',True),
                          ('code_ranges',[]),('data_range',[0x82000800,0x82000900]),('string_range',[0x82004800,0x82004000]),('extra',0)]:
            f=InitializedFixture();f.plan[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_table_schema_count_labels_and_bounds_fail_closed(self):
        for key,value in [('label','../bad'),('table_count',True),('table_count',3),('table_address',0x82003001),
                          ('table_address',0x820033fc),('engine_class_index',True),('extra',0)]:
            f=InitializedFixture();f.plan['tables'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()
        f=InitializedFixture();f.plan['tables']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):f.run()
        for records in [{},{'extra':b'{}'}]:
            f=InitializedFixture();f.metadata=records
            with self.assertRaisesRegex(ValueError,'labels must match'):f.run()

    def test_scope_source_identity_and_bool_tokens_cannot_be_forged(self):
        for change in ['source','scope','class-index','owner-kind','owner-path','bool-token','flag','duplicate-id']:
            f=InitializedFixture();row=f.meta['functions'][0]
            if change=='source':f.meta['source_sha256']='3'*64
            elif change=='scope':f.meta['defining_class_scope']='Other'
            elif change=='class-index':row['defining_class']['object_index']=4
            elif change=='owner-kind':row['owner']['class_path']='Class'
            elif change=='owner-path':row['owner']['path']='Other.One'
            elif change=='bool-token':row['native_token']=True
            elif change=='flag':row['declared_native']=1
            else:f.meta['functions'][1]['owner']['object_index']=5
            f.refresh()
            with self.subTest(change=change),self.assertRaises(ValueError):f.run()

    def test_incomplete_inventory_or_unparsed_headers_cannot_shrink_scope(self):
        for change in ['unparsed','count','omitted','inventory-drop','selected','function-drop','token-mismatch','filter-mode']:
            f=InitializedFixture();fl=f.meta['native_filter']
            if change=='unparsed':f.meta['unparsed']=[{'object':'DemoClass.Bad'}]
            elif change=='count':fl['class_function_count']=2
            elif change=='omitted':fl['omitted_non_native_count']=0
            elif change=='inventory-drop':fl['inventory'].pop()
            elif change=='selected':f.meta['selected_objects'].pop()
            elif change=='function-drop':f.meta['functions'].pop()
            elif change=='token-mismatch':f.meta['functions'][0]['native_token']=1
            else:fl['mode']='guess'
            f.refresh()
            with self.subTest(change=change),self.assertRaises(ValueError):f.run()

    def test_missing_explicit_native_filter_and_scripted_records_rejected(self):
        for change in ['filter','scripted','kind','schema']:
            f=InitializedFixture()
            if change=='filter':del f.meta['native_filter']
            elif change=='scripted':f.meta['include_scripted']=True
            elif change=='kind':f.meta['functions'][0]['script_kind']='bounded-scripted-ui'
            else:f.meta['schema_version']=True
            f.refresh()
            with self.subTest(change=change),self.assertRaises(ValueError):f.run()

    def cli(self,root):
        f=InitializedFixture();image=root/'image.bin';plan=root/'plan.json';meta=root/'metadata.json';out=root/'report.json'
        image.write_bytes(f.image);plan.write_bytes(json.dumps(f.plan).encode());meta.write_bytes(f.metadata['Demo'])
        args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report','Demo',str(meta),'--output',str(out)]
        return image,plan,meta,out,args

    def test_cli_report_readback_no_overwrite_and_unchanged_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli(Path(d));before=[p.read_bytes() for p in [im,plan,meta]]
            self.assertEqual(main(args),0);self.assertEqual(json.loads(out.read_text())['tables'][0]['row_size'],8)
            self.assertEqual(main(args),2);self.assertEqual(before,[p.read_bytes() for p in [im,plan,meta]])

    def test_cli_duplicate_labels_bad_hash_and_ambiguous_json_fail(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli(Path(d));self.assertEqual(main(args+['--native-report','Demo',str(meta)]),2);self.assertFalse(out.exists())
            bad=args.copy();bad[2]='0'*64;self.assertEqual(main(bad),2)
            plan.write_bytes(plan.read_bytes()[:-1]+b',"profile":"duplicate"}');args[6]=digest(plan.read_bytes());self.assertEqual(main(args),2)

    def test_cli_source_mutation_before_publication_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli(Path(d))
            def changed(*a,**k):
                result=inspect_tables(*a,**k);im.write_bytes(b'changed synthetic image');return result
            with patch('tools.inspect_initialized_natives.inspect_tables',side_effect=changed):self.assertEqual(main(args),2)
            self.assertFalse(out.exists())

    def test_cli_late_mutation_removes_own_report(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli(Path(d));read=Path.read_bytes
            def changed(path):
                data=read(path)
                if path==out:meta.write_bytes(b'changed metadata')
                return data
            with patch.object(Path,'read_bytes',changed):self.assertEqual(main(args),2)
            self.assertFalse(out.exists())

    def test_cli_external_report_bytes_survive_readback_failure(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli(Path(d));read=Path.read_bytes
            def changed(path):
                data=read(path)
                if path==out:out.write_bytes(b'external change')
                return data
            with patch.object(Path,'read_bytes',changed):self.assertEqual(main(args),2)
            self.assertEqual(out.read_bytes(),b'external change')


if __name__=='__main__':unittest.main()
