"""Synthetic nested data bindings, never proprietary package fixtures."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.rebuild_tagged_strings import (
    NESTED_PROFILE, PROFILE, apply, digest, main, rewrite_nested_payload, rollback,
)
from tools.patch_tagged_strings import wide_string
from tools.ue3_package import parse_tables


def path(*names):
    return [dict(name=name, array_index=0) for name in names]


def fixture():
    names = ['None', 'DataSource', 'Binding', 'MarkupString', 'Other', 'Children',
             'StrProperty', 'StructProperty', 'ArrayProperty', 'Core', 'Package',
             'Class', 'Thing', 'ObjectA', 'ObjectB', 'Inner']
    word = lambda *v: struct.pack('>' + 'I' * len(v), *[n & 0xffffffff for n in v])
    fn = lambda s: word(names.index(s), 0)
    string = lambda s: word(len(s) + 1) + s.encode('ascii') + b'\0'
    tag = lambda n, t, v: fn(n) + fn(t) + word(len(v), 0) + v
    struct_tag = lambda n, v: fn(n) + fn('StructProperty') + word(len(v), 0) + fn('Binding') + v
    inner = tag('MarkupString', 'StrProperty', string('NO DATA')) + fn('None')
    binding = (tag('MarkupString', 'StrProperty', string('Item Name'))
               + tag('Other', 'StrProperty', wide_string('保持')) + struct_tag('Inner', inner) + fn('None'))
    body = word(31) + struct_tag('DataSource', binding) + tag('Children', 'ArrayProperty', word(2, 2, -1)) + fn('None')
    other = word(32) + fn('None') + b'UNSELECTED NATIVE DATA'
    nt = b''.join(string(n) + bytes(8) for n in names)
    imports = fn('Core') + fn('Package') + word(0) + fn('Core')
    imports += fn('Core') + fn('Class') + word(-1) + fn('Thing')
    export_at = 101 + len(nt) + len(imports); header_size = export_at + 2 * 68
    def export(name, size, at):
        return word(-2, 0, 0) + fn(name) + word(0) + bytes(8) + word(size, at, 0, 0, 0) + bytes(16)
    exports = export('ObjectA', len(body), header_size) + export('ObjectB', len(other), header_size + len(body))
    header = b'\x9e\x2a\x83\xc1' + word((25 << 16) | 446, header_size) + string('None')
    header += word(0, len(names), 101, 2, export_at, 2, 101 + len(nt), 0)
    header += bytes(16) + word(1, 2, len(names), 0, 3004, 42, 0, 0)
    raw = header + nt + imports + exports + body + other
    fields = [dict(path=path('DataSource', 'MarkupString'), before_encoding='ascii', before='Item Name', after='物品名称'),
              dict(path=path('DataSource', 'Inner', 'MarkupString'), before_encoding='ascii', before='NO DATA', after='暂无数据')]
    arrays = [path('Children')]
    new, _ = rewrite_nested_payload(body, parse_tables(raw), fields, arrays)
    plan = dict(schema_version=2, profile=NESTED_PROFILE, source_sha256=digest(raw), source_size=len(raw), output_alignment=32768,
                objects=[dict(object_path='ObjectA', class_path='Core.Thing', tagged_offset=4, before_sha256=digest(body),
                              after_sha256=digest(new), fields=fields, object_reference_arrays=arrays)])
    return raw, plan, body


class NestedTaggedStringTests(unittest.TestCase):
    def setUp(self): self.raw, self.plan, self.body = fixture()

    def rewrite(self, fields=None, arrays=None, body=None):
        obj = self.plan['objects'][0]
        return rewrite_nested_payload(self.body if body is None else body, parse_tables(self.raw),
                                      obj['fields'] if fields is None else fields,
                                      obj['object_reference_arrays'] if arrays is None else arrays)

    def test_nested_growth_and_shrink_parent_lengths_readback_and_rollback(self):
        result, report = apply(self.raw, self.plan)
        self.assertEqual(report['profile'], NESTED_PROFILE)
        self.assertEqual(report['fields'], 2)
        self.assertEqual(rollback(result, self.plan, report)[0], self.raw)
        self.assertEqual(len(result) % 32768, 0)
        old, new = parse_tables(self.raw), parse_tables(result)
        self.assertEqual(old['exports'][1], new['exports'][1])
        e = new['exports'][0]
        changed = result[e['serial_offset']:e['serial_offset'] + e['serial_size']]
        self.assertIn(wide_string('物品名称'), changed)
        self.assertIn(wide_string('暂无数据'), changed)
        self.assertIn(wide_string('保持'), changed)
        self.assertNotIn(b'Item Name', changed)

    def test_array_types_are_explicit_not_guessed(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'): self.rewrite(arrays=[])
        with self.assertRaisesRegex(ValueError, 'unused'): self.rewrite(arrays=[path('Children'), path('Other')])
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.rewrite(arrays=[path('Children')] * 2)
        for count, ref in ((3, 2), (-1, 2), (2, 3), (2, -3)):
            body = self.body.replace(struct.pack('>iii', 2, 2, -1), struct.pack('>iii', count, ref, -1))
            with self.subTest(count=count, ref=ref), self.assertRaises(ValueError): self.rewrite(body=body)

    def test_missing_nonstring_and_wrong_nested_paths_fail(self):
        for parts in (('Absent',), ('Children',), ('Children', 'MarkupString'), ('DataSource', 'Absent')):
            f = copy.deepcopy(self.plan['objects'][0]['fields']); f[0]['path'] = path(*parts)
            with self.subTest(parts=parts), self.assertRaises(ValueError): self.rewrite(fields=f)
        f = copy.deepcopy(self.plan['objects'][0]['fields']); f[0]['path'][0]['array_index'] = True
        with self.assertRaises(ValueError): self.rewrite(fields=f)

    def test_explicit_source_encoding_text_and_protected_tokens(self):
        for key, value in [('before_encoding', 'utf-16-le'), ('before_encoding', 'utf-8'),
                           ('before', '物品'), ('before', 'Item name'), ('after', '%s'), ('after', 'Item Name')]:
            fields = copy.deepcopy(self.plan['objects'][0]['fields']); fields[0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): self.rewrite(fields=fields)
        fields = [dict(path=path('DataSource', 'Other'), before_encoding='utf-16-le', before='保持', after='保留😀')]
        output, edits = self.rewrite(fields=fields)
        self.assertIn(wide_string('保留😀'), output)
        self.assertEqual(len(edits), 1)

    def test_empty_placeholder_is_canonical_zero_count_not_wide_padding(self):
        from tools.patch_tagged_fields import select_field
        fields = copy.deepcopy(self.plan['objects'][0]['fields']); fields[0]['after'] = ''
        output, edits = self.rewrite(fields=fields)
        self.assertEqual(select_field(output, parse_tables(self.raw)['names'], 4, fields[0]['path'])[2], bytes(4))
        self.assertEqual(edits[0]['after_size'], 4)
        self.assertIn(wide_string('保持'), output)
        self.assertIn(wide_string('暂无数据'), output)

    def test_duplicate_overlapping_paths_unknown_keys_and_native_tails(self):
        fields = copy.deepcopy(self.plan['objects'][0]['fields'])
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.rewrite(fields=fields + [fields[0]])
        fields[1]['path'] = path('DataSource')
        with self.assertRaisesRegex(ValueError, 'overlapping'): self.rewrite(fields=fields)
        fields[1]['unexpected'] = 1
        with self.assertRaises(ValueError): self.rewrite(fields=fields)
        with self.assertRaises(ValueError): self.rewrite(body=self.body + b'tail')

    def test_v1_does_not_silently_enable_nested_arrays(self):
        plan = copy.deepcopy(self.plan); plan.update(schema_version=1, profile=PROFILE)
        with self.assertRaises(ValueError): apply(self.raw, plan)
        del plan['objects'][0]['object_reference_arrays']
        with self.assertRaises(ValueError): apply(self.raw, plan)
        plan = copy.deepcopy(self.plan); del plan['objects'][0]['object_reference_arrays']
        with self.assertRaises(ValueError): apply(self.raw, plan)

    def test_rollback_requires_canonical_nested_receipt(self):
        result, report = apply(self.raw, self.plan)
        for change in ('path', 'before_encoding'):
            journal = copy.deepcopy(report); journal['changes'][0]['fields'][0][change] = None
            with self.assertRaises(ValueError): rollback(result, self.plan, journal)
        bad = copy.deepcopy(self.plan); bad['objects'][0]['fields'][0]['after'] = '其他'
        with self.assertRaises(ValueError): rollback(result, bad, report)

    def test_cli_nested_apply_rollback_and_source_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'original.xxx'; plan = root/'plan.json'; output = root/'modified.xxx'
            report = root/'report.json'; restored = root/'restored.xxx'
            source.write_bytes(self.raw); plan.write_bytes((json.dumps(self.plan, ensure_ascii=False)+'\n').encode())
            common = ['--plan', str(plan), '--plan-sha256', digest(plan.read_bytes())]
            self.assertEqual(main(['apply', str(source), '--source-sha256', digest(self.raw), *common,
                                   '--output', str(output), '--report', str(report)]), 0)
            self.assertEqual(main(['rollback', str(output), '--source-sha256', digest(output.read_bytes()), *common,
                                   '--journal', str(report), '--journal-sha256', digest(report.read_bytes()),
                                   '--output', str(restored), '--report', str(root/'rollback.json')]), 0)
            self.assertEqual(source.read_bytes(), self.raw)
            self.assertEqual(restored.read_bytes(), self.raw)
            self.assertNotEqual(output.read_bytes(), self.raw)


if __name__ == '__main__': unittest.main()
