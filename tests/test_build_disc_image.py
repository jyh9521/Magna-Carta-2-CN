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
    def __init__(self, root, payload=b'localized payload'*200, base=0,
                 toc=False, source_sector=41, candidate_sector=41):
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
        record(37,0,b'CookedXenon',38,SECTOR,0x10,right=8 if toc else 0)
        record(38,0,b'sample.xxx',41,3,0x80)
        data[base+40*SECTOR:base+40*SECTOR+3]=b'xex'
        data[base+41*SECTOR:base+41*SECTOR+3]=b'abc'
        self.toc_name='MC2Game/Xbox360TOC.txt'
        if toc:
            self.original_toc=(f'3 7 {source_sector} ..\\MC2Game\\CookedXenon\\sample.xxx 9\r\n'
                               '0 0 42 ..\\MC2Game\\Xbox360TOC.txt 0\r\n'
                               '13 0 99 ..\\OtherDisc\\absent.xxx 0\r\n').encode()
            self.candidate_toc=(f'{len(payload)} 7 {candidate_sector} ..\\MC2Game\\CookedXenon\\sample.xxx 9\r\n'
                                '0 0 42 ..\\MC2Game\\Xbox360TOC.txt 0\r\n'
                                '13 0 99 ..\\OtherDisc\\absent.xxx 0\r\n').encode()
            record(37,32,b'Xbox360TOC.txt',42,len(self.original_toc),0x80)
            data[base+42*SECTOR:base+42*SECTOR+len(self.original_toc)]=self.original_toc
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
        if toc:
            (self.packet/'candidate'/self.toc_name).write_bytes(self.candidate_toc)
            self.manifest['resources'].append(dict(path=self.toc_name,
                original_size=len(self.original_toc),original_sha256=sha(self.original_toc),
                candidate_size=len(self.candidate_toc),candidate_sha256=sha(self.candidate_toc)))
            self.manifest['member_sha256']['candidate/'+self.toc_name]=sha(self.candidate_toc)
        self.refresh()

    def replace_candidate_toc(self, raw):
        (self.packet/'candidate'/self.toc_name).write_bytes(raw)
        self.manifest['resources'][-1].update(candidate_size=len(raw),candidate_sha256=sha(raw))
        self.manifest['member_sha256']['candidate/'+self.toc_name]=sha(raw)
        self.refresh()

    def refresh(self):
        (self.packet/'manifest.json').write_bytes(iso.encoded(self.manifest))
        self.packet_hash=sha256_file(self.packet/'manifest.json')

    def args(self):
        return self.image,self.hash,self.packet,self.packet_hash,1,self.output

    def build(self):
        return iso.build(*self.args(),self.report)


