"""Self-authored Canvas-like rows and metric words; never execute target code."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

import test_initialized_native_tables as fixtures
from tools.ppc_text_measurement import caller_tail_words,helper_words,leaf_words,verify_measurement
from tools.inspect_initialized_natives import main
from tools.xex_image import digest,VirtualImage


class MeasurementFixture(fixtures.InitializedFixture):
    def __init__(self):
        super().__init__();v=self.base;p=self.plan
        p['code_ranges'].append([v+0x6000,v+0x9000]);t=p['tables'][0];t.update(label='Canvas',engine_class='Canvas',symbol_prefix='intUCanvasexec')
        self.meta['defining_class_scope']='Canvas';self.meta['selected_objects']=['Canvas.TextSize','Canvas.StrLen']
        for group in [self.meta['functions'],self.meta['native_filter']['inventory']]:
            for i,r in enumerate(group):
                name=['TextSize','StrLen','Script'][i];r['owner']['path']='Canvas.'+name;r['defining_class']['path']='Canvas'
        for i,name in enumerate(['TextSize','StrLen']):
            at=0x4000+i*0x100;self.image[at:at+128]=bytes(128);encoded=('intUCanvasexec'+name+'\0').encode('utf-16-be');self.image[at:at+len(encoded)]=encoded
        self.put(v+0x3004,v+0x6000)
        c=dict(profile='ppc-canvas-measurement-v1',canvas_label='Canvas',textsize_method='TextSize',caller_tail_offset=388,
            null_message_address=v+0x4520,null_call=v+0x1400,empty_string_address=v+0x4510,string_cleanup=v+0x1500,
            caller_restore=v+0x1600,helper_start=v+0x6500,leaf_start=v+0x6800,zero_float_address=v+0x4500,
            unit_float_address=v+0x4504,global_pointer_slot=v+0x3300)
        p['measurement_path']=c;self.put(c['unit_float_address'],0x3f800000)
        def words(start,values):
            for i,w in enumerate(values):self.put(start+i*4,w)
        words(v+0x6000,[0x60000000]*135);words(v+0x6000+388,caller_tail_words(v+0x6000+388,c))
        words(c['helper_start'],helper_words(c['helper_start'],c));words(c['leaf_start'],leaf_words(c['leaf_start'],c))
        # Keep the old three records and add exact caller/helper entries, not a
        # fictitious .pdata record for the call-free leaf.
        struct.pack_into('<I',self.image,0x5018+124,40);struct.pack_into('<I',self.image,0x5018+0xe0+8,40)
        for i,(s,n,prologue) in enumerate([(v+0x6000,135,3),(v+0x6500,47,5)],3):
            self.put(v+0x600+i*8,s);self.put(v+0x604+i*8,0x40000000|n<<8|prologue)
        self.refresh_measurement()

    def refresh_measurement(self):
        c=self.plan['measurement_path'];v=self.base
        for name,s,n in [('caller_tail',v+0x6000+388,152),('helper',c['helper_start'],188),('leaf',c['leaf_start'],488)]:
            c[name+'_sha256']=digest(self.image[s-v:s-v+n])
        self.refresh();self.metadata={'Canvas':self.metadata['Demo']}


class MeasurementTests(unittest.TestCase):
    def test_named_caller_helper_and_leaf_windows_preserve_input(self):
        f=MeasurementFixture();before=bytes(f.image);r=f.run()['measurement_path']
        self.assertEqual([x['instruction_count'] for x in r['windows']],[38,47,122]);self.assertEqual(bytes(f.image),before)
        self.assertEqual(r['source_binding']['method'],'TextSize');self.assertIsNone(r['leaf_declared_record'])

    def test_direct_index_word_conditions_and_127_fallback_are_explicit(self):
        r=MeasurementFixture().run()['measurement_path']
        self.assertEqual(r['native_observed_offsets']['mode_word'],0x68)
        self.assertEqual(r['native_observed_offsets']['glyph_stride'],20)
        self.assertEqual(r['zero_mode_path']['out_of_range_or_zero_height_fallback'],127)
        self.assertTrue(r['zero_mode_path']['in_range_height_nonzero_keeps_code_unit'])
        self.assertEqual(r['leaf_parameter_block']['string_code_unit_bytes'],2)

    def test_nonzero_mode_bucket_chain_fields_and_value_width(self):
        r=MeasurementFixture().run()['measurement_path']['nonzero_mode_path']
        self.assertEqual((r['entry_stride'],r['key_u16_offset'],r['value_u16_offset']),(8,4,6))
        self.assertEqual(r['chain_end_word'],-1);self.assertEqual(r['missing_fallback'],127)

    def test_no_serialized_mode_or_runtime_font_is_selected(self):
        r=MeasurementFixture().run()['measurement_path']
        for name in ['caller_entry_object_alias_verified','callee_register_preservation_verified','serialized_native_layout_verified',
                     'source_font_mode_bridge_verified','runtime_font_selection_verified','loop_termination_verified',
                     'native_rendering_path_equivalence_verified','game_rendering_verified','executed','image_modified']:
            self.assertIs(r[name],False)
        self.assertFalse(r['global_float_adjustment']['runtime_pointer_value_verified'])

    def test_independent_literals_and_branch_words(self):
        f=MeasurementFixture();s=f.base+0x6800
        self.assertEqual(struct.unpack_from('>I',f.image,0x6804)[0],0x80e30018)
        self.assertEqual(struct.unpack_from('>I',f.image,0x6854)[0],0x81670068)
        self.assertEqual(struct.unpack_from('>I',f.image,0x68f8)[0],0x3960007f)
        self.assertEqual(struct.unpack_from('>I',f.image,0x69e0)[0],0x409afe74)
        self.assertEqual(f.run()['measurement_path']['windows'][2]['end'],s+488)

    def test_every_selected_code_byte_rejects_refreshed_hash_mutation(self):
        for start,n in [(0x6000+388,152),(0x6500,188),(0x6800,488)]:
            for i in range(n):
                f=MeasurementFixture();f.image[start+i]^=1;f.refresh_measurement()
                with self.subTest(start=start,i=i),self.assertRaisesRegex(ValueError,'measurement .* structural'):f.run()

    def test_window_hashes_are_separate_from_template_guards(self):
        for name in ['caller_tail','helper','leaf']:
            f=MeasurementFixture();f.plan['measurement_path'][name+'_sha256']='0'*64
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'window hash'):f.run()

    def test_zero_unit_and_empty_constants_cannot_silently_change(self):
        for at in [0x4500,0x4504,0x4510]:
            f=MeasurementFixture();f.image[at]^=1;f.refresh_measurement()
            with self.subTest(at=at),self.assertRaises(ValueError):f.run()

    def test_profile_scope_types_and_operand_ranges_fail_closed(self):
        for key,value in [('profile','wrong'),('canvas_label','Other'),('textsize_method','StrLen'),('caller_tail_offset',True),
                          ('helper_start',True),('leaf_start',0x82006801),('null_call',0x82003000),
                          ('global_pointer_slot',0x82004500),('zero_float_address',0x82006500),('extra',0)]:
            f=MeasurementFixture();f.plan['measurement_path'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()
        for value in [None,{},True,[]]:
            f=MeasurementFixture();f.plan['measurement_path']=value
            with self.subTest(value=value),self.assertRaises(ValueError):f.run()

    def test_caller_declared_end_must_match_exact_checked_tail(self):
        f=MeasurementFixture();f.put(f.base+0x61c,0x40008603);f.refresh_measurement()
        with self.assertRaisesRegex(ValueError,'caller tail'):f.run()

    def test_helper_extent_and_prologue_are_metadata_checked(self):
        for packed in [0x40002e05,0x40002f04]:
            f=MeasurementFixture();f.put(f.base+0x624,packed);f.refresh_measurement()
            with self.subTest(packed=packed),self.assertRaisesRegex(ValueError,'helper declared'):f.run()

    def test_leaf_is_not_given_a_fictitious_neighbor_function_extent(self):
        f=MeasurementFixture();struct.pack_into('<I',f.image,0x5018+124,48);struct.pack_into('<I',f.image,0x5018+0xe0+8,48)
        f.put(f.base+0x628,f.base+0x6800);f.put(f.base+0x62c,0x40007a00);f.refresh_measurement()
        with self.assertRaisesRegex(ValueError,'leaf unexpectedly covered'):f.run()

    def test_scope_association_cannot_be_replaced_by_unrelated_binding(self):
        f=MeasurementFixture();r=f.run();r['tables'][0]['engine_class']='Other'
        with self.assertRaisesRegex(ValueError,'Canvas.TextSize'):
            verify_measurement(VirtualImage(bytes(f.image),f.base),f.plan['measurement_path'],r['tables'],f.plan['code_ranges'],f.plan['string_range'],f.plan['data_range'])

    def test_old_initialized_report_shape_is_unchanged_without_opt_in(self):
        f=MeasurementFixture();del f.plan['measurement_path'];self.assertNotIn('measurement_path',f.run())
        self.assertNotIn('measurement_path',fixtures.InitializedFixture().run())

    def test_cli_full_measurement_report_reopened_and_inputs_retained(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=MeasurementFixture();image=root/'image.bin';plan=root/'plan.json';meta=root/'metadata.json';out=root/'report.json'
            image.write_bytes(f.image);plan.write_bytes(json.dumps(f.plan).encode());meta.write_bytes(f.metadata['Canvas']);before=[p.read_bytes() for p in [image,plan,meta]]
            args=[str(image),'--sha256',digest(f.image),'--plan',str(plan),'--plan-sha256',digest(plan.read_bytes()),'--native-report','Canvas',str(meta),'--output',str(out)]
            self.assertEqual(main(args),0);self.assertEqual(len(json.loads(out.read_text())['measurement_path']['windows']),3)
            self.assertEqual(main(args),2);self.assertEqual(before,[p.read_bytes() for p in [image,plan,meta]])


if __name__=='__main__':unittest.main()
