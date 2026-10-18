"""Self-authored tagged objects; no original game resources required."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.inspect_font_references import consumers, main, tagged_font_consumers
from test_inspect_font_references import package


def fixture(ref=1, kind='ObjectProperty', raw=None, target_class='Engine.Font', suffix=b''):
    names = ['None', 'CustomFont', kind]
    raw = struct.pack('>i', ref) if raw is None else raw
    tag = struct.pack('>6I', 1, 0, 2, 0, len(raw), 3) + raw
    payload = bytes(4) + tag + suffix + bytes(8)
    target = dict(path='Font.General', class_path=target_class, serial_offset=0, serial_size=0)
    owner = dict(path='Default__CustomWidget', class_path='Game.CustomWidget',
                 serial_offset=9, serial_size=len(payload), archetype=-1)
    return bytes(9) + payload, dict(names=names, exports=[target, owner], imports=[])


class FontConsumerTests(unittest.TestCase):
    def test_custom_widget_and_exact_offset(self):
        data, tables = fixture()
        result = tagged_font_consumers(data, tables)
        link, = result['font_consumers']
        self.assertEqual(link['object_index'], 2)
        self.assertEqual(link['property'], 'CustomFont')
        self.assertEqual(link['array_index'], 3)
        self.assertEqual(link['archetype_reference'], -1)
        self.assertEqual(data[link['logical_package_offset']:link['logical_package_offset'] + 4], struct.pack('>i', 1))
        self.assertEqual(result['coverage'], dict(total_exports=2, parsed_tagged_exports=1, skipped_exports=1, unparsed_exports=0))
        self.assertFalse(result['game_rendering_verified'])
        self.assertFalse(result['inheritance_resolved'])

    def test_import_multifont_and_non_font_name(self):
        data, tables = fixture(-1)
        tables['names'][1] = 'CaptionResource'
        tables['imports'] = [dict(path='Other.Font', class_name=dict(name='MultiFont'))]
        link, = tagged_font_consumers(data, tables)['font_consumers']
        self.assertEqual(link['target']['reference_kind'], 'import')
        self.assertEqual(link['target']['class_name'], 'MultiFont')
        self.assertEqual(link['property'], 'CaptionResource')

    def test_null_wrong_class_and_similar_class_are_not_links(self):
        for ref, cls in [(0, 'Engine.Font'), (1, 'Engine.Texture2D'), (1, 'Engine.FontSample')]:
            result = tagged_font_consumers(*fixture(ref, target_class=cls))
            self.assertEqual(result['font_consumers'], [])
            self.assertEqual(result['coverage']['unparsed_exports'], 0)

    def test_bad_reference_or_payload_is_recorded(self):
        for ref, raw in [(9, None), (-1, None), (1, b'bad')]:
            result = tagged_font_consumers(*fixture(ref, raw=raw))
            self.assertEqual(result['font_consumers'], [])
            self.assertEqual(result['coverage']['unparsed_exports'], 1)

    def test_non_object_types_are_not_guessed(self):
        for kind in ('ArrayProperty', 'IntProperty'):
            result = tagged_font_consumers(*fixture(kind=kind))
            self.assertEqual(result['font_consumers'], [])
            self.assertEqual(result['coverage']['parsed_tagged_exports'], 1)

    def test_malformed_later_reference_discards_object(self):
        extra = struct.pack('>6Ii', 1, 0, 2, 0, 4, 0, 99)
        result = tagged_font_consumers(*fixture(suffix=extra))
        self.assertEqual(result['font_consumers'], [])
        self.assertEqual(result['coverage']['unparsed_exports'], 1)

    def test_payload_bounds_and_truncation(self):
        data, tables = fixture()
        for end in range(9, len(data)):
            self.assertEqual(tagged_font_consumers(data[:end], tables)['coverage']['unparsed_exports'], 1)
        tables['exports'][1]['serial_offset'] = -1
        self.assertEqual(tagged_font_consumers(data, tables)['coverage']['unparsed_exports'], 1)

    def test_metadata_skipped(self):
        data, tables = fixture()
        for cls in ('Class', 'Core.Function', 'Core.ObjectProperty', 'Engine.Font', 'Engine.MultiFont', 'Engine.Texture2D'):
            tables['exports'][1]['class_path'] = cls
            result = tagged_font_consumers(data, tables)
            self.assertEqual(result['coverage']['skipped_exports'], 2)
            self.assertEqual(result['font_consumers'], [])

    def test_real_table_wrapper_and_hash_guard(self):
        data = package()
        result = consumers(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(result['coverage']['parsed_tagged_exports'], 1)
        with self.assertRaises(ValueError):
            consumers(data, '0' * 64)

    def test_cli_reopening_modes_and_source_preservation(self):
        with tempfile.TemporaryDirectory() as d:
            source, output = Path(d) / 'source.pkg', Path(d) / 'report.json'
            data = package(); source.write_bytes(data)
            args = [str(source), '--sha256', hashlib.sha256(data).hexdigest(), '--consumers', '--output', str(output)]
            self.assertEqual(main(args), 0)
            self.assertEqual(json.loads(output.read_text()), consumers(data, hashlib.sha256(data).hexdigest()))
            self.assertEqual(main(args), 1)
            self.assertEqual(source.read_bytes(), data)
            for mode in (['--inventory'], ['--object', 'Default__Engine']):
                with self.assertRaises(SystemExit): main(args + mode)


if __name__ == '__main__':
    unittest.main()
