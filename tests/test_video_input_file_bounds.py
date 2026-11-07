"""Bound the public input helper's allocation despite late file-size changes."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_video_captions import locked_file


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class ReadSpy:
    def __init__(self, stream, requests):
        self.stream = stream
        self.requests = requests

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def read(self, size=-1):
        self.requests.append(size)
        return self.stream.read(size)


class VideoInputFileBoundsTests(unittest.TestCase):
    def test_exact_limit_file_keeps_its_bytes_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'authored.bin'
            source.write_bytes(b'12345678')
            self.assertEqual(locked_file(source, digest(b'12345678'), 8), b'12345678')
            self.assertEqual(source.read_bytes(), b'12345678')

    def test_statically_oversized_file_rejects_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'authored.bin'
            source.write_bytes(b'123456789')
            with (patch.object(Path, 'open', side_effect=AssertionError('oversized input was opened')),
                  self.assertRaisesRegex(ValueError, 'size bound')):
                locked_file(source, digest(b'123456789'), 8)

    def late_change(self, source, replacement, expected, error):
        original_open = Path.open
        requests = []
        resolved = source.resolve()

        def opening(path, *args, **kwargs):
            mode = args[0] if args else kwargs.get('mode', 'r')
            if path == resolved and mode == 'rb':
                with original_open(path, 'wb') as stream:
                    stream.write(replacement)
                return ReadSpy(original_open(path, *args, **kwargs), requests)
            return original_open(path, *args, **kwargs)

        with patch.object(Path, 'open', opening), self.assertRaisesRegex(ValueError, error):
            locked_file(source, digest(expected), 8)
        self.assertEqual(requests, [9], 'The helper must never request an unbounded file read')

    def test_late_growth_rejects_even_when_full_grown_hash_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'authored.bin'
            source.write_bytes(b'abcd')
            replacement = b'0123456789ABCDEF'
            self.late_change(source, replacement, replacement, 'size bound')

    def test_late_shrink_to_empty_rejects_even_when_empty_hash_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'authored.bin'
            source.write_bytes(b'abcd')
            self.late_change(source, b'', b'', 'size bound')

    def test_within_limit_late_mutation_still_rejects_original_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'authored.bin'
            source.write_bytes(b'abcd')
            self.late_change(source, b'changed', b'abcd', 'SHA256 mismatch')


if __name__ == '__main__':
    unittest.main()
