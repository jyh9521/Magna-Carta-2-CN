"""Synthetic packages only; no game assets or native decoder are required."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.rebuild_tagged_strings import apply, rollback, rewrite_payload, main, digest, PROFILE
from tools.patch_tagged_strings import wide_string
from tools.ue3_package import parse_tables, parse_summary


def fixture():
    names = ['None', 'Label', 'Other', 'Stats', 'SStats', 'Value', 'Location', 'Vector',
             'StrProperty', 'IntProperty', 'StructProperty', 'Core', 'Package', 'Class',
             'Thing', 'ObjectA', 'ObjectB', 'ObjectProperty', 'Link', 'NameProperty', 'Name',
             'FloatProperty', 'CreationTime', 'ByteProperty', 'Flag', 'BoolProperty']
    word = lambda *v: struct.pack('>' + 'I' * len(v), *[x & 0xffffffff for x in v])
    fn = lambda n: word(names.index(n), 0)
    string = lambda s: word(len(s) + 1) + s.encode() + b'\0'
    tag = lambda n, t, raw: fn(n) + fn(t) + word(len(raw), 0) + raw
    nested = tag('Value', 'IntProperty', word(30)) + fn('None')
    body = (word(73) + tag('Label', 'StrProperty', wide_string('甲'))
            + tag('Other', 'StrProperty', wide_string('保持'))
            + fn('Stats') + fn('StructProperty') + word(len(nested), 0) + fn('SStats') + nested
            + fn('Location') + fn('StructProperty') + word(12, 0) + fn('Vector') + struct.pack('>fff', 1, 2, 3)
            + tag('Link', 'ObjectProperty', word(2)) + tag('Name', 'NameProperty', fn('ObjectB'))
            + tag('CreationTime', 'FloatProperty', struct.pack('>f', 1.25))
            + tag('Flag', 'ByteProperty', b'\x01') + fn('None'))
    other = word(74) + fn('None') + b'UNSUPPORTED NATIVE TAIL RETAINED'
    nt = b''.join(string(n) + bytes(8) for n in names)
    im = fn('Core') + fn('Package') + word(0) + fn('Core')
    im += fn('Core') + fn('Class') + word(-1) + fn('Thing')
    export_at = 101 + len(nt) + len(im); header_size = export_at + 2 * 68
    def export(name, size, offset):
        return word(-2, 0, 0) + fn(name) + word(0) + bytes(8) + word(size, offset, 0, 0, 0) + bytes(16)
    exports = export('ObjectA', len(body), header_size) + export('ObjectB', len(other), header_size + len(body))
    header = b'\x9e\x2a\x83\xc1' + word((25 << 16) | 446, header_size) + string('None')
    header += word(0, len(names), 101, 2, export_at, 2, 101 + len(nt), 0)
    header += bytes(16) + word(1, 2, len(names), 0, 3004, 42, 0, 0)
    raw = header + nt + im + exports + body + other
    fields = [dict(name='Label', array_index=0, before='甲', after='乙丙丁')]
    changed, _ = rewrite_payload(body, parse_tables(raw), fields)
    plan = dict(schema_version=1, profile=PROFILE, source_sha256=digest(raw), source_size=len(raw), output_alignment=32768,
                objects=[dict(object_path='ObjectA', class_path='Core.Thing', tagged_offset=4,
                              before_sha256=digest(body), after_sha256=digest(changed), fields=fields)])
    return raw, plan


class RebuildTaggedStringTests(unittest.TestCase):
    def setUp(self): self.data, self.plan = fixture()

    def test_growth_changes_only_selected_table_record_and_appends(self):
        output, report = apply(self.data, self.plan)
        self.assertGreater(len(output), len(self.data))
        self.assertEqual(len(output) % 32768, 0)
        self.assertEqual(parse_summary(output), parse_summary(self.data))
        before, after = parse_tables(self.data), parse_tables(output)
        self.assertEqual(before['exports'][1], after['exports'][1])
        row = report['changes'][0]; at = row['table_offset'] + 32
        restored_prefix = bytearray(output[:len(self.data)]); restored_prefix[at:at + 8] = bytes.fromhex(row['old_metadata_hex'])
        self.assertEqual(bytes(restored_prefix), self.data)
        self.assertEqual(rollback(output, self.plan, report)[0], self.data)
        self.assertEqual(report['fields'], 1)
        self.assertTrue(report['unselected_exports_preserved'])
        self.assertTrue(report['original_payloads_retained_inactive'])

    def test_shrinking_and_multiple_fields_are_length_delimited_not_padded(self):
        plan = copy.deepcopy(self.plan)
        plan['objects'][0]['fields'] = [dict(name='Other', array_index=0, before='保持', after='留'),
                                       dict(name='Label', array_index=0, before='甲', after='😀 more')]
        t = parse_tables(self.data); e = t['exports'][0]; b = self.data[e['serial_offset']:e['serial_offset'] + e['serial_size']]
        expected, _ = rewrite_payload(b, t, plan['objects'][0]['fields'])
        plan['objects'][0]['after_sha256'] = digest(expected)
        output, report = apply(self.data, plan); changed = parse_tables(output)['exports'][0]
        self.assertEqual(output[changed['serial_offset']:changed['serial_offset'] + changed['serial_size']], expected)
        self.assertEqual(changed['serial_size'], len(expected))
        self.assertEqual(rollback(output, plan, report)[0], self.data)

    def test_source_identity_class_hash_and_duplicate_selection_guards(self):
        edits = [('source_sha256', '0' * 64), ('source_size', len(self.data) + 1), ('schema_version', True), ('profile', 'unknown'),
                 ('output_alignment', 4), ('output_alignment', True)]
        for key, value in edits:
            plan = copy.deepcopy(self.plan); plan[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): apply(self.data, plan)
        for key, value in [('object_path', 'absent'), ('class_path', 'Wrong'), ('tagged_offset', 8),
                           ('before_sha256', '0' * 64), ('after_sha256', '0' * 64)]:
            plan = copy.deepcopy(self.plan); plan['objects'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): apply(self.data, plan)
        plan = copy.deepcopy(self.plan); plan['objects'] *= 2
        with self.assertRaises(ValueError): apply(self.data, plan)
        plan = copy.deepcopy(self.plan); plan['objects'][0]['fields'] *= 2
        with self.assertRaises(ValueError): apply(self.data, plan)
        out, _ = apply(self.data, self.plan)
        with self.assertRaises(ValueError): apply(out, self.plan)

    def test_wrong_original_value_nonstring_empty_and_tokens_fail_closed(self):
        for key, value in [('before', '错'), ('after', ''), ('after', '甲'), ('name', 'Location'),
                           ('array_index', True), ('array_index', 1)]:
            plan = copy.deepcopy(self.plan); plan['objects'][0]['fields'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): apply(self.data, plan)
        t = parse_tables(self.data); e = t['exports'][0]; p = self.data[e['serial_offset']:e['serial_offset'] + e['serial_size']]
        fields = [dict(name='Label', array_index=0, before='甲', after='%s')]
        with self.assertRaisesRegex(ValueError, 'token'): rewrite_payload(p, t, fields)

    def test_receipt_mutations_and_candidate_corruption_fail(self):
        output, report = apply(self.data, self.plan)
        for key, value in [('output_sha256', '0' * 64), ('source_size', len(self.data) + 1),
                           ('plan_semantic_sha256', '0' * 64), ('schema_version', True)]:
            changed = copy.deepcopy(report); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): rollback(output, self.plan, changed)
        for key, value in [('before_offset', 0), ('before_size', 0), ('object_index', 2), ('table_offset', 0),
                           ('old_metadata_hex', '0' * 16)]:
            changed = copy.deepcopy(report); changed['changes'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): rollback(output, self.plan, changed)
        corrupt = bytearray(output); corrupt[-1] ^= 1
        with self.assertRaises(ValueError): rollback(bytes(corrupt), self.plan, report)

    def test_native_tail_array_and_unsupported_struct_are_rejected(self):
        table = parse_tables(self.data); e = table['exports'][0]
        source = self.data[e['serial_offset']:e['serial_offset'] + e['serial_size']]
        fields = self.plan['objects'][0]['fields']
        with self.assertRaisesRegex(ValueError, 'tail'): rewrite_payload(source + b'X', table, fields)
        # Reinterpret an existing type name without changing the property bytes.
        for kind in ('ArrayProperty', 'DelegateProperty', 'InterfaceProperty'):
            changed = copy.deepcopy(table); changed['names'][changed['names'].index('IntProperty')] = kind
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'unsupported'):
                rewrite_payload(source, changed, fields)
        changed = copy.deepcopy(table); changed['names'][changed['names'].index('Vector')] = 'UnknownNative'
        with self.assertRaises(ValueError): rewrite_payload(source, changed, fields)

    def test_stack_and_class_default_objects_are_rejected(self):
        e = parse_tables(self.data)['exports'][0]
        for low, high in [(0x02000000, 0), (0, 0x200)]:
            data = bytearray(self.data); struct.pack_into('>II', data, e['table_offset'] + 24, low, high)
            plan = copy.deepcopy(self.plan); plan['source_sha256'] = digest(data)
            with self.assertRaisesRegex(ValueError, 'stack/CDO'): apply(bytes(data), plan)

    def test_selected_source_payload_alias_is_not_assumed_inactive(self):
        table = parse_tables(self.data); first, second = table['exports']
        raw = bytearray(self.data)
        struct.pack_into('>II', raw, second['table_offset'] + 32, 4, first['serial_offset'])
        plan = copy.deepcopy(self.plan); plan['source_sha256'] = digest(raw)
        with self.assertRaisesRegex(ValueError, 'overlapping source export'): apply(bytes(raw), plan)

    def test_explicit_numeric_percent_literals_and_real_tokens(self):
        from tools.rebuild_tagged_strings import _protected
        field = dict(literal_percentages=['30%'])
        _protected('Restore 30% energy %s', '恢复30%能量 %s', field)
        _protected('30% recovery', '30% energy', field)  # % e is not a formatter here.
        for target in ('恢复40%能量 %s', '恢复130%能量 %s', '恢复30%能量 %d', '30% 30% %s'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                _protected('Restore 30% energy %s', target, field)
        for value in ([{}], ['bad'], ['30%', '30%'], None):
            with self.assertRaises(ValueError): _protected('30%', '30%', dict(literal_percentages=value))

    def test_duplicate_json_and_source_hash_cli_fail_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.xxx'; plan = root/'plan.json'; output = root/'out.xxx'
            source.write_bytes(self.data); plan.write_bytes(b'{"schema_version":1,"schema_version":1}')
            args = ['apply', str(source), '--source-sha256', digest(self.data), '--plan', str(plan),
                    '--plan-sha256', digest(plan.read_bytes()), '--output', str(output), '--report', str(root/'report.json')]
            self.assertEqual(main(args), 2); self.assertFalse(output.exists())
            plan.write_bytes((json.dumps(self.plan) + '\n').encode())
            args[args.index('--plan-sha256') + 1] = digest(plan.read_bytes())
            args[args.index('--source-sha256') + 1] = '0' * 64
            self.assertEqual(main(args), 2); self.assertFalse(output.exists())

    def test_cli_guarded_apply_and_rollback_and_no_source_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.xxx'; plan = root/'plan.json'
            output = root/'modified.xxx'; journal = root/'journal.json'; restored = root/'restored.xxx'
            source.write_bytes(self.data); plan.write_bytes((json.dumps(self.plan) + '\n').encode())
            common = ['--plan', str(plan), '--plan-sha256', digest(plan.read_bytes())]
            self.assertEqual(main(['apply', str(source), '--source-sha256', digest(self.data), *common,
                                   '--output', str(output), '--report', str(journal)]), 0)
            self.assertEqual(main(['rollback', str(output), '--source-sha256', digest(output.read_bytes()), *common,
                                   '--journal', str(journal), '--journal-sha256', digest(journal.read_bytes()),
                                   '--output', str(restored), '--report', str(root/'restore.json')]), 0)
            self.assertEqual(restored.read_bytes(), self.data)
            self.assertEqual(source.read_bytes(), self.data)
            self.assertEqual(main(['apply', str(source), '--source-sha256', digest(self.data), *common,
                                   '--output', str(source), '--report', str(root/'bad.json')]), 2)


if __name__ == '__main__': unittest.main()
