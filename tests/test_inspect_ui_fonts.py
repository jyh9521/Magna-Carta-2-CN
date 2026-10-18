import struct
import unittest
from tools.inspect_ui_fonts import inspect_links


class UIFootprintTests(unittest.TestCase):
    def case(self, ref=1, kind='ObjectProperty'):
        data = struct.pack('>i', 0) + struct.pack('>IIIIIIiII', 1, 0, 2, 0, 4, 0, ref, 0, 0)
        tables = dict(names=['None', 'StyleFont', kind], imports=[], exports=[
            dict(path='font.General', class_path='Engine.Font', serial_offset=0, serial_size=0),
            dict(path='style.Text', class_path='Engine.UIStyle_Text', serial_offset=0, serial_size=len(data))])
        return data, tables

    def test_direct_link(self):
        r = inspect_links(*self.case())
        self.assertEqual(r['font_bindings'][0]['font_path'], 'font.General')
        self.assertFalse(r['runtime_binding_verified']); self.assertFalse(r['inheritance_resolved'])

    def test_bad_reference_is_reported(self):
        self.assertEqual(len(inspect_links(*self.case(9))['unparsed']), 1)

    def test_wrong_class(self):
        data, tables = self.case(); tables['exports'][0]['class_path'] = 'Engine.Texture2D'
        self.assertTrue(inspect_links(data, tables)['unparsed'])

    def test_wrong_property_type(self):
        self.assertTrue(inspect_links(*self.case(kind='IntProperty'))['unparsed'])

    def test_null_font_not_inferred(self):
        r = inspect_links(*self.case(0))
        self.assertIsNone(r['font_bindings'][0]['font_path'])

    def test_truncation(self):
        data, tables = self.case()
        self.assertTrue(inspect_links(data[:-1], tables)['unparsed'])

    def test_import(self):
        data, tables = self.case(-1)
        tables['imports'] = [dict(path='import.Font', class_name=dict(name='Font'))]
        self.assertEqual(inspect_links(data, tables)['font_bindings'][0]['font_path'], 'import.Font')
