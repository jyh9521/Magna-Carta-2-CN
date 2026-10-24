"""Keep hosted runners independent of developer-installed imaging libraries."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CIWorkflowTests(unittest.TestCase):
    def test_pinned_imaging_dependencies_installed_before_full_suite(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf-8')
        install = 'python -m pip install -r requirements-font.txt'
        suite = 'python -m unittest discover -s tests'
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
