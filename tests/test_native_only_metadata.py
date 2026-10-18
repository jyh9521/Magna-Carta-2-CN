"""Synthetic native/non-native Function headers; no script is executed."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import test_function_metadata as fixtures
from tools.inspect_function_metadata import main


class NativeOnlyTests(unittest.TestCase):
    def mixed(self,bad_header=False):
        f=fixtures.FunctionFixture();e=copy.deepcopy(f.exports[20]);e['path']='RendererClass.Scripted';f.exports.append(e)
        f.replace(24,f.function(script=b'\xff\xff',flags=0x00020001,children=0,friendly='Wrong' if bad_header else 'Scripted'))
        return f

    def run_cli(self,root,f,extra=()):
        source=root/'sample.xxx';source.write_bytes(f.package());out=root/'report.json'
        args=[str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),'--class','RendererClass','--native-only',*extra,'--output',str(out)]
        code=main(args);return code,json.loads(out.read_text(encoding='utf-8')) if out.exists() else None,source

    def test_inventory_all_headers_and_skip_only_non_native_script(self):
        with tempfile.TemporaryDirectory() as d:
            f=self.mixed();expected=f.package();code,r,p=self.run_cli(Path(d),f)
            self.assertEqual(code,0);self.assertEqual(p.read_bytes(),expected)
            self.assertEqual(r['selected_objects'],['RendererClass.SetFont'])
            self.assertEqual(r['native_filter']['class_function_count'],2)
            self.assertEqual(r['native_filter']['omitted_non_native_count'],1)
            self.assertEqual([v['declared_native'] for v in r['native_filter']['inventory']],[True,False])
            self.assertFalse(r['native_filter']['omitted_scripts_decoded'])

    def test_malformed_non_native_header_remains_unparsed_not_omitted(self):
        with tempfile.TemporaryDirectory() as d:
            code,r,_=self.run_cli(Path(d),self.mixed(True));self.assertEqual(code,1)
            self.assertEqual(len(r['unparsed']),1);self.assertEqual(r['native_filter']['class_function_count'],2)
            self.assertEqual(len(r['native_filter']['inventory']),1)

    def test_indexed_native_token_preserved_in_header_and_parsed_record(self):
        with tempfile.TemporaryDirectory() as d:
            f=fixtures.FunctionFixture();body=f.function();at=44+len(f.script);f.replace(21,body[:at]+b'\x01\xd0'+body[at+2:])
            code,r,_=self.run_cli(Path(d),f);self.assertEqual(code,0)
            self.assertEqual(r['functions'][0]['native_token'],464)
            self.assertEqual(r['native_filter']['inventory'][0]['native_token'],464)

    def test_native_only_requires_class_and_excludes_script_decoder(self):
        self.assertEqual(main(['missing','--sha256','0'*64,'--object','Object.Func','--native-only','--output','unused']),2)
        self.assertEqual(main(['missing','--sha256','0'*64,'--class','Object','--native-only','--include-scripted','--output','unused']),2)

    def test_default_report_shape_keeps_opt_in_inventory_absent(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'sample.xxx';source.write_bytes(fixtures.FunctionFixture().package());out=root/'default.json'
            self.assertEqual(main([str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),'--class','RendererClass','--output',str(out)]),0)
            self.assertNotIn('native_filter',json.loads(out.read_text(encoding='utf-8')))

    def test_all_non_native_scope_is_explicit_empty_native_selection(self):
        with tempfile.TemporaryDirectory() as d:
            f=fixtures.FunctionFixture();f.replace(21,f.function(script=b'\xff\xff',flags=0x00020001,children=0))
            code,r,_=self.run_cli(Path(d),f);self.assertEqual(code,0);self.assertEqual(r['functions'],[])
            self.assertEqual(r['selected_objects'],[]);self.assertEqual(r['native_filter']['omitted_non_native_count'],1)


if __name__=='__main__':unittest.main()
