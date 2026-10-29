"""Authored UE3 packages exercise normalization, not a successful game boot."""
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools import normalize_runtime_comparison as runtime
from tools import compose_incremental_comparison as compose
from tools.runtime_package import normalize_package
from tools.ue3_package import parse_summary
from tools.verify_resource_phase import inspect, sha
from test_compose_incremental_comparison import Fixture as BaseFixture, tree
from test_runtime_package import fixture, texture
from test_supplement_font import stored_decoder


class Fixture(BaseFixture):
    def __init__(self, root, candidate=None):
        super().__init__(root)
        self.untouched = 'Game/original.xxx'
        self.names = (self.a, self.keep, self.untouched)
        original = fixture(outer=True)
        raw = fixture()
        candidate = fixture(outer=True, bulk=True) if candidate is None else candidate
        for phase, value in (('controls',original),('raw-controls',raw),('candidate',candidate)):
            (self.base/phase/self.a).write_bytes(value)
            p=self.base/phase/self.untouched;p.write_bytes(original)
        self.sync()

    def sync(self):
        self.manifest['resources']=[];self.manifest['member_sha256']={}
        for phase in ('controls','raw-controls','candidate'):
            lines=[f'{(self.base/phase/name).stat().st_size} 7 {100+i} ../{name} 9\r\n'
                   for i,name in enumerate(self.names)]
            lines.append(f'0 0 250 ../{self.toc} 0\r\n')
            (self.base/phase/self.toc).write_bytes(''.join(lines).encode())
        for name in (*self.names,self.toc):
            row={'path':name}
            for phase,key in (('controls','original'),('raw-controls','raw'),('candidate','candidate')):
                data=(self.base/phase/name).read_bytes()
                row.update({key+'_size':len(data),key+'_sha256':sha(data)})
                self.manifest['member_sha256'][phase+'/'+name]=sha(data)
            self.manifest['resources'].append(row)
        self.save_base()

    def audit(self):
        return runtime.audit(self.base,self.base_hash,self.toc,stored_decoder)

    def build(self):
        return runtime.build(self.base,self.base_hash,self.out,self.toc,stored_decoder)


class NormalizeRuntimeComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def test_audit_is_read_only_and_identifies_generated_lzx(self):
        f=Fixture(self.root);before=tree(f.base)
        report=f.audit()
        self.assertEqual(tree(f.base),before)
        self.assertFalse(f.out.exists())
        self.assertEqual(report['profile'],'xenon-446-25-raw32k-v1')
        self.assertEqual(report['changes_needed'],1)
        self.assertEqual(report['modified_ue3_count'],1)
        row=next(x for x in report['resources'] if x['path']==f.a)
        self.assertTrue(row['normalization']['native_tiles_preserved'])
        self.assertTrue(row['padding']['prefix_identical'])
        self.assertFalse(report['game_started'])
        self.assertFalse(report['resource_writes_performed'])

    def test_raw_odd_length_is_only_zero_padded(self):
        raw=fixture();self.assertNotEqual(len(raw)%32768,0)
        f=Fixture(self.root,raw);report=f.build()
        output=(f.out/'packet/candidate'/f.a).read_bytes()
        self.assertEqual(output[:len(raw)],raw)
        self.assertEqual(output[len(raw):],bytes((-len(raw))%32768))
        self.assertEqual(len(output)%32768,0)
        row=next(x for x in report['resources'] if x['path']==f.a)
        self.assertFalse(row['normalization']['changed'])
        self.assertEqual(row['padding']['source_sha256'],sha(raw))
        self.assertTrue(row['padding']['suffix_all_zero'])

    def test_build_preserves_tiles_controls_opaque_data_and_toc_fields(self):
        f=Fixture(self.root);before=tree(f.base);_,_,_,old_texture=texture(before['candidate/'+f.a])
        report=f.build();packet=f.out/'packet';raw=(packet/'candidate'/f.a).read_bytes()
        self.assertEqual(texture(raw)[3]['tiles'],old_texture['tiles'])
        self.assertEqual(parse_summary(raw)['compression_flags'],0)
        self.assertEqual(tree(f.base),before)
        for phase in ('controls','raw-controls'):
            for name in (*f.names,f.toc):
                self.assertTrue(os.path.samefile(f.base/phase/name,packet/phase/name))
        for name in (f.keep,f.untouched):
            self.assertTrue(os.path.samefile(f.base/'candidate'/name,packet/'candidate'/name))
        self.assertFalse(os.path.samefile(f.base/'candidate'/f.a,packet/'candidate'/f.a))
        self.assertEqual((packet/'candidate'/f.untouched).read_bytes(),before['controls/'+f.untouched])
        old=before['candidate/'+f.toc].splitlines();new=(packet/'candidate'/f.toc).read_bytes().splitlines()
        self.assertEqual([x.split(b' ',1)[1] for x in old],[x.split(b' ',1)[1] for x in new])
        self.assertEqual(new[-1],old[-1])
        spec=json.loads((f.out/'replacements.json').read_text())
        self.assertEqual(spec['kind'],compose.KIND);self.assertEqual(spec['disc'],1)
        self.assertEqual(spec['toc_path'],f.toc);self.assertEqual(len(spec['resources']),1)
        replacement=spec['resources'][0]
        self.assertEqual(replacement['file'],'normalized/candidate/'+f.a)
        self.assertEqual(replacement['before_sha256'],sha(before['candidate/'+f.a]))
        self.assertEqual((f.out/replacement['file']).read_bytes(),raw)
        mh=sha((packet/'manifest.json').read_bytes())
        self.assertEqual(report['packet_manifest_sha256'],mh)
        for phase in ('controls','raw-controls','candidate'):
            self.assertTrue(inspect(packet,mh,packet/phase,phase)[0]['all_resources_match'])

    def test_original_compressed_identical_candidate_is_not_normalized(self):
        f=Fixture(self.root)
        with patch.object(runtime,'normalize_package',wraps=normalize_package) as normalizer:
            report=f.audit()
        self.assertEqual(normalizer.call_count,1)
        row=next(x for x in report['resources'] if x['path']==f.untouched)
        self.assertEqual(row['action'],'preserve-original')
        self.assertGreater(parse_summary((f.base/'candidate'/f.untouched).read_bytes())['compression_flags'],0)

    def test_second_generation_audit_and_build_are_idempotent(self):
        f=Fixture(self.root);f.build();packet=f.out/'packet';mh=sha((packet/'manifest.json').read_bytes())
        before=tree(packet)
        report=runtime.audit(packet,mh,f.toc,stored_decoder)
        self.assertEqual(report['changes_needed'],0)
        second=self.root/'second'
        result=runtime.build(packet,mh,second,f.toc,stored_decoder)
        self.assertEqual(result['status'],'ALREADY_CANONICAL')
        self.assertFalse((second/'packet').exists());self.assertFalse((second/'normalized').exists())
        self.assertEqual(tree(packet),before)

    def test_wrong_hash_and_tampered_each_phase_fail_before_decoding(self):
        f=Fixture(self.root)
        with patch.object(runtime,'normalize_package',side_effect=AssertionError('unexpected decode')):
            with self.assertRaisesRegex(ValueError,'SHA256'):
                runtime.audit(f.base,'0'*64,f.toc,stored_decoder)
            for phase in ('controls','raw-controls','candidate'):
                p=f.base/phase/f.keep;raw=p.read_bytes();p.write_bytes(raw+b'corruption')
                with self.subTest(phase=phase),self.assertRaisesRegex(ValueError,'SHA256'):
                    f.audit()
                p.write_bytes(raw)

    def test_unknown_version_in_modified_package_is_rejected(self):
        data=bytearray(fixture());struct.pack_into('>I',data,4,447 | 25<<16)
        f=Fixture(self.root,bytes(data))
        with self.assertRaisesRegex(ValueError,'serialization profile'):f.build()
        self.assertFalse(f.out.exists())

    def test_non_generated_modified_compressed_package_is_rejected(self):
        data=bytearray(fixture(outer=True))
        for chunk in parse_summary(data)['compressed_chunks']:
            data[chunk['compressed_offset']+24+5+4]=2
        f=Fixture(self.root,bytes(data))
        with self.assertRaisesRegex(ValueError,'residual.*compress'):f.build()
        self.assertFalse(f.out.exists())

    def test_lost_ue3_magic_in_modified_package_is_rejected(self):
        data=bytearray(fixture());data[:4]=b'BAD!';f=Fixture(self.root,bytes(data))
        with self.assertRaisesRegex(ValueError,'magic'):f.build()
        self.assertFalse(f.out.exists())

    def test_rehashed_bad_toc_size_fails_before_any_output(self):
        f=Fixture(self.root);p=f.base/'candidate'/f.toc
        raw=p.read_bytes();bad=b'999999 '+raw.split(b' ',1)[1];p.write_bytes(bad)
        row=next(x for x in f.manifest['resources'] if x['path']==f.toc)
        row.update(candidate_size=len(bad),candidate_sha256=sha(bad))
        f.manifest['member_sha256']['candidate/'+f.toc]=sha(bad);f.save_base()
        with self.assertRaisesRegex(ValueError,'TOC.*size'):f.build()
        self.assertFalse(f.out.exists())

    def test_output_must_be_new_canonical_and_disjoint(self):
        f=Fixture(self.root)
        for output in (f.base,f.base/'nested',self.root):
            with self.subTest(output=output),self.assertRaises(ValueError):
                runtime.build(f.base,f.base_hash,output,f.toc,stored_decoder)

    def test_source_change_during_normalization_is_detected(self):
        f=Fixture(self.root);real=normalize_package
        def change(*args):
            result=real(*args);p=f.base/'candidate'/f.keep;p.write_bytes(p.read_bytes()+b'changed');return result
        with patch.object(runtime,'normalize_package',side_effect=change),self.assertRaisesRegex(ValueError,'changed'):
            f.build()
        self.assertFalse(f.out.exists())

    def test_compose_failure_cleans_owned_files_but_preserves_foreign_file(self):
        f=Fixture(self.root);before=tree(f.base)
        def fail(*args):
            (f.out/'foreign.txt').write_bytes(b'not owned')
            raise OSError('injected compose failure')
        with patch.object(runtime.compose,'build',side_effect=fail),self.assertRaises(OSError):f.build()
        self.assertEqual(tree(f.out),{'foreign.txt':b'not owned'});self.assertEqual(tree(f.base),before)

    def test_unexpected_outer_output_is_not_a_clean_success(self):
        f=Fixture(self.root);real=compose.build
        def foreign(*args):
            result=real(*args);(f.out/'foreign-empty').mkdir();return result
        with patch.object(runtime.compose,'build',side_effect=foreign),self.assertRaisesRegex(ValueError,'unexpected.*directory'):
            f.build()
        self.assertTrue((f.out/'foreign-empty').exists())
        self.assertTrue((f.out/'packet/manifest.json').exists())

    def test_cli_audit_codes_and_no_resource_writes(self):
        raw=fixture();f=Fixture(self.root,raw);before=tree(f.base)
        args=['audit','--packet-root',str(f.base),'--manifest-sha256',f.base_hash,
              '--toc-path',f.toc,'--output-dir',str(f.out)]
        self.assertEqual(runtime.main(args),1)
        self.assertEqual(set(tree(f.out)),{'audit.json'})
        self.assertEqual(tree(f.base),before)
        bad=self.root/'bad';args[args.index('--output-dir')+1]=str(bad)
        args[args.index('--manifest-sha256')+1]='0'*64
        self.assertEqual(runtime.main(args),2);self.assertFalse(bad.exists())

    def test_cli_build_and_canonical_audit_succeed_without_decoder_for_raw(self):
        f=Fixture(self.root,fixture())
        self.assertEqual(runtime.main(['build','--packet-root',str(f.base),
            '--manifest-sha256',f.base_hash,'--toc-path',f.toc,'--output-dir',str(f.out)]),0)
        packet=f.out/'packet';mh=sha((packet/'manifest.json').read_bytes())
        self.assertEqual(runtime.main(['audit','--packet-root',str(packet),
            '--manifest-sha256',mh,'--toc-path',f.toc,'--output-dir',str(self.root/'canonical-audit')]),0)


if __name__=='__main__':unittest.main()
