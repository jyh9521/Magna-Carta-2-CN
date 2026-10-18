"""Synthetic append-only font/package fixtures; optional raster modules not required."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools import supplement_font as supplement
from tools.lzx_stored import wrap_ue3_chunk
from tools.ue3_package import parse_summary, parse_tables
from tools.ue3_fonts import parse_font_payload

NAMES = ["None", "Core", "Engine", "Package", "Class", "Font", "Texture2D", "General", "Atlas", "Characters", "ArrayProperty", "Textures", "IsRemapped", "IntProperty", "StartU", "StartV", "USize", "VSize", "TextureIndex", "ByteProperty", "SizeX", "SizeY", "Format", "Other"]


def word(*values):
    return struct.pack(">" + "I" * len(values), *values)


def fname(value):
    return word(NAMES.index(value), 0)


def prop(name, kind, raw):
    return fname(name) + fname(kind) + word(len(raw), 0) + raw


def font_payload(metric_height=24):
    metric = {"StartU": 0, "StartV": 0, "USize": 4, "VSize": metric_height, "TextureIndex": 0}
    tagged = prop("Characters", "ArrayProperty", word(1) + supplement.tagged_glyph(NAMES, metric))
    tagged += prop("Textures", "ArrayProperty", word(1, 2)) + prop("IsRemapped", "IntProperty", word(1)) + fname("None")
    native = word(1, 0, 0, 4, metric_height) + b"\0" + word(1, 2, 0, 1) + struct.pack(">HHI", 65, 0, 1)
    return word(0) + tagged + native


def atlas_payload(offset, compressed=False):
    props = prop("SizeX", "IntProperty", word(128)) + prop("SizeY", "IntProperty", word(128))
    props += prop("Format", "ByteProperty", b"\7") + fname("None")
    prefix = word(1) + props
    prefix += word(0, 0, 0, offset + len(prefix) + 16) + word(1)
    raw = bytes(range(256)) * 64
    pixels = wrap_ue3_chunk(raw) if compressed else raw
    return prefix + word(64 if compressed else 0, len(raw), len(pixels), offset + len(prefix) + 16) + pixels + word(128, 128)


def package_fixture(compressed=False, texture_compressed=False, font_height=24):
    string = lambda value: word(len(value) + 1) + value.encode() + b"\0"
    names = b"".join(string(n) + bytes(8) for n in NAMES)
    imports = fname("Core") + fname("Package") + word(0) + fname("Engine")
    imports += fname("Core") + fname("Class") + word(0xFFFFFFFF) + fname("Font")
    imports += fname("Core") + fname("Class") + word(0xFFFFFFFF) + fname("Texture2D")
    export_offset = 101 + len(names) + len(imports)
    header_size = export_offset + 3 * 68
    font = font_payload(font_height)
    atlas = atlas_payload(header_size + len(font), texture_compressed)
    def export(class_ref, name, outer, size, offset):
        return word(class_ref & 0xFFFFFFFF, 0, outer) + fname(name) + word(0) + bytes(8) + word(size, offset, 0, 0, 0) + bytes(16)
    exports = export(-2, "General", 0, len(font), header_size)
    exports += export(-3, "Atlas", 1, len(atlas), header_size + len(font))
    exports += export(0, "Other", 0, 8, header_size + len(font) + len(atlas))
    summary = b"\x9e\x2a\x83\xc1" + word((25 << 16) | 446, header_size) + string("None")
    summary += word(0, len(NAMES), 101, 3, export_offset, 3, 101 + len(names), 0) + bytes(16)
    summary += word(1, 3, len(NAMES), 0, 3004, 42, 0, 0)
    logical = summary + names + imports + exports + font + atlas + b"RETAINED"
    if not compressed:
        return logical
    first = wrap_ue3_chunk(logical[101:header_size])
    second = wrap_ue3_chunk(logical[header_size:])
    prefix = bytearray(logical[:101])
    struct.pack_into(">II", prefix, 93, 4, 2)
    entries = word(101, header_size - 101, 133, len(first))
    entries += word(header_size, len(logical) - header_size, 133 + len(first), len(second))
    return bytes(prefix) + entries + first + second + b"TRAILING-PADDING"


def stored_decoder(data, size):
    # Controlled synthetic decoder for this project's type3 test writer only.
    output = bytearray()
    position = 0
    while position < len(data):
        if data[position] != 255:
            raise ValueError("test decoder requires long Xbox frames")
        count, stored_size = struct.unpack(">HH", data[position + 1:position + 5])
        frame = data[position + 5:position + 5 + stored_size]
        output.extend(frame[16:16 + count])
        position += 5 + stored_size
    if len(output) != size:
        raise ValueError("test decoder size mismatch")
    return bytes(output)


def plan():
    return {"schema_version": 1, "in_game_verified": False, "font_size": 22,
            "glyphs": [{"character": chr(0x4E2D), "texture_index": 0, "x": 8, "y": 8, "width": 24, "height": 24}]}


class FontAppendTests(unittest.TestCase):
    def test_original_records_retained(self):
        data = font_payload()
        addition = {"codepoint": 0x4E2D, "StartU": 8, "StartV": 8, "USize": 24, "VSize": 24, "TextureIndex": 0}
        out = supplement.append_font_payload(data, NAMES, [addition])
        old, new = parse_font_payload(data, NAMES), parse_font_payload(out, NAMES)
        self.assertEqual(len(new["characters"]), 2)
        self.assertEqual((new["remap"][-1]["codepoint"], new["remap"][-1]["glyph_index"]), (0x4E2D, 1))
        old_tag = old["characters"][0]["tagged_offset"]
        new_tag = new["characters"][0]["tagged_offset"]
        self.assertEqual(data[old_tag:old_tag + 145], out[new_tag:new_tag + 145])
        old_native, new_native = old["characters"][0]["native_offset"], new["characters"][0]["native_offset"]
        self.assertEqual(data[old_native:old_native + 17], out[new_native:new_native + 17])

    def test_reject_existing_codepoint(self):
        metric = {"codepoint": 65, "StartU": 8, "StartV": 8, "USize": 24, "VSize": 24, "TextureIndex": 0}
        with self.assertRaisesRegex(supplement.FormatError, "already mapped"):
            supplement.append_font_payload(font_payload(), NAMES, [metric])

    def test_control_and_non_bmp_rejected(self):
        for char in ("\n", " ", chr(0xD800), chr(0x1F600), "ab"):
            p = plan()
            p["glyphs"][0]["character"] = char
            with self.subTest(char=repr(char)), self.assertRaises(supplement.FormatError):
                supplement.validate_plan(p)

    def test_duplicate_and_misaligned_rejected(self):
        p = plan()
        p["glyphs"].append(dict(p["glyphs"][0]))
        with self.assertRaisesRegex(supplement.FormatError, "duplicate"):
            supplement.validate_plan(p)
        p = plan()
        p["glyphs"][0]["x"] = 9
        with self.assertRaisesRegex(supplement.FormatError, "block-aligned"):
            supplement.validate_plan(p)


class PackageSupplementTests(unittest.TestCase):
    def run_build(self, data, p=None):
        return supplement.supplement_package(data, hashlib.sha256(data).hexdigest(), "General", p or plan(), {0x4E2D: bytes([255]) * 576}, stored_decoder)

    def test_uncompressed_append_and_unaffected_payload(self):
        data = package_fixture()
        out, report = self.run_build(data)
        self.assertEqual(report["original_glyph_count"], 1)
        self.assertEqual(report["supplemented_glyph_count"], 2)
        self.assertEqual(report["unaffected_exports_byte_identical"], 1)
        self.assertEqual(report["changed_tile_blocks"], 36)
        self.assertTrue(report["all_pixels_outside_selected_cells_identical"])
        self.assertFalse(report["runtime_rendering_verified"])
        old, new = parse_tables(data), parse_tables(out)
        for before, after in zip(old["exports"][:2], new["exports"][:2]):
            self.assertGreaterEqual(after["serial_offset"], len(data))
            start, size = before["serial_offset"], before["serial_size"]
            self.assertEqual(out[start:start + size], data[start:start + size])

    def test_compressed_original_other_chunk_and_padding_preserved(self):
        data = package_fixture(compressed=True)
        out, report = self.run_build(data)
        self.assertEqual(report["package_compression"]["new_chunk_count"], 3)
        self.assertEqual(report["package_compression"]["preserved_compressed_chunks"], 1)
        old_s, new_s = parse_summary(data), parse_summary(out)
        old, new = old_s["compressed_chunks"][1], new_s["compressed_chunks"][1]
        self.assertEqual(data[old["compressed_offset"]:old["compressed_offset"] + old["compressed_size"]], out[new["compressed_offset"]:new["compressed_offset"] + new["compressed_size"]])
        self.assertTrue(out.endswith(b"TRAILING-PADDING"))

    def test_standalone_lzx_atlas_variant(self):
        data = package_fixture(texture_compressed=True)
        _, report = self.run_build(data)
        self.assertEqual(report["original_texture_bulk_flags"], 64)

    def test_hash_guard(self):
        with self.assertRaisesRegex(supplement.FormatError, "SHA-256 mismatch"):
            supplement.supplement_package(package_fixture(), "0" * 64, "General", plan(), {}, stored_decoder)

    def test_placement_overlap_original_blocks(self):
        p = plan()
        p["glyphs"][0]["x"] = p["glyphs"][0]["y"] = 0
        with self.assertRaisesRegex(supplement.FormatError, "overlaps"):
            self.run_build(package_fixture(), p)

    def test_metric_height23_preserves_maximum_and_all_old_records(self):
        p = plan()
        p["metric_height"] = 23
        data = package_fixture(font_height=23)
        alphas = {0x4E2D: bytes([255]) * (24 * 23) + bytes(24)}
        out, report = supplement.supplement_package(data, hashlib.sha256(data).hexdigest(), "General", p, alphas, stored_decoder)
        self.assertEqual(report["original_max_glyph_height"], 23)
        self.assertEqual(report["supplemented_max_glyph_height"], 23)
        self.assertEqual(set(report["original_record_sha256"]), {"tagged", "native", "remap"})
        font = parse_tables(out)["exports"][0]
        payload = out[font["serial_offset"]:font["serial_offset"] + font["serial_size"]]
        self.assertEqual(parse_font_payload(payload, NAMES)["characters"][-1]["VSize"], 23)

    def test_font_maximum_height_regression_rejected(self):
        p = plan()
        p["glyphs"][0]["height"] = 28
        with self.assertRaisesRegex(supplement.FormatError, "maximum font height"):
            self.run_build(package_fixture(), p)

    def test_nonzero_alpha_below_metric_height_rejected(self):
        p = plan()
        p["metric_height"] = 23
        with self.assertRaisesRegex(supplement.FormatError, "would clip"):
            self.run_build(package_fixture(), p)

    def test_unknown_font_object_guard(self):
        data = package_fixture()
        with self.assertRaisesRegex(supplement.FormatError, "exactly one"):
            supplement.supplement_package(data, hashlib.sha256(data).hexdigest(), "Wrong", plan(), {}, stored_decoder)

    def test_cli_rejects_existing_output_and_input_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.xxx"
            source.write_bytes(package_fixture())
            output = Path(temp) / "output.xxx"
            output.write_bytes(b"existing")
            def call(dest):
                return supplement.main([str(source), "--package-sha256", hashlib.sha256(source.read_bytes()).hexdigest(),
                    "--font-file", str(Path(temp) / "font.otf"), "--font-sha256", "0" * 64, "--font-object", "General",
                    "--plan", str(Path(temp) / "plan.json"), "--lzx-library", str(Path(temp) / "decoder.dll"),
                    "--output", str(dest), "--report", str(Path(temp) / "report.json")])
            self.assertEqual(call(source), 1)
            self.assertEqual(call(output), 1)
            self.assertEqual(output.read_bytes(), b"existing")
            self.assertEqual(source.read_bytes(), package_fixture())


if __name__ == "__main__":
    unittest.main()
