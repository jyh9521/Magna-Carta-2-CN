import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_ui_style_graph import Fixture, word
from tools.probe_ui_style_font import main, patch_graph
from tools.ue3_ui_styles import StyleGraph


class StyleProbeTests(unittest.TestCase):
    def setUp(self):
        self.contexts=Fixture().build();self.data=self.contexts['sample']['logical']

    def probe(self, **changes):
        args=dict(data=self.data,graph=StyleGraph(self.contexts),package='sample',style_path='Styles.General',
                  expected_font='Font.General',target_font='Font.Donor');args.update(changes)
        return patch_graph(**args)

    def test_only_four_byte_field_and_inverse(self):
        output,report=self.probe();change,=report['changes'];offset=change['offset']
        self.assertEqual(len(output),len(self.data));self.assertEqual(output[:offset],self.data[:offset])
        self.assertEqual(output[offset+4:],self.data[offset+4:]);self.assertEqual(output[offset:offset+4],word(7))
        self.assertTrue(report['inverse_byte_identical']);self.assertFalse(report['deployment_performed'])
        c=copy.deepcopy(self.contexts);c['sample']['logical']=output
        restored,_=self.probe(data=output,graph=StyleGraph(c),expected_font='Font.Donor',target_font='Font.General')
        self.assertEqual(restored,self.data)

    def test_object_name_expected_target_guards(self):
        for kw in [dict(style_path='missing'),dict(expected_font='Font.Donor'),dict(target_font='Font.General'),
                   dict(target_font='Styles.General'),dict(target_font='missing'),dict(data=b'different')]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):self.probe(**kw)

    def test_null_custom_data_and_outside_font_reference(self):
        for ref in [0,999]:
            c=copy.deepcopy(self.contexts);g=StyleGraph(c);field=g.one(('sample',4),['TextStyle','CustomStyleData'])
            raw=bytearray(c['sample']['logical']);raw[field['logical_package_offset']:field['logical_package_offset']+4]=word(ref)
            c['sample']['logical']=bytes(raw)
            with self.assertRaises(ValueError):self.probe(data=bytes(raw),graph=StyleGraph(c))

    def test_duplicate_fields_and_state_map_no_guessing(self):
        c=copy.deepcopy(self.contexts);c['sample']['tables']['exports'].append(c['sample']['tables']['exports'][2].copy())
        with self.assertRaises(ValueError):self.probe(graph=StyleGraph(c))
        c=copy.deepcopy(self.contexts);c['sample']['tables']['exports'][2]['serial_size']-=1
        with self.assertRaises(ValueError):self.probe(graph=StyleGraph(c))

    def test_cli_readback_no_overwrite_alias_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(self.data)
            dep=root/'engine.xxx';dep.write_bytes(b'engine')
            output=root/'out.xxx';report=root/'report.json'
            args=[str(source),'--sha256',hashlib.sha256(self.data).hexdigest(),'--style-object','Styles.General',
                  '--expected-font','Font.General','--target-font','Font.Donor','--output',str(output),'--report',str(report),
                  '--reference-package','Engine',str(dep),'unused']
            returns=[(self.contexts[k]['logical'],self.contexts[k]['tables']) for k in ['sample','engine','sample']]
            with patch('tools.probe_ui_style_font.parse_summary',return_value=dict(compression_flags=0,compressed_chunks=[])),patch('tools.probe_ui_style_font._tables',side_effect=returns):
                self.assertEqual(main(args),0)
            r=json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),r['output_sha256'])
            self.assertEqual(main(args),2)
            alias=args.copy();alias[alias.index('--output')+1]=str(source)
            self.assertEqual(main(alias),2)
            alias=args.copy();alias[alias.index('--output')+1]=str(dep)
            self.assertEqual(main(alias),2)
            self.assertEqual(source.read_bytes(),self.data)

    def test_cli_compressed_unknown_hash_and_invalid_profile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(self.data)
            args=[str(source),'--sha256',hashlib.sha256(self.data).hexdigest(),'--style-object','Styles.General',
                  '--expected-font','Font.General','--target-font','Font.Donor','--output',str(root/'out'),'--report',str(root/'report')]
            with patch('tools.probe_ui_style_font.parse_summary',return_value=dict(compression_flags=1,compressed_chunks=[{}])):
                self.assertEqual(main(args),2)
            self.assertEqual(main(args),2)
            args[args.index('--sha256')+1]='0'*64
            self.assertEqual(main(args),2)
            self.assertFalse((root/'out').exists());self.assertFalse((root/'report').exists())


if __name__=='__main__':unittest.main()
