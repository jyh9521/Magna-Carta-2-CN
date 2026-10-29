"""Push gating, clean-source identity and the shared validation contract."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools import ci_preflight as preflight, validate_ci
from tools.run_test_suite import aliased_temporary_directories

ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')

    def git(self, *args):
        return preflight.git(self.repo, *args).decode().strip()

    def commit(self):
        self.git('add', '--all')
        self.git('commit', '-q', '-m', 'Fixture')
        return self.git('rev-parse', 'HEAD')

    def test_export_uses_commit_not_ignored_or_unstaged_files(self):
        self.git('config', 'core.autocrlf', 'true')
        (self.repo / '.gitignore').write_text('build/\n')
        (self.repo / 'sample.txt').write_bytes(b'committed')
        revision = self.commit()
        (self.repo / 'sample.txt').write_bytes(b'unstaged')
        (self.repo / 'build').mkdir()
        (self.repo / 'build/private.bin').write_bytes(b'not a source dependency')
        (self.repo / 'untracked.txt').write_bytes(b'untracked')
        before = self.git('status', '--porcelain')
        snapshot = self.root / 'snapshot'
        commit, hashes = preflight.export_revision(self.repo, revision, snapshot)
        self.assertEqual(commit, revision)
        self.assertEqual((snapshot / 'sample.txt').read_bytes(), b'committed')
        self.assertEqual(hashes['sample.txt'], hashlib.sha256(b'committed').hexdigest())
        self.assertFalse((snapshot / 'build').exists())
        self.assertFalse((snapshot / 'untracked.txt').exists())
        self.assertEqual(self.git('status', '--porcelain'), before)

    def test_export_rejects_attributes_that_hide_committed_inputs(self):
        (self.repo / '.gitattributes').write_text('hidden.txt export-ignore\n')
        (self.repo / 'hidden.txt').write_text('must be tested')
        revision = self.commit()
        with self.assertRaisesRegex(ValueError, 'committed file inventory'):
            preflight.export_revision(self.repo, revision, self.root / 'snapshot')

    def test_archive_traversal_and_links_are_rejected(self):
        for i, name in enumerate(('../outside.txt', '/outside.txt', 'C:/outside.txt', 'a\\b', '.git/config', 'link')):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w') as archive:
                item = tarfile.TarInfo(name)
                if name == 'link':
                    item.type = tarfile.SYMTYPE
                    item.linkname = '../outside'
                archive.addfile(item)
            with self.subTest(name=name), self.assertRaises(ValueError):
                preflight.extract_source(stream.getvalue(), self.root / f'bad-{i}')

    def test_foreign_git_and_python_environment_are_not_inherited(self):
        with patch.dict(os.environ, {'GIT_DIR': str(self.repo / '.git'),
                                    'GIT_INDEX_FILE': str(self.root / 'foreign-index'),
                                    'PYTHONPATH': 'developer-packages', 'PYTHONHOME': 'private-python'}):
            env = preflight.isolated_environment()
        for key in ('GIT_DIR', 'GIT_INDEX_FILE', 'PYTHONPATH', 'PYTHONHOME'):
            self.assertNotIn(key, env)
        self.assertEqual(env['PYTHONNOUSERSITE'], '1')

    def hook_source(self):
        directory = self.repo / '.githooks'
        directory.mkdir()
        (directory / 'pre-push').write_bytes((ROOT / '.githooks/pre-push').read_bytes())

    def test_hook_install_is_idempotent_and_preserves_other_hooks(self):
        self.hook_source()
        hook = preflight.install_hook(self.repo)
        self.assertEqual(preflight.install_hook(self.repo), hook)
        hook.write_bytes(b'#!/bin/sh\nexit 7\n')
        with self.assertRaisesRegex(ValueError, 'existing pre-push'):
            preflight.install_hook(self.repo)
        self.assertEqual(hook.read_bytes(), b'#!/bin/sh\nexit 7\n')

    def test_custom_hooks_path_is_preserved(self):
        self.hook_source()
        self.git('config', 'core.hooksPath', '.custom-hooks')
        with self.assertRaisesRegex(ValueError, 'custom core.hooksPath'):
            preflight.install_hook(self.repo)
        self.assertEqual(self.git('config', '--get', 'core.hooksPath'), '.custom-hooks')

    def test_push_revisions_include_each_commit_once_and_skip_only_deletion(self):
        a, b, zero = 'a' * 40, 'b' * 40, '0' * 40
        lines = f'refs/heads/main {a} refs/heads/main {b}\nrefs/tags/v1 {a} refs/tags/v1 {zero}\n(delete) {zero} refs/heads/old {b}\n'
        self.assertEqual(preflight.pushed_revisions(lines), [a])
        self.assertEqual(preflight.pushed_revisions(''), [])
        with self.assertRaises(ValueError):
            preflight.pushed_revisions('refs/heads/main invalid')

    def test_real_push_blocks_committed_failure_even_with_uncommitted_fix(self):
        # A tiny local bare remote proves the actual hook, not a mocked push.
        # Empty requirements avoid dependency downloads in this canary fixture.
        self.hook_source()
        (self.repo / '.gitignore').write_text('build/\n')
        (self.repo / 'requirements-font.txt').write_text('')
        (self.repo / 'tools').mkdir()
        (self.repo / 'tools/ci_preflight.py').write_bytes((ROOT / 'tools/ci_preflight.py').read_bytes())
        validator = self.repo / 'tools/validate_ci.py'
        validator.write_text('raise SystemExit(1)\n')
        self.commit()
        remote = self.root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True, env=preflight.isolated_environment())
        self.git('remote', 'add', 'origin', str(remote))
        preflight.install_hook(self.repo)
        validator.write_text('raise SystemExit(0)\n')
        before = self.git('status', '--porcelain')
        env = preflight.isolated_environment()
        result = subprocess.run(['git', '-C', str(self.repo), 'push', 'origin', 'main'], env=env,
                                capture_output=True, text=True, encoding='utf-8', timeout=120)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('status=FAIL', result.stdout + result.stderr)
        self.assertEqual(self.git('status', '--porcelain'), before)
        remote_refs = preflight.git(remote, 'for-each-ref', '--format=%(objectname)')
        self.assertEqual(remote_refs.strip(), b'')
        good = self.commit()
        result = subprocess.run(['git', '-C', str(self.repo), 'push', 'origin', 'main'], env=env,
                                capture_output=True, text=True, encoding='utf-8', timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(preflight.git(remote, 'rev-parse', 'refs/heads/main').decode().strip(), good)


class SharedValidationTests(unittest.TestCase):
    def test_all_original_checks_and_both_temp_layouts_are_mandatory(self):
        commands = dict(validate_ci.validation_commands('python', 'reports'))
        self.assertEqual(set(commands), {'dependencies', 'repository', 'bytecode', 'glossary',
                                        'tests-native', 'tests-alias', 'references-fetch', 'references-check'})
        self.assertIn('native', commands['tests-native'])
        self.assertIn('alias', commands['tests-alias'])
        self.assertIn('--check', commands['glossary'])
        self.assertIn('--with-references', commands['references-check'])

    def test_failure_still_writes_report_and_returns_failure(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td).resolve()
            with patch.object(validate_ci, 'STEPS', (('intentional-failure', ('-c', 'raise SystemExit(7)')),)), redirect_stdout(io.StringIO()):
                self.assertEqual(validate_ci.validate(directory), 1)
            report = json.loads((directory / 'ci-results.json').read_bytes())
            self.assertFalse(report['passed'])
            self.assertEqual(report['checks'][0]['exit_code'], 7)
            self.assertTrue((directory / 'intentional-failure.log').is_file())

    def test_alias_is_same_file_and_original_cleanup_is_used(self):
        original = tempfile.TemporaryDirectory
        with aliased_temporary_directories() as metrics:
            with tempfile.TemporaryDirectory() as td:
                alias = Path(td)
                actual = alias.resolve()
                self.assertNotEqual(alias, actual)
                self.assertTrue(alias.samefile(actual))
                (alias / 'marker').write_bytes(b'fixture')
            self.assertFalse(actual.exists())
            self.assertEqual(metrics['aliased_directories'], 1)
        self.assertIs(tempfile.TemporaryDirectory, original)


if __name__ == '__main__':
    unittest.main()
