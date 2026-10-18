import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from tools.inspect_font_references import tagged_font_names, inspect, main

NAMES = ['None', 'TinyFontName', 'StrProperty', 'Other', 'IntProperty']
word = lambda *v: struct.pack('>' + 'I' * len(v), *v)
fname = lambda v: word(NAMES.index(v), 0)
string = lambda s: word(len(s) + 1) + s.encode() + b'\0'


def payload(raw=None, kind='StrProperty', index=0, duplicate=False):
    tag = fname('TinyFontName') + fname(kind)
    raw = string('Resource.Font') if raw is None else raw
    tag += word(len(raw), index) + raw
    return word(0) + tag + (tag if duplicate else b'') + fname('None')


def package():
    # One bounded tagged defaults export; no game assets or native decoder.
    names = NAMES + ['Core', 'Package', 'Class', 'Thing', 'Default__Engine']
    fn = lambda i: word(i, 0)
    nt = b''.join(string(n) + bytes(8) for n in names)
    im = fn(5) + fn(6) + word(0) + fn(5) + fn(5) + fn(7) + word(0xffffffff) + fn(8)
    header_size = 101 + len(nt) + len(im) + 68
    body = payload()
    ex = word(0xfffffffe, 0, 0) + fn(9) + word(0) + bytes(8)
    ex += word(len(body), header_size, 0, 0, 0) + bytes(16)
    header = b'\x9e\x2a\x83\xc1' + word((25 << 16) | 446, header_size) + string('None')
    header += word(0, len(names), 101, 1, 101 + len(nt) + len(im), 2, 101 + len(nt), 0)
    header += bytes(16) + word(1, 1, len(names), 0, 3004, 42, 0, 0)
    return header + nt + im + ex + body


class FontReferenceTests(unittest.TestCase):
    def test_tagged_defaults_and_offset(self):
        p = payload(); refs = tagged_font_names(p, NAMES)
        self.assertEqual(refs, [dict(property='TinyFontName', value='Resource.Font', value_offset=28)])
        self.assertEqual(p[refs[0]['value_offset']:], string('Resource.Font') + fname('None'))

    def test_guards(self):
        for p in (payload(kind='IntProperty'), payload(index=1), payload(duplicate=True),
                  payload(string('Resource.Font') + b'junk'), payload(word(3) + b'bad')):
            with self.subTest(p=p), self.assertRaises(ValueError):
                tagged_font_names(p, NAMES)

    def test_package_hash_export_and_runtime_boundary(self):
        b = package(); h = hashlib.sha256(b).hexdigest()
        r = inspect(b, h)
        self.assertEqual(r['references'][0]['value'], 'Resource.Font')
        self.assertFalse(r['game_rendering_verified'])
        with self.assertRaises(ValueError): inspect(b, '0'*64)
        with self.assertRaises(ValueError): inspect(b, h, 'missing')

    def test_truncated_payload(self):
        for n in range(len(payload())):
            with self.subTest(n=n), self.assertRaises(ValueError):
                tagged_font_names(payload()[:n], NAMES)

    def test_cli_reopens_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source.pkg'; b = package(); source.write_bytes(b)
            args = [str(source), '--sha256', hashlib.sha256(b).hexdigest(), '--output', str(root/'report.json')]
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args), 1)
            self.assertEqual(source.read_bytes(), b)
