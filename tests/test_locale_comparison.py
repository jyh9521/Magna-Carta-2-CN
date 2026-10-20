"""Self-authored raw package and phase-inspector contracts; no game data."""
import struct
from pathlib import Path
import tempfile
import unittest
from tools.build_locale_comparison import raw_phase,prepare,KIND
from tools import verify_resource_phase as phase
from test_resource_phase import Fixture
from test_supplement_font import package_fixture,stored_decoder


def inputs():
    a=bytearray(package_fixture(compressed=True));struct.pack_into('>I',a,21,0x0288000d);a=bytes(a);b=package_fixture()
    toc=f'{len(a)} 7 8 ../Game/a.xxx 0\r\n{len(b)} 9 10 ../Game/b.xxx 0\r\n0 0 17 ../Game/TOC.txt 0\r\n'.encode()
    return {'Game/a.xxx':a,'Game/b.xxx':b,'Game/TOC.txt':toc,'Movies/d1.txt':b'original subtitles',
            'Game/INT':b'original INT'},['Game/a.xxx','Game/b.xxx'],'Game/TOC.txt'


def comparison(f):
    f.manifest.update(kind=KIND,disc=1,composition_manifest_sha256='1'*64,
        comparison_plan_canonical_sha256='2'*64,unknown_control_syntax_resolved=False,
        raw_control_method='source-derived-uncompressed-fonts-original-text-disc-toc')
    for r in f.manifest['resources']:
        p=r['path'];r.update(raw_sha256=f.manifest['member_sha256']['raw-controls/'+p],raw_size=len(f.data['raw-controls',p]))
    f.refresh();return f


class LocaleComparisonTests(unittest.TestCase):
    def test_raw_text_unchanged_and_source_not_mutated(self):
        o,fonts,toc=inputs();before=dict(o);raw,r=raw_phase(o,fonts,toc,stored_decoder)
        self.assertEqual(o,before);self.assertEqual(raw['Movies/d1.txt'],o['Movies/d1.txt'])
        self.assertEqual(raw['Game/INT'],o['Game/INT']);self.assertNotEqual(raw['Game/a.xxx'],o['Game/a.xxx'])
        self.assertEqual(raw['Game/b.xxx'],o['Game/b.xxx']);self.assertEqual(len(r['toc_changes']),1)
        self.assertTrue(r['toc']['inverse_byte_identical']);self.assertIn(b'0 0 17 ../Game/TOC.txt 0\r\n',raw[toc])
        self.assertTrue(all(p['logical_payload_preserved'] for p in r['font_packages']))

    def test_raw_roles_reject_foreign_or_toc_fonts(self):
        o,fonts,toc=inputs()
        for bad in [[],fonts+fonts,[toc],['missing']]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):raw_phase(o,bad,toc,stored_decoder)

    def test_case_alias_and_traversal_rejected(self):
        o,fonts,toc=inputs()
        for path in ['game/INT','../escape','Game/bad.']:
            bad=dict(o);bad[path]=b'x'
            with self.subTest(path=path),self.assertRaises(ValueError):raw_phase(bad,fonts,toc,stored_decoder)

    def test_raw_inventory_bounded(self):
        for o in [{},{str(i):b'x' for i in range(33)}]:
            with self.assertRaisesRegex(ValueError,'count'):raw_phase(o,[],'toc')

    def test_toc_source_size_mismatch_rejected(self):
        o,f,toc=inputs();o[toc]=o[toc].replace(str(len(o[f[0]])).encode(),b'1',1)
        with self.assertRaises(ValueError):raw_phase(o,f,toc,stored_decoder)

    def test_bad_package_not_silently_passthrough(self):
        o,f,toc=inputs();o[f[0]]=b'bad'
        with self.assertRaises(ValueError):raw_phase(o,f,toc,stored_decoder)

    def test_invalid_plan_stops_before_inputs(self):
        for k,v in [('schema_version',True),('kind','offline-font-route-probe'),('game_rendering_verified',True)]:
            p=dict(schema_version=1,kind=KIND,game_rendering_verified=False);p[k]=v
            with self.subTest(k=k),self.assertRaisesRegex(ValueError,'comparison plan'):prepare(p,'.')

    def test_comparison_all_three_phase_checks_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            f=comparison(Fixture(Path(d)))
            for kind in phase.PHASES:
                for r in f.manifest['resources']:(f.game/r['path']).write_bytes(f.data[kind,r['path']])
                r=f.run(kind);self.assertTrue(r['all_resources_match']);self.assertFalse(r['game_started'])

    def test_raw_size_and_hash_contract_rejected(self):
        for key,val in [('raw_size',True),('raw_size',1),('raw_sha256','0'*64)]:
            with tempfile.TemporaryDirectory() as d:
                f=comparison(Fixture(Path(d)));f.manifest['resources'][0][key]=val;f.refresh()
                with self.assertRaisesRegex(ValueError,'row/member'):f.run('raw-controls')

    def test_unadapted_composition_kind_stays_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=comparison(Fixture(Path(d)));f.manifest['kind']='offline-disc-locale-composition';f.refresh()
            with self.assertRaisesRegex(ValueError,'unsupported'):f.run()

    def test_new_contract_requires_disc_raw_and_unverified_state(self):
        for key,val in [('disc',True),('disc',3),('raw_package_outputs',False),('unknown_control_syntax_resolved',True),
                        ('raw_control_method','translated-fonts'),('composition_manifest_sha256','bad')]:
            with tempfile.TemporaryDirectory() as d:
                f=comparison(Fixture(Path(d)));f.manifest[key]=val;f.refresh()
                with self.subTest(key=key),self.assertRaises(ValueError):f.run()

    def test_unchanged_legacy_packet_still_accepted(self):
        with tempfile.TemporaryDirectory() as d:self.assertTrue(Fixture(Path(d)).run()['all_resources_match'])

    def test_wrong_trusted_manifest_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=comparison(Fixture(Path(d)))
            with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):phase.inspect(f.packet,'0'*64,f.game,'candidate')
