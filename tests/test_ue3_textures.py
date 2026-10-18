"""Synthetic framing/tiling/BC3 tests; no proprietary assets."""
import hashlib
import struct
import unittest
import zlib
from unittest.mock import patch

from tools import ue3_textures as textures

NAMES = ["None", "SizeX", "SizeY", "IntProperty", "Format", "ByteProperty"]


def word(value):
    return struct.pack(">I", value)


def name(value):
    return word(NAMES.index(value)) + word(0)


def prop(key, kind, data):
    return name(key) + name(kind) + word(len(data)) + word(0) + data


def chunk(payload=b"x", size=16384):
    return word(0x9E2A83C1) + word(131072) + word(len(payload)) + word(size) + word(len(payload)) + word(size) + payload


def fixture():
    props = prop("SizeX", "IntProperty", word(128)) + prop("SizeY", "IntProperty", word(128))
    props += prop("Format", "ByteProperty", b"\7") + name("None")
    prefix = word(4) + props
    source = word(0) * 3 + word(1000 + len(prefix) + 16)
    mip_prefix = prefix + source + word(1)
    bulk = chunk()
    return mip_prefix + word(64) + word(16384) + word(len(bulk)) + word(1000 + len(mip_prefix) + 16) + bulk + word(128) * 2


class ChunkTests(unittest.TestCase):
    def test_framing_and_decoder(self):
        meta, data = textures.compressed_chunk(chunk(), 16384, lambda payload, size: bytes(size))
        self.assertEqual(meta["blocks"][0]["offset"], 24)
        self.assertEqual(len(data), 16384)

    def test_metadata_only(self):
        self.assertIsNone(textures.compressed_chunk(chunk(), 16384)[1])

    def test_truncation_rejected(self):
        data = chunk()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(textures.FormatError):
                textures.compressed_chunk(data[:end], 16384)

    def test_output_size_guard(self):
        with self.assertRaisesRegex(textures.FormatError, "decoder output"):
            textures.compressed_chunk(chunk(), 16384, lambda *_: b"bad")

    def test_count_guard(self):
        with self.assertRaisesRegex(textures.FormatError, "element count"):
            textures.compressed_chunk(chunk(), 42)

    def test_block_totals_guard(self):
        data = bytearray(chunk())
        data[16:20] = word(2)
        with self.assertRaisesRegex(textures.FormatError, "totals"):
            textures.compressed_chunk(data, 16384)

    def test_tail_guard(self):
        with self.assertRaisesRegex(textures.FormatError, "physical size"):
            textures.compressed_chunk(chunk() + b"x", 16384)


class TexturePayloadTests(unittest.TestCase):
    def parse(self, data=None, decoder=None):
        return textures.parse_texture_payload(fixture() if data is None else data, NAMES, 1000, decoder)

    def test_payload_metadata(self):
        result, previews = self.parse()
        self.assertEqual(result["mips"][0]["bulk"]["flags"], 64)
        self.assertEqual(result["format_byte"], 7)
        self.assertEqual(result["source_art"]["element_count"], 0)
        self.assertFalse(result["decoded"])
        self.assertEqual(previews, [])

    def test_payload_decode(self):
        result, previews = self.parse(decoder=lambda payload, size: bytes(size))
        self.assertTrue(result["decoded"])
        self.assertEqual(len(previews[0]), 128 * 128 * 4)
        self.assertEqual(result["mips"][0]["decoded_tiled_sha256"], hashlib.sha256(bytes(16384)).hexdigest())

    def test_every_prefix_truncation(self):
        data = fixture()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(textures.FormatError):
                self.parse(data[:end])

    def test_extra_bytes(self):
        with self.assertRaisesRegex(textures.FormatError, "trailing"):
            self.parse(fixture() + b"x")

    def test_dimensions(self):
        with self.assertRaisesRegex(textures.FormatError, "dimensions mismatch"):
            self.parse(fixture()[:-4] + word(64))

    def test_bad_sourceart_offset(self):
        data = bytearray(fixture())
        offset = self.parse()[0]["properties_end"] + 12
        data[offset:offset + 4] = word(0)
        with self.assertRaisesRegex(textures.FormatError, "not inline"):
            self.parse(data)

    def test_profile_guard(self):
        with patch.object(textures, "parse_summary", return_value={"compression_flags": 4}):
            with self.assertRaisesRegex(textures.FormatError, "uncompressed"):
                textures.inspect_package(b"fixture")


