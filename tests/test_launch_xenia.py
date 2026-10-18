"""Synthetic config-preservation tests; no emulator or game required."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from launch_xenia import prepare, launch, verify_config, main


CONFIG = b'[GPU]\r\ngpu = "vulkan" # user setting\r\n[HID]\r\nkeyboard_mode = 0\r\n'


class ConfigLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Hosted Windows TEMP can use an 8.3 alias (RUNNER~1). The launcher
        # deliberately canonicalizes paths; compare canonical paths too.
        self.root = Path(self.temp.name).resolve()
        self.exe = self.root / "emulator space" / "emulator.exe"
        self.exe.parent.mkdir()
        self.exe.write_bytes(b"synthetic executable")
        self.config = self.exe.parent / "user.config.toml"
        self.config.write_bytes(CONFIG)
        self.game = self.root / "game" / "default.xex"
        self.game.parent.mkdir()
        self.game.write_bytes(b"synthetic game")
        self.run = self.root / "experiment space"

    def prepare(self, **kwargs):
        return prepare(self.exe, self.config, self.game, self.run, **kwargs)

    def log(self, value=CONFIG):
        (self.run / "runtime.log").write_bytes(
            b"i> 123 ----------- CONFIG DUMP -----------\n" + value +
            b"\n----------- END OF CONFIG DUMP ----\n")

    def test_snapshot_byte_identity_and_no_tuning_overrides(self):
        record = self.prepare()
        self.assertEqual(Path(record["config_snapshot"]).read_bytes(), CONFIG)
        self.assertEqual(self.config.read_bytes(), CONFIG)
        self.assertEqual(record["tuning_overrides"], [])
        self.assertFalse(record["game_rendering_verified"])
        self.assertEqual(len(record["command"]), 7)
        self.assertEqual(record["command"][2], f"--config={self.run / 'config.snapshot.toml'}")
        self.assertNotIn('--gpu=', ' '.join(record['command']))
        self.assertNotIn('--keyboard_mode=', ' '.join(record['command']))

    def test_expected_hash(self):
        self.prepare(expected_config=hashlib.sha256(CONFIG).hexdigest())

    def test_wrong_hash_has_no_output(self):
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            self.prepare(expected_config='0' * 64)
        self.assertFalse(self.run.exists())

    def test_invalid_toml_has_no_output(self):
        self.config.write_text('[broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.run.exists())

    def test_missing_input(self):
        self.exe.unlink()
        with self.assertRaisesRegex(ValueError, 'missing input'):
            self.prepare()

    def test_existing_run_refused(self):
        self.run.mkdir()
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_game_tree_is_not_run_directory(self):
        for p in (self.game.parent, self.game.parent / 'child'):
            with self.subTest(p=p), self.assertRaisesRegex(ValueError, 'outside game tree'):
                prepare(self.exe, self.config, self.game, p)

    def test_launch_array_cwd_pid_and_inputs_retained(self):
        record = self.prepare()
        with patch('launch_xenia.subprocess.Popen', return_value=Mock(pid=123)) as popen:
            launch(self.run, record)
        popen.assert_called_once_with(record['command'], cwd=str(self.exe.parent))
        self.assertEqual(record['pid'], 123)
        self.assertEqual(record['status'], 'started')
        self.assertEqual(self.config.read_bytes(), CONFIG)
        with self.assertRaisesRegex(ValueError, 'not prepared'):
            launch(self.run, record)

    def test_config_changed_before_launch(self):
        record = self.prepare()
        self.config.write_bytes(CONFIG + b'\n')
        with patch('launch_xenia.subprocess.Popen') as popen:
            with self.assertRaisesRegex(ValueError, 'config changed'):
                launch(self.run, record)
            popen.assert_not_called()

    def test_executable_changed_before_launch(self):
        record = self.prepare()
        self.exe.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'input changed'):
            launch(self.run, record)

    def test_config_dump_semantic_identity(self):
        self.prepare()
        self.log(b'[GPU]\ngpu="vulkan"\n[HID]\nkeyboard_mode=0\n')
        result = verify_config(self.run)
        self.assertEqual(result['status'], 'config-dump-matches')
        self.assertFalse(result['game_rendering_verified'])

    def test_mismatched_dump(self):
        self.prepare()
        self.log(CONFIG.replace(b'vulkan', b'd3d12'))
        with self.assertRaisesRegex(ValueError, 'differs'):
            verify_config(self.run)

    def test_missing_multiple_and_incomplete_dump(self):
        self.prepare()
        for value in (b'', b'----------- CONFIG DUMP -----------',
                      b'----------- CONFIG DUMP -----------' * 2):
            (self.run / 'runtime.log').write_bytes(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_config(self.run)

    def test_mutated_snapshot_fails_verification(self):
        record = self.prepare()
        self.log()
        Path(record['config_snapshot']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'config changed'):
            verify_config(self.run)

    def test_cli_prepare_and_verify(self):
        self.assertEqual(main(['--exe', str(self.exe), '--config', str(self.config),
                               '--game', str(self.game), '--run-dir', str(self.run)]), 0)
        self.log()
        self.assertEqual(main(['--verify', str(self.run)]), 0)
        self.assertEqual(main(['--verify', str(self.run), '--launch']), 1)
        self.assertEqual(main([]), 1)


if __name__ == '__main__':
    unittest.main()
