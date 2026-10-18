"""Synthetic-only XDVDFS regression fixtures; no original assets required."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from disc_inventory import Disc, FormatError, MAGIC, sha256_file


def fixture(name=b"sample.txt", flags=0x80, left=0, right=0, start=40, size=3):
    data = bytearray(42 * 2048)
    data[0x10000:0x10000 + 20] = MAGIC
    data[0x10800 - 20:0x10800] = MAGIC
    struct.pack_into("<II", data, 0x10000 + 20, 36, 2048)
    struct.pack_into("<HHIIBB", data, 36 * 2048, left, right, start, size, flags, len(name))
    data[36 * 2048 + 14:36 * 2048 + 14 + len(name)] = name
    data[40 * 2048:40 * 2048 + 3] = b"abc"
    return data


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image = self.root / "fixture.iso"

    def tearDown(self):
        self.temp.cleanup()

    def disc(self, data=None):
        self.image.write_bytes(fixture() if data is None else data)
        return Disc(self.image)

    def test_inventory_hash_extract_no_source_changes(self):
        disc = self.disc()
        before = sha256_file(self.image)
        records = disc.inventory()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["offset"], 81920)
        self.assertEqual(disc.resource_hash(records[0]), hashlib.sha256(b"abc").hexdigest())
        out = disc.extract(records[0], self.root / "output")
        self.assertEqual(out.read_bytes(), b"abc")
        self.assertEqual(before, sha256_file(self.image))
        with self.assertRaises(FileExistsError):
            disc.extract(records[0], self.root / "output")

    def test_unknown_image(self):
        self.image.write_bytes(bytes(81920))
        with self.assertRaises(FormatError):
            Disc(self.image)

    def test_trailing_magic_required(self):
        data = fixture(); data[0x10800 - 1] = 0
        with self.assertRaises(FormatError):
            self.disc(data)

    def test_extent_bounds(self):
        with self.assertRaises(FormatError):
            self.disc(fixture(start=999)).inventory()

    def test_directory_bounds(self):
        data = fixture(); struct.pack_into("<I", data, 0x10000 + 20, 100)
        with self.assertRaises(FormatError):
            self.disc(data).inventory()

    def test_tree_pointer_bounds(self):
        with self.assertRaises(FormatError):
            self.disc(fixture(left=600)).inventory()

    def test_cyclic_tree(self):
        data = fixture(right=8)
        struct.pack_into("<HHIIBB", data, 36 * 2048 + 32, 8, 0, 40, 3, 128, 1)
        data[36 * 2048 + 46] = ord("x")
        with self.assertRaisesRegex(FormatError, "cyclic tree"):
            self.disc(data).inventory()

    def test_cyclic_directory(self):
        with self.assertRaisesRegex(FormatError, "cyclic directory"):
            self.disc(fixture(flags=0x10, start=36, size=2048)).inventory()

    def test_path_safety(self):
        for name in (b"..", b".", b"a/b", b"a\\b", b"a:b", b"a\0b", b"CON", b"NUL.txt", b"COM1", b"a.", b"a ", b"a?b"):
            with self.subTest(name=name), self.assertRaises(FormatError):
                self.disc(fixture(name)).inventory()

    def test_overlap(self):
        with self.assertRaises(FormatError):
            self.disc(fixture(right=1)).inventory()

    def test_truncated_name(self):
        data = fixture(); data[36 * 2048 + 13] = 255
        struct.pack_into("<I", data, 0x10000 + 24, 20)
        with self.assertRaises(FormatError):
            self.disc(data).inventory()

    def test_extraction_escape(self):
        disc = self.disc(); record = disc.inventory()[0]; record["path"] = "../escape"
        with self.assertRaises(FormatError):
            disc.extract(record, self.root / "output")

    def test_explicit_base(self):
        self.image.write_bytes(bytes(2048) + fixture())
        disc = Disc(self.image, base=2048)
        self.assertEqual(disc.inventory()[0]["offset"], 83968)

    def test_duplicate_casefold_path(self):
        data = fixture(right=8)
        name = b"SAMPLE.TXT"
        struct.pack_into("<HHIIBB", data, 36 * 2048 + 32, 0, 0, 40, 3, 128, len(name))
        data[36 * 2048 + 46:36 * 2048 + 46 + len(name)] = name
        with self.assertRaisesRegex(FormatError, "duplicate"):
            self.disc(data).inventory()

    def test_non_ascii_rejected(self):
        with self.assertRaises(UnicodeDecodeError):
            self.disc(fixture(b"\xff")).inventory()


if __name__ == "__main__":
    unittest.main()
