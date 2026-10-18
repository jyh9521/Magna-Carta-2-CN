"""Self-authored instruction/literal/metadata fixtures, no target execution."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import test_style_predicate as fixtures
from tools.ppc_style_predicate import predicate_words
from tools.ppc_style_reference_helper import helper_words,verify_style_reference_helper
from tools.ppc_class_tables import registration_words
from tools.xex_image import digest,VirtualImage
from tools.inspect_native_bindings import main


class ReferenceFixture(fixtures.PredicateFixture):
    def __init__(self):
        super().__init__();v=self.base
        self.plan['code_ranges'].append([v+0x6000,v+0x9000])
        self.le(0x5018+0xe0+40+8,0x1000)  # expand the synthetic read-only literal section
        c=dict(profile='ppc-style-reference-helper-v1',start=v+0x6000,save_helper=v+0x1920,
            restore_helper=v+0x1930,lookup_call=v+0x1940,make_name_call=v+0x1950,fallbacks=[])
        self.plan['style_reference_helper']=c; self.plan['style_predicate']['reference_helper']=c['start']
        self.words(self.plan['style_predicate']['start'],predicate_words(self.plan['style_predicate']['start'],c['start']))
        for i in range(3):
            row=dict(native_name='UStyle'+chr(65+i),name_address=v+0x2600+i*0x40,tag_name='DefaultStyle'+chr(65+i),
                tag_address=v+0x2700+i*0x40,registration_start=v+0x6600+i*0x200,callback_word=v+0x810+i*4,size_operand=104+i*4)
            c['fallbacks'].append(row)
            for key,text in [('name_address',row['native_name']),('tag_address',row['tag_name'])]:
                at=row[key]-v;encoded=(text+'\0').encode('utf-16-be');self.image[at:at+len(encoded)]=encoded
            self.words(row['registration_start'],[0x60000000]*70)
            at=row['registration_start']+52
            self.words(at,registration_words(at,row['name_address'],row['callback_word'],row['size_operand'],self.plan['class_tables']))
        self.words(c['start'],helper_words(c['start'],c))
        self.le(0x5018+124,80);self.le(0x5018+0xe0+8,80)
        for i,(start,count,prologue) in enumerate([(c['start'],90,3)]+[(r['registration_start'],70,5) for r in c['fallbacks']],6):
            self.put(v+0x600+i*8,start);self.put(v+0x604+i*8,0x40000000|count<<8|prologue)
        self.refresh_reference()

    def refresh_reference(self):
        c=self.plan['style_reference_helper'];s=c['start']-self.base;c['sha256']=digest(self.image[s:s+360])
        for row in c['fallbacks']:
            s=row['registration_start']+52-self.base;row['registration_sha256']=digest(self.image[s:s+64])
        self.refresh_predicate()


class ReferenceHelperTests(unittest.TestCase):
    def test_full_helper_and_three_name_tag_registration_associations(self):
        f=ReferenceFixture();before=bytes(f.image);r=f.run()['style_reference_helper']
        self.assertEqual(r['instruction_count'],90);self.assertTrue(r['predicate_call_association_verified'])
        self.assertEqual([a['tag_name'] for a in r['class_name_tag_operand_associations']],['DefaultStyleA','DefaultStyleB','DefaultStyleC'])
        self.assertEqual([a['native_name'] for a in r['class_name_tag_operand_associations']],['UStyleA','UStyleB','UStyleC'])
        self.assertEqual(bytes(f.image),before)

    def test_independent_instruction_encodings_and_64bit_name_copy(self):
        f=ReferenceFixture();raw=f.image[0x6000:0x6168]
        self.assertEqual(struct.unpack_from('>I',raw,24)[0],0x91630000)
        self.assertEqual(struct.unpack_from('>I',raw,80)[0],0xe97e0000)
        self.assertEqual(struct.unpack_from('>I',raw,92)[0],0xf9610050)
        self.assertEqual(struct.unpack_from('>I',raw,184)[0],0x816b003c)
        self.assertEqual(struct.unpack_from('>I',raw,340)[0],0x915c0000)

    def test_loops_and_optional_flag_stores_are_not_runtime_claims(self):
        f=ReferenceFixture();r=f.run()['style_reference_helper'];s=f.base+0x6000
        self.assertEqual([p['comparison']-s for p in r['class_chain_loops']],[176,212,248])
        self.assertEqual([p['backedge']-s for p in r['class_chain_loops']],[192,228,264])
        self.assertEqual(r['direct_optional_flag_stores'],[{'address':s+44,'value':0},{'address':s+136,'value':1}])
        for key in ['loop_termination_verified','external_call_semantics_verified','callee_register_preservation_verified',
                    'serialized_native_layout_verified','native_owner_pointer_identity_verified','runtime_dispatch_verified',
                    'effective_style_verified','active_font_verified','executed','image_modified']:
            self.assertIs(r[key],False)

    def test_every_helper_byte_rejects_mutation_even_with_refreshed_hash(self):
        for i in range(360):
            f=ReferenceFixture();f.image[0x6000+i]^=1;f.refresh_reference()
            with self.subTest(i=i),self.assertRaisesRegex(ValueError,'reference helper structural'):f.run()

    def test_every_registration_byte_rejects_refreshed_hash_mutation(self):
        for row_index in range(3):
            for i in range(64):
                f=ReferenceFixture();at=0x6600+row_index*0x200+52+i;f.image[at]^=1;f.refresh_reference()
                with self.subTest(row=row_index,i=i),self.assertRaisesRegex(ValueError,'registration argument template'):f.run()

    def test_literal_content_boundary_number_and_address_guards(self):
        for field in ['name_address','tag_address']:
            for mutation in ['content','boundary','unaligned','outside']:
                f=ReferenceFixture();row=f.plan['style_reference_helper']['fallbacks'][0];at=row[field]-f.base
                if mutation=='content':f.image[at+1]^=1
                elif mutation=='boundary':f.image[at-1]=1
                elif mutation=='unaligned':row[field]+=1
                else:row[field]=f.base+0x6000
                f.refresh_reference()
                with self.subTest(field=field,mutation=mutation),self.assertRaisesRegex(ValueError,'literal boundary'):f.run()

    def test_unknown_and_malformed_profile_fields_fail(self):
        for value in [None,True,{},[]]:
            f=ReferenceFixture();f.plan['style_reference_helper']=value
            with self.subTest(value=value),self.assertRaises(ValueError):f.run()
        for key,value in [('profile','wrong'),('extra',0),('save_helper',True),('restore_helper',0x82001931),
                          ('lookup_call',0x82006004),('make_name_call',0x8200a000)]:
            f=ReferenceFixture();f.plan['style_reference_helper'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):f.run()

    def test_fallback_count_fields_types_duplicates_and_names_fail(self):
        for change in ['count','type','fields','duplicate','order','name','tag','size-bool','reg-bool','callback-align','callback-self']:
            f=ReferenceFixture();c=f.plan['style_reference_helper'];row=c['fallbacks'][0]
            if change=='count':c['fallbacks'].pop()
            elif change=='type':c['fallbacks']={}
            elif change=='fields':row['extra']=0
            elif change=='duplicate':c['fallbacks'][1]=copy.deepcopy(row)
            elif change=='order':c['fallbacks'][0],c['fallbacks'][1]=c['fallbacks'][1],c['fallbacks'][0]
            elif change=='name':row['native_name']='StyleA'
            elif change=='tag':row['tag_name']='bad tag'
            elif change=='size-bool':row['size_operand']=True
            elif change=='reg-bool':row['registration_start']=True
            elif change=='callback-align':row['callback_word']+=1
            else:row['callback_word']=c['start']+4
            with self.subTest(change=change),self.assertRaises(ValueError):f.run()

    def test_helper_hash_and_parent_predicate_target_guards(self):
        f=ReferenceFixture();f.plan['style_reference_helper']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'window hash'):f.run()
        f=ReferenceFixture();f.plan['style_reference_helper']['start']+=4
        with self.assertRaisesRegex(ValueError,'verified predicate call'):f.run()

    def test_helper_declared_extent_and_prologue_required(self):
        for packed in [0x40005903,0x40005a04]:
            f=ReferenceFixture();f.put(f.base+0x634,packed);f.refresh_reference()
            with self.subTest(packed=packed),self.assertRaisesRegex(ValueError,'declared extent/prologue'):f.run()

    def test_missing_registration_entry_not_inferred_from_adjacent(self):
        f=ReferenceFixture();f.put(f.base+0x638,f.base+0x65fc);f.refresh_reference()
        with self.assertRaisesRegex(ValueError,'registration lacks covering'):f.run()

    def test_opt_in_dependency_and_unchanged_old_report_shape(self):
        f=ReferenceFixture();del f.plan['style_predicate']
        with self.assertRaisesRegex(ValueError,'explicit style predicate'):f.run()
        f=ReferenceFixture();del f.plan['style_reference_helper'];self.assertNotIn('style_reference_helper',f.run())
        self.assertNotIn('style_reference_helper',fixtures.PredicateFixture().run())

    def cli_fixture(self,directory):
        root=Path(directory);f=ReferenceFixture();im=root/'image.bin';plan=root/'plan.json';meta=root/'metadata.json';out=root/'report.json'
        im.write_bytes(f.image);plan.write_bytes(json.dumps(f.plan).encode());meta.write_bytes(f.metadata_raw)
        return im,plan,meta,out,[str(im),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report',str(meta),'--output',str(out)]

    def test_cli_report_reopening_and_input_identity(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli_fixture(d);before=[p.read_bytes() for p in [im,plan,meta]]
            self.assertEqual(main(args),0);r=json.loads(out.read_text());self.assertEqual(r['style_reference_helper']['instruction_count'],90)
            self.assertEqual(main(args),2);self.assertEqual(before,[p.read_bytes() for p in [im,plan,meta]])

    def test_cli_wrong_helper_plan_never_publishes_output(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli_fixture(d);p=json.loads(plan.read_bytes());p['style_reference_helper']['lookup_call']+=4
            plan.write_bytes(json.dumps(p).encode());args[6]=digest(plan.read_bytes());self.assertEqual(main(args),2);self.assertFalse(out.exists())

    def test_cli_late_mutation_and_external_output_preservation(self):
        with tempfile.TemporaryDirectory() as d:
            im,plan,meta,out,args=self.cli_fixture(d);read=Path.read_bytes
            def changed(path):
                data=read(path)
                if path==out:im.write_bytes(b'changed fixture');out.write_bytes(b'external bytes')
                return data
            with patch.object(Path,'read_bytes',changed):self.assertEqual(main(args),2)
            self.assertEqual(out.read_bytes(),b'external bytes')


if __name__=='__main__':
    unittest.main()
