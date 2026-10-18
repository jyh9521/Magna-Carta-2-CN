import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_font_binding_audit import alias_package,context
from tools.ue3_ui_styles import StyleGraph
from tools.font_binding_audit import fingerprint
from tools.build_font_binding_probe import build,validate_plan,main


class ProbeBundleTests(unittest.TestCase):
    def test_disc_plans_share_exact_font_sources_but_lock_distinct_tocs(self):
        root=Path(__file__).resolve().parents[1]/'references/probes'
        one=json.loads((root/'login-font-geometry.json').read_text(encoding='utf-8'))
        two=json.loads((root/'login-font-geometry-disc2.json').read_text(encoding='utf-8'))
        self.assertEqual(one['sources'],two['sources'])
        self.assertEqual(one['expected_semantic_sha256'],two['expected_semantic_sha256'])
        self.assertNotEqual(one['toc']['sha256'],two['toc']['sha256'])
        validate_plan(one);validate_plan(two)

    def fixture(self,root):
        game=root/'original';game.mkdir();(game/'Game').mkdir()
        sources=[];toc=[]
        for i,label in enumerate(['one','two','three']):
            raw=alias_package(i);(game/'Game'/(label+'.xxx')).write_bytes(raw)
            sources.append(dict(label=label,path='Game/'+label+'.xxx',sha256=hashlib.sha256(raw).hexdigest(),font_object='Assets.General'))
            toc.append(f'{len(raw)} 0 1 ..\\Game\\{label}.xxx 0\r\n')
        t=''.join(toc).encode();(game/'Xbox360TOC.txt').write_bytes(t)
        fp=fingerprint(StyleGraph(dict(one=context(alias_package()))),('one',1))
        plan=dict(schema_version=1,game_rendering_verified=False,required_source_count=3,canonical_font_path='assets.general',
                  expected_namespace_guid='a'*32,expected_semantic_sha256=fp['semantic_sha256'],codepoint=65,expected_glyph=0,target_glyph=1,
                  sources=sources,toc=dict(path='Xbox360TOC.txt',sha256=hashlib.sha256(t).hexdigest()))
        return game,plan

    def test_three_aliases_controls_candidates_and_inverse(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,plan=self.fixture(root);out=root/'probe';r=build(plan,game,out)
            self.assertEqual(len(r['sources']),3);self.assertFalse(r['deployment_performed'])
            self.assertEqual(len({x['semantic_after'] for x in r['sources']}),1)
            self.assertEqual(r['toc_changes'],[])
            for row in r['sources']:
                files=row['files'];self.assertEqual(Path(files['controls']['path']).read_bytes(),Path(files['inverse-check']['path']).read_bytes())
                self.assertNotEqual(files['controls']['sha256'],files['candidates']['sha256'])
                self.assertEqual(hashlib.sha256((game/row['source_path']).read_bytes()).hexdigest(),row['source_sha256'])
            self.assertEqual(json.loads((out/'manifest.json').read_text(encoding='utf-8')),r)

    def test_plan_count_labels_paths_guids_and_scalar_guards(self):
        with tempfile.TemporaryDirectory() as d:
            _,plan=self.fixture(Path(d))
            bad=[]
            for key,value in [('required_source_count',2),('game_rendering_verified',True),('expected_namespace_guid','0'*32),('target_glyph',True),('codepoint',65536)]:
                p=copy.deepcopy(plan);p[key]=value;bad.append(p)
            for key,value in [('label','../bad'),('label','CON'),('path','../Game/one.xxx'),('sha256','0'*63)]:
                p=copy.deepcopy(plan);p['sources'][0][key]=value;bad.append(p)
            p=copy.deepcopy(plan);p['sources'][1]['label']='ONE';bad.append(p)
            bad += [[],{},dict(plan,sources=[1,2,3])]
            for p in bad:
                with self.subTest(p=p),self.assertRaises((ValueError,TypeError)):validate_plan(p)

    def test_hash_semantic_font_and_donor_fail_before_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,plan=self.fixture(root)
            for i,change in enumerate(['hash','semantic','font','donor','guid']):
                p=copy.deepcopy(plan)
                if change=='hash':p['sources'][0]['sha256']='0'*64
                elif change=='semantic':p['expected_semantic_sha256']='0'*64
                elif change=='font':p['sources'][0]['font_object']='Missing'
                elif change=='donor':p['target_glyph']=99
                else:p['expected_namespace_guid']='b'*32
                out=root/str(i)
                with self.assertRaises(ValueError):build(p,game,out)
                self.assertFalse(out.exists())

    def test_existing_output_and_game_tree_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,plan=self.fixture(root);out=root/'existing';out.mkdir()
            for target in [out,game/'probe']:
                with self.assertRaises(ValueError):build(plan,game,target)
            self.assertFalse((game/'probe').exists())

    def test_cli_reopening_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,plan=self.fixture(root);p=root/'plan.json';p.write_text(json.dumps(plan),encoding='utf-8')
            args=['--plan',str(p),'--game-root',str(game),'--output-dir',str(root/'output')]
            self.assertEqual(main(args),0);self.assertEqual(main(args),2)

    def test_geometry_report_readback_failure_is_not_success(self):
        from tools.ue3_package import write_report as real_write
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,plan=self.fixture(root)
            def broken(path,report):
                real_write(path,{'corrupt':True} if path.parent.name=='reports' else report)
            with patch('tools.build_font_binding_probe.write_report',side_effect=broken):
                with self.assertRaisesRegex(ValueError,'reopening'):build(plan,game,root/'output')
            self.assertFalse((root/'output/manifest.json').exists())


if __name__=='__main__':unittest.main()
