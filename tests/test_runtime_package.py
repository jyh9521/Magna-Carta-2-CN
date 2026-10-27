import hashlib
import struct
import unittest

from tools.runtime_package import normalize_package
from tools.ue3_package import parse_summary, parse_tables
from tools.supplement_font import decode_logical
from tools.texture_layout import read_texture
from tools.ue3_fonts import read_properties, unique_properties
from tools.ue3_package import Reader
from test_supplement_font import stored_decoder
from test_texture_layout import profile_fixture


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture(outer=False, bulk=False, fmt=7):
    data, _, _ = profile_fixture(fmt, compressed=bulk, package_compressed=outer)
    if outer:
        data = bytearray(data)
        struct.pack_into('>I', data, 21, parse_summary(data)['package_flags'] | 0x02000000)
        data = bytes(data)
    return data


def texture(data):
    summary = parse_summary(data)
    logical = decode_logical(data, summary, stored_decoder)
    tables = parse_tables(logical, summary, len(logical))
    export = tables['exports'][1]
    payload = logical[export['serial_offset']:export['serial_offset'] + export['serial_size']]
    for fmt in (5, 7):
        try:
            tx = read_texture(payload, tables['names'], export['serial_offset'],
                              {'kind': 'xbox-inline-bc-v1', 'format': fmt}, stored_decoder)
            return logical, tables, export, tx
        except ValueError:
            pass
    raise AssertionError('fixture texture was not readable')


