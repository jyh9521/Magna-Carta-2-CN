"""Optional DLC preflight and launch rechecks, using mocked process creation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools.launch_xenia import main, prepare, launch


REL = "0000000000000000/4E4D0811/00000002/" + "A" * 40
DATA = b"synthetic DLC"


class ContentLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.exe = self.root / "emulator.exe"
        self.exe.write_bytes(b"synthetic exe")
        self.game = self.root / "game" / "default.xex"
        self.game.parent.mkdir()
        self.game.write_bytes(b"synthetic game")
        self.config = self.root / "config.toml"
        self.config.write_bytes(b'[Content]\nlicense_mask=0\n')
        self.run = self.root / "run"
        self.bundle = self.root / "bundle"
        target = self.bundle / "files" / REL
        target.parent.mkdir(parents=True)
        target.write_bytes(DATA)
        self.manifest = dict(schema_version=1, kind="xenia-content-bundle", title_id="4E4D0811",
            files=[dict(path=REL, size=len(DATA), sha256=hashlib.sha256(DATA).hexdigest())])
        raw = json.dumps(self.manifest).encode()
        (self.bundle / "manifest.json").write_bytes(raw)
        self.sha = hashlib.sha256(raw).hexdigest()

    def prepare(self, **kwargs):
        return prepare(self.exe, self.config, self.game, self.run,
                       content_bundle=self.bundle, content_manifest_sha256=self.sha, **kwargs)

    def test_default_remains_content_free_and_same_command(self):
        record = prepare(self.exe, self.config, self.game, self.run)
        self.assertNotIn("content_bundle", record)
        self.assertFalse((self.run / "content").exists())
        self.assertEqual(len(record["command"]), 7)

    def test_optional_bundle_copied_and_checked_before_mock_launch(self):
        original = self.config.read_bytes()
        record = self.prepare()
        self.assertEqual((self.run / "content" / REL).read_bytes(), DATA)
        self.assertFalse(record["content_bundle"]["profiles_copied"])
        self.assertFalse(record["content_bundle"]["saves_copied"])
        self.assertEqual(self.config.read_bytes(), original)
        self.assertEqual(len(record["command"]), 7)
        with patch("tools.launch_xenia.subprocess.Popen", return_value=Mock(pid=321)) as popen:
            launch(self.run, record)
        popen.assert_called_once()
        self.assertEqual(record["status"], "started")

    def test_preflight_failure_leaves_no_run(self):
        (self.bundle / "files" / REL).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.run.exists())

    def test_missing_option_partner_leaves_no_run(self):
        for kwargs in ({"content_bundle": self.bundle}, {"content_manifest_sha256": self.sha}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, "supplied together"):
                prepare(self.exe, self.config, self.game, self.run, **kwargs)
            self.assertFalse(self.run.exists())

    def test_run_cannot_be_inside_bundle(self):
        self.run = self.bundle / "new-run"
        with self.assertRaisesRegex(ValueError, "outside content bundle"):
            self.prepare()
        self.assertFalse(self.run.exists())

    def test_changed_source_prevents_launch(self):
        record = self.prepare()
        (self.bundle / "files" / REL).write_bytes(b"changed")
        with patch("tools.launch_xenia.subprocess.Popen") as popen:
            with self.assertRaises(ValueError):
                launch(self.run, record)
            popen.assert_not_called()

    def test_changed_installed_content_prevents_launch(self):
        record = self.prepare()
        (self.run / "content" / REL).write_bytes(b"changed")
        with patch("tools.launch_xenia.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "installed content file changed"):
                launch(self.run, record)
            popen.assert_not_called()

    def test_unknown_installed_content_prevents_launch(self):
        record = self.prepare()
        (self.run / "content" / "unexpected").write_bytes(b"do not launch")
        with patch("tools.launch_xenia.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                launch(self.run, record)
            popen.assert_not_called()

    def test_changed_record_prevents_launch(self):
        record = self.prepare()
        record["content_bundle"]["files"] = {}
        with patch("tools.launch_xenia.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "run record changed"):
                launch(self.run, record)
            popen.assert_not_called()

    def test_changed_content_command_root_prevents_launch(self):
        record = self.prepare()
        record["command"] = [arg if not arg.startswith("--content_root=") else
                             "--content_root=C:/unrelated-saves" for arg in record["command"]]
        with patch("tools.launch_xenia.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "command root changed"):
                launch(self.run, record)
            popen.assert_not_called()

    def test_cli_optional_prepare_and_verify_conflict(self):
        args = ["--exe", str(self.exe), "--config", str(self.config), "--game", str(self.game),
                "--run-dir", str(self.run), "--content-bundle", str(self.bundle),
                "--content-manifest-sha256", self.sha]
        self.assertEqual(main(args), 0)
        self.assertTrue((self.run / "content" / REL).is_file())
        self.assertEqual(main(["--verify", str(self.run), "--content-bundle", str(self.bundle)]), 1)


if __name__ == "__main__":
    unittest.main()
