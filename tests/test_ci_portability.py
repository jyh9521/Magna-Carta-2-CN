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

    def test_reference_validation_fetches_pinned_inputs_before_check(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf8')
        fetch = 'python tools/series_terms.py fetch'
        check = 'python tools/series_terms.py check --with-references'
        self.assertIn(fetch, workflow)
        self.assertIn(check, workflow)
        self.assertLess(workflow.index(fetch), workflow.index(check))
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
