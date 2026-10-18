"""Self-authored Core class/CDO boundaries; no original package dependency."""
import unittest

from tools.ue3_ui_styles import StyleGraph
from test_ui_style_graph import Fixture, word


def core_fixture():
    body = word(0, 0, 0)  # NetIndex, None FName
    def export(path, cls, parent=0, archetype=0):
        return dict(path=path, class_path='Class' if not cls else 'Core.' + ('Component' if cls == 2 else 'Object'),
                    super=parent, outer=0, archetype=archetype,
                    object_flags='0000000000000000' if not cls else '0000000000000200',
                    serial_offset=0, serial_size=0 if not cls else len(body), **{'class':cls})
    return dict(logical=body, sha256='synthetic', tables=dict(names=['None'], imports=[], exports=[
        export('Object', 0), export('Component', 0, 1),
        export('Default__Component', 2, archetype=4), export('Default__Object', 1)]))


class CoreAncestryTests(unittest.TestCase):
    def test_component_ancestry_includes_object_when_core_supplied(self):
        g = StyleGraph(dict(core=core_fixture()))
        self.assertEqual(g.class_chain(('core',3)), ['core.component','core.object'])

    def test_component_default_object_prototype_is_compatible(self):
        a = StyleGraph(dict(core=core_fixture())).archetype_audit(('core',3))
        self.assertEqual(a['explicit_archetypes']['termination'], 'null-archetype')
        self.assertEqual(a['unresolved'], [])
        self.assertEqual(len(a['class_default_candidates'][0]['nodes']), 2)
        self.assertFalse(a['effective_values_resolved'])

    def test_unsupplied_core_keeps_component_boundary(self):
        g = StyleGraph(Fixture().build())
        self.assertEqual(g.class_chain(('sample',2))[-1], 'core.component')

    def test_supplied_broken_core_is_not_hidden_by_boundary(self):
        for kind in ('missing', 'cycle', 'non-class'):
            p = Fixture().build(); c = core_fixture(); p['core'] = c
            if kind == 'missing': c['tables']['exports'][1]['path'] = 'Other'
            elif kind == 'cycle': c['tables']['exports'][1]['super'] = 2
            else: c['tables']['exports'][1]['super'] = 3
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                StyleGraph(p).class_chain(('sample',2))

    def scalar(self, kind, payload, index=0):
        f = Fixture(); p = f.build(); c = core_fixture()
        body = word(0) + f.props(f.prop('Value',kind,payload(f),index=index))
        c['logical'] = body; c['tables']['names'] = f.names
        c['tables']['exports'][2]['serial_size'] = len(body)
        return StyleGraph(dict(core=c)).parse(('core',3))['flattened'][0]

    def test_signed_int_and_index_preserved(self):
        r = self.scalar('IntProperty', lambda f: word(-17), 2)
        self.assertEqual(r['value'], -17)
        self.assertEqual(r['property_path'][0]['array_index'], 2)

    def test_byte_and_named_enum_encodings_are_distinct(self):
        r = self.scalar('ByteProperty', lambda f: b'\x02')
        self.assertEqual((r['value'],r['value_encoding']), (2,'u8'))
        r = self.scalar('ByteProperty', lambda f: f.fname('SomeEnum',3))
        self.assertEqual(r['value'], dict(name='SomeEnum',number=3))
        self.assertEqual(r['value_encoding'], 'FName')

    def test_scalar_sizes_are_exact(self):
        for kind, sizes in [('IntProperty',(0,1,3,5,8)),('ByteProperty',(0,2,4,7,9))]:
            for n in sizes:
                with self.subTest(kind=kind,n=n),self.assertRaises(ValueError):
                    self.scalar(kind,lambda f: bytes(n))

    def test_enum_name_bounds_are_checked(self):
        with self.assertRaisesRegex(ValueError,'FName index'):
            self.scalar('ByteProperty',lambda f: word(1000000,0))


if __name__ == '__main__': unittest.main()
