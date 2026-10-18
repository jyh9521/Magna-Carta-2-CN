"""Entirely self-authored schema/graph fixtures; no game execution or assets."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools.inspect_ui_fonts import main
from tools.ue3_package import Reader
from tools.ue3_ui_styles import StyleGraph, object_flags, read_name, style_id


def word(*v):
    return struct.pack('>' + 'I' * len(v), *(n & 0xffffffff for n in v))


class Fixture:
    def __init__(self):
        self.names = ['None']

    def fname(self, name, number=0):
        if name not in self.names:
            self.names.append(name)
        return word(self.names.index(name), number)

    def prop(self, name, kind, raw=b'', struct_name=None, index=0, boolean=0):
        result = self.fname(name) + self.fname(kind) + word(len(raw), index)
        if kind == 'StructProperty': result += self.fname(struct_name)
        if kind == 'BoolProperty': result += word(boolean)
        return result + raw

    def props(self, *values):
        return b''.join(values) + self.fname('None')

    def sid(self, words=(1, 2, 3, 4)):
        return self.props(*(self.prop(name, 'IntProperty', word(value)) for name, value in zip('ABCD', words)))

    def build(self):
        object_import = dict(path='Core.Object', class_name=dict(name='Class'))
        component_import = dict(path='Core.Component', class_name=dict(name='Class'))
        specs = [('UIObject', -1), ('UIComponent', -2), ('UIComp_DrawString', 2), ('UILabel', 1),
                 ('UIStyle', -1), ('UIStyle_Data', -1), ('UIStyle_Combo', 6), ('UIStyle_Text', 6),
                 ('Font', -1), ('UIComp_Event', 2)]
        engine_exports = [dict(path=name, class_path='Class', super=parent, outer=0, archetype=0,
                               object_flags='0000000000000000', serial_offset=0, serial_size=0, **{'class':0})
                          for name, parent in specs]
        engine = dict(logical=b'', sha256='engine', tables=dict(names=[], exports=engine_exports,
                        imports=[object_import, component_import]))
        imports = [dict(path='Engine.' + name, class_name=dict(name='Class'))
                   for name in ['UIComp_DrawString', 'UILabel', 'UIStyle', 'UIStyle_Combo', 'UIStyle_Text', 'Font']]
        imports.append(dict(path='Engine.Default__UIState_Enabled', class_name=dict(name='UIState_Enabled')))
        self.markup = '<Strings:Fixture.Scene.Warning>'
        raw = self.markup.encode() + b'\0'
        binding = self.props(self.prop('MarkupString', 'StrProperty', word(len(raw)) + raw))
        label = word(1) + self.props(self.prop('DataSource', 'StructProperty', binding, 'UIDataStoreBinding'),
                                   self.prop('StringRenderComponent', 'ObjectProperty', word(2)))
        style_ref = self.props(self.prop('AssignedStyleID', 'StructProperty', self.sid(), 'STYLE_ID'))
        style_prop = self.prop('StringStyle', 'StructProperty', style_ref, 'UIStyleReference')
        renderer = word(-2, 42) + self.props(style_prop)
        style = word(2) + self.props(self.prop('StyleID', 'StructProperty', self.sid(), 'STYLE_ID')) + word(1, -7, 4)
        combo = word(3) + self.props(self.prop('TextStyle', 'StructProperty',
                        self.props(self.prop('CustomStyleData', 'ObjectProperty', word(5))), 'StyleDataReference'))
        text = word(4) + self.props(self.prop('StyleFont', 'ObjectProperty', word(6)))
        parent = word(5) + self.props()
        template = word(0) + self.fname('TemplateComponent', 7) + word(99) + self.props(style_prop)
        own_cdo = word(6) + self.props(style_prop)
        bodies = [label, renderer, style, combo, text, b'', b'', parent, template, own_cdo]
        paths = ['WarningLabel', 'WarningLabel.Renderer', 'Styles.General', 'Styles.General.Combo',
                 'Styles.General.Combo.Text', 'Font.General', 'Font.Donor', 'Default__Label',
                 'Default__Label.Renderer', 'Default__Renderer']
        classes = [-2, -1, -3, -4, -5, -6, -6, -2, -1, -1]
        data, exports = bytearray(bytes(11)), []
        for i, (body, path, cls) in enumerate(zip(bodies, paths, classes), 1):
            exports.append(dict(path=path, class_path=imports[-cls-1]['path'],
                serial_offset=len(data), serial_size=len(body), outer=8 if i == 9 else 0,
                archetype=0, export_flags=1, object_flags='0000000000000200' if i in (8, 10) else '0000000000000000',
                super=0, **{'class':cls}))
            data.extend(body)
        return dict(sample=dict(logical=bytes(data),sha256='sample', tables=dict(names=self.names,imports=imports,exports=exports)), engine=engine)


class StyleGraphTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(); self.packages = self.fixture.build(); self.g = StyleGraph(self.packages)

    def test_complete_text_component_id_state_font_chain(self):
        r = self.g.trace('sample', 'Fixture.Scene.Warning')
        self.assertEqual(len(r['text_matches']), 1)
        match = r['text_matches'][0]
        self.assertEqual(match['assigned_style_id'], '00000001-00000002-00000003-00000004')
        self.assertEqual(match['renderer_prefix']['tagged_offset'], 8)
        self.assertEqual(match['renderer_prefix']['template_owner_class'], -2)
        candidate, = match['candidate_paths']
        self.assertEqual(candidate['font']['object_index'], 6)
        self.assertEqual([n['object_index'] for n in candidate['hops']], [3,4,5])
        self.assertFalse(r['runtime_binding_verified']);self.assertFalse(r['inherited_values_resolved'])
        self.assertEqual(match['unresolved'], [])

    def test_component_template_and_cdo_routes(self):
        template = self.g.parse(('sample',9))['prefix']
        self.assertEqual(template['tagged_offset'],16)
        self.assertEqual(template['template_name'],dict(name='TemplateComponent',number=7))
        self.assertEqual(template['net_index'],99)
        cdo = self.g.parse(('sample',10))['prefix']
        self.assertEqual(cdo['tagged_offset'],4);self.assertTrue(cdo['class_default'])
        self.assertNotIn('template_owner_class',cdo)

    def test_flags_are_two_words_not_big_endian_u64(self):
        self.assertEqual(object_flags(dict(object_flags='0200000000000200')),(0x2000000,0x200))
        with self.assertRaises(ValueError):object_flags(dict(object_flags='00'))

    def test_exact_nested_offsets(self):
        field = self.g.one(('sample',1),['DataSource','MarkupString'])
        raw = self.packages['sample']['logical'];offset=field['logical_package_offset']
        self.assertEqual(Reader(raw[offset:]).string(),self.fixture.markup)
        font = self.g.one(('sample',5),['StyleFont'])
        self.assertEqual(raw[font['logical_package_offset']:font['logical_package_offset']+4],word(6))

    def test_class_hierarchy_and_import_identity(self):
        self.assertIn('core.component',self.g.class_chain(('sample',2)))
        self.assertIn('engine.uiobject',self.g.class_chain(('sample',1)))
        self.assertEqual(self.g.reference('sample',-1),('engine',3))
        self.packages['sample']['tables']['imports'][0]['class_name']['name']='Font'
        with self.assertRaisesRegex(ValueError,'class mismatch'):self.g.reference('sample',-1)

    def test_missing_duplicate_import_and_label(self):
        missing = copy.deepcopy(self.packages);del missing['engine']
        with self.assertRaises(ValueError):StyleGraph(missing).parse(('sample',2))
        dup = copy.deepcopy(self.packages);dup['engine']['tables']['exports'].append(dup['engine']['tables']['exports'][2].copy())
        with self.assertRaisesRegex(ValueError,'ambiguous'):StyleGraph(dup).reference('sample',-1)
        with self.assertRaisesRegex(ValueError,'duplicate'):StyleGraph(dict(self.packages, SAMPLE=self.packages['sample']))

    def test_class_cycle_and_outer_cycle(self):
        self.packages['engine']['tables']['exports'][1]['super']=3
        with self.assertRaisesRegex(ValueError,'cyclic'):self.g.class_chain(('sample',2))
        fresh=copy.deepcopy(self.packages);fresh['sample']['tables']['exports'][8]['outer']=9
        with self.assertRaisesRegex(ValueError,'cyclic'):StyleGraph(fresh).cdo_outer(('sample',9))

    def test_hasstack_is_not_guessed(self):
        self.packages['sample']['tables']['exports'][1]['object_flags']='0200000000000000'
        with self.assertRaisesRegex(ValueError,'HasStack'):self.g.parse(('sample',2))

    def test_wrong_template_owner_and_prefix_truncation(self):
        context=self.packages['sample'];e=context['tables']['exports'][1];start=e['serial_offset']
        raw=bytearray(context['logical']);raw[start:start+4]=word(1);context['logical']=bytes(raw)
        with self.assertRaisesRegex(ValueError,'TemplateOwnerClass'):self.g.parse(('sample',2))
        for size in range(self.packages['sample']['tables']['exports'][8]['serial_size']):
            fresh=self.fixture.build();fresh['sample']['tables']['exports'][8]['serial_size']=size
            with self.assertRaises(ValueError):StyleGraph(fresh).parse(('sample',9))

    def test_nested_trailing_bytes_are_rejected(self):
        f=self.fixture;e=self.packages['sample']['tables']['exports'][0]
        nested=f.props(f.prop('MarkupString','StrProperty',word(2)+b'x\0'))+b'x'
        body=word(1)+f.props(f.prop('DataSource','StructProperty',nested,'UIDataStoreBinding'))
        e['serial_offset']=len(self.packages['sample']['logical']);e['serial_size']=len(body)
        self.packages['sample']['logical']+=body
        with self.assertRaisesRegex(ValueError,'trailing'):self.g.parse(('sample',1))

    def test_guid_schema_malformed_and_raw_guid_not_accepted(self):
        props=self.g.parse(('sample',3))['properties']
        self.assertEqual(props[0]['struct'],'STYLE_ID')
        with self.assertRaises(ValueError):style_id([])
        with self.assertRaises(ValueError):style_id([dict(name=k,type='IntProperty',array_index=0,raw=b'bad') for k in 'ABCD'])

    def test_state_map_trailing_invalid_duplicate_and_wrong_data(self):
        context=self.packages['sample'];e=context['tables']['exports'][2];raw=context['logical']
        end=e['serial_offset']+e['serial_size']
        for replacement in (word(1,-7,6),word(1,0,4),word(2,-7,4),word(0,-7,4)):
            fresh=copy.deepcopy(self.packages);fresh['sample']['logical']=raw[:end-12]+replacement+raw[end:]
            with self.assertRaises(ValueError):StyleGraph(fresh).state_map(('sample',3))

    def test_duplicate_state_keys_and_negative_counts(self):
        for tail in (word(2,-7,4,-7,4),word(-1)):
            fresh=copy.deepcopy(self.packages);node=fresh['sample']['tables']['exports'][2]
            old=fresh['sample']['logical'][node['serial_offset']:node['serial_offset']+node['serial_size']]
            replacement=old[:-12]+tail;node['serial_offset']=len(fresh['sample']['logical']);node['serial_size']=len(replacement)
            fresh['sample']['logical']+=replacement
            with self.assertRaisesRegex(ValueError,'duplicate|count'):StyleGraph(fresh).state_map(('sample',3))

    def test_nested_depth_is_bounded(self):
        f=self.fixture;raw=f.props()
        for _ in range(10):raw=f.props(f.prop('Nested','StructProperty',raw,'UIStyleReference'))
        body=word(1)+raw;ctx=self.packages['sample'];e=ctx['tables']['exports'][0]
        e['serial_offset']=len(ctx['logical']);e['serial_size']=len(body);ctx['logical']+=body
        with self.assertRaisesRegex(ValueError,'depth'):self.g.parse(('sample',1))

    def test_array_index_or_duplicate_trace_field_not_silently_selected(self):
        f=self.fixture;ctx=self.packages['sample'];e=ctx['tables']['exports'][4]
        for props in [f.props(f.prop('StyleFont','ObjectProperty',word(6),index=1)),
                      f.props(f.prop('StyleFont','ObjectProperty',word(6)),f.prop('StyleFont','ObjectProperty',word(6)))]:
            fresh=copy.deepcopy(self.packages);body=word(1)+props;e2=fresh['sample']['tables']['exports'][4]
            e2['serial_offset']=len(fresh['sample']['logical']);e2['serial_size']=len(body);fresh['sample']['logical']+=body
            r=StyleGraph(fresh).trace('sample','Fixture.Scene.Warning')
            self.assertFalse(r['text_matches'][0]['candidate_paths']);self.assertTrue(r['text_matches'][0]['unresolved'])

    def test_opaque_struct_not_interpreted(self):
        f=Fixture();p=f.build();e=p['sample']['tables']['exports'][0]
        body=word(1)+f.props(f.prop('Unknown','StructProperty',word(0xdeadbeef),'NativeStruct'))
        p['sample']['logical']+=body;e['serial_offset']=len(p['sample']['logical'])-len(body);e['serial_size']=len(body)
        parsed=StyleGraph(p).parse(('sample',1));self.assertEqual(len(parsed['opaque']),1)

    def test_null_font_stays_unresolved(self):
        field=self.g.one(('sample',5),['StyleFont']);raw=bytearray(self.packages['sample']['logical'])
        raw[field['logical_package_offset']:field['logical_package_offset']+4]=word(0)
        self.packages['sample']['logical']=bytes(raw)
        r=StyleGraph(self.packages).trace('sample','Fixture.Scene.Warning')
        self.assertFalse(r['text_matches'][0]['candidate_paths']);self.assertTrue(r['text_matches'][0]['unresolved'])

    def test_ambiguous_style_id_keeps_all_candidates(self):
        other=copy.deepcopy(self.packages['sample']);other['tables']['exports']=other['tables']['exports'][:3]
        self.packages['other']=other
        r=StyleGraph(self.packages).trace('sample','Fixture.Scene.Warning')
        self.assertEqual(r['text_matches'][0]['style_definition_count'],2)
        self.assertTrue(r['text_matches'][0]['unresolved'])

    def test_cli_modes_new_output_and_readback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(b'fixture');report=root/'out.json'
            engine=root/'engine.xxx';engine.write_bytes(b'engine')
            args=[str(source),'--sha256','unused','--deep','--text-token','Fixture.Scene.Warning','--output',str(report),
                  '--reference-package','Engine',str(engine),'unused']
            contexts=[self.packages['sample'],self.packages['engine']]
            def tables(data,digest,decoder):
                c=contexts.pop(0);return c['logical'],c['tables']
            with patch('tools.inspect_font_references._tables',side_effect=tables),patch.object(Path,'read_bytes',return_value=b'fixture'):
                self.assertEqual(main(args),0)
            r=json.loads(report.read_text(encoding='utf-8'));self.assertEqual(len(r['text_matches']),1)
            with patch('tools.inspect_font_references._tables',side_effect=[(c['logical'],c['tables']) for c in self.packages.values()]):
                self.assertEqual(main(args),2)
            self.assertEqual(source.read_bytes(),b'fixture')
            self.assertEqual(main([str(source),'--sha256','unused','--deep','--output',str(report)]),2)
            self.assertEqual(main([str(source),'--sha256','unused','--text-token','token','--output',str(report)]),2)


if __name__=='__main__':unittest.main()
