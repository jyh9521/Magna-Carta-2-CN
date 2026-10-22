import unittest
from test_function_metadata import FunctionFixture
from test_ui_style_graph import word
from tools.ue3_function_metadata import function_header, parse_function_metadata


class StateFunctionFixture(FunctionFixture):
    def __init__(self):
        super().__init__()
        self.imports.append(dict(path='Core.State', class_name=dict(name='Class')))
        self.ref['State'] = -len(self.imports)
        self.exports.append(dict(path='RendererClass.Wait', class_path='Core.State', outer=1,
            super=0, archetype=0, object_flags='0000000000000000', serial_offset=0,
            serial_size=0, **{'class': self.ref['State']}))
        self.replace(24, word(0) + self.f.props())
        self.exports[20]['outer'] = 24
        self.exports[20]['path'] = 'RendererClass.Wait.SetFont'
        for e in self.exports[21:23]:
            e['path'] = e['path'].replace('RendererClass.SetFont', 'RendererClass.Wait.SetFont')


class StateFunctionMetadataTests(unittest.TestCase):
    def test_state_owner_keeps_declaring_state_and_defining_class_distinct(self):
        f = StateFunctionFixture()
        h = function_header(f.graph(), ('sample', 21))
        self.assertEqual(h['outer'], ('sample', 1))
        self.assertEqual(h['declaring_owner'], ('sample', 24))

    def test_signature_and_stub_are_still_fully_checked(self):
        r = StateFunctionFixture().parsed()
        self.assertEqual(r['declaring_owner']['class_path'], 'Core.State')
        self.assertEqual(r['defining_class']['path'], 'RendererClass')
        self.assertEqual(r['parameters'][0]['name'], 'NewFont')
        self.assertFalse(r['native_implementation_verified'])

    def test_null_import_nested_cycle_nonclass_and_out_of_range_state_parent_rejected(self):
        for owner in [0, -1, 24, 21, 3, 99999]:
            f = StateFunctionFixture(); f.exports[23]['outer'] = owner
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                f.parsed()

    def test_state_like_wrong_class_is_not_accepted(self):
        for kind in ['State', 'Other.State', 'Core.ScriptStruct', 'Core.Function']:
            f = StateFunctionFixture(); f.exports[23]['class_path'] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                f.parsed()

    def test_missing_function_owner_and_out_of_range_are_rejected(self):
        for owner in [0, 99999]:
            f = StateFunctionFixture(); f.exports[20]['outer'] = owner
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                f.parsed()

    def test_state_does_not_waive_function_header_or_tail_guards(self):
        for mode in ['trailing', 'oversize', 'friendly']:
            f = StateFunctionFixture()
            raw = f.function() + b'bad' if mode == 'trailing' else f.function(size=999999) if mode == 'oversize' else f.function(friendly='None')
            f.replace(21, raw)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                f.parsed()

    def test_direct_class_contract_is_unchanged(self):
        f = FunctionFixture(); h = function_header(f.graph(), ('sample', 21))
        self.assertEqual(h['outer'], h['declaring_owner'])
        self.assertEqual(f.parsed()['defining_class']['class_path'], 'Class')

    def test_bounded_script_uses_state_defining_class_for_instance_scope(self):
        f = StateFunctionFixture(); f.exports[0]['super'] = 0
        f.replace(21, f.function(script=b'\x04\x00' + word(23) + b'\x53', flags=0x20001))
        r = parse_function_metadata(f.graph(), ('sample', 21), include_scripted=True)
        self.assertEqual(r['script_kind'], 'bounded-scripted-ui')
        self.assertEqual(r['declaring_owner']['object_index'], 24)
        self.assertEqual(r['defining_class']['object_index'], 1)


if __name__ == '__main__':
    unittest.main()