class PixelTests(unittest.TestCase):
    def test_tiling_is_bijection_for_full_128_square(self):
        offsets = {textures.xbox_tiled_block_offset(x, y, 32) for y in range(32) for x in range(32)}
        self.assertEqual(offsets, set(range(1024)))

    def test_untile_swaps_every_word(self):
        data = bytes(range(16)) * 1024
        out = textures.untile_dxt5(data, 128, 128)
        self.assertEqual(out[:16], bytes([1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14]))

    def test_untile_invalid_size(self):
        with self.assertRaises(textures.FormatError):
            textures.untile_dxt5(bytes(16), 128, 128)

    def test_lower_mip_unsupported(self):
        with self.assertRaises(textures.FormatError):
            textures.untile_dxt5(bytes(16384), 16, 16)

    def test_bc3_opaque_red(self):
        block = bytes([255, 0]) + bytes(6) + struct.pack("<HHI", 0xF800, 0, 0)
        self.assertEqual(textures.decode_dxt5(block, 4, 4), bytes([255, 0, 0, 255]) * 16)

    def test_bc3_alpha_special_case(self):
        # a0 <= a1 gives explicit alpha[6]=0 / alpha[7]=255.
        indices = sum(7 << (i * 3) for i in range(16))
        block = b"\0\1" + indices.to_bytes(6, "little") + struct.pack("<HHI", 0xFFFF, 0, 0)
        self.assertEqual(textures.decode_dxt5(block, 4, 4), bytes([255]) * 64)

    def test_png_framing_crc_and_pixels(self):
        png = textures.png_rgba(bytes([255, 0, 0, 255]), 1, 1)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        position = 8
        while position < len(png):
            size = int.from_bytes(png[position:position + 4], "big")
            kind = png[position + 4:position + 8]
            data = png[position + 8:position + 8 + size]
            self.assertEqual(zlib.crc32(kind + data), int.from_bytes(png[position + 8 + size:position + 12 + size], "big"))
            if kind == b"IDAT":
                self.assertEqual(zlib.decompress(data), b"\0\xff\0\0\xff")
            position += size + 12



class SupplementPrimitiveTests(unittest.TestCase):
    def test_all_alpha_values_quantization_bound(self):
        for start in range(0, 256, 16):
            alpha = bytes(range(start, start + 16))
            block = textures.encode_white_bc3_block(alpha)
            decoded = textures.decode_dxt5(block, 4, 4)
            self.assertTrue(all(decoded[i:i + 3] == bytes([255]) * 3 for i in range(0, 64, 4)))
            self.assertLessEqual(max(abs(a - b) for a, b in zip(alpha, decoded[3::4])), 18)

    def test_alpha_endpoints_exact(self):
        for alpha in (bytes(16), bytes([255]) * 16):
            self.assertEqual(textures.decode_dxt5(textures.encode_white_bc3_block(alpha), 4, 4)[3::4], alpha)

    def test_only_selected_tile_blocks_change_and_input_immutable(self):
        tiled = bytes(range(256)) * 256
        original = tiled
        alpha = bytes((x * 11 + y * 7) % 256 for y in range(24) for x in range(24))
        out = textures.supplement_white_dxt5_cell(tiled, 512, 64, 420, 24, 24, 24, alpha)
        offsets = {textures.xbox_tiled_block_offset(105 + bx, 6 + by, 128) * 16 for by in range(6) for bx in range(6)}
        changed = {i for i in range(0, len(tiled), 16) if tiled[i:i + 16] != out[i:i + 16]}
        self.assertEqual(changed, offsets)
        self.assertEqual(tiled, original)
        decoded = textures.decode_dxt5(textures.untile_dxt5(out, 512, 64), 512, 64)
        actual = bytes(decoded[((24 + y) * 512 + 420 + x) * 4 + 3] for y in range(24) for x in range(24))
        self.assertLessEqual(max(abs(a - b) for a, b in zip(alpha, actual)), 18)

    def test_inverse_scatter_roundtrip_exact_block_bytes(self):
        linear = bytes(range(256)) + bytes(range(64))
        # A 20x16 cell is 320 bytes, all caller-supplied BC3 bits roundtrip exactly.
        out = textures.scatter_linear_dxt5_cell(bytes(65536), 512, 64, 420, 24, 20, 16, linear)
        decoded = textures.untile_dxt5(out, 512, 64)
        cell = b"".join(decoded[((6 + row) * 128 + 105) * 16:((6 + row) * 128 + 110) * 16] for row in range(4))
        self.assertEqual(cell, linear)

    def test_bad_block_alpha(self):
        for values in (bytes(15), [300] * 16, [-1] * 16):
            with self.assertRaises(textures.FormatError):
                textures.encode_white_bc3_block(values)

    def test_bad_cell_alpha_length(self):
        with self.assertRaises(textures.FormatError):
            textures.supplement_white_dxt5_cell(bytes(65536), 512, 64, 420, 24, 24, 24, bytes(575))

    def test_scatter_rejects_misaligned_and_outside_cells(self):
        for x, y in ((419, 24), (500, 24), (420, 44), (-4, 24)):
            with self.subTest(x=x, y=y), self.assertRaises(textures.FormatError):
                textures.scatter_linear_dxt5_cell(bytes(65536), 512, 64, x, y, 24, 24, bytes(576))

    def test_scatter_rejects_buffer_mismatch(self):
        with self.assertRaises(textures.FormatError):
            textures.scatter_linear_dxt5_cell(bytes(10), 512, 64, 420, 24, 24, 24, bytes(576))


if __name__ == "__main__":
    unittest.main()
