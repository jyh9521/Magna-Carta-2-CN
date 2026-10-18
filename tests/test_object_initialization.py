"""Self-authored metadata/callback words plus arithmetic zero-fill geometry."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from test_native_class_tables import ClassFixture
from tools.ppc_class_tables import registration_words
from tools.ppc_object_initialization import (metadata_base_words,metadata_constructor_words,saved_register_words,
                                           restored_register_words,zero_fill_words,zero_fill_partition,wrapper_windows)
from tools.ppc_native_bindings import d,mr,branch
from tools.xex_image import MAX_IMAGE,digest
from tools.inspect_native_bindings import main


class InitializationFixture(ClassFixture):
    def __init__(self):
        super().__init__();v=self.base;c=dict(profile='ppc-object-initialization-v1',metadata_base_start=v+0x6000,metadata_constructor_start=v+0x6200,
            save_start=v+0x6600,restore_start=v+0x6680,zero_fill_start=v+0x6800,size_getter_start=v+0x6900,wrapper_start=v+0x6a00,
            allocation_start=v+0x7000,fallback_class_helper=v+0x8000,registry_flag_address=v+0x3100,registry_head_address=v+0x3104,
            base_initial_table=v+0x2700,base_final_table=v+0x2710,metadata_table=v+0x2500,
            post_callback_helpers=[v+0x8100,v+0x8200],post_allocation_helpers=[v+0x8300,v+0x8400,v+0x8500],wrapper_cleanup_helpers=[v+0x8600,v+0x8700])
        self.plan['object_initialization']=c;self.plan['code_ranges'].append([v+0x6000,v+0xa000])
        self.plan['class_tables']['registration_helper']=c['metadata_constructor_start'];row=self.plan['class_tables']['classes'][0]
        s=row['registration_start']+52;self.words(s,registration_words(s,row['name_address'],row['callback_start'],row['size_operand'],self.plan['class_tables']))
        struct.pack_into('<I',self.image,0x5018+124,72);struct.pack_into('<I',self.image,0x5018+0xe0+8,72)
        for i,(s,n,prolog) in enumerate([(v+0x6000,57,1),(v+0x6200,77,3),(v+0x6a00,149,3),(v+0x7000,739,4)],5):
            self.put(v+0x600+i*8,s);self.put(v+0x604+i*8,0x40000000|n<<8|prolog)
        self.words(c['wrapper_start'],[0x60000000]*149);self.words(c['allocation_start'],[0x60000000]*739)
        for start,words in [(c['save_start'],saved_register_words()),(c['restore_start'],restored_register_words()),
                            (c['metadata_base_start'],metadata_base_words(c['metadata_base_start'],c)),
                            (c['metadata_constructor_start'],metadata_constructor_words(c['metadata_constructor_start'],c)),
                            (c['zero_fill_start'],zero_fill_words(c['zero_fill_start'])),(c['size_getter_start'],[d(32,3,3,0x50),0x4e800020])]:self.words(start,words)
        for _,start,words in wrapper_windows(c['wrapper_start'],c):self.words(start,words)
        a=c['allocation_start']+0x97c;self.words(a,[d(32,11,24,0),mr(3,24),d(32,10,11,0x120),0x7d4903a6,0x4e800421,mr(5,3),d(14,4,0,0),mr(3,30),branch(a+32,c['zero_fill_start'],True)])
        for i,off in enumerate([0xaf0,0xb00,0xb0c]):self.put(c['allocation_start']+off,branch(c['allocation_start']+off,c['post_allocation_helpers'][i],True))
        self.words(c['metadata_table'],[v+0x6000]*73);self.put(c['metadata_table']+0x120,c['size_getter_start']);self.refresh_initialization()
    def windows(self):
        c=self.plan['object_initialization'];out=[('save_helpers',c['save_start'],20),('restore_helpers',c['restore_start'],21),('metadata_base',c['metadata_base_start'],57),
            ('metadata_constructor',c['metadata_constructor_start'],77),('zero_fill',c['zero_fill_start'],40),('size_getter',c['size_getter_start'],2)]
        out += [(name,s,len(words)) for name,s,words in wrapper_windows(c['wrapper_start'],c)]
        out += [('allocation_clear',c['allocation_start']+0x97c,9)]+[('post_allocation_'+str(i),c['allocation_start']+off,1) for i,off in enumerate([0xaf0,0xb00,0xb0c])]
        return out
    def refresh_initialization(self):
        c=self.plan['object_initialization'];v=self.base
        for name,s,n in self.windows():c[name+'_sha256']=digest(self.image[s-v:s-v+n*4])
        for name,key,n in [('metadata_base','metadata_base_start',57),('metadata_constructor','metadata_constructor_start',77),('wrapper','wrapper_start',149),('allocation','allocation_start',739)]:
            s=c[key];c[name+'_function_sha256']=digest(self.image[s-v:s-v+n*4])
        c['metadata_table_sha256']=digest(self.image[c['metadata_table']-v:c['metadata_table']-v+73*4]);self.refresh_class()


class ObjectInitializationTests(unittest.TestCase):
    def test_complete_scoped_metadata_size_callback_storage_chain_is_read_only(self):
        f=InitializationFixture();before=bytes(f.image);r=f.run()['object_initialization'];m=r['metadata_chain']
        self.assertEqual((m['size_word_offset'],m['callback_word_offset'],m['size_virtual_slot']),(0x50,0x11c,0x120))
        self.assertTrue(m['argument_preservation_inside_checked_helpers_verified']);self.assertTrue(m['metadata_constructor_returns_entry_r3'])
        self.assertEqual(bytes(f.image),before);self.assertFalse(r['executed']);self.assertFalse(r['image_modified'])

    def test_callback_zero_allocation_skips_site_without_inventing_class_null_guard(self):
        f=InitializationFixture();r=f.run()['object_initialization']['callback_dispatch']
        self.assertTrue(r['allocation_zero_result_skips_selected_callback_site']);self.assertFalse(r['class_pointer_null_handling_verified'])
        self.assertEqual(r['allocation_zero_branch_target'],f.base+0x6c28);self.assertEqual(r['call_instruction'],f.base+0x6b58)
        self.assertFalse(r['allocation_callee_register_preservation_verified']);self.assertFalse(r['runtime_reachability_verified'])

    def test_clear_is_an_intermediate_phase_not_effective_font_state(self):
        f=InitializationFixture();r=f.run()['object_initialization'];phase=r['clear_phase']
        self.assertEqual(phase['fill_value_operand'],0);self.assertEqual(phase['destination_register'],'r30')
        self.assertTrue(phase['zero_after_clear_if_preconditions_hold']);self.assertFalse(phase['zero_at_callback_entry_verified'])
        self.assertFalse(phase['zero_at_rendering_verified']);self.assertFalse(phase['complete_allocation_control_flow_verified'])
        self.assertEqual(len(phase['post_allocation_call_targets']),3);self.assertEqual(len(phase['post_callback_call_targets']),2)
        self.assertFalse(r['active_font_verified']);self.assertFalse(r['constructor_effective_values_verified'])

    def test_partition_exhaustive_small_lengths_and_all_alignments(self):
        for n in range(1025):
            for align in range(4):
                start=0x1000+align;r=zero_fill_partition(start,n);expected_prefix=0
                while expected_prefix<n and (start+expected_prefix)%4:expected_prefix+=1
                self.assertEqual(r['prefix_bytes'],expected_prefix)
                spans=r['intervals'];self.assertEqual(spans[0]['start'],start);self.assertEqual(spans[-1]['end'],start+n)
                self.assertTrue(all(a['end']==b['start'] for a,b in zip(spans,spans[1:])))
                self.assertEqual(sum(s['end']-s['start'] for s in spans),n)
                self.assertEqual(r['blocks16']*16+r['words4']*4+r['tail_bytes']+r['prefix_bytes'],n)

    def test_zero_lengths_alignment_prefix_word_bulk_and_tail_canaries(self):
        for start,n in [(0x1001,0),(0x1001,2),(0x1001,3),(0x1001,4),(0x1003,20),(0x1000,0x110),(0x1002,0x148)]:
            r=zero_fill_partition(start,n);written=set()
            for span in r['intervals']:
                self.assertFalse(written.intersection(range(span['start'],span['end'])));written.update(range(span['start'],span['end']))
            self.assertEqual(written,set(range(start,start+n)));self.assertNotIn(start-1,written);self.assertNotIn(start+n,written)

    def test_partition_large_limits_and_nonwrapping_empty_end(self):
        for start,n in [(0,MAX_IMAGE),(0xffffffff,0),(0xfffffff0,16),(0x82000000,MAX_IMAGE)]:
            r=zero_fill_partition(start,n);self.assertEqual(r['end'],start+n);self.assertTrue(r['arithmetic_only']);self.assertFalse(r['target_executed'])
        for start,n in [(True,1),(0,True),(-1,1),(0,-1),(0,MAX_IMAGE+1),(0xffffffff,2),(0x100000000,0)]:
            with self.subTest(start=start,n=n),self.assertRaises(ValueError):zero_fill_partition(start,n)

    def test_component_font_ranges_are_in_size_but_runtime_values_remain_unproved(self):
        r=InitializationFixture().run()['object_initialization'];case=r['class_size_geometry_cases'][0]
        self.assertEqual(case['constructed_metadata_size_operand'],0x110);self.assertTrue(case['pointer_range_within_size']);self.assertTrue(case['flag_range_within_size'])
        self.assertEqual(len(case['synthetic_alignment_geometries']),4);self.assertFalse(r['constructor_effective_values_verified'])

    def test_every_structural_window_byte_fails_even_with_refreshed_hashes(self):
        f=InitializationFixture()
        for _,s,n in f.windows():
            for i in range(n*4):
                g=InitializationFixture();g.image[s-g.base+i]^=1;g.refresh_initialization()
                with self.subTest(address=s+i),self.assertRaises(ValueError):g.run()

    def test_full_function_hashes_guard_uninterpreted_allocation_and_wrapper_regions(self):
        for key,offset in [('allocation_start',0x100),('wrapper_start',0x60)]:
            f=InitializationFixture();c=f.plan['object_initialization'];f.image[c[key]-f.base+offset]^=1;f.refresh_class()
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'hash'):f.run()

    def test_trusted_relock_does_not_pretend_uninterpreted_regions_were_parsed(self):
        f=InitializationFixture();f.image[0x7100]^=1;f.refresh_initialization();r=f.run()['object_initialization']
        self.assertFalse(r['declared_functions']['allocation']['all_words_structurally_checked'])
        self.assertFalse(r['declared_functions']['wrapper']['all_words_structurally_checked'])
        self.assertTrue(r['declared_functions']['metadata_base']['all_words_structurally_checked'])
        self.assertFalse(r['clear_phase']['complete_allocation_control_flow_verified'])

    def test_pdata_function_extent_and_missing_entry_guards(self):
        for offset,value in [(0x634,0x40003801),(0x638,0x82006204),(0x644,0x40009403),(0x62c,0x40003801)]:
            f=InitializationFixture();f.put(f.base+offset,value);f.refresh_initialization()
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.run()

    def test_metadata_table_size_getter_slot_and_code_word_bounds(self):
        for off,value in [(0,0),(4,0x82000600),(8,0x82006001),(0x120,0x82006000)]:
            f=InitializationFixture();f.put(f.base+0x2500+off,value);f.refresh_initialization()
            with self.subTest(off=off),self.assertRaises(ValueError):f.run()
        f=InitializationFixture();f.plan['object_initialization']['metadata_table_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash'):f.run()

    def test_metadata_helper_must_be_the_one_in_name_registration_chain(self):
        f=InitializationFixture();f.plan['object_initialization']['metadata_constructor_start']=f.base+0x6210
        with self.assertRaisesRegex(ValueError,'does not match class registration'):f.run()

    def test_object_global_table_helper_and_phase_array_guards_fail_closed(self):
        for key,value in [('profile','unknown'),('zero_fill_start',True),('save_start',0x82003000),('registry_flag_address',0x82002000),
                          ('base_initial_table',0x82003100),('post_callback_helpers',[]),('post_allocation_helpers',[1,2,3]),('wrapper_cleanup_helpers',[True,False])]:
            f=InitializationFixture();f.plan['object_initialization'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_branch_prediction_bits_and_ctr_prefix_are_part_of_exact_contract(self):
        words=zero_fill_words(0x1000);self.assertEqual(len(words),40)
        self.assertEqual(words[0],0x38050001);self.assertEqual(words[8],0x4002fff0)
        self.assertEqual(words[19],0x4320ffec);self.assertEqual(words[33],0x4de20020)
        self.assertEqual(words[-1],0x4e800020)

    def test_metadata_callback_alias_and_size_store_have_independent_encodings(self):
        f=InitializationFixture();self.assertEqual(struct.unpack_from('>I',f.image,0x6000+33*4)[0],0x90830050)
        self.assertEqual(struct.unpack_from('>I',f.image,0x6200+8*4)[0],0x7d3c4b78)
        self.assertEqual(struct.unpack_from('>I',f.image,0x6200+51*4)[0],0x9383011c)

    def test_store_sites_tie_geometry_to_checked_zero_template_without_memory_access(self):
        f=InitializationFixture();phase=f.run()['object_initialization']['clear_phase'];z=f.plan['object_initialization']['zero_fill_start']
        self.assertEqual(phase['store_sites']['prefix'],[z+20]);self.assertEqual(phase['store_sites']['blocks16'],[z+56,z+60,z+64,z+68])
        self.assertEqual(phase['store_sites']['tail'],[z+136,z+144,z+152]);self.assertFalse(phase['runtime_memory_writability_verified'])
        self.assertFalse(phase['address_translation_verified']);self.assertIn('CTR starts size+1',phase['prefix_count_rule'])

    def test_metadata_zeros_do_not_become_component_font_default_evidence(self):
        f=InitializationFixture();words=metadata_constructor_words(f.base+0x6200,f.plan['object_initialization'])
        self.assertIn(0x916300d8,words);self.assertIn(0x916300e4,words)
        r=f.run();self.assertFalse(r['class_tables']['classes'][0]['font_pointer_flag_written_by_leaf'])
        self.assertFalse(r['object_initialization']['constructor_effective_values_verified'])

    def test_optional_profile_does_not_change_legacy_report_shape(self):
        self.assertNotIn('object_initialization',ClassFixture().run())
        f=InitializationFixture();del f.plan['class_tables']
        with self.assertRaisesRegex(ValueError,'requires explicit class table'):f.run()

    def test_cli_self_authored_pipeline_report_reopening_and_immutable_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=InitializationFixture();im=root/'image.bin';p=root/'plan.json';m=root/'metadata.json';out=root/'out.json'
            im.write_bytes(f.image);p.write_text(json.dumps(f.plan));m.write_bytes(f.metadata_raw);before=[x.read_bytes() for x in [im,p,m]]
            args=[str(im),'--sha256',digest(f.image),'--plan',str(p),'--plan-sha256',digest(p.read_bytes()),'--native-report',str(m),'--output',str(out)]
            self.assertEqual(main(args),0);r=json.loads(out.read_bytes());self.assertFalse(r['object_initialization']['executed'])
            self.assertEqual([x.read_bytes() for x in [im,p,m]],before);self.assertEqual(main(args),2)


if __name__=='__main__':unittest.main()
