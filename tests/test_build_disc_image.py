"""Self-authored nested XDVDFS images; no game data required."""
import contextlib
import copy
import hashlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

from tools import build_disc_image as iso
from tools.disc_inventory import Disc, MAGIC, SECTOR, sha256_file


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Fixture:
    def __init__(self, root, payload=b'localized payload'*200, base=0):
        self.root=root; self.image=root/'original.iso'; self.packet=root/'packet'
        self.output=root/'candidate.iso'; self.report=root/'image.json'
        data=bytearray(base+44*SECTOR)
        data[base+0x10000:base+0x10000+20]=MAGIC
        data[base+0x10800-20:base+0x10800]=MAGIC
        struct.pack_into('<II',data,base+0x10000+20,36,SECTOR)
        def record(table,offset,name,sector,size,flags,right=0):
            start=base+table*SECTOR+offset
            struct.pack_into('<HHIIBB',data,start,0,right,sector,size,flags,len(name))
            data[start+14:start+14+len(name)]=name
        record(36,0,b'MC2Game',37,SECTOR,0x10,right=8)
        record(36,32,b'default.xex',40,3,0x80)
        record(37,0,b'CookedXenon',38,SECTOR,0x10)
        record(38,0,b'sample.xxx',41,3,0x80)
        data[base+40*SECTOR:base+40*SECTOR+3]=b'xex'
        data[base+41*SECTOR:base+41*SECTOR+3]=b'abc'
        self.image.write_bytes(data); self.hash=sha(data)
        self.name='MC2Game/CookedXenon/sample.xxx'
        p=self.packet/'candidate'/self.name;p.parent.mkdir(parents=True);p.write_bytes(payload)
        self.manifest=dict(schema_version=1,kind='offline-disc-locale-raw-comparison',disc=1,
            source_image_sha256=self.hash,game_rendering_verified=False,deployment_performed=False,
            raw_package_outputs=True,unknown_control_syntax_resolved=False,
            raw_control_method='source-derived-uncompressed-fonts-original-text-disc-toc',
            composition_manifest_sha256='1'*64,comparison_plan_canonical_sha256='2'*64,
            resources=[dict(path=self.name,original_size=3,original_sha256=sha(b'abc'),
                            candidate_size=len(payload),candidate_sha256=sha(payload))],
            member_sha256={'candidate/'+self.name:sha(payload)})
        self.refresh()

    def refresh(self):
        (self.packet/'manifest.json').write_bytes(iso.encoded(self.manifest))
        self.packet_hash=sha256_file(self.packet/'manifest.json')

    def args(self):
        return self.image,self.hash,self.packet,self.packet_hash,1,self.output

    def build(self):
        return iso.build(*self.args(),self.report)


class DiscImageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_nested_build_full_verification_and_exact_inverse(self):
        f=Fixture(self.root);r=f.build();v=iso.verify(*f.args(),report=r)
        self.assertEqual((v['files'],v['directories'],v['localized_files']),(2,2,1))
        self.assertFalse(v['game_started']);self.assertFalse(v['game_rendering_verified'])
        self.assertEqual(sha256_file(f.image),f.hash)
        d=Disc(f.output);entries={r['path']:r for r in d.inventory()}
        self.assertEqual(d.resource_hash(entries[f.name]),f.manifest['resources'][0]['candidate_sha256'])
        self.assertEqual(d.resource_hash(entries['default.xex']),sha(b'xex'))
        restored=self.root/'restored.iso'
        proof=iso.restore(f.output,f.report,sha256_file(f.report),restored)
        self.assertEqual(restored.read_bytes(),f.image.read_bytes())
        self.assertTrue(proof['modified_image_unchanged'])
        self.assertEqual(sha256_file(f.output),r['output']['sha256'])

    def test_repeat_build_is_byte_deterministic(self):
        f=Fixture(self.root);r=f.build()
        another=self.root/'another.iso'
        r2=iso.build(*f.args()[:-1],another,self.root/'another.json')
        self.assertEqual(r['output']['sha256'],r2['output']['sha256'])

    def test_identical_resource_preserves_complete_image(self):
        f=Fixture(self.root,payload=b'abc');r=f.build()
        self.assertEqual(r['changes'],[]);self.assertEqual(f.image.read_bytes(),f.output.read_bytes())

    def test_empty_replacement_supported(self):
        f=Fixture(self.root,payload=b'');r=f.build()
        self.assertEqual(r['changes'][0]['size'],0)
        self.assertEqual(r['output']['size'],f.image.stat().st_size)

    def test_sector_padding(self):
        f=Fixture(self.root,payload=b'a'*(SECTOR+1));r=f.build()
        self.assertEqual(r['output']['size'],f.image.stat().st_size+2*SECTOR)
        self.assertEqual(f.output.read_bytes()[-(SECTOR-1):],bytes(SECTOR-1))

    def test_nonzero_partition_base(self):
        f=Fixture(self.root,base=0x2080000);r=f.build()
        self.assertEqual(r['source']['partition_base'],0x2080000)
        self.assertEqual(r['changes'][0]['offset'],0x2080000+44*SECTOR)
        self.assertEqual(r['changes'][0]['sector'],44)

    def test_unknown_original_hash_rejected_before_output(self):
        f=Fixture(self.root);f.hash='0'*64
        with self.assertRaisesRegex(ValueError,'original image SHA256'):f.build()
        self.assertFalse(f.output.exists())

    def test_disc_packet_identity_rejected(self):
        for field,value in [('disc',2),('source_image_sha256','0'*64)]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as d:
                f=Fixture(Path(d).resolve());f.manifest[field]=value;f.refresh()
                with self.assertRaisesRegex(ValueError,'disc identity'):f.build()
                self.assertFalse(f.output.exists())

    def test_original_resource_identity_rejected(self):
        f=Fixture(self.root);f.manifest['resources'][0]['original_sha256']='0'*64;f.refresh()
        with self.assertRaisesRegex(ValueError,'original resource hash'):f.build()

    def test_tampered_candidate_rejected(self):
        f=Fixture(self.root);(f.packet/'candidate'/f.name).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'member SHA256'):f.build()
        self.assertFalse(f.output.exists())

    def test_output_and_report_must_be_new(self):
        f=Fixture(self.root);f.output.write_bytes(b'keep')
        with self.assertRaises(ValueError):f.build()
        self.assertEqual(f.output.read_bytes(),b'keep')
        with self.assertRaises(ValueError):iso.build(*f.args()[:-1],f.image,f.report)
        self.assertEqual(sha256_file(f.image),f.hash)

    def test_wrong_manifest_hash_rejected(self):
        f=Fixture(self.root);f.packet_hash='0'*64
        with self.assertRaisesRegex(ValueError,'SHA256'):f.build()

    def test_original_padding_corruption_is_detected(self):
        f=Fixture(self.root);f.build()
        with f.output.open('r+b') as stream:stream.seek(4);stream.write(b'X')
        with self.assertRaisesRegex(ValueError,'original prefix'):iso.verify(*f.args())

    def test_appended_payload_corruption_is_detected(self):
        f=Fixture(self.root);r=f.build()
        with f.output.open('r+b') as stream:stream.seek(r['changes'][0]['offset']);stream.write(b'X')
        with self.assertRaisesRegex(ValueError,'file hash mismatch'):iso.verify(*f.args())

    def test_directory_field_corruption_is_detected(self):
        f=Fixture(self.root);r=f.build()
        with f.output.open('r+b') as stream:stream.seek(r['changes'][0]['field_offset']);stream.write(bytes(8))
        with self.assertRaisesRegex(ValueError,'inverse expected-byte'):iso.verify(*f.args())

    def test_truncated_output_is_detected(self):
        f=Fixture(self.root);f.build()
        with f.output.open('r+b') as stream:stream.truncate(f.output.stat().st_size-1)
        with self.assertRaisesRegex(ValueError,'path/size'):iso.verify(*f.args())

    def test_report_provenance_is_checked(self):
        f=Fixture(self.root);r=f.build();r['disc']=2
        with self.assertRaisesRegex(ValueError,'provenance'):iso.verify(*f.args(),report=r)

    def test_rollback_rejects_hash_and_existing_destination(self):
        f=Fixture(self.root);f.build()
        with self.assertRaisesRegex(ValueError,'SHA256'):iso.restore(f.output,f.report,'0'*64,self.root/'restore.iso')
        with self.assertRaisesRegex(ValueError,'new and distinct'):iso.restore(f.output,f.report,sha256_file(f.report),f.image)
        self.assertEqual(sha256_file(f.image),f.hash)

    def test_rollback_rejects_changed_image(self):
        f=Fixture(self.root);f.build()
        with f.output.open('r+b') as stream:stream.seek(0);stream.write(b'x')
        with self.assertRaisesRegex(ValueError,'modified image identity'):
            iso.restore(f.output,f.report,sha256_file(f.report),self.root/'restore.iso')

    def test_inverse_rejects_overlapping_fields(self):
        f=Fixture(self.root);r=f.build();rows=r['changes']*2
        with self.assertRaisesRegex(ValueError,'overlapping'):iso.original_prefix(f.output,f.image.stat().st_size,rows)

    def test_out_of_bounds_field_beyond_4_gib_is_not_wrapped(self):
        # A high offset must not wrap into a valid low 32-bit location.
        f=Fixture(self.root);r=f.build();row=copy.deepcopy(r['changes'][0])
        row['field_offset']=2**32+4
        with self.assertRaisesRegex(ValueError,'invalid or overlapping'):
            iso.original_prefix(f.output,f.image.stat().st_size,[row])

    def test_executable_replacement_rejected(self):
        f=Fixture(self.root)
        p=f.packet/'candidate/default.xex';p.write_bytes(b'changed')
        f.manifest['resources']=[dict(path='default.xex',original_size=3,original_sha256=sha(b'xex'),
            candidate_size=7,candidate_sha256=sha(b'changed'))]
        f.manifest['member_sha256']={'candidate/default.xex':sha(b'changed')};f.refresh()
        with self.assertRaisesRegex(ValueError,'executable replacement'):f.build()
        self.assertFalse(f.output.exists())

    def test_cli_failure_is_nonzero(self):
        f=Fixture(self.root)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code=iso.main(['build','--image',str(f.image),'--image-sha256','0'*64,
                '--packet',str(f.packet),'--packet-sha256',f.packet_hash,'--disc','1',
                '--output',str(f.output),'--report',str(f.report)])
        self.assertEqual(code,2);self.assertIn('original image SHA256 mismatch',out.getvalue())


if __name__=='__main__':
    unittest.main()
