"""Synthetic-only observations: candidates must never become automatic repairs."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.coalesced import EmbeddedFile, SerializedString, parse, serialize
from tools.audit_wide_line_boundaries import audit, main


def fixture(text, encoding='utf-16-le'):
    return serialize([EmbeddedFile(SerializedString('fixture.int', 'ascii', 0),
                                   SerializedString(text, encoding, 0))])


class WideLineBoundaryAuditTests(unittest.TestCase):
    def test_normal_wide_crlf_has_no_candidate(self):
        data = fixture('[Section]\r\nKey=Value\r\n')
        self.assertEqual(audit(data)['candidate_count'], 0)
        self.assertEqual(serialize(parse(data)), data)

    def test_both_parities_are_observations(self):
        report = audit(fixture('A\u0a0d\x00B\u0d41\u000a'))
        doc = report['documents'][0]
        self.assertEqual(doc['candidate_parity'], [0, 1])
        self.assertEqual(doc['container_offsets'],
                         [doc['payload_offset'] + i for i in doc['candidate_offsets']])

    def test_no_repair_or_narrow_codec_guess(self):
        data = fixture('A\u0a0d\x00B')
        self.assertTrue(audit(data)['roundtrip_identical'])
        self.assertEqual(parse(data)[0].content.text, 'A\u0a0d\x00B')
        self.assertEqual(audit(fixture('ASCII\r\n', 'ascii'))['candidate_count'], 0)

    def test_cli_new_output_is_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'input', Path(tmp) / 'report.json'
            data = fixture('A\u0a0d\x00B'); source.write_bytes(data)
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(['--source', str(source), '--expected-sha256',
                               hashlib.sha256(data).hexdigest(), '--output', str(output)])
            self.assertEqual(result, 0); self.assertEqual(source.read_bytes(), data)
            report = json.loads(output.read_bytes())
            self.assertNotIn('text', report['documents'][0])
            self.assertEqual(report['input_sha256'], hashlib.sha256(data).hexdigest())

    def test_wrong_hash_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'input', Path(tmp) / 'report.json'
            data = fixture('x'); source.write_bytes(data)
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(['--source', str(source), '--expected-sha256', '0' * 64,
                               '--output', str(output)])
            self.assertEqual(result, 1); self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), data)

    def test_existing_output_and_source_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input'; data = fixture('x'); source.write_bytes(data)
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(['--source', str(source), '--expected-sha256',
                               hashlib.sha256(data).hexdigest(), '--output', str(source)])
            self.assertEqual(result, 1); self.assertEqual(source.read_bytes(), data)

    def test_source_locked_remainder_profile(self):
        root = Path(__file__).resolve().parents[1]
        p = json.loads((root / 'locales/zh-Hans/remainder-audit.json').read_bytes())
        self.assertEqual(len(p['entries']), 24)
        self.assertEqual(len({e['id'] for e in p['entries']}), 24)
        self.assertEqual(sum(e['classification'] == 'mixed-encoding-structure-research'
                             for e in p['entries']), 3)
        self.assertEqual(sum(e['classification'] == 'isolated-laughter-context-unverified'
                             for e in p['entries']), 1)
        for e in p['entries']:
            self.assertRegex(e['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertNotIn('source', e); self.assertNotIn('translation', e)


if __name__ == '__main__':
    unittest.main()
