import unittest
from pathlib import Path

from tools.prepare_oneclick_probe import launcher
from tools.runtime_envelope import require_raw_envelope,generated_stored_chunk
from tools.runtime_package import normalize_package
from test_runtime_package import fixture,sha,stored_decoder


class RuntimeLauncherTests(unittest.TestCase):
    def test_candidate_entry_requires_runtime_envelope_not_only_matching_hashes(self):
        args = [Path('python.exe'), Path('project'), Path('packet'), '1'*64,
                Path('xenia.exe'), Path('config.toml'), '2'*64]
        self.assertIn(b'--runtime-envelope', launcher(*args, 'candidate'))
        self.assertNotIn(b'--runtime-envelope', launcher(*args, 'raw-controls'))

    def test_matching_generated_package_is_rejected_until_normalized(self):
        raw=fixture(outer=True,bulk=True)
        with self.assertRaisesRegex(ValueError,'compressed outer'):
            require_raw_envelope(raw)
        normalized,proof=normalize_package(raw,sha(raw),stored_decoder)
        self.assertEqual(require_raw_envelope(normalized)['outer_compression'],0)
        self.assertTrue(proof['changed'])
        self.assertEqual(normalize_package(normalized,sha(normalized),stored_decoder)[0],normalized)

    def test_raw_but_unaligned_is_not_delivery_ready(self):
        raw=fixture()
        self.assertNotEqual(len(raw)%32768,0)
        with self.assertRaisesRegex(ValueError,'aligned'):require_raw_envelope(raw)
        padded=raw+bytes(-len(raw)%32768)
        self.assertEqual(require_raw_envelope(padded)['alignment'],32768)
        self.assertEqual(padded[:len(raw)],raw)

    def test_unknown_profile_and_compression_bit_fail_closed(self):
        import struct
        raw=bytearray(fixture()+bytes(-len(fixture())%32768))
        struct.pack_into('>I',raw,4,447|(25<<16))
        with self.assertRaisesRegex(ValueError,'unsupported'):require_raw_envelope(bytes(raw))
        raw=bytearray(fixture()+bytes(-len(fixture())%32768))
        struct.pack_into('>I',raw,21,0x02000000)
        with self.assertRaisesRegex(ValueError,'compressed outer'):require_raw_envelope(bytes(raw))

    def test_inner_generated_stream_is_rejected_even_if_outer_is_raw_aligned(self):
        raw=fixture(bulk=True);raw+=bytes(-len(raw)%32768)
        with self.assertRaisesRegex(ValueError,'stored-LZX bulk'):require_raw_envelope(raw)
        fixed,_=normalize_package(raw,sha(raw),stored_decoder)
        require_raw_envelope(fixed)

    def test_exact_writer_recognizer_rejects_similar_or_truncated_streams(self):
        from tools.lzx_stored import wrap_ue3_chunk
        for size in (1,2,32767,32768,32769,131072,131073):
            raw=wrap_ue3_chunk(b'x'*size)
            self.assertTrue(generated_stored_chunk(raw))
            self.assertFalse(generated_stored_chunk(raw[:-1]))
            self.assertFalse(generated_stored_chunk(raw+b'\0'))
        raw=bytearray(wrap_ue3_chunk(b'abc'));raw[24+5+4]=2
        self.assertFalse(generated_stored_chunk(bytes(raw)))

    def test_resource_gate_fails_even_when_every_declared_hash_matches(self):
        import json,tempfile
        from tools.verify_resource_phase import inspect
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);packet=root/'packet';name='Game/example.xxx'
            original=fixture();candidate=fixture(outer=True,bulk=True)
            row=dict(path=name);members={}
            for phase,data,key in [('controls',original,'original'),('raw-controls',original,'raw'),('candidate',candidate,'candidate')]:
                path=packet/phase/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                members[phase+'/'+name]=sha(data);row[key+'_sha256']=sha(data);row[key+'_size']=len(data)
            m=dict(schema_version=1,kind='offline-disc-locale-raw-comparison',deployment_performed=False,
                   game_rendering_verified=False,raw_package_outputs=True,resources=[row],member_sha256=members,
                   disc=1,raw_control_method='source-derived-uncompressed-fonts-original-text-disc-toc',
                   unknown_control_syntax_resolved=False,composition_manifest_sha256='1'*64,
                   comparison_plan_canonical_sha256='2'*64)
            manifest=json.dumps(m).encode();(packet/'manifest.json').write_bytes(manifest)
            basic,_=inspect(packet,sha(manifest),packet/'candidate','candidate')
            self.assertTrue(basic['all_resources_match'])
            guarded,_=inspect(packet,sha(manifest),packet/'candidate','candidate',runtime_envelope=True)
            self.assertTrue(guarded['all_resources_match'])
            self.assertFalse(guarded['all_runtime_envelopes_match'])
            self.assertEqual(guarded['runtime_envelope_checked'],1)
            candidate=b'BAD!'+candidate[4:]
            (packet/'candidate'/name).write_bytes(candidate)
            row['candidate_sha256']=sha(candidate);members['candidate/'+name]=sha(candidate)
            manifest=json.dumps(m).encode();(packet/'manifest.json').write_bytes(manifest)
            guarded,_=inspect(packet,sha(manifest),packet/'candidate','candidate',runtime_envelope=True)
            self.assertTrue(guarded['all_resources_match'])
            self.assertFalse(guarded['all_runtime_envelopes_match'])
            self.assertEqual(guarded['runtime_envelope_checked'],1)


class EngineLocalTextureTests(unittest.TestCase):
    def test_local_texture_class_bulk_is_gated_and_normalized_without_reencoding(self):
        import struct
        from tools.ue3_package import parse_summary,parse_tables
        from test_runtime_package import texture
        data=bytearray(fixture(bulk=True))
        summary=parse_summary(data);tables=parse_tables(data,summary,len(data))
        matches=[i for i,entry in enumerate(tables['imports'])
                 if entry['path']=='Engine.Texture2D']
        self.assertEqual(len(matches),1)
        # The synthetic 446/25 import record is 28 bytes. An outer of zero
        # exposes the same local class spelling used by the real Engine.xxx.
        struct.pack_into('>i',data,summary['import_offset']+28*matches[0]+16,0)
        raw=bytes(data)+bytes(-len(data)%32768)
        self.assertEqual(parse_tables(raw,parse_summary(raw),len(raw))['exports'][1]['class_path'],
                         'Texture2D')
        tiles_before=texture(raw)[3]['tiles']
        with self.assertRaisesRegex(ValueError,'stored-LZX bulk'):
            require_raw_envelope(raw)
        normalized,proof=normalize_package(raw,sha(raw),stored_decoder)
        self.assertEqual(proof['converted_bulk_count'],1)
        self.assertTrue(proof['native_tiles_preserved'])
        self.assertEqual(texture(normalized)[3]['tiles'],tiles_before)
        self.assertEqual(require_raw_envelope(normalized)['outer_compression'],0)


if __name__ == '__main__':
    unittest.main()
