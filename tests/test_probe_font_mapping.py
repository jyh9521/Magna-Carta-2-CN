import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.probe_font_mapping import probe, main
from tools.supplement_font import supplement_package
from tools.ue3_fonts import parse_font_payload
from tools.ue3_package import parse_tables
from test_supplement_font import package_fixture, plan, stored_decoder


class MappingProbeTests(unittest.TestCase):
    def fixture(self):
        b = package_fixture()
        out, _ = supplement_package(b, hashlib.sha256(b).hexdigest(), 'General',
                                     plan(), {0x4E2D: bytes([255]) * 576}, stored_decoder)
        return out

    def change(self, b, **kw):
        args = dict(expected_hash=hashlib.sha256(b).hexdigest(), font_object='General',
                    codepoint=65, expected_glyph=0, target_glyph=1)
        args.update(kw)
        return probe(b, **args)

    def test_only_selected_field_changes_and_reverse_is_exact(self):
        b = self.fixture(); out, report = self.change(b)
        offset = report['field_offset']
        self.assertEqual(len(out), len(b))
        self.assertEqual(out[:offset], b[:offset])
        self.assertEqual(out[offset + 2:], b[offset + 2:])
        self.assertEqual(out[offset:offset + 2], b'\0\1')
        self.assertFalse(report['game_rendering_verified'])
        reverse, _ = self.change(out, expected_glyph=1, target_glyph=0)
        self.assertEqual(reverse, b)
        t = parse_tables(out); e = t['exports'][0]
        f = parse_font_payload(out[e['serial_offset']:e['serial_offset']+e['serial_size']], t['names'])
        self.assertEqual(f['remap'][0]['glyph_index'], 1)

    def test_hash_mapping_and_export_guards(self):
        b = self.fixture()
        for kw in ({'expected_hash': '0'*64}, {'font_object': 'missing'},
                   {'codepoint': 66}, {'expected_glyph': 2}, {'target_glyph': 2},
                   {'target_glyph': 0}, {'codepoint': True}, {'target_glyph': -1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                self.change(b, **kw)

    def test_compressed_input_rejected(self):
        with self.assertRaisesRegex(ValueError, 'uncompressed'):
            self.change(package_fixture(compressed=True))

    def test_cli_outputs_reopen_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source.pkg'; b = self.fixture(); source.write_bytes(b)
            args = [str(source), '--sha256', hashlib.sha256(b).hexdigest(), '--font-object', 'General',
                    '--codepoint', '0x41', '--expected-glyph', '0', '--target-glyph', '1',
                    '--output', str(root/'out.pkg'), '--report', str(root/'report.json')]
            self.assertEqual(main(args), 0)
            r = json.loads((root/'report.json').read_text())
            self.assertEqual(hashlib.sha256((root/'out.pkg').read_bytes()).hexdigest(), r['output_sha256'])
            self.assertEqual(main(args), 1)
            self.assertEqual(source.read_bytes(), b)

    def test_input_output_alias_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source'; source.write_bytes(b'unchanged')
            args = [str(source), '--sha256', '0'*64, '--font-object', 'General',
                    '--codepoint', '65', '--expected-glyph', '0', '--target-glyph', '1',
                    '--output', str(source), '--report', str(root/'report')]
            self.assertEqual(main(args), 1)
            self.assertEqual(source.read_bytes(), b'unchanged')
