import hashlib
import struct
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch
from tools.decompress_package import main
from tools.decompress_package import decompress_copy
from tools.ue3_package import parse_summary
from test_supplement_font import package_fixture, stored_decoder


class DecompressCopyTests(unittest.TestCase):
    def fixture(self):
        b = bytearray(package_fixture(compressed=True))
        struct.pack_into('>I', b, 21, 0x0288000d)
        return bytes(b)

    def run_copy(self, b, **kw):
        return decompress_copy(b, hashlib.sha256(b).hexdigest(), stored_decoder, **kw)

    def test_all_compression_fields_and_payload_preserved(self):
        b = self.fixture(); out, report = self.run_copy(b)
        s = parse_summary(out)
        self.assertEqual(s['package_flags'], 0x0088000d)
        self.assertEqual(s['compression_flags'], 0)
        self.assertEqual(s['compressed_chunks'], [])
        self.assertEqual(len(out) % 32768, 0)
        self.assertTrue(report['logical_payload_preserved'])
        self.assertFalse(report['game_rendering_verified'])
        self.assertEqual(b, self.fixture())

    def test_alignment_is_explicit_and_bounded(self):
        for a in (1, 2048, 32768):
            out, _ = self.run_copy(self.fixture(), alignment=a)
            self.assertEqual(len(out) % a, 0)
        for a in (0, -1, True, 65536):
            with self.assertRaises(ValueError):
                self.run_copy(self.fixture(), alignment=a)

    def test_hash_guard(self):
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            decompress_copy(self.fixture(), '0' * 64, stored_decoder)

    def test_uncompressed_input_rejected(self):
        with self.assertRaisesRegex(ValueError, 'LZX-compressed'):
            self.run_copy(package_fixture())

    def test_missing_package_compression_flag(self):
        with self.assertRaisesRegex(ValueError, 'compressed package flag'):
            self.run_copy(package_fixture(compressed=True))

    def test_decoder_failure_propagates(self):
        def bad(*_):
            raise ValueError('decode failed')
        b = self.fixture()
        with self.assertRaisesRegex(ValueError, 'decode failed'):
            decompress_copy(b, hashlib.sha256(b).hexdigest(), bad)


class DecompressCliTests(unittest.TestCase):
    def test_cli_reopens_output_and_report(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'sample.pkg'
            data = DecompressCopyTests().fixture()
            source.write_bytes(data)
            output, report = root / 'output.pkg', root / 'report.json'
            args = [str(source), '--sha256', hashlib.sha256(data).hexdigest(),
                    '--lzx-library', str(root / 'decoder.dll'), '--output', str(output),
                    '--report', str(report)]
            with patch('tools.decompress_package.LzxDecoder', return_value=stored_decoder):
                self.assertEqual(main(args), 0)
                import json
                record = json.loads(report.read_text())
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), record['output_sha256'])
                self.assertEqual(source.read_bytes(), data)
                self.assertEqual(main(args), 1)

    def test_alias_and_existing_paths_fail_before_decoder(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'source.pkg'; source.write_bytes(b'original')
            for output, report in ((source, root/'report'), (root/'out', root/'out')):
                with patch('tools.decompress_package.LzxDecoder') as decoder:
                    self.assertEqual(main([str(source), '--sha256', '0'*64,
                        '--lzx-library', str(root/'decoder.dll'), '--output', str(output),
                        '--report', str(report)]), 1)
                    decoder.assert_not_called()
                self.assertEqual(source.read_bytes(), b'original')
