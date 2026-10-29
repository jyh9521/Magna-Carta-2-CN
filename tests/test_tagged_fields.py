import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch as mock_patch

from tools.patch_tagged_fields import digest, main, patch, prepare, scalar_bytes, select_field
from tools.audit_ui_spacing import ini_rows, width
from tools.coalesced import EmbeddedFile, SerializedString


class Fixture:
    def __init__(self):
        self.names = ['None', 'Position', 'StructProperty', 'UIBounds', 'Value', 'FloatProperty',
                      'Alignment', 'ByteProperty', 'Enabled', 'BoolProperty']

    def name(self, value):
        return struct.pack('>II', self.names.index(value), 0)

    def tag(self, name, kind, raw, index=0, structure=None, boolean=None):
        result = self.name(name) + self.name(kind) + struct.pack('>II', len(raw), index)
        if structure:
            result += self.name(structure)
        if boolean is not None:
            result += struct.pack('>I', boolean)
        return result + raw

    def build(self):
        children = self.tag('Value', 'FloatProperty', struct.pack('>f', 100))
        children += self.tag('Value', 'FloatProperty', struct.pack('>f', 30), 2) + self.name('None')
        payload = b'\0' * 4 + self.tag('Position', 'StructProperty', children, structure='UIBounds')
        payload += self.tag('Alignment', 'ByteProperty', b'\x02')
        payload += self.tag('Enabled', 'BoolProperty', b'', boolean=1) + self.name('None')
        data = b'header' + payload + b'unrelated'
        ctx = dict(logical=data, tables=dict(names=self.names, exports=[dict(path='Scene.Label', class_path='Label', serial_offset=6, serial_size=len(payload))]))
        fields = [dict(property_path=[dict(name='Position', array_index=0), dict(name='Value', array_index=0)], type='FloatProperty', before=100, after=80),
                  dict(property_path=[dict(name='Alignment', array_index=0)], type='ByteProperty', before=2, after=0),
                  dict(property_path=[dict(name='Enabled', array_index=0)], type='BoolProperty', before=1, after=0)]
        changed = bytearray(payload)
        for f in fields:
            kind, offset, old = select_field(payload, self.names, 4, f['property_path'])
            changed[offset:offset + len(old)] = scalar_bytes(kind, f['after'])
        plan = dict(schema_version=1, profile='ue3-tagged-scalar-fields-v1', objects=[dict(object_path='Scene.Label', class_path='Label', tagged_offset=4,
                    before_sha256=digest(payload), after_sha256=digest(changed), fields=fields)])
        return data, ctx, plan


