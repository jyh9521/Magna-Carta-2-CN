"""Self-authored serialized selectors; no original assets or runtime calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_ui_style_graph as fixtures
from tools.owner_style_audit import audit_owner_primary_style, style_font_paths
from tools.ue3_ui_styles import StyleGraph


class OwnerStyleTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.Fixture(); self.p = self.f.build()

    def append(self, node, prop):
        graph = StyleGraph(self.p); context = self.p[node[0]]; e = graph.export(*node)
        body = context['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']]
        end = graph.parse(node)['tagged_end']
        body = body[:end-8] + prop + body[end-8:]
        e['serial_offset'] = len(context['logical']); e['serial_size'] = len(body)
        context['logical'] += body

    def primary(self, *children, **kwargs):
        return self.f.prop('PrimaryStyle', 'StructProperty', self.f.props(*children), 'UIStyleReference', **kwargs)

    def tag(self, name='DefaultComboStyle', number=0, field='DefaultStyleTag'):
        return self.f.prop(field, 'NameProperty', self.f.fname(name, number))

    def setup_tag(self):
        self.append(('sample', 1), self.primary(self.tag()))
        self.append(('sample', 3), self.tag(field='StyleTag'))

    def test_absent_primary_is_not_fallback(self):
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))
        self.assertEqual(r['selector_observations'], [])
        for flag in ['inherited_values_merged', 'fallback_order_verified', 'native_owner_pointer_identity_verified', 'runtime_binding_verified']:
            self.assertIs(r[flag], False)
        self.assertTrue(r['prototype_audit']['unresolved'])

    def test_tag_traces_nested_combo_font_without_replacing_component_route(self):
        self.setup_tag(); g = StyleGraph(self.p)
        r = audit_owner_primary_style(g, ('sample', 1)); item, = r['selector_observations']
        self.assertEqual(item['plane'], 'explicit-archetype')
        self.assertEqual(item['style_definition_count'], 1)
        path, = item['candidate_paths']; self.assertEqual(path['font']['object_index'], 6)
        self.assertEqual([n['object_index'] for n in path['hops']], [3, 4, 5])
        self.assertEqual(g.trace('sample', 'Fixture.Scene.Warning')['text_matches'][0]['assigned_style_id'], '00000001-00000002-00000003-00000004')

    def test_fname_casefold_but_number_must_match(self):
        self.append(('sample', 1), self.primary(self.tag('DEFAULTCOMBOSTYLE', 2)))
        self.append(('sample', 3), self.tag('DefaultComboStyle', 1, field='StyleTag'))
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['selector_observations'][0]
        self.assertEqual(r['style_definition_count'], 0); self.assertTrue(r['unresolved'])
        self.append(('sample', 3), self.tag('DefaultComboStyle', 2, field='StyleTag'))
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))
        self.assertTrue(r['style_catalog_errors'])  # duplicate tag is not a match

    def test_matching_casefold_tag(self):
        self.append(('sample', 1), self.primary(self.tag('DEFAULTCOMBOSTYLE', 2)))
        self.append(('sample', 3), self.tag('DefaultComboStyle', 2, field='StyleTag'))
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['selector_observations'][0]
        self.assertEqual(r['style_definition_count'], 1)

    def test_duplicate_style_candidates_all_retained(self):
        self.setup_tag(); other = copy.deepcopy(self.p['sample']['tables']['exports'][2])
        other['path'] = 'OtherSkin.SameTag'; self.p['sample']['tables']['exports'].append(other)
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['selector_observations'][0]
        self.assertEqual(r['style_definition_count'], 2); self.assertEqual(len(r['candidate_paths']), 2)

    def test_zero_and_none_selectors_are_explicit_but_not_matches(self):
        self.append(('sample', 1), self.primary(self.tag('None'),
            self.f.prop('AssignedStyleID', 'StructProperty', self.f.sid((0, 0, 0, 0)), 'STYLE_ID')))
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))
        self.assertEqual(len(r['selector_observations']), 2)
        self.assertTrue(all(o['selector_is_zero_or_none'] and not o['candidate_paths'] for o in r['selector_observations']))

    def test_assigned_id_is_separate_from_tag_and_does_not_override(self):
        self.setup_tag(); self.append(('sample', 1), self.primary())
        self.assertTrue(audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['unresolved'])
        self.setUp()
        self.append(('sample', 1), self.primary(self.tag('Missing'), self.f.prop('AssignedStyleID', 'StructProperty', self.f.sid(), 'STYLE_ID')))
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['selector_observations']
        self.assertEqual([o['style_definition_count'] for o in r], [1, 0])

    def test_indexed_and_wrong_typed_selectors_are_rejected(self):
        for prop in [self.primary(self.tag(), index=1), self.primary(self.f.prop('DefaultStyleTag', 'IntProperty', fixtures.word(1)))]:
            with self.subTest(prop=prop):
                self.p = self.f.build(); self.append(('sample', 1), prop)
                r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))
                self.assertTrue(r['unresolved']); self.assertEqual(r['selector_observations'], [])

    def test_cdo_evidence_is_not_merged_into_instance(self):
        engine = self.p['engine']; engine['tables']['names'] = self.f.names
        body = fixtures.word(0) + self.f.props(self.primary(self.tag()))
        engine['logical'] = body
        engine['tables']['exports'].append(dict(path='AnyName', class_path='UILabel', serial_offset=0,
            serial_size=len(body), outer=0, archetype=0, super=0, object_flags='0000000000000200', **{'class': 4}))
        self.append(('sample', 3), self.tag(field='StyleTag'))
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))
        self.assertEqual(r['prototype_audit']['explicit_archetypes']['nodes'][0]['fields'], [])
        item, = r['selector_observations']; self.assertEqual(item['plane'], 'class-default-candidate')
        self.assertEqual(item['owner']['path'], 'AnyName'); self.assertFalse(r['inherited_values_merged'])

    def test_null_custom_data_is_unresolved_not_default_font(self):
        self.setup_tag(); g = StyleGraph(self.p); p = self.p['sample']
        offset = g.one(('sample', 4), ['TextStyle', 'CustomStyleData'])['logical_package_offset']
        raw = bytearray(p['logical']); raw[offset:offset+4] = fixtures.word(0); p['logical'] = bytes(raw)
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['selector_observations'][0]
        self.assertEqual(r['candidate_paths'], []); self.assertIn('null CustomStyleData', r['unresolved'][0]['reason'])

    def test_invalid_state_map_keeps_error(self):
        p = self.p['sample']; e = p['tables']['exports'][2]; e['serial_size'] -= 1
        paths, errors = style_font_paths(StyleGraph(self.p), ('sample', 3))
        self.assertEqual(paths, []); self.assertTrue(errors)

    def test_cdo_style_not_added_to_catalog(self):
        self.setup_tag(); self.p['sample']['tables']['exports'][2]['object_flags'] = '0000000000000200'
        r = audit_owner_primary_style(StyleGraph(self.p), ('sample', 1))['selector_observations'][0]
        self.assertEqual(r['style_definition_count'], 0)

    def add_text_cdo(self):
        engine = self.p['engine']; engine['tables']['names'] = self.f.names
        # A separate font in the defining package; no runtime alias is chosen.
        engine['tables']['exports'].append(dict(path='OtherFont', class_path='Font', serial_offset=0,
            serial_size=0, outer=0, archetype=0, super=0, object_flags='0000000000000000', **{'class': 9}))
        body = fixtures.word(0) + self.f.props(self.f.prop('StyleFont', 'ObjectProperty', fixtures.word(11)))
        engine['logical'] = body
        engine['tables']['exports'].append(dict(path='AnyTextDefault', class_path='UIStyle_Text', serial_offset=0,
            serial_size=len(body), outer=0, archetype=0, super=0, object_flags='0000000000000200', **{'class': 8}))

    def test_explicit_and_cdo_fonts_are_independent_observations(self):
        self.add_text_cdo()
        paths, errors = style_font_paths(StyleGraph(self.p), ('sample', 3))
        self.assertEqual(errors, [])
        self.assertEqual([(p['font']['package'], p['font']['object_index']) for p in paths], [('sample', 6), ('engine', 11)])
        self.assertEqual([p['font_source_plane'] for p in paths], ['explicit-archetype', 'class-default-candidate'])
        self.assertTrue(all(not p['inherited_values_merged'] for p in paths))

    def test_absent_font_retains_cdo_observation_without_inferred_merge(self):
        self.add_text_cdo(); p = self.p['sample']; e = p['tables']['exports'][4]
        body = fixtures.word(0) + self.f.props(); e['serial_offset'] = len(p['logical']); e['serial_size'] = len(body); p['logical'] += body
        paths, errors = style_font_paths(StyleGraph(self.p), ('sample', 3))
        self.assertEqual(errors, []); path, = paths
        self.assertEqual(path['font_source_plane'], 'class-default-candidate')
        self.assertEqual(path['text_data_prototype_audit']['explicit_archetypes']['nodes'][0]['fields'], [])

    def test_null_explicit_font_is_not_silently_replaced_by_cdo(self):
        self.add_text_cdo(); g = StyleGraph(self.p); p = self.p['sample']
        offset = g.one(('sample', 5), ['StyleFont'])['logical_package_offset']
        raw = bytearray(p['logical']); raw[offset:offset+4] = fixtures.word(0); p['logical'] = bytes(raw)
        paths, errors = style_font_paths(StyleGraph(self.p), ('sample', 3))
        self.assertEqual(len(paths), 1); self.assertIn('not a resolved Font', errors[0]['reason'])
        self.assertEqual(paths[0]['font_source_plane'], 'class-default-candidate')

    def test_cli_audit_serializes_owner_evidence_and_collects_both_fonts(self):
        from tools.inspect_ui_fonts import main
        self.setup_tag(); self.add_text_cdo()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'sample.xxx'; source.write_bytes(b'source')
            engine = root/'engine.xxx'; engine.write_bytes(b'engine'); report = root/'report.json'
            args = [str(source), '--sha256', '0'*64, '--deep', '--text-token', 'Fixture.Scene.Warning',
                '--audit-bindings', '--reference-package', 'Engine', str(engine), '0'*64, '--output', str(report)]
            contexts = [(self.p[k]['logical'], self.p[k]['tables']) for k in ['sample', 'engine']]
            with patch('tools.inspect_font_references._tables', side_effect=contexts), \
                    patch('tools.inspect_ui_fonts.parse_summary', return_value={'guid': 'a'*32}), \
                    patch('tools.font_binding_audit.audit_font_candidates', return_value={'groups': []}) as fonts:
                self.assertEqual(main(args), 0)
            r = json.loads(report.read_text(encoding='utf-8'))
            self.assertIn('owner_primary_style_audit', r['text_matches'][0])
            self.assertEqual(set(fonts.call_args.args[1]), {('sample', 6), ('engine', 11)})
            self.assertFalse(r['runtime_binding_verified']); self.assertEqual(source.read_bytes(), b'source')


if __name__ == '__main__':
    unittest.main()
