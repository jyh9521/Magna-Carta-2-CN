"""Synthetic build-planning checks; no compiler/network dependency in CI."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_lzx import (COMMIT, URL, build_path, validate_checkout,
                             obtain_checkout, quote_batch_path, msvc_batch,
                             posix_command, build)


class LzxBuildTests(unittest.TestCase):
    def test_pinned_identity(self):
        self.assertEqual(len(COMMIT), 40)
        self.assertEqual(URL, "https://github.com/kyz/libmspack.git")

    def test_build_path_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(build_path(root / "build/lzx/native", root), (root / "build/lzx/native").resolve())
            for bad in (root, root / "build", root / "foreign", root / "build/../../escape"):
                with self.subTest(path=bad), self.assertRaises(ValueError):
                    build_path(bad, root)

    def test_batch_path_metacharacters(self):
        for char in ('"', '%', '!', '&', '|', '<', '>', '^', '\r', '\n'):
            with self.subTest(char=char), self.assertRaises(ValueError):
                quote_batch_path(Path('root' + char + 'bad'))
        path = Path("root with space/file")
        self.assertEqual(quote_batch_path(path), '"' + str(path) + '"')

    def test_compiler_plans(self):
        source, bridge, output = Path('/source'), Path('/bridge.c'), Path('/output/library')
        plan = posix_command('test-cc', source, bridge, output)
        self.assertEqual(plan[0], 'test-cc')
        self.assertIn(str(source / 'lzxd.c'), plan)
        self.assertNotIn('shell', plan)
        script = msvc_batch(Path('/vcvars64.bat'), source, bridge, output)
        self.assertIn('chcp 65001', script)
        self.assertIn('if errorlevel 1 exit /b 1', script)
        self.assertIn('/LD /O2', script)
        self.assertIn('/OUT:', script)

    def checkout_fixture(self, root):
        (root / '.git').mkdir()
        source = root / 'libmspack/mspack'
        source.mkdir(parents=True)
        for name in ('lzxd.c', 'lzx.h', 'mspack.h'):
            (source / name).write_text('fixture', encoding='utf-8')
        return source

    def test_readonly_checkout_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.checkout_fixture(root)
            with patch('tools.build_lzx.command', side_effect=[URL, COMMIT, '']) as run:
                self.assertEqual(validate_checkout(root), source)
                self.assertEqual(run.call_count, 3)
                self.assertFalse(any(x in str(run.call_args_list) for x in ('checkout', 'reset', 'fetch')))
            for values, message in ((['wrong'], 'origin'), ([URL, 'wrong'], 'commit'),
                                    ([URL, COMMIT, ' M lzxd.c'], 'modified')):
                with self.subTest(message=message), patch('tools.build_lzx.command', side_effect=values):
                    with self.assertRaisesRegex(ValueError, message):
                        obtain_checkout(root)

    def test_foreign_directory_rejected_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / 'do-not-touch'
            marker.write_text('original')
            with patch('tools.build_lzx.command') as run, self.assertRaisesRegex(ValueError, 'not a Git'):
                obtain_checkout(root)
            run.assert_not_called()
            self.assertEqual(marker.read_text(), 'original')
            self.assertEqual(list(root.iterdir()), [marker])

    def test_existing_output_rejected_before_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('tools.build_lzx.build_path', return_value=Path(temp)), patch('tools.build_lzx.obtain_checkout') as obtain:
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    build(Path(temp))
                obtain.assert_not_called()

    def test_missing_sources_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.checkout_fixture(root)
            (root / 'libmspack/mspack/lzx.h').unlink()
            with patch('tools.build_lzx.command', side_effect=[URL, COMMIT, '']):
                with self.assertRaisesRegex(ValueError, 'missing'):
                    validate_checkout(root)
