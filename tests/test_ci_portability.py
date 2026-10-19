"""CI entry-point regressions; no game launch or upstream network required."""
from pathlib import Path
import unittest
from unittest.mock import patch

import test_runtime_patch as runtime_fixture

ROOT = Path(__file__).resolve().parents[1]


class CIPortabilityTests(unittest.TestCase):
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
        with patch('os.path.relpath', side_effect=ValueError('different drive roots')):
            case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)


if __name__ == '__main__':
    unittest.main()
