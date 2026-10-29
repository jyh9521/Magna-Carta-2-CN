"""Keep hosted runners independent of developer-installed imaging libraries."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CIWorkflowTests(unittest.TestCase):
    def test_pinned_imaging_dependencies_installed_before_full_suite(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf-8')
        install = 'python -m pip install -r requirements-font.txt'
        suite = 'python tools/validate_ci.py --report-dir build/ci'
        self.assertIn(install, workflow)
        self.assertLess(workflow.index(install), workflow.index(suite))
        requirements = (ROOT / 'requirements-font.txt').read_text(encoding='utf-8')
        self.assertRegex(requirements, r'(?m)^Pillow==\d+\.\d+\.\d+$')
        self.assertRegex(requirements, r'(?m)^fonttools==\d+\.\d+\.\d+$')

    def test_matrix_and_failure_reporting_remain_enabled(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf-8')
        self.assertIn('ubuntu-latest, windows-latest', workflow)
        self.assertIn("'3.12', '3.14'", workflow)
        self.assertNotIn('continue-on-error: true', workflow)
        self.assertIn('on: [push, pull_request, workflow_dispatch]', workflow)

    def test_diagnostics_survive_failed_checks_and_actions_are_pinned(self):
        import re
        workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf-8')
        self.assertIn('if: always()', workflow)
        self.assertIn('path: build/ci/', workflow)
        self.assertIn('ci-${{ matrix.os }}-py${{ matrix.python }}', workflow)
        actions = re.findall(r'uses: (\S+)', workflow)
        self.assertEqual(len(actions), 3)
        for action in actions:
            self.assertRegex(action, r'^actions/[a-z-]+@[0-9a-f]{40}$')
