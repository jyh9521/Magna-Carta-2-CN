import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools import sample_catalog as s
from tools.coalesced import EmbeddedFile, SerializedString, serialize, extract_entries, parse


class SampleCatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = serialize([EmbeddedFile(SerializedString('fixture.int', 'ascii', 0),
            SerializedString('[Scene]\r\nVoice=source {0}\\n\r\nOther=untouched\r\n', 'utf-16-le', 0))])
        row = extract_entries(parse(self.data), 'Game/Coalesced.int')[0]
        self.plan = dict(schema_version=1, input_sha256=s.sha256(self.data), resource=row['resource'],
            source_mode='sha256-utf8', entries=[dict(id=row['id'], source_sha256=s.sha256(row['source'].encode()),
                                                  translation='真实对话 {0}\\n')])
        self.catalog = s.export_catalog(self.data, self.plan)

    def test_export_import_plan_and_binary_identical(self):
        plan = s.import_plan(self.data, self.catalog)
        self.assertEqual(plan, self.plan)
        self.assertEqual(s.rebuild(self.data, plan), s.rebuild(self.data, self.plan))
        self.assertEqual(self.catalog['entries'][0]['status'], 'draft')
        self.assertNotIn('source', plan['entries'][0])

    def test_catalog_translation_is_editable(self):
        self.catalog['entries'][0]['translation'] = '更长的对话样本 {0}\\n'
        after = s.rebuild(self.data, s.import_plan(self.data, self.catalog))
        rows = extract_entries(parse(after), self.plan['resource'])
        self.assertEqual(rows[0]['source'], '更长的对话样本 {0}\\n')
        self.assertEqual(rows[1]['source'], 'untouched')

    def test_tampered_identity_source_selector_hash_and_resource_reject(self):
        for key, value in [('id','missing'), ('source','wrong'), ('section','wrong'),
                           ('key','Other'), ('occurrence',True), ('source_sha256','0'*64), ('resource','other')]:
            catalog = copy.deepcopy(self.catalog); catalog['entries'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): s.import_plan(self.data, catalog)

    def test_tokens_newlines_empty_duplicate_and_wrong_version_reject(self):
        for value in ['', 'lost {0}', '\\n {0}', 'physical\n {0}\\n', 'nul\0 {0}\\n']:
            catalog = copy.deepcopy(self.catalog); catalog['entries'][0]['translation'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): s.import_plan(self.data, catalog)
        self.catalog['entries'] *= 2
        with self.assertRaises(ValueError): s.import_plan(self.data, self.catalog)
        with self.assertRaises(ValueError): s.import_plan(self.data+b'x', self.catalog)

    def test_cli_export_import_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            root=Path(d); src=root/'source'; src.write_bytes(self.data)
            plan=root/'plan.json'; plan.write_text(json.dumps(self.plan),encoding='utf8')
            catalog=root/'catalog.json'; result=root/'result.json'
            self.assertEqual(s.main(['export',str(src),str(plan),'--output',str(catalog)]),0)
            self.assertEqual(s.main(['import',str(src),str(catalog),'--output',str(result)]),0)
            self.assertEqual(json.loads(result.read_bytes()),self.plan)
            self.assertEqual(s.main(['import',str(src),str(catalog),'--output',str(result)]),2)
            self.assertEqual(src.read_bytes(),self.data)


if __name__ == '__main__': unittest.main()
