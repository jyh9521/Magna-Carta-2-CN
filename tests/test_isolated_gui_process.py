import os
import sys
import unittest
from tools.isolated_gui_process import run


@unittest.skipUnless(os.name == 'nt', 'Windows desktop API')
class IsolatedGuiTests(unittest.TestCase):
    def test_exit_and_desktop_unchanged(self):
        result = run([sys.executable, '-c', 'raise SystemExit(7)'], timeout=10)
        self.assertEqual(result['exit_code'], 7)
        self.assertFalse(result['timed_out'])
        self.assertTrue(result['input_desktop_unchanged'])
        self.assertFalse(result['desktop_switched'])

    def test_modal_window_stays_private_and_is_killed_on_timeout(self):
        result = run([sys.executable, '-c',
            "import ctypes; ctypes.windll.user32.MessageBoxW(None,'Private fixture','Localization isolated fixture',0)"], timeout=2)
        self.assertEqual(result['exit_code'], 124)
        self.assertTrue(result['timed_out'])
        self.assertTrue(result['input_desktop_unchanged'])
        self.assertIn('Localization isolated fixture', result['window_titles'])
        self.assertTrue(result['child_tree_closed'])

    def test_invalid_timeout(self):
        with self.assertRaises(ValueError): run([sys.executable], timeout=0)


if __name__ == '__main__': unittest.main()