def legacy_image(f):
    """Recreate the old writer, including its missing TOC-sector adjustment."""
    disc=Disc(f.image); inventory=disc.inventory()
    entries={r['path']:r for r in inventory}; locations=iso.entry_offsets(disc,inventory)
    data=bytearray(f.image.read_bytes()); changes=[]
    for resource in sorted(f.manifest['resources'],key=lambda r:r['path'].casefold()):
        old=entries[resource['path']]
        payload=(f.packet/'candidate'/resource['path']).read_bytes()
        if sha(payload)==resource['original_sha256'] and len(payload)==old['size']:
            continue
        offset=len(data); sector=(offset-disc.base)//SECTOR; field=locations[resource['path']]+4
        before=bytes(data[field:field+8]); after=struct.pack('<II',sector,len(payload))
        changes.append(dict(path=resource['path'],field_offset=field,before_hex=before.hex(),
            after_hex=after.hex(),sector=sector,offset=offset,size=len(payload),sha256=sha(payload)))
        data.extend(payload); data.extend(bytes((-len(payload))%SECTOR)); data[field:field+8]=after
    f.output.write_bytes(data)
    report=dict(schema_version=1,kind=iso.KIND,disc=1,
        source=dict(path=str(f.image),size=disc.size,sha256=f.hash,partition_base=disc.base),
        packet=dict(path=str(f.packet),manifest_sha256=f.packet_hash),
        output=dict(path=str(f.output),size=len(data),sha256=sha(data)),changes=changes)
    f.report.write_bytes(iso.encoded(report))
    return report


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

    def test_toc_sectors_follow_payload_and_self_without_other_edits(self):
        f=Fixture(self.root,toc=True); report=f.build()
        disc=Disc(f.output); entries={r['path']:r for r in disc.inventory()}
        toc=entries[f.toc_name]; actual=disc.read(toc['offset'],toc['size'])
        expected=f.candidate_toc.replace(b'7 41 ',f'7 {entries[f.name]["sector"]} '.encode())
        expected=expected.replace(b'0 0 42 ',f'0 0 {toc["sector"]} '.encode())
        self.assertEqual(actual,expected)
        self.assertTrue(actual.splitlines()[1].startswith(b'0 0 '))
        self.assertEqual((f.packet/'candidate'/f.toc_name).read_bytes(),f.candidate_toc)
        self.assertEqual(report['schema_version'],2)
        self.assertTrue(report['toc_relocations'][0]['inverse_byte_identical'])
        self.assertEqual(report['toc_relocations'][0]['candidate_sha256'],sha(f.candidate_toc))
        proof=iso.verify(*f.args(),report=report)
        self.assertEqual(proof['toc_rows_checked'],2)
        restored=self.root/'restored.iso'
        iso.restore(f.output,f.report,sha256_file(f.report),restored)
        self.assertEqual(restored.read_bytes(),f.image.read_bytes())

    def test_toc_original_sector_mismatch_rejected_before_output(self):
        f=Fixture(self.root,toc=True,source_sector=40)
        with self.assertRaisesRegex(ValueError,'original TOC sector mismatch'):f.build()
        self.assertFalse(f.output.exists())

    def test_toc_candidate_sector_mismatch_rejected_before_output(self):
        f=Fixture(self.root,toc=True,candidate_sector=40)
        with self.assertRaisesRegex(ValueError,'candidate TOC sector mismatch'):f.build()
        self.assertFalse(f.output.exists())

    def test_toc_candidate_size_mismatch_rejected_before_output(self):
        f=Fixture(self.root,toc=True)
        f.replace_candidate_toc(f.candidate_toc.replace(b'3400 7 ',b'3399 7 '))
        with self.assertRaisesRegex(ValueError,'TOC size mismatch'):f.build()
        self.assertFalse(f.output.exists())

    def test_toc_duplicate_path_rejected_before_output(self):
        f=Fixture(self.root,toc=True)
        f.replace_candidate_toc(f.candidate_toc+f.candidate_toc.splitlines(keepends=True)[0])
        with self.assertRaisesRegex(ValueError,'duplicate or case-ambiguous TOC'):f.build()
        self.assertFalse(f.output.exists())

    def test_toc_legacy_mismatch_fails_verification_but_restores(self):
        f=Fixture(self.root,toc=True); report=legacy_image(f)
        with self.assertRaisesRegex(ValueError,'TOC sector mismatch'):
            iso.verify(*f.args(),report=report)
        restored=self.root/'legacy-restored.iso'
        iso.restore(f.output,f.report,sha256_file(f.report),restored)
        self.assertEqual(restored.read_bytes(),f.image.read_bytes())

    def test_legacy_without_toc_still_verifies_and_restores(self):
        f=Fixture(self.root); report=legacy_image(f)
        self.assertEqual(iso.verify(*f.args(),report=report)['status'],'PASS')
        restored=self.root/'legacy-restored.iso'
        iso.restore(f.output,f.report,sha256_file(f.report),restored)
        self.assertEqual(restored.read_bytes(),f.image.read_bytes())

    def test_toc_missing_self_row_is_rejected(self):
        f=Fixture(self.root,toc=True)
        f.replace_candidate_toc(b''.join(f.candidate_toc.splitlines(keepends=True)[::2]))
        with self.assertRaisesRegex(ValueError,'TOC path set mismatch'):f.build()
        self.assertFalse(f.output.exists())

    def test_identical_toc_packet_preserves_complete_image(self):
        f=Fixture(self.root,payload=b'abc',toc=True); report=f.build()
        self.assertEqual(report['changes'],[])
        self.assertEqual(report['toc_relocations'],[])
        self.assertEqual(f.output.read_bytes(),f.image.read_bytes())
        self.assertEqual(iso.verify(*f.args(),report=report)['toc_rows_checked'],2)

    def test_source_only_toc_is_relocated_for_equal_size_replacement(self):
        f=Fixture(self.root,payload=b'xyz',toc=True)
        f.manifest['resources'].pop()
        del f.manifest['member_sha256']['candidate/'+f.toc_name]
        (f.packet/'candidate'/f.toc_name).unlink(); f.refresh()
        report=f.build()
        self.assertEqual({r['path'] for r in report['changes']},{f.name,f.toc_name})
        self.assertEqual(iso.verify(*f.args(),report=report)['toc_rows_checked'],2)

    def test_source_only_toc_rejects_stale_sizes(self):
        f=Fixture(self.root,toc=True)
        f.manifest['resources'].pop()
        del f.manifest['member_sha256']['candidate/'+f.toc_name]
        (f.packet/'candidate'/f.toc_name).unlink(); f.refresh()
        with self.assertRaisesRegex(ValueError,'TOC size mismatch'):f.build()
        self.assertFalse(f.output.exists())

    def test_toc_zero_self_size_is_enforced(self):
        f=Fixture(self.root,toc=True)
        f.replace_candidate_toc(f.candidate_toc.replace(b'0 0 42 ',b'130 0 42 '))
        with self.assertRaisesRegex(ValueError,'TOC size mismatch'):f.build()
        self.assertFalse(f.output.exists())

    def test_toc_relocation_report_tampering_is_detected(self):
        f=Fixture(self.root,toc=True); report=f.build()
        report['toc_relocations'][0]['inverse_byte_identical']=False
        with self.assertRaisesRegex(ValueError,'TOC relocation report mismatch'):
            iso.verify(*f.args(),report=report)

    def test_relocation_helper_preserves_spelling_and_reverses_growing_spans(self):
        name='G/sample.xxx'; toc_path='G/Xbox360TOC.txt'
        raw=(b'0003 7 0041 ..\\G\\sample.xxx 9\r\n'
             b'0 0 42 ..\\G\\Xbox360TOC.txt 0\n'
             b'13 0 99 ..\\Other\\absent.xxx 0')
        old={name:dict(sector=41,size=3),toc_path:dict(sector=42,size=len(raw))}
        target={name:dict(sector=123456,size=10000),toc_path:dict(sector=123999,size=0)}
        saved=copy.deepcopy((old,target))
        output,proof=iso.relocate_toc(raw,old,target,toc_path)
        expected=raw.replace(b'0003 7 0041',b'10000 7 123456').replace(b'0 0 42 ',b'0 0 123999 ')
        self.assertEqual(output,expected)
        self.assertEqual((old,target),saved)
        inverse=bytearray(output)
        for edit in sorted(proof['edits'],key=lambda r:r['output_byte_offset'],reverse=True):
            start=edit['output_byte_offset']; before=bytes.fromhex(edit['before_hex'])
            after=bytes.fromhex(edit['after_hex'])
            self.assertEqual(inverse[start:start+len(after)],after)
            inverse[start:start+len(after)]=before
        self.assertEqual(inverse,raw)
        self.assertEqual({r['field'] for r in proof['edits']},{'size','sector'})

    def test_toc_helper_rejects_wrong_expected_sector_and_uint32_target(self):
        f=Fixture(self.root,toc=True)
        entries={r['path']:r for r in Disc(f.image).inventory()}
        bad=copy.deepcopy(entries); bad[f.name]['sector']+=1
        with self.assertRaisesRegex(ValueError,'TOC sector mismatch'):
            iso.relocate_toc(f.original_toc,bad,entries,f.toc_name)
        bad=copy.deepcopy(entries); bad[f.name]['sector']=2**32
        with self.assertRaisesRegex(ValueError,'exceeds uint32'):
            iso.relocate_toc(f.original_toc,entries,bad,f.toc_name)


if __name__=='__main__':
    unittest.main()
