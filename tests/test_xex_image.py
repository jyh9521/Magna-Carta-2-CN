"""Self-authored XEX/PE structures and injected cipher contract; no game data."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools.xex_image import MAX_IMAGE,FormatError,digest,parse_xex,decode_image,inspect_pe,crypto_backend
from tools.extract_xex_image import main
from tools.check_repository import executable_signature,violations


def put(data,offset,value,fmt='>I'):struct.pack_into(fmt,data,offset,value)


class XexFixture:
    def __init__(self,encrypted=False,basic=True):
        self.image=bytearray(65536);im=self.image;im[:2]=b'MZ';put(im,0x3c,0x80,'<I');im[0x80:0x84]=b'PE\0\0'
        put(im,0x84,0x1f2,'<H');put(im,0x86,1,'<H');put(im,0x94,0xe0,'<H')
        opt=0x98;put(im,opt,0x10b,'<H');put(im,opt+16,0x400,'<I');put(im,opt+28,0x82000000,'<I');put(im,opt+56,0x20000,'<I')
        section=opt+0xe0;im[section:section+8]=b'.text\0\0\0';struct.pack_into('<4I',im,section+8,0x100,0x400,0x100,0x400);put(im,section+36,0x60000020,'<I')
        im[0x400:0x500]=b'PPC!'*64;im[0xc000:0xc080]=b'fixture!'*16
        header=bytearray(0x1000);header[:4]=b'XEX2';put(header,4,1);put(header,8,0x1000);put(header,16,0x100);put(header,20,4)
        for i,(key,value) in enumerate([(0x3ff,0x400),(0x10201,0x82000000),(0x10100,0x82000400),(0x40006,0x480)]):struct.pack_into('>II',header,24+i*8,key,value)
        put(header,0x100,0x19c);put(header,0x104,len(im));put(header,0x210,0x82000000);header[0x250:0x260]=bytes([0x11])*16
        put(header,0x280,1);put(header,0x284,0x13)
        struct.pack_into('>IHH',header,0x400,24 if basic else 8,int(encrypted),int(basic))
        if basic:struct.pack_into('>4I',header,0x408,0x8000,0x4000,0x4000,0)
        struct.pack_into('>4I4BI',header,0x480,123,1,1,456,0,0,1,2,0)
        self.raw=header+(im[:0x8000]+im[0xc000:] if basic else im)
    def decode(self,**kw):return decode_image(bytes(self.raw),digest(self.raw),**kw)
    def parse(self):return parse_xex(bytes(self.raw),digest(self.raw))


class ContractCipher:
    """Identity test double, explicitly NOT a cryptographic implementation."""
    def __init__(self):self.calls=[]
    def decrypt(self,key,data):self.calls.append(('decrypt',key,len(data)));return data
    def encrypt(self,key,data):self.calls.append(('encrypt',key,len(data)));return data


class XexImageTests(unittest.TestCase):
    def test_plain_basic_full_image_and_inverse_source_bytes(self):
        f=XexFixture();image,restored,r=f.decode()
        self.assertEqual(image,f.image);self.assertEqual(restored,f.raw);self.assertTrue(r['roundtrip_verified'])
        self.assertEqual(r['image_sha256'],digest(f.image));self.assertFalse(r['executed'])
        self.assertEqual(r['execution_id']['disc'],1);self.assertEqual(r['execution_id']['disc_count'],2)
        self.assertFalse(r['rsa_signature_verified']);self.assertFalse(r['stored_page_digests_verified'])
        self.assertEqual(r['page_ranges'],[dict(offset=0,size=65536,kind=3)])

    def test_plain_uncompressed_exact_payload_profile(self):
        f=XexFixture(basic=False);image,restored,r=f.decode()
        self.assertEqual(image,f.image);self.assertEqual(restored,f.raw);self.assertEqual(r['compression'],0)
        put(f.raw,0x400,16)
        with self.assertRaises(ValueError):f.parse()

    def test_encrypted_contract_concatenates_blocks_before_cbc_and_after_inverse(self):
        f=XexFixture(encrypted=True);cipher=ContractCipher();image,restored,r=f.decode(key=bytes([0x22])*16,cipher=cipher)
        self.assertEqual(image,f.image);self.assertEqual(restored,f.raw)
        self.assertEqual(cipher.calls,[('decrypt',bytes([0x22])*16,16),('decrypt',bytes([0x11])*16,0xc000),('encrypt',bytes([0x11])*16,0xc000)])

    def test_key_selection_and_cipher_contract_sizes(self):
        f=XexFixture(encrypted=True)
        for kw in [{},{'key':b'x','cipher':ContractCipher()},{'key':bytes(16)}]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):f.decode(**kw)
        with self.assertRaises(ValueError):XexFixture().decode(key=bytes(16))
        for which in ['key','payload','inverse']:
            class Bad(ContractCipher):
                def decrypt(self,key,data):return b'' if (which=='key' and len(data)==16) or (which=='payload' and len(data)>16) else data
                def encrypt(self,key,data):return b'X'*len(data) if which=='inverse' else data
            with self.subTest(which=which),self.assertRaises(ValueError):f.decode(key=bytes(16),cipher=Bad())

    def test_every_header_prefix_truncation_and_sample_payload_truncations(self):
        raw=bytes(XexFixture().raw)
        for n in [*range(0x1000),0x1001,len(raw)-16,len(raw)-1]:
            part=raw[:n]
            with self.subTest(n=n),self.assertRaises(ValueError):parse_xex(part,digest(part))

    def test_hash_magic_module_reserved_and_header_bounds(self):
        f=XexFixture()
        with self.assertRaisesRegex(ValueError,'hash'):parse_xex(f.raw,'0'*64)
        for offset,value in [(0,0),(4,2),(12,1),(8,len(f.raw)+16),(8,0xfff),(16,16),(20,0),(20,4097)]:
            g=XexFixture();put(g.raw,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):g.parse()

    def test_optional_duplicate_missing_and_file_info_ranges(self):
        for offset,value in [(24,0x999ff),(32,0x3ff),(28,4),(28,0xffc),(0x400,7),(0x400,0x2000)]:
            f=XexFixture();put(f.raw,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.parse()

    def test_security_bounds_image_base_and_page_extents(self):
        for offset,value in [(0x100,1),(0x100,0x1000),(0x104,0),(0x104,MAX_IMAGE+1),(0x104,65535),
                             (0x210,0),(0x280,0),(0x280,65536),(0x284,0x10),(0x284,0x14),(0x284,0x23)]:
            f=XexFixture();put(f.raw,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.parse()

    def test_compression_encryption_block_shapes_and_totals(self):
        for offset,value,fmt in [(0x404,2,'>H'),(0x406,2,'>H'),(0x400,9,'>I'),(0x400,16,'>I'),(0x408,0,'>I'),(0x40c,0,'>I'),(0x410,1,'>I')]:
            f=XexFixture();put(f.raw,offset,value,fmt)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.parse()
        f=XexFixture(encrypted=True);put(f.raw,0x408,0x7fff);put(f.raw,0x410,0x4001)
        with self.assertRaisesRegex(ValueError,'alignment'):f.parse()
        f=XexFixture();header=bytearray(0x100000);header[:0x1000]=f.raw[:0x1000]
        put(header,8,len(header));put(header,0x400,8+65537*8);f.raw=header+f.raw[0x1000:]
        with self.assertRaisesRegex(ValueError,'overlong basic'):f.parse()

    def test_execution_header_bounds(self):
        for value in [0xff8,0x100,0x400,0]:
            f=XexFixture();put(f.raw,52,value)
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'execution ID'):f.parse()

    def test_pe_wrong_key_machine_and_entry_checks(self):
        for offset,value,fmt in [(0,0,'<H'),(0x80,0,'<I'),(0x84,0x14c,'<H'),(0x86,0,'<H'),(0x94,2,'<H'),
                                  (0x98,0x20b,'<H'),(0x98+28,0x400000,'<I'),(0x98+16,0x800,'<I')]:
            f=XexFixture();put(f.raw,0x1000+offset,value,fmt)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):f.decode()

    def test_pe_raw_pointers_and_declared_size_do_not_remap_xex_bytes(self):
        f=XexFixture();put(f.image,0x98+0xe0+20,0x999999,'<I');put(f.image,0x98+0xe0+8,0x20000,'<I')
        r=inspect_pe(f.image,0x82000000,0x82000400)
        self.assertTrue(r['pe_headers_for_annotation_only']);self.assertFalse(r['sections'][0]['fully_present_in_xex_image'])
        self.assertEqual(r['sections'][0]['raw_pointer'],0x999999)
        self.assertEqual(r['declared_pe_image_size'],0x20000)

    def test_cli_writes_reopens_three_new_outputs_without_crypto(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=XexFixture();source=root/'source.xex';source.write_bytes(f.raw)
            args=[str(source),'--sha256',digest(f.raw),'--output',str(root/'image.bin'),'--report',str(root/'report.json'),'--roundtrip-output',str(root/'restored.xex')]
            with patch('tools.extract_xex_image.crypto_backend') as crypto:self.assertEqual(main(args),0);crypto.assert_not_called()
            self.assertEqual((root/'image.bin').read_bytes(),f.image);self.assertEqual((root/'restored.xex').read_bytes(),f.raw)
            self.assertFalse(json.loads((root/'report.json').read_text())['executed']);self.assertEqual(source.read_bytes(),f.raw)

    def test_cli_alias_existing_output_and_expected_image_hash_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=XexFixture();source=root/'source.xex';source.write_bytes(f.raw)
            base=[str(source),'--sha256',digest(f.raw),'--output',str(root/'image.bin'),'--report',str(root/'report.json')]
            for index in [4,6]:
                args=base.copy();args[index]=str(source);self.assertEqual(main(args),2)
            args=base+['--image-sha256','0'*64];self.assertEqual(main(args),2);self.assertFalse((root/'image.bin').exists())
            (root/'report.json').write_text('existing');self.assertEqual(main(base),2);self.assertEqual((root/'report.json').read_text(),'existing')

    def test_bad_source_profile_precedes_optional_crypto_import(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=XexFixture(encrypted=True);source=root/'source.xex';source.write_bytes(f.raw)
            base=[str(source),'--sha256',digest(f.raw),'--key','retail','--output',str(root/'image.bin'),'--report',str(root/'report.json')]
            with patch('tools.extract_xex_image.crypto_backend') as crypto:
                args=base.copy();args[2]='0'*64;self.assertEqual(main(args),2);crypto.assert_not_called()
                source.write_bytes(b'not XEX');args[2]=digest(b'not XEX');self.assertEqual(main(args),2);crypto.assert_not_called()
            self.assertFalse((root/'image.bin').exists())

    def test_cli_key_guard_and_injected_encrypted_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=XexFixture(encrypted=True);source=root/'source.xex';source.write_bytes(f.raw)
            args=[str(source),'--sha256',digest(f.raw),'--output',str(root/'image.bin'),'--report',str(root/'report.json')]
            self.assertEqual(main(args),2)
            with patch('tools.extract_xex_image.crypto_backend',return_value=ContractCipher()):self.assertEqual(main(args+['--key','devkit']),0)
            self.assertEqual((root/'image.bin').read_bytes(),f.image)

    def test_cli_late_source_change_has_no_success_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=XexFixture();source=root/'source.xex';source.write_bytes(f.raw)
            def mutate(*a,**kw):
                result=decode_image(*a,**kw);source.write_bytes(b'changed fixture');return result
            args=[str(source),'--sha256',digest(f.raw),'--output',str(root/'image.bin'),'--report',str(root/'report.json')]
            with patch('tools.extract_xex_image.decode_image',side_effect=mutate):self.assertEqual(main(args),2)
            self.assertFalse((root/'image.bin').exists());self.assertFalse((root/'report.json').exists())

    def test_unknown_backend_is_not_a_silent_fallback(self):
        with self.assertRaises(ValueError):crypto_backend('unknown')


class NativeSignatureHygieneTests(unittest.TestCase):
    def test_pe_image_disguised_as_data_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'payload.data';p.write_bytes(XexFixture().image)
            self.assertTrue(executable_signature(p));self.assertEqual(violations(['payload.data'],root),['payload.data'])

    def test_elf_signature_disguised_as_data_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'payload.data').write_bytes(b'\x7fELF'+bytes(64))
            self.assertEqual(violations(['payload.data'],root),['payload.data'])

    def test_plain_source_and_truncated_mz_are_not_native_images(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for data in [b'normal source',b'MZ',b'MZ'+bytes(64)]:
                p=root/'source.txt';p.write_bytes(data);self.assertFalse(executable_signature(p))
            self.assertEqual(violations(['source.txt','missing.txt'],root),[])

    def test_path_only_api_and_oversized_pe_offset_remain_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=bytearray(64);data[:2]=b'MZ';put(data,0x3c,0xffffffff,'<I');(root/'payload.data').write_bytes(data)
            self.assertEqual(violations(['payload.data']),[]);self.assertEqual(violations(['payload.data'],root),[])


if __name__=='__main__':unittest.main()
