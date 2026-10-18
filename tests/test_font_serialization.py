"""Self-authored PE/function/registration fixtures; never execute PPC words."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_native_class_tables import ClassFixture
from tools.ppc_class_tables import registration_words,font_initializer_words
from tools.ppc_font_serialization import templates,inspect_serialization
from tools.inspect_font_serialization import main
from tools.xex_image import digest


class SerializationFixture(ClassFixture):
    def __init__(self):
        super().__init__();v=self.base
        c={k:v+offset for k,offset in dict(font=0x6000,multifont=0x6200,glyph_array=0x6400,map_array=0x6600,
            glyph_record=0x6800,map_record=0x6a00,save29=0x1800,restore29=0x1810,parent=0x1820,texture_array=0x1830,
            rehash=0x1840,free=0x1850,float_array=0x1860,save27=0x1870,restore27=0x1880,resize=0x1890,append=0x18a0).items()}
        p=dict(schema_version=1,profile='ppc-font-serialization-v1',image_base=v,code_ranges=[[v+0x800,v+0x2000],[v+0x6000,v+0x9000]],
            readonly_range=[v+0x2000,v+0x2800],calls=c,registration=dict(common_name_address=v+0x2240,shared_callback=v+0x1900,registration_helper=v+0x1910),classes=[],windows={})
        records=[]
        for name,words in templates(c).items():
            self.words(c[name],words);pro=5 if name in ('multifont','glyph_record','map_record') else 3
            p['windows'][name]=dict(prologue_words=pro);records.append((c[name],len(words),pro))
        self.put(v+0x21fc,0x12345678)  # UFont follows non-string bytes, not NUL.
        for i,family in enumerate(['Font','MultiFont']):
            address=v+0x2200+i*0x20;reg=v+0x1000+i*0x200;cb=v+0x1400+i*0x100;table=v+0x2300+i*0x200
            row=dict(name='U'+family,name_address=address,registration_start=reg,callback=cb,table=table)
            encoded=(row['name']+'\0').encode('utf-16-be');self.image[address-v:address-v+len(encoded)]=encoded
            self.words(reg+52,registration_words(reg+52,address,cb,0x70 if i==0 else 0x7c,p['registration']))
            self.words(cb,font_initializer_words(family,table));self.words(table,[v+0x800]*(70+i));self.put(table+0x34,c['font' if i==0 else 'multifont'])
            records.append((reg,70,5));p['classes'].append(row)
        self.le(0x5018+124,len(records)*8);self.le(0x5018+0xe0+8,len(records)*8)
        for i,(start,n,pro) in enumerate(sorted(records)):
            self.put(v+0x600+i*8,start);self.put(v+0x604+i*8,0x40000000|n<<8|pro)
        self.plan=p;self.refresh_serialization()

    def refresh_serialization(self):
        v=self.base;p=self.plan;sha=lambda start,n:digest(self.image[start-v:start-v+n])
        for name,words in templates(p['calls']).items():p['windows'][name]['sha256']=sha(p['calls'][name],len(words)*4)
        for i,row in enumerate(p['classes']):
            row['registration_sha256']=sha(row['registration_start']+52,64)
            row['callback_sha256']=sha(row['callback'],52);row['table_sha256']=sha(row['table'],(70+i)*4)
        p['image_sha256']=digest(self.image)

    def run(self):return inspect_serialization(bytes(self.image),self.plan)


class FontSerializationTests(unittest.TestCase):
    def test_full_six_windows_and_input_immutability(self):
        f=SerializationFixture();before=bytes(f.image);r=f.run()
        self.assertEqual([w['instruction_count'] for w in r['windows']],[58,17,81,75,47,27]);self.assertEqual(bytes(f.image),before)

    def test_operand_anchored_full_name_has_no_previous_nul_requirement(self):
        f=SerializationFixture();r=f.run()['classes'][0]
        self.assertEqual(r['native_name'],'UFont');self.assertEqual(r['passed_name_address'],r['literal_address']+2)
        self.assertFalse(r['literal_preceding_nul_required']);self.assertEqual(f.image[0x21fe:0x2200],b'\x56\x78')

    def test_callback_does_not_initialize_mode_or_spacing(self):
        for row in SerializationFixture().run()['classes']:
            self.assertEqual(row['callback_map_zero_offsets'],[0x54,0x58,0x5c,0x60]);self.assertEqual(row['callback_bucket_count'],8)
            self.assertFalse(row['callback_initializes_mode_or_spacing']);self.assertFalse(row['complete_table_extent_verified'])

    def test_serialized_record_sizes_are_not_runtime_strides(self):
        r=SerializationFixture().run();g=r['glyph_record'];m=r['map_record']
        self.assertEqual((g['serialized_bytes'],g['native_stride']),(17,20));self.assertEqual(g['transfer_sizes'],[4,4,4,4,1])
        self.assertEqual((m['serialized_bytes'],m['native_stride']),(4,8));self.assertEqual(m['transferred_offsets'],[4,6]);self.assertFalse(m['next_link_serialized'])

    def test_word_order_and_offsets(self):
        r=SerializationFixture().run();o=r['native_entry_offsets']
        self.assertEqual((o['spacing_word'],o['mode_word']),(0x6c,0x68))
        self.assertEqual(r['transfer_order'],['glyph_array','texture_array','spacing_word','map_array','mode_word'])

    def test_archive_and_runtime_claims_remain_false(self):
        r=SerializationFixture().run()
        for name in ['archive_virtual_call_semantics_verified','callee_register_preservation_verified','serialized_field_identity_verified',
            'runtime_font_selection_verified','game_rendering_verified','executed','image_modified']:self.assertIs(r[name],False)

    def test_every_function_byte_rejects_even_with_refreshed_hash(self):
        for name,words in templates(SerializationFixture().plan['calls']).items():
            for i in range(len(words)*4):
                f=SerializationFixture();f.image[f.plan['calls'][name]-f.base+i]^=1;f.refresh_serialization()
                with self.subTest(name=name,i=i),self.assertRaisesRegex(ValueError,'structural mismatch'):f.run()

    def test_every_registration_and_callback_byte_rejects_refreshed_hash(self):
        for cls in range(2):
            for key,n,offset in [('registration_start',64,52),('callback',52,0)]:
                for i in range(n):
                    f=SerializationFixture();f.image[f.plan['classes'][cls][key]-f.base+offset+i]^=1;f.refresh_serialization()
                    with self.subTest(cls=cls,key=key,i=i),self.assertRaisesRegex(ValueError,'structural mismatch'):f.run()

    def test_independent_instruction_anchors(self):
        f=SerializationFixture()
        for offset,word in [(0x6038,0x389e006c),(0x60cc,0x389e0068),(0x6818,0x38a00004),(0x688c,0x38a00001),(0x6a20,0x38840004)]:
            self.assertEqual(struct.unpack_from('>I',f.image,offset)[0],word)

    def test_class_literal_and_slot_mismatch(self):
        for key in ['literal','slot']:
            f=SerializationFixture();f.put(f.base+(0x2200 if key=='literal' else 0x2334),0);f.refresh_serialization()
            with self.assertRaisesRegex(ValueError,'literal mismatch|slot34 mismatch'):f.run()

    def test_pdata_extent_and_prologue_mismatch(self):
        for value in [0x40003903,0x40003a04]:
            f=SerializationFixture();f.put(f.base+0x614,value);f.refresh_serialization()
            with self.assertRaisesRegex(ValueError,'pdata'):f.run()

    def test_hashes_do_not_replace_structural_checks(self):
        f=SerializationFixture();f.plan['windows']['font']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'window hash'):f.run()
        f=SerializationFixture();f.plan['image_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'image SHA256'):f.run()

    def test_scope_alignment_and_helper_fields(self):
        changes=[lambda p:p['classes'].reverse(),lambda p:p['calls'].update(parent=0),lambda p:p['calls'].update(parent=1),
            lambda p:p['calls'].update(extra=1),lambda p:p['windows'].pop('font'),lambda p:p['readonly_range'].__setitem__(0,p['image_base'])]
        for change in changes:
            f=SerializationFixture();change(f.plan)
            with self.assertRaises(ValueError):f.run()

    def test_cli_reopens_deterministic_report_and_rejects_overwrite(self):
        f=SerializationFixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);im=root/'image';p=root/'plan';out=root/'report';im.write_bytes(f.image);raw=json.dumps(f.plan).encode();p.write_bytes(raw)
            args=[str(im),'--sha256',digest(f.image),'--plan',str(p),'--plan-sha256',digest(raw),'--output',str(out)]
            self.assertEqual(main(args),0);before=out.read_bytes();self.assertEqual(main(args),2);self.assertEqual(out.read_bytes(),before)
            out.unlink();self.assertEqual(main(args),0);self.assertEqual(out.read_bytes(),before)

    def test_cli_source_lock_rejects_no_output(self):
        f=SerializationFixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);im=root/'image';p=root/'plan';out=root/'report';im.write_bytes(f.image);raw=json.dumps(f.plan).encode();p.write_bytes(raw)
            args=[str(im),'--sha256','0'*64,'--plan',str(p),'--plan-sha256',digest(raw),'--output',str(out)]
            self.assertEqual(main(args),2);self.assertFalse(out.exists())

    def test_cli_input_change_before_writing_leaves_no_report(self):
        f=SerializationFixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);im=root/'image';p=root/'plan';out=root/'report';im.write_bytes(f.image);raw=json.dumps(f.plan).encode();p.write_bytes(raw)
            args=[str(im),'--sha256',digest(f.image),'--plan',str(p),'--plan-sha256',digest(raw),'--output',str(out)]
            def changed(image,plan):
                result=inspect_serialization(image,plan);im.write_bytes(b'changed');return result
            with patch('tools.inspect_font_serialization.inspect_serialization',side_effect=changed):self.assertEqual(main(args),2)
            self.assertFalse(out.exists())

    def test_cli_input_change_after_writing_removes_only_owned_report(self):
        f=SerializationFixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);im=root/'image';p=root/'plan';out=root/'report';im.write_bytes(f.image);raw=json.dumps(f.plan).encode();p.write_bytes(raw)
            args=[str(im),'--sha256',digest(f.image),'--plan',str(p),'--plan-sha256',digest(raw),'--output',str(out)]
            read=Path.read_bytes
            def changed(path):
                result=read(path)
                if path==out:im.write_bytes(b'changed')
                return result
            with patch.object(Path,'read_bytes',changed):self.assertEqual(main(args),2)
            self.assertFalse(out.exists())

    def test_malformed_readonly_and_unknown_plan_fields_reject(self):
        for value in [[],[0],['bad',1],[1,1]]:
            f=SerializationFixture();f.plan['readonly_range']=value
            with self.assertRaisesRegex(ValueError,'readonly range malformed'):f.run()
        f=SerializationFixture();f.plan['extra']=False
        with self.assertRaisesRegex(ValueError,'plan fields'):f.run()


if __name__=='__main__':unittest.main()
