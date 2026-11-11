"""Self-authored bytes prove stale instructions fail independently of game data."""
import hashlib
import unittest

from tools.audit_installer_release import compare_usage


class InstallerUsageTests(unittest.TestCase):
    def test_current_instructions_pass_and_stale_instructions_fail(self):
        old=b'old authored instructions';new=b'new authored instructions'
        manifest=dict(usage_sha256=hashlib.sha256(old).hexdigest())
        self.assertEqual(compare_usage(manifest,old,old),[])
        self.assertEqual(compare_usage(manifest,new,old),['current usage instructions'])

    def test_internal_corruption_and_stale_source_are_separate(self):
        self.assertEqual(compare_usage(dict(usage_sha256='0'*64),b'new',b'old'),
                         ['embedded usage identity','current usage instructions'])

    def test_bounded_bytes_only(self):
        for a,b in [(b'',b'a'),(b'a',b''),('text',b'a'),(b'a',b'a'*(4*1024*1024+1))]:
            with self.assertRaises(ValueError):compare_usage({},a,b)


if __name__=='__main__':unittest.main()
