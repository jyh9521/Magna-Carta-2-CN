"""End-to-end synthetic probe packets, no game, decoder DLL or font asset."""
import json
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import test_locale_candidate as fixtures
from test_supplement_font import stored_decoder
from tools import build_font_route_probe as route


class RouteProbeTests(unittest.TestCase):
    def fixture(self,root):
        game,_,old=fixtures.CandidateAssemblyTests().fixture(root)
        p=dict(schema_version=1,kind='offline-font-route-probe',game_rendering_verified=False,font_plans=[old['font_plan']],
            text_plan=old['text_plan'],text_resource=old['text_resource'],expected_text_sha256=old['expected_text_sha256'])
        return game,root/'font.bin',p

    def run_build(self,root,game,font,p):
        with patch.object(route,'rasterize_plan',return_value=({0x6587:bytes([255])*576},[])):
            return route.build(p,game,root,font,root/'packet',stored_decoder)

    def verify(self,root,font,p):
        with patch.object(route,'rasterize_plan',return_value=({0x6587:bytes([255])*576},[])):
            return route.verify(p,root/'packet',root,font,stored_decoder)

    def test_packet_replay_exact_and_originals_restored(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,p=self.fixture(root);r=self.run_build(root,game,font,p);self.assertEqual(self.verify(root,font,p),r)
            self.assertEqual((r['font_object_count'],len(r['resources'])),(3,5));self.assertFalse(r['deployment_performed'])
            for row in r['resources']:self.assertEqual((root/'packet/rollback-check'/row['path']).read_bytes(),(game/row['path']).read_bytes())

    def test_corrupted_candidate_and_extra_file_rejected(self):
        for extra in [False,True]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);game,font,p=self.fixture(root);r=self.run_build(root,game,font,p)
                path=root/'packet'/('unexpected' if extra else 'candidate/'+r['resources'][0]['path']);path.write_bytes(b'changed')
                with self.assertRaises(ValueError):self.verify(root,font,p)

    def test_duplicate_family_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,p=self.fixture(root);p['font_plans']*=2
            with self.assertRaisesRegex(ValueError,'duplicate font route family'):self.run_build(root,game,font,p)
            self.assertFalse((root/'packet').exists())

    def test_source_and_raster_hash_rejected_before_publication(self):
        for path in ['font.bin','original/Game/one.xxx']:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);game,font,p=self.fixture(root);(root/path).write_bytes(b'changed')
                with self.assertRaises(ValueError):self.run_build(root,game,font,p)
                self.assertFalse((root/'packet').exists())

    def test_wrong_text_hash_and_family_scope_rejected(self):
        for change in [lambda p:p.update(expected_text_sha256='0'*64),lambda p:p.update(font_plans=[])]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);game,font,p=self.fixture(root);change(p)
                with self.assertRaises(ValueError):self.run_build(root,game,font,p)
                self.assertFalse((root/'packet').exists())

    def test_existing_output_and_original_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,p=self.fixture(root);self.run_build(root,game,font,p)
            with self.assertRaisesRegex(ValueError,'new and outside'):self.run_build(root,game,font,p)
            with self.assertRaisesRegex(ValueError,'new and outside'):route.build(p,game,root,font,game/'new',stored_decoder)

    def test_manifest_cannot_lie_about_rendering(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,p=self.fixture(root);self.run_build(root,game,font,p);manifest=root/'packet/manifest.json';r=json.loads(manifest.read_bytes());r['game_rendering_verified']=True;manifest.write_bytes(route.encoded(r))
            with self.assertRaisesRegex(ValueError,'replay mismatch'):self.verify(root,font,p)

    def test_raw_controls_have_separate_toc_and_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,p=self.fixture(root);p['raw_packages']=True
            # The older stored-frame fixture omitted the package compression bit;
            # add it explicitly, without weakening the production decoder guard.
            fp=json.loads((root/'font-plan.json').read_bytes())
            for source in fp['sources']:
                path=game/source['path'];raw=bytearray(path.read_bytes());summary=route.parse_summary(raw,len(raw))
                if summary['compression_flags']:
                    struct.pack_into('>I',raw,21,0x02000000);path.write_bytes(raw);source['sha256']=route.digest(raw)
            encoded=route.encoded(fp);(root/'font-plan.json').write_bytes(encoded);p['font_plans'][0]['sha256']=route.digest(encoded)
            r=self.run_build(root,game,font,p)
            self.assertTrue(r['raw_package_outputs']);self.assertEqual(self.verify(root,font,p),r)
            for row in r['resources']:
                relative=row['path'];raw=(root/'packet/raw-controls'/relative).read_bytes()
                if relative.endswith('.xxx'):self.assertEqual(route.parse_summary(raw,len(raw))['compression_flags'],0)
            self.assertNotEqual((root/'packet/raw-controls/Xbox360TOC.txt').read_bytes(),(root/'packet/candidate/Xbox360TOC.txt').read_bytes())

    def test_raw_flag_does_not_accept_integer_boolean(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,p=self.fixture(root);p['raw_packages']=1
            with self.assertRaisesRegex(ValueError,'explicit boolean'):self.run_build(root,game,font,p)


if __name__=='__main__':unittest.main()
