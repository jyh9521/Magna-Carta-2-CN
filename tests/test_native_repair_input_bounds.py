"""Native repair dependencies use bounded reads, including final rechecks."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_native_pixel_repairs import locked_bytes, MAX_SOURCE_BYTES


class NativeRepairInputBoundsTests(unittest.TestCase):
    def fixture(self, root, raw=b'owned-data'):
        path = Path(root)/'source.bin'
        path.write_bytes(raw)
        return path, hashlib.sha256(raw).hexdigest()

    def test_exact_boundary_and_digest_are_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            path, expected = self.fixture(root)
            self.assertEqual(locked_bytes(path, expected, 10), b'owned-data')

    def test_stat_oversize_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as root:
            path, expected = self.fixture(root)
            with patch.object(Path, 'open', side_effect=AssertionError('must not allocate')):
                with self.assertRaisesRegex(ValueError, 'size bound'):
                    locked_bytes(path, expected, 9)

    def test_late_growth_uses_limit_plus_one_not_unbounded_read(self):
        with tempfile.TemporaryDirectory() as root:
            path, expected = self.fixture(root, b'x')
            reads = []
            class GrowingStream(io.BytesIO):
                def read(self, n=-1):
                    reads.append(n)
                    return super().read(n)
            with patch.object(Path, 'open', return_value=GrowingStream(b'x'*100)):
                with self.assertRaisesRegex(ValueError, 'size bound'):
                    locked_bytes(path, expected, 8)
            self.assertEqual(reads, [9])

    def test_changed_or_empty_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path, expected = self.fixture(root)
            path.write_bytes(b'other-data')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                locked_bytes(path, expected, 10)
            path.write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'size bound'):
                locked_bytes(path, hashlib.sha256(b'').hexdigest(), 10)

    def test_caller_cannot_disable_or_expand_the_allocation_bound(self):
        with tempfile.TemporaryDirectory() as root:
            path, expected = self.fixture(root)
            for limit in (0, -1, True, 10.0, MAX_SOURCE_BYTES+1):
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    locked_bytes(path, expected, limit)


if __name__ == '__main__':
    unittest.main()
