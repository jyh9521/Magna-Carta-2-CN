"""Synthetic PE, registration arguments and static table/initializer/getter words."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from test_native_style_selection import StyleFixture
from tools.ppc_class_tables import registration_words,initializer_words,getter_words,halves
from tools.xex_image import digest
from tools.inspect_native_bindings import main


class ClassFixture(StyleFixture):
    def __init__(self,family='base'):
        super().__init__();v=self.base;im=self.image
        struct.pack_into('<H',im,0x5006,2)
        self.le(0x5018+124,40);self.le(0x5018+0xe0+8,40)
        sec=0x5018+0xe0+40;im[sec:sec+8]=b'.rdata\0\0'
        struct.pack_into('<4I',im,sec+8,0x800,0x2000,0x800,0x2222);self.le(sec+36,0x40000040)
        c=dict(profile='ppc-class-name-table-v1',common_name_address=v+0x2240,shared_callback=v+0x1900,
               registration_helper=v+0x1910,base_secondary_table=v+0x2260,secondary_table=v+0x2280,
               getter_start=v+0x1b00,getter_prologue=v+0x1920,getter_epilogue=v+0x1930,
               reference_helper=v+0x1940,state_helper=v+0x1950,cast_helper=v+0x1960)
        row=dict(native_name='UFixture',name_address=v+0x2200,table_address=v+0x2300,
                 callback_start=v+0x1400,registration_start=v+0x1600,size_operand=0x110,initializer_family=family)
        c['classes']=[row];self.plan['class_tables']=c
        name=(row['native_name']+'\0').encode('utf-16-be');im[0x2200:0x2200+len(name)]=name
        self.words(v+0x1634,registration_words(v+0x1634,row['name_address'],row['callback_start'],row['size_operand'],c))
        self.words(row['callback_start'],initializer_words(family,row['table_address'],c))
        self.words(c['getter_start'],getter_words(c['getter_start'],c))
        self.words(row['table_address'],[v+0x800]*81);self.put(row['table_address']+0x128,c['getter_start'])
        for i,(s,n) in enumerate([(v+0x1600,70),(v+0x1b00,61)],3):self.put(v+0x600+i*8,s);self.put(v+0x604+i*8,0x40000000|n<<8|3)
        self.refresh_class()
    def refresh_class(self):
        c=self.plan['class_tables'];v=self.base;c['getter_sha256']=digest(self.image[c['getter_start']-v:c['getter_start']-v+244])
        for row in c['classes']:
            for key,start,n in [('registration',row['registration_start']+52,64),('initializer',row['callback_start'],84),('table',row['table_address'],324)]:
                row[key+'_sha256']=digest(self.image[start-v:start-v+n])
        self.refresh_style()


class NativeClassTableTests(unittest.TestCase):
    def test_scoped_name_callback_table_and_verified_getter_association(self):
        f=ClassFixture();before=bytes(f.image);r=f.run()['class_tables'];row=r['classes'][0]
        self.assertEqual(row['registration_name'],'Fixture');self.assertEqual(row['name_argument_address'],f.base+0x2202)
        self.assertEqual(row['slot128'],f.base+0x1b00);self.assertEqual(row['callback_argument_word'],f.base+0x1400)
        self.assertTrue(r['static_slot_target_association_verified']);self.assertFalse(r['runtime_dispatch_verified'])
        self.assertEqual(bytes(f.image),before);self.assertFalse(r['executed']);self.assertFalse(r['image_modified'])

    def test_base_initializer_retains_both_secondary_stores_in_order(self):
        r=ClassFixture().run()['class_tables']['classes'][0];stores=r['ordered_explicit_stores']
        self.assertEqual([s['offset'] for s in stores],[0x6c,0,0x6c,0x70,0x74,0xa0,0xa1,0xbc,0xbd])
        self.assertNotEqual(stores[0]['value'],stores[2]['value']);self.assertEqual(stores[-1]['width'],1)
        self.assertFalse(r['font_pointer_flag_written_by_leaf']);self.assertFalse(r['full_constructor_state_verified'])

    def test_derived_initializer_order_and_null_guard(self):
        r=ClassFixture('derived').run()['class_tables']['classes'][0];stores=r['ordered_explicit_stores']
        self.assertEqual([s['offset'] for s in stores],[0x6c,0x70,0x74,0xa0,0xa1,0xbc,0xbd,0,0x6c])
        self.assertIn('zero path returns without stores',r['initializer_guard'])
        self.assertIsNone(r['callback_pdata_record'])

    def test_getter_owner_vs_component_branch_operands_not_runtime_style_names(self):
        f=ClassFixture();r=f.run()['class_tables']['getter'];self.assertEqual(r['related_object_word_offset'],0x28)
        self.assertEqual(r['selection_virtual_slot'],0x124);self.assertEqual(r['nonzero_result_base']['addend'],0xe8)
        self.assertEqual(r['zero_result_base']['addend'],0x174);self.assertEqual(r['selected_pointer_word_offset'],0x1c)
        self.assertFalse(r['selection_virtual_target_verified']);self.assertFalse(r['callee_register_preservation_verified'])
        # Independent encodings: BEQ after virtual-call result selects owner branch.
        self.assertEqual(struct.unpack_from('>I',f.image,0x1b84)[0],0x419a0020)
        self.assertEqual(struct.unpack_from('>I',f.image,0x1b88)[0],0x3bfe00e8)
        self.assertEqual(struct.unpack_from('>I',f.image,0x1ba4)[0],0x3bff0174)

    def test_every_getter_registration_and_initializer_byte_rejects_refreshed_hash_mutations(self):
        for family in ['base','derived']:
            for start,n in [(0x1b00,244),(0x1634,64),(0x1400,84)]:
                for i in range(n):
                    f=ClassFixture(family);f.image[start+i]^=1;f.refresh_class()
                    with self.subTest(family=family,start=start,i=i),self.assertRaises(ValueError):f.run()

    def test_table_hash_rejects_every_mutated_byte_without_silently_relocking(self):
        for i in range(324):
            f=ClassFixture();f.image[0x2300+i]^=1;f.refresh_style()
            with self.subTest(i=i),self.assertRaisesRegex(ValueError,'table window hash'):f.run()

    def test_trusted_relocked_table_still_requires_code_words_and_exact_slot128(self):
        for offset,value in [(0,0),(4,0x82000801),(8,0x82000600),(0x128,0x82000800)]:
            f=ClassFixture();f.put(f.base+0x2300+offset,value);f.refresh_class()
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.run()

    def test_other_slots_are_hash_locked_not_falsely_assigned_helper_semantics(self):
        f=ClassFixture();f.put(f.base+0x2300+0x12c,f.base+0x810);f.refresh_class()
        row=f.run()['class_tables']['classes'][0];self.assertEqual(row['slot12c'],f.base+0x810)
        self.assertFalse(row['table_end_verified']);self.assertEqual(row['table_window_words'],81)

    def test_class_names_require_full_u_prefix_boundary_content_and_scope(self):
        for key,value in [('native_name','Fixture'),('native_name','UOther'),('name_address',0x82002202)]:
            f=ClassFixture();f.plan['class_tables']['classes'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()
        f=ClassFixture();f.image[0x21ff]=1;f.refresh_class()
        with self.assertRaisesRegex(ValueError,'name boundary'):f.run()
        f=ClassFixture();name='UOther';row=f.plan['class_tables']['classes'][0];row['native_name']=name;f.image[0x2200:0x2212]=(name+'\0').encode('utf-16-be').ljust(18,b'\0');f.refresh_class()
        with self.assertRaises(ValueError):f.run()

    def test_empty_duplicate_oversize_and_non_list_class_rows_fail(self):
        for value in [[],{},[None]*65]:
            f=ClassFixture();f.plan['class_tables']['classes']=value
            with self.subTest(value=type(value)),self.assertRaises(ValueError):f.run()
        f=ClassFixture();f.plan['class_tables']['classes']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):f.run()

    def test_profile_address_types_ranges_and_initializer_family_fail_closed(self):
        for key,value in [('profile','wrong'),('getter_start',True),('shared_callback',0x82003000),('secondary_table',0x82000600)]:
            f=ClassFixture();f.plan['class_tables'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()
        for key,value in [('size_operand',True),('size_operand',32768),('initializer_family','unknown'),('callback_start',0x82001401),('table_address',0x82002301)]:
            f=ClassFixture();f.plan['class_tables']['classes'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_readonly_section_is_required_and_writable_executable_flags_rejected(self):
        for flags in [0,0x80000000,0xc0000040,0x60000020]:
            f=ClassFixture();f.le(0x5018+0xe0+40+36,flags);f.refresh_class()
            with self.subTest(flags=flags),self.assertRaises(ValueError):f.run()
        f=ClassFixture();f.image[0x5120:0x5128]=b'.other\0\0';f.refresh_class()
        with self.assertRaises(ValueError):f.run()

    def test_pdata_words_are_not_accepted_as_a_readonly_method_table(self):
        f=ClassFixture();f.plan['class_tables']['classes'][0]['table_address']=f.base+0x600
        f.words(f.base+0x1400,initializer_words('base',f.base+0x600,f.plan['class_tables']));f.refresh_class()
        with self.assertRaisesRegex(ValueError,'outside .rdata'):f.run()

    def test_registration_and_getter_require_exact_declared_records(self):
        for offset,value in [(0x61c,0x40001003),(0x618,0x82001b04),(0x620,0x82001704)]:
            f=ClassFixture();f.put(f.base+offset,value);f.refresh_class()
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.run()

    def test_callback_leaf_pdata_absence_is_a_checked_condition(self):
        f=ClassFixture();f.put(f.base+0x618,f.base+0x1400);f.put(f.base+0x61c,0x40001500);f.refresh_class()
        with self.assertRaises(ValueError):f.run()

    def test_readonly_section_cannot_overlap_code_or_pdata(self):
        for start,size in [(0x1000,0x1800),(0x600,40)]:
            f=ClassFixture();f.le(0x5120+8,size);f.le(0x5120+12,start);f.refresh_class()
            with self.subTest(start=start),self.assertRaises(ValueError):f.run()

    def test_class_size_and_suffix_pointer_are_instruction_operands_not_guesses(self):
        f=ClassFixture();f.plan['class_tables']['classes'][0]['size_operand']=0x148;f.refresh_class()
        with self.assertRaisesRegex(ValueError,'argument chain'):f.run()
        f=ClassFixture();f.put(f.base+0x1634+48,0x38cb0000);f.refresh_class()
        with self.assertRaisesRegex(ValueError,'argument chain'):f.run()

    def test_signed_low_halves_reconstruct_addresses_without_unsigned_addi_guess(self):
        for value in [0x821c13c0,0x82331510,0x826a8f00,0xffffffff,0x80000000]:
            hi,lo=halves(value);self.assertEqual(((hi<<16)+lo)&0xffffffff,value)
        self.assertEqual(halves(0x826a8f00),(0x826b,-0x7100))

    def test_opt_in_requires_style_profile_and_old_report_shape_stays_unchanged(self):
        self.assertNotIn('class_tables',StyleFixture().run())
        f=ClassFixture();del f.plan['style_selection']
        with self.assertRaisesRegex(ValueError,'requires explicit style'):f.run()

    def test_cli_synthetic_class_plan_outputs_reopen_and_inputs_stay_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=ClassFixture();im=root/'image.bin';p=root/'plan.json';meta=root/'metadata.json';out=root/'report.json'
            im.write_bytes(f.image);p.write_text(json.dumps(f.plan));meta.write_bytes(f.metadata_raw);paths=[im,p,meta];before=[x.read_bytes() for x in paths]
            args=[str(im),'--sha256',digest(f.image),'--plan',str(p),'--plan-sha256',digest(p.read_bytes()),'--native-report',str(meta),'--output',str(out)]
            self.assertEqual(main(args),0);r=json.loads(out.read_bytes());self.assertFalse(r['class_tables']['executed'])
            self.assertEqual([x.read_bytes() for x in paths],before);self.assertEqual(main(args),2)


if __name__=='__main__':unittest.main()
