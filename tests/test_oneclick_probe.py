"""Prepare synthetic complete resource trees; never run CMD/Xenia/game code."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_resource_phase import Fixture
from tools import prepare_oneclick_probe as ready


class OneclickTests(unittest.TestCase):
    def fixture(self,root):
        f=Fixture(root)
        for row in f.manifest['resources']:(f.game/row['path']).write_bytes(f.data['controls',row['path']])
        (f.game/'default.xex').write_bytes(b'synthetic original game, never execute')
        (f.game/'movie.bin').write_bytes(b'unmodified shared-format asset')
        (f.game/'empty').mkdir();project=root/'project';(project/'tools').mkdir(parents=True)
        for name in ['launch_xenia.py','verify_resource_phase.py']:(project/'tools'/name).write_bytes(b'# fixture dependency, not executable test logic')
        exe=root/'emulator.exe';exe.write_bytes(b'fixture, never execute');config=root/'user.toml';config.write_bytes(b'[GPU]\ngpu="d3d12"\n')
        return f,project,exe,config,root/'prepared'

    def run_prepare(self,f,project,exe,config,out):
        return ready.prepare(f.game,f.packet,f.hash,ready.digest(f.game/'default.xex'),exe,config,out,project)

    def test_two_full_independent_copies_and_clickable_text(self):
        with tempfile.TemporaryDirectory() as d:
            f,p,e,c,out=self.fixture(Path(d));before=c.read_bytes();r=self.run_prepare(f,p,e,c,out)
            self.assertFalse(r['game_started']);self.assertFalse(r['game_rendering_verified']);self.assertTrue(r['full_independent_copies'])
            for phase in ['candidate','raw-controls']:
                for row in f.manifest['resources']:self.assertEqual((out/phase/row['path']).read_bytes(),f.data[phase,row['path']])
                self.assertEqual((out/phase/'movie.bin').read_bytes(),b'unmodified shared-format asset');self.assertTrue((out/phase/'empty').is_dir())
                self.assertFalse((out/phase/'movie.bin').samefile(f.game/'movie.bin'))
            self.assertEqual(c.read_bytes(),before);self.assertEqual(json.loads((out/'PREPARED.json').read_bytes()),r)
            cmd=(out/'开始中文测试.cmd').read_text(encoding='utf8');self.assertIn('--launch',cmd);self.assertIn('if errorlevel 1 goto failed',cmd)
            self.assertIn('--config-sha256',cmd);self.assertIn('--phase candidate',cmd)

    def test_writing_prepared_copy_cannot_change_original(self):
        with tempfile.TemporaryDirectory() as d:
            f,p,e,c,out=self.fixture(Path(d));self.run_prepare(f,p,e,c,out);(out/'candidate/movie.bin').write_bytes(b'user edits test copy')
            self.assertEqual((f.game/'movie.bin').read_bytes(),b'unmodified shared-format asset')

    def test_output_existing_source_child_and_packet_child_reject(self):
        with tempfile.TemporaryDirectory() as d:
            f,p,e,c,out=self.fixture(Path(d))
            for target in [f.game,f.game/'child',f.packet/'child']:
                with self.assertRaisesRegex(ValueError,'new and disjoint'):self.run_prepare(f,p,e,c,target)

    def test_wrong_game_and_manifest_hash_reject_before_copy(self):
        with tempfile.TemporaryDirectory() as d:
            f,p,e,c,out=self.fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'default.xex SHA256'):ready.prepare(f.game,f.packet,f.hash,'0'*64,e,c,out,p)
            f.hash='0'*64
            with self.assertRaisesRegex(ValueError,'manifest SHA256'):self.run_prepare(f,p,e,c,out)
            self.assertFalse(out.exists())

    def test_modified_original_or_packet_resource_reject(self):
        for target in ['game','packet']:
            with tempfile.TemporaryDirectory() as d:
                f,p,e,c,out=self.fixture(Path(d));path=f.game/'Game/A.dat' if target=='game' else f.packet/'candidate/Game/A.dat';path.write_bytes(b'changed')
                with self.assertRaises(ValueError):self.run_prepare(f,p,e,c,out)
                self.assertFalse(out.exists())

    def test_insufficient_space_rejects_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            f,p,e,c,out=self.fixture(Path(d))
            with patch.object(ready.shutil,'disk_usage',return_value=type('Usage',(),{'free':0})()),self.assertRaisesRegex(ValueError,'insufficient free'):self.run_prepare(f,p,e,c,out)
            self.assertFalse(out.exists())

    def test_source_mutation_does_not_publish_launchers(self):
        with tempfile.TemporaryDirectory() as d:
            f,p,e,c,out=self.fixture(Path(d));copy=ready.shutil.copyfile
            def changed(a,b):
                result=copy(a,b);(f.game/'movie.bin').write_bytes(b'mutated');return result
            with patch.object(ready.shutil,'copyfile',side_effect=changed),self.assertRaisesRegex(ValueError,'source changed|copied game member hash mismatch'):self.run_prepare(f,p,e,c,out)
            self.assertFalse((out/'开始中文测试.cmd').exists())

    def test_cmd_quotes_spaces_unicode_and_rejects_expansion(self):
        raw=ready.launcher(Path('C:/some space/python.exe'),Path('C:/工程'),Path('C:/packet'),'1'*64,Path('C:/emu.exe'),Path('C:/user.toml'),'2'*64,'candidate')
        self.assertIn(ready.quote(Path('C:/some space/python.exe')),raw.decode());self.assertIn('DisableDelayedExpansion',raw.decode())
        for path in ['C:/bad%PATH%','C:/bad"quote','bad\npath']:
            with self.assertRaises(ValueError):ready.quote(path)


if __name__=='__main__':unittest.main()
