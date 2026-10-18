"""Self-authored virtual PE/CE records/PPC templates. Never execute target words."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.xex_image import VirtualImage,digest
from tools.ppc_native_bindings import inspect_bindings
from tools.ppc_pdata import read_pdata,exact_record
from tools.ppc_style_selection import verify_style_selection,overlay_words,final_words,applied_tail_words
from tools.inspect_native_bindings import main
from test_native_bindings import NativeFixture,D,MR,B


class StyleFixture(NativeFixture):
    def __init__(self):
        super().__init__();v=self.base
        self.plan['code_ranges']=[[v+0x100,v+0x600],[v+0x700,v+0x2000]]
        im=self.image;im[:2]=b'MZ';self.le(0x3c,0x5000);im[0x5000:0x5004]=b'PE\0\0'
        struct.pack_into('<HH',im,0x5004,0x1f2,1);struct.pack_into('<H',im,0x5014,0xe0)
        struct.pack_into('<H',im,0x5018,0x10b);self.le(0x5018+28,v);self.le(0x5018+92,16)
        self.le(0x5018+120,0x600);self.le(0x5018+124,24)
        sec=0x5018+0xe0;im[sec:sec+8]=b'.pdata\0\0';struct.pack_into('<4I',im,sec+8,24,0x600,0x800,0x7777)
        c=dict(profile='ppc-style-overlay-v1',final_method='SetFont',applied_method='DisableCustomFont',
               final_wrapper_tail_offset=0xec,applied_wrapper_tail_offset=0xc0,final_start=v+0x1000,overlay_start=v+0x1200,
               prologue_helper=v+0x1500,producer_helper=v+0x1600,copy_call_target=v+0x1700,
               epilogue_helper=v+0x1800,applied_epilogue=v+0x1900,final_wrapper_epilogue=v+0x1a00)
        self.plan['style_selection']=c;s=c['final_start'];ov=c['overlay_start'];ft=v+0x800+0xec;at=v+0xa00+0xc0
        self.words(ov,overlay_words(ov));self.words(s,final_words(s,c))
        self.words(ft,[MR(4,30),MR(3,28),B(ft+8,s,1),D(36,3,27,0),D(14,1,1,0xf0),B(ft+20,c['final_wrapper_epilogue'])])
        self.words(at,applied_tail_words(at,c['applied_epilogue']))
        for i,(start,end) in enumerate([(v+0x800,ft+24),(v+0xa00,at+44),(s,s+128)]):
            self.put(v+0x600+i*8,start);self.put(v+0x604+i*8,0x40000000|((end-start)//4)<<8|3)
        self.refresh_style()
    def le(self,offset,value):struct.pack_into('<I',self.image,offset,value)
    def refresh_style(self):
        c=self.plan['style_selection'];v=self.base
        for name,s,n in [('overlay',c['overlay_start'],188),('final',c['final_start'],128),
                         ('final_wrapper_tail',v+0x800+c['final_wrapper_tail_offset'],24),
                         ('applied_wrapper_tail',v+0xa00+c['applied_wrapper_tail_offset'],44)]:
            c[name+'_sha256']=digest(self.image[s-v:s-v+n])
        self.refresh()
    def pdata(self):return read_pdata(bytes(self.image),self.base,self.plan['code_ranges'])


class NativeStyleTests(unittest.TestCase):
    def test_optional_plan_preserves_existing_report_shape(self):
        f=NativeFixture();self.assertNotIn('style_selection',f.run())
        f=StyleFixture();before=bytes(f.image);r=f.run()['style_selection']
        self.assertEqual(bytes(f.image),before);self.assertFalse(r['executed']);self.assertFalse(r['image_modified'])
        self.assertEqual(r['virtual_slot_byte_offset'],0x128);self.assertEqual(r['copy_call_size_operand'],100)
        for key in ['producer_semantics_verified','copy_semantics_verified','virtual_target_verified','active_font_verified']:
            self.assertIs(r[key],False)

    def test_two_font_guards_and_unique_disjoint_output_store(self):
        f=StyleFixture();r=f.run()['style_selection']['font_overlay']
        self.assertEqual(r['required_conditions'],['flag bit nonzero','pointer word nonzero'])
        self.assertEqual((r['flag_word_offset'],r['pointer_word_offset'],r['output_word_offset']),(0xe4,0xd8,0x20))
        self.assertEqual(r['flag_mask'],'20000000');self.assertTrue(r['bypass_preserves_output_word'])
        # Independent encoding check: BEQ CR6 bypasses the single +0x20 store.
        words=struct.unpack('>47I',f.image[0x1200:0x12bc]);self.assertEqual(words[23],0x419a0014)
        self.assertEqual(words[26],0x419a0008);self.assertEqual(words[27],0x91640020)
        stores=[w&65535 for w in words if w>>26 in (36,38,52)]
        self.assertEqual(stores.count(0x20),1);self.assertEqual(stores,[0,4,8,12,12,32,56,60,61])

    def test_every_template_byte_mutation_rejected_even_after_refreshing_hash(self):
        for start,size in [(0x1200,188),(0x1000,128),(0x8ec,24),(0xac0,44)]:
            for i in range(size):
                f=StyleFixture();f.image[start+i]^=1;f.refresh_style()
                with self.subTest(start=start,i=i),self.assertRaises(ValueError):f.run()

    def test_window_hashes_checked_before_structural_acceptance(self):
        for name in ['overlay','final','final_wrapper_tail','applied_wrapper_tail']:
            f=StyleFixture();f.plan['style_selection'][name+'_sha256']='0'*64
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'hash'):f.run()

    def test_helper_addresses_offsets_and_profile_are_bounded(self):
        for key,value in [('profile','unknown'),('overlay_start',True),('copy_call_target',0x82002000),
                          ('final_wrapper_epilogue',0x82003000),('applied_wrapper_tail_offset',4097)]:
            f=StyleFixture();f.plan['style_selection'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_pdata_end_not_next_start_and_missing_leaf_remains_absent(self):
        f=StyleFixture();t=f.pdata();first=t['records'][0];second=t['records'][1]
        self.assertLess(first['end'],second['start']);self.assertEqual(first['length_words'],65)
        self.assertEqual(first['prologue_end'],first['start']+12)
        self.assertIsNone(exact_record(t,f.base+0x1200));self.assertIsNone(exact_record(t,first['end']))
        with self.assertRaises(ValueError):exact_record(t,True)
        self.assertEqual(f.run()['style_selection']['overlay_pdata_record'],None)

    def test_all_raw_flag_pairs_retained_without_unwinder_semantics(self):
        for pair in range(4):
            f=StyleFixture();packed=f.pdata()['records'][0]['packed_word'];f.put(f.base+0x604,(int(packed,16)&0x3fffffff)|(pair<<30))
            t=f.pdata();r=t['records'][0];self.assertEqual(r['thirty_two_bit'],pair&1);self.assertEqual(r['exception_flag'],pair>>1)
            self.assertFalse(t['flag_semantics_verified']);self.assertFalse(t['unwinding_performed'])

    def test_directory_section_identity_count_alignment_and_bounds(self):
        for offset,value in [(0x5018+92,3),(0x5018+92,17),(0x5018+120,0x604),(0x5018+124,23),
                             (0x5018+124,0),(0x5018+124,1048584),(0x5018+0xe0+8,32)]:
            f=StyleFixture();f.le(offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.pdata()
        f=StyleFixture();struct.pack_into('<H',f.image,0x5014,96)
        with self.assertRaises(ValueError):f.pdata()

    def test_record_zero_length_prologue_order_overlap_and_code_bounds(self):
        for offset,value in [(0x604,0x40000000),(0x604,0x40000102),(0x608,0x82000800),
                             (0x608,0x82000804),(0x600,0x82000801),(0x600,0x82003000),(0x604,0x403fffff)]:
            f=StyleFixture();f.put(f.base+offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.pdata()

    def test_pdata_raw_pointer_is_not_used_and_code_ranges_cannot_overlap_table(self):
        f=StyleFixture();f.le(0x5018+0xe0+20,0xffffffff);self.assertEqual(f.pdata()['record_count'],3)
        for ranges in [[[f.base+0x100,f.base+0x2000]],[[f.base+0x801,f.base+0x2000]],[]]:
            with self.subTest(ranges=ranges),self.assertRaises(ValueError):read_pdata(bytes(f.image),f.base,ranges)

    def test_declared_end_mismatch_and_overlay_coverage_rejected(self):
        f=StyleFixture();f.put(f.base+0x614,0x40002103);f.refresh_style()
        with self.assertRaisesRegex(ValueError,'declared pdata end'):f.run()
        f=StyleFixture();f.put(f.base+0x600,f.base+0x1200);f.put(f.base+0x604,0x40002f00)
        f.put(f.base+0x608,f.base+0x1300);f.put(f.base+0x610,f.base+0x1400);f.refresh_style()
        with self.assertRaises(ValueError):f.run()

    def test_cli_extended_plan_reopens_report_and_never_changes_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=StyleFixture();im=root/'image.bin';p=root/'plan.json';m=root/'meta.json';out=root/'report.json'
            im.write_bytes(f.image);p.write_text(json.dumps(f.plan));m.write_bytes(f.metadata_raw)
            args=[str(im),'--sha256',digest(f.image),'--plan',str(p),'--plan-sha256',digest(p.read_bytes()),'--native-report',str(m),'--output',str(out)]
            before=[x.read_bytes() for x in [im,p,m]];self.assertEqual(main(args),0)
            r=json.loads(out.read_bytes());self.assertFalse(r['style_selection']['executed'])
            self.assertEqual([x.read_bytes() for x in [im,p,m]],before)
            self.assertEqual(main(args),2)

    def test_pdata_physical_truncation_and_invalid_machine_are_rejected(self):
        f=StyleFixture()
        for n in [0,1,64,0x618,0x5018,0x511f]:
            with self.subTest(n=n),self.assertRaises(ValueError):read_pdata(bytes(f.image[:n]),f.base,f.plan['code_ranges'])
        struct.pack_into('<H',f.image,0x5004,0x14c)
        with self.assertRaises(ValueError):f.pdata()

    def test_output_records_exact_bound_native_extents_not_inferred_gaps(self):
        f=StyleFixture();r=f.run()['style_selection'];extents=r['declared_native_extents']
        self.assertEqual(set(extents),{'SetFont','DisableCustomFont'})
        self.assertEqual(extents['SetFont']['end'],f.base+0x904)
        edges=r['font_overlay']['guard_edges']
        self.assertEqual([e['taken'] for e in edges],[f.base+0x1270]*2)
        self.assertEqual(edges[1]['fallthrough'],r['font_overlay']['store_instruction'])

    def test_narrow_static_model_has_no_constructor_or_font_instance_claim(self):
        r=StyleFixture().run()['style_selection']
        self.assertIsNone(r['overlay_pdata_record'])
        self.assertFalse(r['constructor_values_verified']);self.assertFalse(r['complete_native_struct_layout_verified'])
        self.assertFalse(r['pdata_summary']['complete_code_coverage_verified'])
        self.assertFalse(r['callee_register_preservation_verified'])


if __name__=='__main__':unittest.main()
