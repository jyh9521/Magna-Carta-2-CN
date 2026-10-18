"""Synthetic data only; no proprietary font payloads are fixtures."""
import struct
import unittest
from unittest.mock import patch

from tools import ue3_fonts as fonts

NAMES = ["None", "Characters", "ArrayProperty", "Textures", "IsRemapped", "IntProperty",
         "StartU", "StartV", "USize", "VSize", "TextureIndex", "ByteProperty", "BoolProperty"]


def word(value):
    return struct.pack(">I", value)


def name(value):
    return word(NAMES.index(value)) + word(0)


def prop(key, kind, data):
    return name(key) + name(kind) + word(len(data)) + word(0) + data


def fixture(remapped=True):
    values = (1, 2, 3, 4)
    glyph = b"".join(prop(key, "IntProperty", word(value)) for key, value in zip(
        ("StartU", "StartV", "USize", "VSize"), values))
    glyph += prop("TextureIndex", "ByteProperty", b"\0") + name("None")
    tagged = prop("Characters", "ArrayProperty", word(1) + glyph)
    tagged += prop("Textures", "ArrayProperty", word(1) + word(2))
    if remapped:
        tagged += prop("IsRemapped", "IntProperty", word(1))
    native = word(1) + b"".join(map(word, values)) + b"\0"
    native += word(1) + word(2) + word(0)
    native += word(1) + struct.pack(">HH", 0x4E2D, 0) if remapped else word(0)
    native += word(int(remapped))
    return word(7) + tagged + name("None") + native


class FontPayloadTests(unittest.TestCase):
    def parse(self, data=None):
        return fonts.parse_font_payload(fixture() if data is None else data, NAMES)

    def test_metrics_and_explicit_remap(self):
        result = self.parse()
        self.assertEqual(result["characters"][0]["USize"], 3)
        self.assertEqual(result["remap"][0]["codepoint"], 0x4E2D)
        self.assertEqual(result["textures"], [2])
        self.assertEqual(result["net_index"], 7)

    def test_unremapped(self):
        result = self.parse(fixture(False))
        self.assertFalse(result["is_remapped"])
        self.assertEqual(result["remap"], [])

    def test_every_truncation_fails(self):
        data = fixture()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(fonts.FormatError):
                self.parse(data[:end])

    def test_native_metrics_mismatch(self):
        data = bytearray(fixture())
        offset = self.parse()["characters"][0]["native_offset"]
        data[offset:offset + 4] = word(8)
        with self.assertRaisesRegex(fonts.FormatError, "character mismatch"):
            self.parse(data)

    def test_native_texture_mismatch(self):
        data = bytearray(fixture())
        offset = self.parse()["unknown_zero_offset"] - 4
        data[offset:offset + 4] = word(9)
        with self.assertRaisesRegex(fonts.FormatError, "texture references mismatch"):
            self.parse(data)

    def test_remap_target_outside_characters(self):
        data = bytearray(fixture())
        offset = self.parse()["remap"][0]["offset"] + 2
        data[offset:offset + 2] = b"\0\1"
        with self.assertRaisesRegex(fonts.FormatError, "invalid glyph"):
            self.parse(data)

    def test_unknown_native_field_fails(self):
        data = bytearray(fixture())
        offset = self.parse()["unknown_zero_offset"]
        data[offset:offset + 4] = word(1)
        with self.assertRaisesRegex(fonts.FormatError, "nonzero native field"):
            self.parse(data)

    def test_trailing_bytes_fail(self):
        with self.assertRaisesRegex(fonts.FormatError, "trailing bytes"):
            self.parse(fixture() + b"\0")

    def test_remap_flag_mismatch(self):
        with self.assertRaisesRegex(fonts.FormatError, "IsRemapped mismatch"):
            self.parse(fixture()[:-4] + word(0))

    def test_duplicate_property_fails(self):
        p = {"name": "Characters", "array_index": 0}
        with self.assertRaises(fonts.FormatError):
            fonts.unique_properties([p, p])

    def test_bool_uses_four_bytes_in_this_profile(self):
        data = prop("IsRemapped", "BoolProperty", b"") + word(1) + name("None")
        reader = fonts.Reader(data)
        self.assertEqual(fonts.read_properties(reader, NAMES)[0]["bool"], 1)
        self.assertEqual(reader.pos, len(data))

    def test_unsupported_property_fname_fails(self):
        with self.assertRaises(fonts.FormatError):
            fonts.read_properties(fonts.Reader(word(999) + word(0)), NAMES)

    def test_numbered_property_fname_fails(self):
        with self.assertRaises(fonts.FormatError):
            fonts.read_properties(fonts.Reader(word(1) + word(1)), NAMES)

    def test_object_array_rejects_trailing_bytes(self):
        with self.assertRaises(fonts.FormatError):
            fonts.object_array({"type": "ArrayProperty", "raw": word(0) + b"x"})

    def test_compressed_package_rejected(self):
        with patch.object(fonts, "parse_summary", return_value={"compression_flags": 4}):
            with self.assertRaisesRegex(fonts.FormatError, "uncompressed"):
                fonts.inspect_package(b"fixture")


if __name__ == "__main__":
    unittest.main()
