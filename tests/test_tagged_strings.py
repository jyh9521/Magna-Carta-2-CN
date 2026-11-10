import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch as mock_patch

from tools.patch_tagged_strings import digest, locked, main, patch, prepare, wide_string


def fixture():
    names = ['None', 'Label', 'StrProperty', 'Other', 'IntProperty']
    name = lambda n: struct.pack('>II', names.index(n), 0)
    string = wide_string('甲乙')
    payload = (b'\0' * 4 + name('Label') + name('StrProperty') + struct.pack('>II', len(string), 0)
               + string + name('Other') + name('IntProperty') + struct.pack('>III', 4, 0, 73)
               + name('None'))
    after = payload[:28] + wide_string('丙丁') + payload[28 + len(string):]
    data = b'HEADER' + payload + b'UNRELATED'
    ctx = dict(logical=data, tables=dict(names=names, exports=[dict(path='Scene.Label', class_path='Text',
               object_flags='0000000000000000', serial_offset=6, serial_size=len(payload))]))
    plan = dict(schema_version=1, profile='ue3-equal-size-wide-tagged-strings-v1', objects=[
        dict(object_path='Scene.Label', class_path='Text', tagged_offset=4,
             before_sha256=digest(payload), after_sha256=digest(after),
             fields=[dict(name='Label', array_index=0, before='甲乙', after='丙丁')])])
    return data, ctx, plan


class TaggedStringTests(unittest.TestCase):
    def setUp(self):
        self.data, self.ctx, self.plan = fixture()

    def test_endianness_count_and_unicode_units(self):
        self.assertEqual(wide_string('甲乙'), b'\xff\xff\xff\xfd\x32\x75\x59\x4e\0\0')
        self.assertEqual(struct.unpack('>i', wide_string('😀')[:4])[0], -3)

    def test_apply_and_inverse_keep_all_unowned_bytes(self):
        out, report = patch(self.data, self.ctx, self.plan)
        self.assertEqual(len(out), len(self.data))
        self.assertEqual(out[:34], self.data[:34])
        self.assertEqual(out[44:], self.data[44:])
        self.assertEqual(report['fields'], 1)
        restored, _ = patch(out, dict(self.ctx, logical=out), self.plan, True)
        self.assertEqual(restored, self.data)
        self.assertFalse(report['game_rendering_verified'])

    def test_invalid_string_inputs_and_surrogates(self):
        for value in ['', None, 3, 'a\0b', 'a\nb', 'a\rb', '\u200b', 'a' * 4097, '\ud800']:
            with self.subTest(value=repr(value)), self.assertRaises((ValueError, UnicodeError)):
                wide_string(value)

    def test_size_noop_source_type_and_tokens_guarded(self):
        for key, value in [('after', '甲'), ('after', '甲乙'), ('before', '乙甲'),
                           ('name', 'Other'), ('array_index', True), ('array_index', 1)]:
            plan = copy.deepcopy(self.plan); plan['objects'][0]['fields'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                patch(self.data, self.ctx, plan)
        plan = copy.deepcopy(self.plan)
        plan['objects'][0]['fields'][0].update(before='%s', after='%d')
        with self.assertRaisesRegex(ValueError, 'tokens'):
            patch(self.data, self.ctx, plan)

    def test_object_identity_profile_and_double_apply_guarded(self):
        for key, value in [('class_path', 'Other'), ('object_path', 'Absent'), ('tagged_offset', 8),
                           ('before_sha256', '0' * 64), ('after_sha256', '0' * 64)]:
            plan = copy.deepcopy(self.plan); plan['objects'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                patch(self.data, self.ctx, plan)
        for key, value in [('schema_version', True), ('profile', 'other'), ('objects', [])]:
            plan = copy.deepcopy(self.plan); plan[key] = value
            with self.assertRaises(ValueError): patch(self.data, self.ctx, plan)
        out, _ = patch(self.data, self.ctx, self.plan)
        with self.assertRaises(ValueError): patch(out, dict(self.ctx, logical=out), self.plan)
        with self.assertRaises(ValueError): prepare(self.data, self.ctx, self.plan, 'unknown')

    def test_duplicates_and_export_boundaries_guarded(self):
        for kind in ('objects', 'fields'):
            plan = copy.deepcopy(self.plan)
            if kind == 'objects': plan['objects'] *= 2
            else: plan['objects'][0]['fields'] *= 2
            with self.assertRaises(ValueError): patch(self.data, self.ctx, plan)
        for key, value in [('serial_size', 9999), ('serial_offset', -1),
                           ('object_flags', '0200000000000000'), ('object_flags', '0000000000000200')]:
            ctx = copy.deepcopy(self.ctx); ctx['tables']['exports'][0][key] = value
            with self.assertRaises(ValueError): patch(self.data, ctx, self.plan)
        with self.assertRaises(ValueError): patch(self.data + b'x', self.ctx, self.plan)

    def test_tail_refused_even_when_expected_hash_matches(self):
        ctx = copy.deepcopy(self.ctx); ctx['tables']['exports'][0]['serial_size'] += 1
        plan = copy.deepcopy(self.plan)
        plan['objects'][0]['before_sha256'] = digest(self.data[6:-8])
        with self.assertRaisesRegex(ValueError, 'tail'): patch(self.data, ctx, plan)

    def test_cli_exact_source_hash_and_output_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.xxx'; plan = root/'plan.json'
            output = root/'out.xxx'; report = root/'report.json'
            source.write_bytes(self.data); plan.write_text(json.dumps(self.plan), encoding='utf8')
            args = ['apply', str(source), '--source-sha256', digest(self.data), '--plan', str(plan),
                    '--plan-sha256', digest(plan.read_bytes()), '--output', str(output), '--report', str(report)]
            for flag in ('--source-sha256', '--plan-sha256'):
                bad = args.copy(); bad[bad.index(flag) + 1] = '0' * 64
                self.assertEqual(main(bad), 2)
                self.assertFalse(output.exists())
                self.assertFalse(report.exists())
            with mock_patch('tools.patch_tagged_strings.parse_summary', return_value=dict(byte_order='big', compression_flags=0)), \
                    mock_patch('tools.patch_tagged_strings.context', return_value=self.ctx):
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args), 2)
                bad = args.copy(); bad[bad.index('--output') + 1] = str(source)
                self.assertEqual(main(bad), 2)
            self.assertEqual(source.read_bytes(), self.data)
            self.assertEqual(digest(output.read_bytes()), json.loads(report.read_bytes())['output_sha256'])

    def test_bounded_inputs_and_duplicate_plan_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.xxx'; plan = root/'plan.json'
            source.write_bytes(self.data)
            for sha, limit in [('0' * 64, 9999), (digest(self.data), 1), ('invalid', 9999)]:
                with self.assertRaises(ValueError): locked(source, sha, limit)
            self.assertEqual(locked(source, digest(self.data), len(self.data)), self.data)
            plan.write_bytes(b'{"schema_version":1,"schema_version":1}')
            with mock_patch('tools.patch_tagged_strings.parse_summary', return_value=dict(byte_order='big', compression_flags=0)), \
                    mock_patch('tools.patch_tagged_strings.context', return_value=self.ctx):
                self.assertEqual(main(['apply', str(source), '--source-sha256', digest(self.data),
                                      '--plan', str(plan), '--plan-sha256', digest(plan.read_bytes()),
                                      '--output', str(root/'out.xxx'), '--report', str(root/'report.json')]), 2)
            self.assertFalse((root/'out.xxx').exists())


if __name__ == '__main__': unittest.main()