class TaggedFieldTests(unittest.TestCase):
    def setUp(self):
        self.data, self.ctx, self.plan = Fixture().build()

    def test_same_size_precise_fields_and_byte_identical_inverse(self):
        result, report = patch(self.data, self.ctx, self.plan)
        self.assertEqual(len(result), len(self.data))
        self.assertEqual(result[:6], self.data[:6]); self.assertEqual(result[-9:], b'unrelated')
        self.assertEqual(report['fields'], 3); self.assertTrue(report['inverse_byte_identical'])
        self.assertFalse(report['game_rendering_verified'])
        restored, _ = patch(result, dict(self.ctx, logical=result), self.plan, reverse=True)
        self.assertEqual(restored, self.data)

    def test_modified_state_rejects_baseline_and_double_application(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            prepare(self.data, self.ctx, self.plan, 'modified')
        result, _ = patch(self.data, self.ctx, self.plan)
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            patch(result, dict(self.ctx, logical=result), self.plan)

    def test_unrelated_bytes_compose_but_selected_payload_drift_fails(self):
        data = self.data[:-9] + b'unchanged'
        result, _ = patch(data, dict(self.ctx, logical=data), self.plan)
        self.assertEqual(result[-9:], b'unchanged')
        data = self.data[:7] + b'X' + self.data[8:]
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            patch(data, dict(self.ctx, logical=data), self.plan)

    def test_expected_scalar_hash_and_type_guards(self):
        for field, value in [('before', 99), ('type', 'IntProperty'), ('after', 100)]:
            p = copy.deepcopy(self.plan); p['objects'][0]['fields'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                patch(self.data, self.ctx, p)
        p = copy.deepcopy(self.plan); p['objects'][0]['after_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            patch(self.data, self.ctx, p)

    def test_duplicate_objects_fields_missing_and_wrong_prefix(self):
        variants = []
        p = copy.deepcopy(self.plan); p['objects'] *= 2; variants.append(p)
        p = copy.deepcopy(self.plan); p['objects'][0]['fields'] *= 2; variants.append(p)
        p = copy.deepcopy(self.plan); p['objects'][0]['object_path'] = 'Missing'; variants.append(p)
        p = copy.deepcopy(self.plan); p['objects'][0]['tagged_offset'] = 8; variants.append(p)
        p = copy.deepcopy(self.plan); p['objects'][0]['fields'][0]['property_path'][1]['array_index'] = 9; variants.append(p)
        for p in variants:
            with self.subTest(plan=p), self.assertRaises(ValueError):
                patch(self.data, self.ctx, p)

    def test_context_identity_class_and_export_bounds(self):
        with self.assertRaises(ValueError):
            patch(self.data + b'x', self.ctx, self.plan)
        for key, value in [('class_path', 'Other'), ('serial_size', 99999)]:
            c = copy.deepcopy(self.ctx); c['tables']['exports'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                patch(self.data, c, self.plan)

    def test_scalar_limits(self):
        for kind, value in [('FloatProperty', float('nan')), ('FloatProperty', float('inf')), ('FloatProperty', True),
                            ('BoolProperty', 2), ('BoolProperty', False), ('ByteProperty', 256), ('IntProperty', '3'), ('StrProperty', 'x')]:
            with self.subTest(kind=kind, value=value), self.assertRaises((ValueError, struct.error)):
                scalar_bytes(kind, value)

    def test_cli_exact_hash_guard_new_outputs_and_no_source_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'source.xxx'; profile = root/'profile.json'
            output = root/'out.xxx'; report = root/'diff.json'
            source.write_bytes(self.data); profile.write_bytes(json.dumps(self.plan).encode())
            args = ['apply', str(source), '--source-sha256', digest(self.data), '--profile', str(profile),
                    '--profile-sha256', digest(profile.read_bytes()), '--output', str(output), '--report', str(report)]
            with mock_patch('tools.patch_tagged_fields.parse_summary', return_value=dict(compression_flags=0, byte_order='big')), mock_patch('tools.patch_tagged_fields.context', return_value=self.ctx):
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args), 2)
                alias = args.copy(); alias[alias.index('--output') + 1] = str(source)
                self.assertEqual(main(alias), 2)
            self.assertEqual(source.read_bytes(), self.data)
            self.assertEqual(digest(output.read_bytes()), json.loads(report.read_bytes())['output_sha256'])
            args[args.index('--source-sha256') + 1] = '0' * 64
            self.assertEqual(main(args), 2)

    def test_locale_contract_covers_all_five_dynamic_cost_consumers(self):
        root = Path(__file__).resolve().parents[1]
        fields = json.loads((root/'locales/zh-Hans/gameplay-ui-fields-v9.json').read_bytes())
        spacing = json.loads((root/'locales/zh-Hans/gameplay-ui-spacing-v9.json').read_bytes())
        self.assertEqual(len(fields['objects']), 15)
        self.assertEqual(sum(len(o['fields']) for o in fields['objects']), 21)
        self.assertEqual([r['name'] for r in spacing['cost_roles']], ['Selected', 'X_0', 'X_1', 'X_2', 'X_3'])
        self.assertEqual([len(r['shadows']) for r in spacing['cost_roles']], [4] * 5)
        self.assertEqual(spacing['names']['expected_count'], 119)
        self.assertEqual(spacing['numeric_domain']['expected_count'], 620)
        self.assertEqual(len(spacing['footer_groups']), 2)

    def test_font_advance_remap_and_missing_glyph(self):
        font = dict(is_remapped=True, remap=[dict(codepoint=ord('甲'), glyph_index=0), dict(codepoint=ord('1'), glyph_index=1)],
                    characters=[dict(USize=27), dict(USize=12)])
        self.assertEqual(width('甲1', font), 39)
        with self.assertRaisesRegex(ValueError, 'missing'):
            width('乙', font)

    def test_ini_lookup_preserves_machine_keys_and_duplicates(self):
        file = EmbeddedFile(SerializedString('..\\Test.int', 'ascii', 0), SerializedString('[Section]\nKey=值\n', 'utf-16-le', 0))
        self.assertEqual(ini_rows([file], 'Test.int'), [dict(section='Section', key='Key', value='值')])
        with self.assertRaises(ValueError):
            ini_rows([file, file], 'Test.int')


if __name__ == '__main__':
    unittest.main()
