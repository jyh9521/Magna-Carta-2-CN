"""CI entry-point regressions; no game launch or upstream network required."""
from contextlib import nullcontext
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

import test_image_review_v4 as glyph_fixture
import test_runtime_patch as runtime_fixture

ROOT = Path(__file__).resolve().parents[1]


class CIPortabilityTests(unittest.TestCase):
    def test_glyph_snapshot_fixture_accepts_noncanonical_temp_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / 'spelling').mkdir()
            # Exercise the same alias-vs-resolved mismatch as Windows 8.3 TEMP
            # paths without requiring short names, symlinks or Windows itself.
            alias = root / 'spelling' / '..'
            self.assertNotEqual(alias, alias.resolve())
            self.assertTrue(alias.samefile(root))
            case = glyph_fixture.AuthoredGlyphBuilderTests(
                'test_builder_resolves_and_snapshots_glyph_bytes')
            result = unittest.TestResult()
            with patch('tempfile.TemporaryDirectory',
                       return_value=nullcontext(str(alias))):
                case.run(result)
            self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

    def test_revision_fixture_accepts_noncanonical_temp_path(self):
        import test_compose_revision_layers as fixture
        from tools.run_test_suite import aliased_temporary_directories
        case = fixture.RevisionLayerTests(
            'test_locked_replacement_roundtrip_and_immutable_inputs')
        result = unittest.TestResult()
        with aliased_temporary_directories() as metrics:
            case.run(result)
        self.assertGreater(metrics['aliased_directories'], 0)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

    def test_reference_validation_fetches_pinned_inputs_before_check(self):
        from tools.validate_ci import validation_commands
        workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf8')
        self.assertIn('python tools/validate_ci.py --report-dir build/ci', workflow)
        commands = list(validation_commands('python', 'report'))
        names = [name for name, _ in commands]
        self.assertLess(names.index('references-fetch'), names.index('references-check'))
        self.assertEqual(dict(commands)['references-fetch'][-2:], ['tools/series_terms.py', 'fetch'])
        self.assertEqual(dict(commands)['references-check'][-3:],
                         ['tools/series_terms.py', 'check', '--with-references'])
        self.assertNotIn('continue-on-error', workflow)
        self.assertIn('fail-fast: false', workflow)

    def test_relative_launch_fixture_does_not_relativize_across_drives(self):
        case = runtime_fixture.RuntimePatchTests(
            'test_launch_accepts_relative_run_directory_without_false_inventory_failure')
        result = unittest.TestResult()
        original = runtime_fixture.launch_xenia.launch
        previous = Path.cwd()

        def checked_launch(run_dir, record):
            # stat('.') observes the OS working directory, not a mocked getcwd.
            self.assertTrue(os.path.samefile('.', Path(record['config_snapshot']).parent.parent))
            return original(run_dir, record)

        with patch('os.path.relpath', side_effect=ValueError('different drive roots')), \
                patch.object(runtime_fixture.launch_xenia, 'launch', side_effect=checked_launch):
            case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        self.assertTrue(os.path.samefile('.', previous))


if __name__ == '__main__':
    unittest.main()
