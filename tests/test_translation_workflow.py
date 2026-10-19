import json
from pathlib import Path
import tempfile
import unittest

from tools.translation_style import style_errors
from tools.export_translation_catalogs import export_sources, digest
from tools.coalesced import parse, serialize
from tools.validate_catalog import validate


class StyleTests(unittest.TestCase):
    rules = {'single_clause_no_full_stop': ['item_description', 'skill_description']}

    def check(self, text, kind='item_description'):
        return style_errors(dict(translation=text, text_kind=kind), self.rules)

    def test_description(self):
        self.assertTrue(self.check('恢复生命值。'))
        self.assertTrue(self.check('恢复生命值.'))
        self.assertFalse(self.check('恢复生命值'))
        self.assertFalse(self.check('恢复生命值，并解除中毒。'))
        self.assertFalse(self.check('恢复生命值。解除中毒。'))

    def test_scope(self):
        self.assertFalse(self.check('喂，你想害死我吗？', 'dialogue'))
        self.assertFalse(self.check('这是普通正文。', 'prose'))
        self.assertFalse(self.check('这是普通正文。', 'unclassified'))

    def test_tokens_and_lines(self):
        self.assertTrue(self.check('恢复{0}点生命值。'))
        self.assertTrue(self.check('普通木剑。\\n攻击+5'))
        self.assertFalse(self.check('普通木剑\\n攻击+5'))
        self.assertTrue(self.check('伤害提高1.5倍。'))
        self.assertTrue(self.check('技能攻击力提高20%。'))

    def test_catalog_opt_in(self):
        row = dict(id='test', resource='fixture', context='fixture', source_locale='und',
                   source='Restores HP.', translation='恢复生命值。', status='draft',
                   reviewer='', text_kind='item_description')
        catalog = dict(schema_version=1, entries=[row])
        self.assertEqual(validate(catalog), [])
        self.assertTrue(validate(catalog, self.rules))
        row['text_kind'] = 'dialogue'
        self.assertEqual(validate(catalog, self.rules), [])


class ExportTests(unittest.TestCase):
    def test_real_shape_synthetic_container(self):
        import struct
        def string(s):
            raw = s.encode('utf-16-le') + b'\0\0'
            return struct.pack('>i', -len(raw)//2) + raw
        raw = struct.pack('>i', 2) + string('..\\Localization\\INT\\Sample.int') + string('[Scene]\nLine=hello\n')
        self.assertEqual(serialize(parse(raw)), raw)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'source').write_bytes(raw)
            source = dict(path='source', sha256=digest(raw), resource='Localization/Coalesced.int',
                          role='translation', source_locale='und', disc=1)
            profile = dict(sources=[source, dict(source, disc=2)])
            report = export_sources(root, profile, root/'out')
            self.assertEqual(report['unique_catalog_entries'], 1)
            self.assertEqual(report['groups'][0]['discs'], [1, 2])
            self.assertEqual(len(list((root/'out').rglob('*.json'))), 2)
            with self.assertRaises(ValueError):
                export_sources(root, profile, root/'out')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                export_sources(root, dict(sources=[dict(source, sha256='0'*64)]), root/'bad')
            self.assertFalse((root/'bad').exists())


if __name__ == '__main__':
    unittest.main()
