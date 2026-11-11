import struct
import unittest

from tools import texture_inspection as inspection
from tools.ue3_package import Reader, FormatError, parse_summary, parse_tables
from tools.ue3_fonts import read_properties, unique_properties
from tools.supplement_font import decode_logical
from tools.lzx_stored import wrap_ue3_chunk
from test_supplement_font import stored_decoder
from test_texture_layout import profile_fixture


def fixture(fmt=2, width=2, height=2, mips=1, external=False, compressed=False):
    raw, _, _ = profile_fixture()
    summary = parse_summary(raw)
    logical = decode_logical(raw, summary, stored_decoder)
    table = parse_tables(logical, summary, len(logical))
    export = table['exports'][1]
    serial = export['serial_offset']
    reader = Reader(logical[serial:serial + export['serial_size']])
    reader.i32()
    props = unique_properties(read_properties(reader, table['names']))
    payload = bytearray(reader.data[:reader.pos])
    struct.pack_into('>I', payload, props['SizeX']['value_offset'], width)
    struct.pack_into('>I', payload, props['SizeY']['value_offset'], height)
    payload[props['Format']['value_offset']] = fmt
    payload += struct.pack('>IIIII', 0, 0, 0, serial + len(payload) + 16, mips)
    tail = max(0, min(width.bit_length(), height.bit_length()) - 5)
    headers = []
    bulks = {}
    for i in range(mips):
        headers.append(len(payload))
        if i > tail:
            payload += struct.pack('>IIII', 0x21, 0, 0xffffffff, 0xffffffff)
        else:
            layout = inspection.unit_layout(width, height, fmt, i)
            data = bytes((j * 13 + 7) % 256 for j in range(layout['storage_bytes']))
            encoded = wrap_ue3_chunk(data) if compressed or external else data
            flags = 0x41 if external else 0x40 if compressed else 0
            at = 8192 if external else serial + len(payload) + 16
            payload += struct.pack('>IIII', flags, len(data), len(encoded), at)
            if not external:
                payload += encoded
            bulks[i] = encoded
        minimum = 1 if fmt == 2 else 4
        payload += struct.pack('>II', max(minimum, width >> i), max(minimum, height >> i))
    return bytes(payload), table['names'], serial, headers, bulks


class TextureInspectionTests(unittest.TestCase):
    def test_format2_argb_endian_channels(self):
        layout = inspection.unit_layout(2, 2, 2)
        tiled = bytearray(layout['storage_bytes'])
        for offset in layout['offsets']:
            tiled[offset:offset + 4] = bytes([128, 16, 32, 64])
        image = inspection.decode_units(bytes(tiled), layout, 2)
        self.assertEqual(image.tobytes(), bytes([16, 32, 64, 128]) * 4)

    def test_packed_tail_mip_coordinates_and_nonoverlap(self):
        for width, height, fmt in [(1024, 256, 2), (64, 64, 7), (16, 128, 5), (256, 64, 5)]:
            groups = {}
            for mip in range(max(width, height).bit_length()):
                layout = inspection.unit_layout(width, height, fmt, mip)
                prior = groups.setdefault(layout['owner_mip'], set())
                self.assertFalse(prior.intersection(layout['offsets']))
                prior.update(layout['offsets'])
                self.assertLessEqual(max(layout['offsets']) + layout['unit_bytes'], layout['storage_bytes'])
        self.assertEqual(inspection.unit_layout(1024, 256, 2, 10)['origin_units'], [4, 0])

    def test_raw_and_lzx_parse_to_exact_native_end(self):
        for fmt, w, h, count in [(2, 2, 2, 1), (2, 256, 2, 1), (2, 1024, 256, 11), (5, 16, 128, 8), (7, 64, 64, 7)]:
            for compressed in [False, True]:
                p, names, at, _, _ = fixture(fmt, w, h, count, compressed=compressed)
                texture = inspection.read_texture(p, names, at, stored_decoder)
                self.assertEqual(len(texture['mips']), count)
                for mip in texture['mips']:
                    image = inspection.decode_mip(texture, mip['index'])
                    self.assertEqual(image.size, (max(1, w >> mip['index']), max(1, h >> mip['index'])))

    def test_external_requires_explicit_resolver_and_same_chunk_validation(self):
        p, names, at, _, bulks = fixture(5, 128, 32, 8, external=True)
        with self.assertRaisesRegex(FormatError, 'resolver'):
            inspection.read_texture(p, names, at, stored_decoder)
        seen = []
        def resolve(mip):
            seen.append((mip['index'], mip['data_offset']))
            return bulks[mip['index']]
        texture = inspection.read_texture(p, names, at, stored_decoder, resolve)
        self.assertEqual(seen, [(0, 8192), (1, 8192)])
        self.assertEqual(inspection.decode_mip(texture, 0).size, (128, 32))
        with self.assertRaises(FormatError):
            inspection.read_texture(p, names, at, stored_decoder, lambda _: b'bad')

    def test_unknown_flags_sentinel_inline_pointer_and_native_size_rejected(self):
        p, names, at, headers, _ = fixture(5, 16, 128, 8)
        for offset, value in [(headers[0], 128), (headers[0] + 12, 0), (headers[1] + 4, 1), (headers[1] + 8, 0), (len(p) - 4, 8)]:
            changed = bytearray(p)
            struct.pack_into('>I', changed, offset, value)
            with self.subTest(offset=offset), self.assertRaises(FormatError):
                inspection.read_texture(bytes(changed), names, at, stored_decoder)
        with self.assertRaises(FormatError):
            inspection.read_texture(p + b'\0', names, at, stored_decoder)

    def test_tail_owner_and_allocation_counts_fail_closed(self):
        p, names, at, headers, _ = fixture(5, 16, 128, 8)
        for offset, value in [(headers[0] + 4, 8191), (headers[0], 0x21), (headers[1], 0)]:
            changed = bytearray(p)
            struct.pack_into('>I', changed, offset, value)
            with self.assertRaises(FormatError):
                inspection.read_texture(bytes(changed), names, at, stored_decoder)

    def test_geometry_and_mip_bounds(self):
        for args in [(3, 2, 2), (True, 2, 2), (2, 2, 6), (2, 2, 2, 2), (8192, 8192, 2)]:
            with self.assertRaises(FormatError):
                inspection.unit_layout(*args)


if __name__ == '__main__':
    unittest.main()
