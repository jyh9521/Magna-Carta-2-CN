"""Self-authored bytecode/storage fixtures; no original assets or game execution."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_function_metadata import FunctionFixture
from test_ui_style_graph import word
from tools.ue3_script_boundaries import (function_storage, decode_boundaries,
                                        function_boundary_report, native_declarations,
                                        classify_export_offset)
from tools.inspect_script_boundaries import main


def decode(raw, **kw):
    return decode_boundaries(raw, ['None', 'Call'],
        lambda ref: dict(reference=ref, class_name='IntProperty', path='sample.value') if ref else None,
        {0x70:dict(package='sample', export=1, path='Root.Call')}, **kw)


class ScriptBoundaryTests(unittest.TestCase):
    def test_real_unicode_opcode_and_false_positive_int_operand_are_distinct(self):
        code = b'\x1d\x00\x34\x00\x00\x34'+ '\ud55c'.encode('utf-16-be')+b'\0\0\x53'
        result = decode(code)
        self.assertEqual([x['op'] for x in result['statements']], ['Int', 'UnicodeString', 'EndOfScript'])
        self.assertEqual(result['statements'][1]['value'], '\ud55c')
        self.assertEqual(next(x for x in result['atoms'] if x['start'] <= 2 < x['end'])['field'], 'int_literal')
        self.assertEqual(result['atoms'][0]['start'], 0)
        self.assertEqual(result['atoms'][-1]['end'], len(code))
        self.assertEqual(b''.join(bytes.fromhex(x['hex']) for x in result['atoms']), code)

    def test_literal_parent_chain_retains_source_consumer_and_exact_bytes(self):
        r = decode(b'\x70\x1fabc\0\x16\x53')
        literal = next(t for t in r['tokens'] if t['op'] == 'String')
        self.assertEqual(literal['parents'], [0])
        self.assertEqual(r['tokens'][0]['callee']['path'], 'Root.Call')
        self.assertFalse(r['runtime_execution_observed'])
        self.assertFalse(r['native_implementation_verified'])

    def test_every_truncated_parameterized_expression_is_rejected(self):
        raw = b'\x70\x1d\x00\x34\x00\x00\x1ftext\0\x16\x53'
        for n in range(len(raw)):
            with self.subTest(n=n), self.assertRaises(ValueError):
                decode(raw[:n])
        decode(raw)

    def test_unknown_opcode_and_early_nested_or_absent_end_are_rejected(self):
        for raw in (b'\x50\x53', b'\x53\x0b', b'\x04\x53', b'\x0b', b'\x70\x53\x16\x53'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw)

    def test_unterminated_ansi_unicode_and_unpaired_surrogate_fail(self):
        for raw in (b'\x1fabc', b'\x34\x00', b'\x34\xd8\x00\0\0\x53'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw)

    def test_reference_class_not_only_integer_bounds_is_checked(self):
        with self.assertRaisesRegex(ValueError, 'wrong declaration class'):
            decode_boundaries(b'\0'+word(1)+b'\x53', [], lambda _: dict(class_name='Function'), {})
        r = decode_boundaries(b'\1'+word(1)+b'\x53', [],
                              lambda _:dict(class_name='ComponentProperty', path='sample.component'), {})
        self.assertEqual(r['tokens'][0]['reference']['binding']['class_name'], 'ComponentProperty')

    def test_fname_index_and_negative_instance_fail(self):
        for raw in (b'\x21'+word(9, 0)+b'\x53', b'\x21'+word(1, -1)+b'\x53'):
            with self.assertRaisesRegex(ValueError, 'FName'):
                decode(raw)
        self.assertEqual(decode(b'\x21'+word(1, 3)+b'\x53')['tokens'][0]['name']['canonical'], 'Call_2')

    def test_native_token_requires_unique_source_binding(self):
        with self.assertRaisesRegex(ValueError, 'unbound native'):
            decode(b'\x71\x16\x53')
        self.assertEqual(decode(b'\x60\x70\x16\x53')['tokens'][0]['native'], 0x70)

    def test_depth_tokens_and_argument_budgets_fail_closed(self):
        for raw, kw in ((b'\x2d'*5+b'\x27\x53', dict(max_depth=3)),
                        (b'\x0b'*5+b'\x53', dict(max_tokens=3)),
                        (b'\x70\x26\x26\x16\x53', dict(max_arguments=1))):
            with self.assertRaisesRegex(ValueError, 'bound'):
                decode(raw, **kw)

    def test_conditional_keeps_both_skip_fields_and_three_child_boundaries(self):
        raw = b'\x45\x27\0\3\x26\0\1\x25\x53'
        r = decode(raw)
        t = r['tokens'][0]
        self.assertEqual((t['condition']['at'], t['when_true']['at'], t['when_false']['at']), (1, 4, 7))
        self.assertEqual((t['true_skip'], t['false_skip']), (3, 1))
        self.assertEqual([a['field'] for a in r['atoms'] if 'conditional_' in a['field']],
                         ['conditional_true_skip', 'conditional_false_skip'])

    def test_numbered_friendly_name_is_exact_canonical_export_not_mismatch_waiver(self):
        f = FunctionFixture();f.exports[20]['path']='RendererClass.SetFont_2'
        f.replace(21, f.function()[:-4]+word(3))
        r = function_storage(f.graph(), ('sample', 21))
        self.assertEqual(r['friendly_canonical'], 'SetFont_2')
        f.exports[20]['path']='RendererClass.SetFont_1'
        with self.assertRaisesRegex(ValueError, 'friendly name'):
            function_storage(f.graph(), ('sample', 21))

    def test_net_metadata_reads_exact_replication_word_and_tail(self):
        f = FunctionFixture();raw=f.function(flags=0x20441)
        f.replace(21, raw[:-8]+b'\xff\xff'+raw[-8:])
        r=function_storage(f.graph(), ('sample', 21))
        self.assertEqual(r['replication_offset'], 65535)
        self.assertEqual(r['friendly_canonical'], 'SetFont')
        self.assertEqual([s for s in r['storage_spans'] if s['field']=='replication_offset'][0]['end']-
                         [s for s in r['storage_spans'] if s['field']=='replication_offset'][0]['start'], 2)
        for bad in (raw, raw[:-8]+b'\xff'+raw[-8:], raw[:-8]+b'\xff\xff\xff'+raw[-8:]):
            f.replace(21, bad)
            with self.assertRaises(ValueError):function_storage(f.graph(), ('sample', 21))

    def test_larger_script_profile_is_bounded_without_weakening_strict_ui_reader(self):
        from tools.ue3_function_metadata import function_header
        f=FunctionFixture();f.replace(21, f.function(script=b'\x0b'*10243+b'\x53', flags=2))
        self.assertEqual(len(function_storage(f.graph(), ('sample',21))['script']), 10244)
        with self.assertRaisesRegex(ValueError, 'bounded function profile'):
            function_header(f.graph(), ('sample',21))
        with self.assertRaisesRegex(ValueError, 'explicit storage profile'):
            function_storage(f.graph(), ('sample',21), max_script_size=10242)

    def test_every_storage_truncation_and_extra_byte_is_rejected(self):
        f=FunctionFixture();raw=f.function()
        for n in range(len(raw)):
            f.replace(21, raw[:n])
            with self.subTest(n=n), self.assertRaises(ValueError):function_storage(f.graph(), ('sample',21))
        f.replace(21, raw+b'x')
        with self.assertRaisesRegex(ValueError, 'trailing'):function_storage(f.graph(), ('sample',21))

    def test_native_stub_declaration_order_still_verified(self):
        f=FunctionFixture();r=function_boundary_report(f.graph(), ('sample',21), {})
        self.assertIsNotNone(r['native_stub_declarations'])
        self.assertEqual(r['payload_sha256'], hashlib.sha256(f.function()).hexdigest())
        f.replace(21, f.function(script=b'\x29'+word(23)+b'\x0b\x53'))
        with self.assertRaisesRegex(ValueError, 'order mismatch'):
            function_boundary_report(f.graph(), ('sample',21), {})

    def test_offset_classification_distinguishes_metadata_opcode_and_literal_operand(self):
        f=FunctionFixture();f.replace(21,f.function(script=b'\x34\xac\x00\0\0\x53',flags=2,
                                                     editor=(0,0,0x34000000,1)))
        r=function_boundary_report(f.graph(), ('sample',21), {})
        self.assertEqual(classify_export_offset(r,32)['status'],'not_bytecode_metadata')
        self.assertEqual(classify_export_offset(r,44)['status'],'real_unicode_token')
        self.assertEqual(classify_export_offset(r,45)['status'],'not_unicode_opcode')
        with self.assertRaisesRegex(ValueError,'outside'):
            classify_export_offset(r,999999)

    def test_native_inventory_binds_only_unique_tokens(self):
        f=FunctionFixture();raw=f.function();off=44+len(f.script)
        f.replace(21,raw[:off]+b'\0\x70'+raw[off+2:])
        inventory=native_declarations(f.graph())
        self.assertEqual(inventory['bindings'][0x70]['path'],'RendererClass.SetFont')
        self.assertEqual(inventory['unparsed_headers'],[])
        f.exports.append(dict(f.exports[20]))
        inventory=native_declarations(f.graph())
        self.assertNotIn(0x70,inventory['bindings'])
        self.assertEqual(len(inventory['ambiguous'][0x70]),2)

    def test_non_native_declaration_never_binds_numeric_native_dispatch(self):
        f=FunctionFixture();raw=f.function(flags=2);off=44+len(f.script)
        f.replace(21,raw[:off]+b'\0\x70'+raw[off+2:])
        inventory=native_declarations(f.graph())
        self.assertEqual(inventory['bindings'],{})
        self.assertEqual(len(inventory['unparsed_headers']),1)

    def test_cli_writes_reopened_source_bound_readonly_report(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'Sample.xxx';raw=FunctionFixture().package();path.write_bytes(raw)
            out=Path(d)/'report.json'
            with contextlib.redirect_stdout(io.StringIO()):
                code=main([str(path),'--sha256',hashlib.sha256(raw).hexdigest(),
                           '--object','RendererClass.SetFont','--output',str(out)])
            self.assertEqual(code,0);r=json.loads(out.read_bytes())
            self.assertEqual(len(r['functions']),1);self.assertEqual(r['unparsed'],[])
            self.assertEqual(path.read_bytes(),raw);self.assertFalse(r['game_rendering_verified'])

    def test_cli_hash_guard_precedes_native_decoder_and_existing_output_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'Sample.xxx';raw=FunctionFixture().package();path.write_bytes(raw)
            out=Path(d)/'report.json';args=[str(path),'--sha256','0'*64,'--object','RendererClass.SetFont',
                                         '--lzx-library',str(Path(d)/'missing.dll'),'--output',str(out)]
            with patch('tools.inspect_script_boundaries.LzxDecoder') as lib, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args),2);lib.assert_not_called()
            self.assertFalse(out.exists());out.write_text('keep')
            with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(main(args),2)
            self.assertEqual(out.read_text(),'keep')

    def test_cli_unsupported_script_is_explicit_partial_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            f=FunctionFixture();f.replace(21,f.function(script=b'\x50\x53',flags=2))
            path=Path(d)/'Sample.xxx';raw=f.package();path.write_bytes(raw);out=Path(d)/'report.json'
            with contextlib.redirect_stdout(io.StringIO()):
                code=main([str(path),'--sha256',hashlib.sha256(raw).hexdigest(),'--object',
                           'RendererClass.SetFont','--output',str(out)])
            self.assertEqual(code,1);self.assertIn('unsupported opcode',json.loads(out.read_bytes())['unparsed'][0]['reason'])


if __name__=='__main__':unittest.main()
