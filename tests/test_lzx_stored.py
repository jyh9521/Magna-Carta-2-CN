"""Independent stored-format checks on synthetic data; no native CI requirement."""
import struct
import unittest
from unittest.mock import patch

from tools.lzx_stored import encode_framed, wrap_ue3_chunk


def inspect_stored_stream(data):
    """Tiny test-only decoder for this stored-only subset, not Huffman LZX."""
    output = bytearray()
    at = 0
    frames = []
    while at < len(data):
        if data[at] != 255 or at + 5 > len(data):
            raise ValueError("bad Xbox header")
        count, encoded_count = struct.unpack_from(">HH", data, at + 1)
        at += 5
        if not 1 <= count <= 32768 or at + encoded_count > len(data):
            raise ValueError("bad Xbox range")
        frame = data[at:at + encoded_count]
        at += encoded_count
        if len(frame) < 16:
            raise ValueError("short stored header")
        # Read each word MSB-first as an independent bit sequence.
        bits = ''.join(f'{word:016b}' for word in struct.unpack_from('<HH', frame))
        if not frames:
            if bits[0] != '0':
                raise ValueError("Intel transform enabled")
            bits = bits[1:]
        if int(bits[:3], 2) != 3:
            raise ValueError("not a stored block")
        length = int(bits[3:27], 2)
        if length != count or any(bit != '0' for bit in bits[27:]):
            raise ValueError("stored length/alignment mismatch")
        if struct.unpack_from('<III', frame, 4) != (1, 1, 1):
            raise ValueError("invalid repeated offsets")
        if len(frame) != 16 + count + (count & 1):
            raise ValueError("stored physical size mismatch")
        if count & 1 and frame[-1] != 0:
            raise ValueError("invalid odd pad")
        output += frame[16:16 + count]
        frames.append((count, encoded_count))
    if not frames:
        raise ValueError("empty stream")
    return bytes(output), frames


def inspect_chunk(data):
    magic, block_size, total_comp, total_unc = struct.unpack_from('>IIII', data)
    if magic != 0x9e2a83c1 or block_size != 131072:
        raise ValueError('invalid chunk header')
    count = (total_unc + block_size - 1) // block_size
    table = [struct.unpack_from('>II', data, 16 + i * 8) for i in range(count)]
    if sum(x[0] for x in table) != total_comp or sum(x[1] for x in table) != total_unc:
        raise ValueError('chunk totals mismatch')
    at = 16 + 8 * count
    output = bytearray()
    for compressed, uncompressed in table:
        decoded, _ = inspect_stored_stream(data[at:at + compressed])
        if len(decoded) != uncompressed:
            raise ValueError('chunk output length mismatch')
        output += decoded
        at += compressed
    if at != len(data):
        raise ValueError('unexpected chunk trailer')
    return bytes(output), table


class StoredLzxTests(unittest.TestCase):
    def test_exact_small_golden_bytes(self):
        self.assertEqual(encode_framed(b'A').hex(),
                         'ff00010012003010000100000001000000010000004100')

    def test_boundaries_and_patterns(self):
        for size in (1, 2, 3, 32767, 32768, 32769, 65535, 65536, 98305, 131071, 131072):
            for value in (b'\0', b'\xe8', bytes(range(256))):
                with self.subTest(size=size, pattern=value[:4]):
                    source = (value * ((size + len(value) - 1) // len(value)))[:size]
                    encoded = encode_framed(source)
                    decoded, frames = inspect_stored_stream(encoded)
                    self.assertEqual(decoded, source)
                    self.assertEqual(len(frames), (size + 32767) // 32768)
                    self.assertTrue(all(raw <= 32768 and comp <= 65535 for raw, comp in frames))

    def test_distinct_first_and_later_headers(self):
        source = b'x' * 32769
        encoded = encode_framed(source)
        _, frames = inspect_stored_stream(encoded)
        second = 5 + frames[0][1] + 5
        self.assertEqual(encoded[5:9], b'\x08\x30\0\0')
        self.assertEqual(encoded[second:second + 4], b'\0\x60\x20\0')

    def test_guards(self):
        for invalid in (b'', b'x' * 131073):
            with self.subTest(size=len(invalid)), self.assertRaises(ValueError):
                encode_framed(invalid)
        for invalid in (bytearray(b'x'), 'x', None):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                encode_framed(invalid)
            with self.assertRaises(TypeError):
                wrap_ue3_chunk(invalid)
        with self.assertRaises(ValueError):
            wrap_ue3_chunk(b'')
        with patch('tools.lzx_stored.MAX_CHUNK_SIZE', 3):
            with self.assertRaises(ValueError):
                wrap_ue3_chunk(b'1234')

    def test_chunk_single_multiple_and_partial_blocks(self):
        for size in (1, 32768, 131072, 131073, 262144, 262145):
            with self.subTest(size=size):
                source = bytes((i * 131 + 17) % 256 for i in range(size))
                encoded = wrap_ue3_chunk(source)
                decoded, table = inspect_chunk(encoded)
                self.assertEqual(decoded, source)
                self.assertEqual(len(table), (size + 131071) // 131072)
                self.assertEqual(table[-1][1], (size - 1) % 131072 + 1)

    def test_input_is_unchanged_and_output_deterministic(self):
        source = b'original' * 5000
        identity = bytes(source)
        self.assertEqual(encode_framed(source), encode_framed(source))
        self.assertEqual(wrap_ue3_chunk(source), wrap_ue3_chunk(source))
        self.assertEqual(source, identity)

class OptionalNativeStoredTests(unittest.TestCase):
    @unittest.skipUnless(__import__('os').environ.get('MC2_LZX_LIBRARY'), 'optional native adapter not requested')
    def test_native_roundtrip(self):
        import os
        from pathlib import Path
        from tools.ue3_package import LzxDecoder
        decoder = LzxDecoder(Path(os.environ['MC2_LZX_LIBRARY']))
        for size in (1, 2, 32767, 32768, 32769, 131072):
            with self.subTest(size=size):
                source = bytes((i * 131 + 17) % 256 for i in range(size))
                self.assertEqual(decoder(encode_framed(source), size), source)
        for size in (131073, 262145):
            source = bytes((i * 131 + 17) % 256 for i in range(size))
            chunk = wrap_ue3_chunk(source)
            _, _, _, total = struct.unpack_from('>IIII', chunk)
            count = (total + 131071) // 131072
            table = [struct.unpack_from('>II', chunk, 16 + i * 8) for i in range(count)]
            at = 16 + 8 * count
            decoded = bytearray()
            for compressed, uncompressed in table:
                decoded.extend(decoder(chunk[at:at + compressed], uncompressed))
                at += compressed
            self.assertEqual(decoded, source)
