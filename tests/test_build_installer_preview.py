"""Source-only preview packaging must never overwrite the production installer."""
from pathlib import Path
import tempfile
import unittest

from tools.build_installer_preview import prepare_runner, replace_once, sha, stage_sources


class PreviewBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def test_source_copy_is_independent_and_existing_destination_is_rejected(self):
        source = self.write('src/installer/lib/main.dart', 'original entry\n')
        entry = self.write('src/installer/lib/expressive_preview.dart', 'preview entry\n')
        names = ['src/installer/lib/main.dart', 'src/installer/lib/expressive_preview.dart']
        destination = self.root / 'work/project'
        inventory = stage_sources(self.root, destination, names)
        self.assertEqual(inventory[names[0]], sha(source))
        self.assertEqual(inventory[names[1]], sha(entry))
        (destination / 'lib/main.dart').write_text('copy only', encoding='utf-8')
        self.assertEqual(source.read_text(encoding='utf-8'), 'original entry\n')
        with self.assertRaises(ValueError):
            stage_sources(self.root, destination, names)

    def test_source_inventory_rejects_escape_before_creating_destination(self):
        for name in ['src/installer/../../secret', '/src/installer/main.dart',
                     'src\\installer\\main.dart', 'src/installer/C:/bad', 'dist/original.exe']:
            destination = self.root / 'rejected'
            with self.subTest(name=name), self.assertRaises(ValueError):
                stage_sources(self.root, destination, [name])
            self.assertFalse(destination.exists())

    def test_runner_rewrites_only_staged_metadata(self):
        base = 'src/installer/'
        self.write(base + 'windows/CMakeLists.txt', 'set(BINARY_NAME "MC2Installer")\n')
        self.write(base + 'windows/runner/main.cpp',
                   'Win32Window::Size size(1080, 870);\nL"《真名法典2》简体中文汉化补丁"\n')
        self.write(base + 'windows/runner/Runner.rc',
                   '"v1.0" "MC2Installer.exe" "《真名法典2》简体中文汉化补丁"\n')
        names = [p.relative_to(self.root).as_posix() for p in (self.root / base).rglob('*') if p.is_file()]
        destination = self.root / 'stage'
        inventory = stage_sources(self.root, destination, names)
        prepare_runner(destination)
        self.assertIn('MC2ExpressivePreview', (destination / 'windows/CMakeLists.txt').read_text())
        self.assertIn('0.1.0-preview', (destination / 'windows/runner/Runner.rc').read_text(encoding='utf-8'))
        for name, digest in inventory.items():
            self.assertEqual(sha(self.root / name), digest)

    def test_unknown_runner_source_is_not_silently_patched(self):
        path = self.write('unexpected.txt', 'unknown content')
        with self.assertRaises(ValueError):
            replace_once(path, 'expected', 'replacement')
        self.assertEqual(path.read_text(), 'unknown content')

    def test_duplicate_match_is_rejected_without_write(self):
        path = self.write('duplicate.txt', 'expected expected')
        with self.assertRaises(ValueError):
            replace_once(path, 'expected', 'replacement')
        self.assertEqual(path.read_text(), 'expected expected')


if __name__ == '__main__':
    unittest.main()