class RuntimePackageTests(unittest.TestCase):
    def test_generated_outer_clears_all_three_compression_fields(self):
        data = fixture(outer=True)
        result, proof = normalize_package(data, sha(data), stored_decoder)
        summary = parse_summary(result)
        self.assertEqual(summary['compression_flags'], 0)
        self.assertEqual(summary['compressed_chunks'], [])
        self.assertEqual(summary['package_flags'] & 0x02000000, 0)
        self.assertEqual(len(result) % 32768, 0)
        self.assertGreater(proof['generated_outer_chunks'], 0)
        self.assertTrue(proof['outer_decompressed'])
        self.assertFalse(proof['game_rendering_verified'])

    def test_generated_bulk_becomes_raw_without_reencoding_tiles(self):
        for fmt in (5, 7):
            for outer in (False, True):
                with self.subTest(fmt=fmt, outer=outer):
                    data = fixture(outer=outer, bulk=True, fmt=fmt)
                    old_logical, old_tables, old_export, old_texture = texture(data)
                    result, proof = normalize_package(data, sha(data), stored_decoder)
                    logical, tables, export, tx = texture(result)
                    self.assertEqual(tx['flags'], 0)
                    self.assertEqual(tx['tiles'], old_texture['tiles'])
                    self.assertGreater(export['serial_offset'], old_export['serial_offset'])
                    self.assertEqual(proof['converted_bulk_count'], 1)
                    self.assertTrue(proof['native_tiles_preserved'])
                    for idx in (0, 2):
                        before, after = old_tables['exports'][idx], tables['exports'][idx]
                        self.assertEqual(before, after)
                        off, size = before['serial_offset'], before['serial_size']
                        self.assertEqual(old_logical[off:off + size], logical[off:off + size])
                    self.assertEqual(data, fixture(outer=outer, bulk=True, fmt=fmt))

    def test_already_raw_input_is_byte_identical(self):
        data = fixture()
        result, proof = normalize_package(data, sha(data), stored_decoder)
        self.assertEqual(result, data)
        self.assertFalse(proof['changed'])
        self.assertEqual(proof['input_sha256'], proof['output_sha256'])

    def test_normalization_is_idempotent(self):
        data = fixture(outer=True, bulk=True)
        result, _ = normalize_package(data, sha(data), stored_decoder)
        again, proof = normalize_package(result, sha(result), stored_decoder)
        self.assertEqual(result, again)
        self.assertFalse(proof['changed'])

    def test_expected_sha_is_mandatory_before_decoding(self):
        def unexpected(*_):
            self.fail('decoder called before hash guard')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            normalize_package(fixture(outer=True), '0' * 64, unexpected)

    def test_inconsistent_outer_package_bit_is_rejected(self):
        data = bytearray(fixture(outer=True))
        struct.pack_into('>I', data, 21, parse_summary(data)['package_flags'] & ~0x02000000)
        data = bytes(data)
        with self.assertRaisesRegex(ValueError, 'package flag'):
            normalize_package(data, sha(data), stored_decoder)

    def test_uncompressed_with_compressed_package_bit_is_rejected(self):
        data = bytearray(fixture())
        struct.pack_into('>I', data, 21, parse_summary(data)['package_flags'] | 0x02000000)
        data = bytes(data)
        with self.assertRaisesRegex(ValueError, 'package flag'):
            normalize_package(data, sha(data), stored_decoder)

    def test_unknown_serialization_version_is_rejected(self):
        data = bytearray(fixture())
        struct.pack_into('>I', data, 4, 447 | 25 << 16)
        data = bytes(data)
        with self.assertRaisesRegex(ValueError, 'serialization profile'):
            normalize_package(data, sha(data), stored_decoder)

    def test_hashes_sizes_and_nonselected_export_evidence(self):
        data = fixture(outer=True, bulk=True)
        result, proof = normalize_package(data, sha(data), stored_decoder)
        self.assertEqual(proof['input_sha256'], sha(data))
        self.assertEqual(proof['output_sha256'], sha(result))
        self.assertEqual(proof['output_size'], len(result))
        self.assertEqual(proof['nonselected_exports_preserved'], 2)
        record = proof['textures'][0]
        self.assertEqual(record['before_tiles_sha256'], record['after_tiles_sha256'])
        self.assertEqual(record['after_flags'], 0)

    def test_valid_nonidentical_stored_bulk_is_not_misidentified_as_generated(self):
        data = fixture(bulk=True)
        _, _, export, tx = texture(data)
        data = bytearray(data)
        # R0 differs, but these raw stored blocks never use a repeat offset.
        at = export['serial_offset'] + tx['payload_offset'] + 24 + 5 + 4
        data[at] = 2
        data = bytes(data)
        result, proof = normalize_package(data, sha(data), stored_decoder)
        self.assertEqual(result, data)
        self.assertFalse(proof['changed'])
        self.assertEqual(proof['original_lzx_texture_exports_preserved'], 1)

    def test_non_generated_compressed_outer_is_retained_exactly(self):
        data = bytearray(fixture(outer=True))
        for chunk in parse_summary(data)['compressed_chunks']:
            # Each small synthetic chunk has one UE3 block and one Xbox frame.
            data[chunk['compressed_offset'] + 24 + 5 + 4] = 2
        data = bytes(data)
        result, proof = normalize_package(data, sha(data), stored_decoder)
        self.assertEqual(result, data)
        self.assertEqual(proof['generated_outer_chunks'], 0)
        self.assertFalse(proof['changed'])

    def test_unknown_texture_with_generated_stream_fails_closed(self):
        data = fixture(bulk=True)
        logical, tables, export, _ = texture(data)
        off = export['serial_offset']
        reader = Reader(logical[off:off + export['serial_size']])
        reader.i32()
        props = unique_properties(read_properties(reader, tables['names']))
        data = bytearray(data)
        data[off + props['Format']['value_offset']] = 2
        data = bytes(data)
        with self.assertRaisesRegex(ValueError, 'generated stored-LZX in unsupported texture'):
            normalize_package(data, sha(data), stored_decoder)

    def test_unknown_raw_texture_layout_is_preserved_not_guessed(self):
        data = fixture()
        logical, tables, export, _ = texture(data)
        off = export['serial_offset']
        reader = Reader(logical[off:off + export['serial_size']])
        reader.i32()
        props = unique_properties(read_properties(reader, tables['names']))
        data = bytearray(data)
        data[off + props['Format']['value_offset']] = 2
        data = bytes(data)
        result, proof = normalize_package(data, sha(data), stored_decoder)
        self.assertEqual(result, data)
        self.assertEqual(proof['raw_texture_exports_preserved'], 1)


if __name__ == '__main__':
    unittest.main()
