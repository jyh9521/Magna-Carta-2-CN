import contextlib
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools.build_coalesced import main, rebuild, sha256
from tools.coalesced import EmbeddedFile, SerializedString, extract_entries, parse, serialize


class RebuildTests(unittest.TestCase):
    def setUp(self):
        self.data = serialize([EmbeddedFile(SerializedString('fixture.int', 'ascii', 0),
                              SerializedString('[Test]\r\nText=source {0}\\n\r\nOther=keep\n', 'utf-16-le', 0))])
        self.rows = extract_entries(parse(self.data), 'synthetic')
        self.plan = dict(schema_version=1, input_sha256=sha256(self.data), resource='synthetic',
                         entries=[dict(id=self.rows[0]['id'], source=self.rows[0]['source'],
                                       translation='自制测试 {0}\\n')])

    def test_variable_length_roundtrip(self):
        out = rebuild(self.data, self.plan)
        rows = extract_entries(parse(out), 'synthetic')
        self.assertNotEqual(len(out), len(self.data))
        self.assertEqual(rows[0]['source'], '自制测试 {0}\\n')
        self.assertEqual(rows[1]['source'], 'keep')
        self.assertIn('Text=自制测试 {0}\\n\r\nOther=keep\n', parse(out)[0].content.text)

    def test_noop_identical(self):
        self.plan['entries'] = []
        self.assertEqual(rebuild(self.data, self.plan), self.data)

    def test_hash_guard(self):
        self.plan['input_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            rebuild(self.data, self.plan)

    def test_expected_source_guard(self):
        self.plan['entries'][0]['source'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'source'):
            rebuild(self.data, self.plan)

    def test_duplicate_id(self):
        self.plan['entries'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            rebuild(self.data, self.plan)

    def test_unknown_id(self):
        self.plan['entries'][0]['id'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'unknown'):
            rebuild(self.data, self.plan)

    def test_tokens_and_newlines(self):
        for target in ['missing tokens', 'line\n {0}\\n', 'line\r {0}\\n', 'nul\0 {0}\\n', '\\n {0}']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.plan['entries'][0]['translation'] = target
                rebuild(self.data, self.plan)

    def test_invalid_schema(self):
        self.plan['schema_version'] = 9
        with self.assertRaises(ValueError):
            rebuild(self.data, self.plan)

    def test_cli_preserves_inputs_and_refuses_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); src = root/'input'; plan = root/'plan.json'; out = root/'output'
            src.write_bytes(self.data); plan.write_text(json.dumps(self.plan), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(src), str(plan), '--output', str(out)]), 0)
                self.assertEqual(main([str(src), str(plan), '--output', str(out)]), 2)
                self.assertEqual(main([str(src), str(plan), '--output', str(src)]), 2)
            self.assertEqual(src.read_bytes(), self.data)


if __name__ == '__main__':
    unittest.main()
