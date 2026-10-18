"""Synthetic font/text/TOC dependency assembly; no game/font/DLL requirement."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_build_font_supplement as font_fixtures
from test_supplement_font import stored_decoder
from test_text_font_coverage import fixture as text_fixture
from tools import build_locale_candidate as assembler
from tools.build_coalesced import rebuild
from tools.coalesced import extract_entries, parse
from tools.font_binding_plan import digest, read_locked_json
from tools.update_resource_sizes import update_sizes


def write_json(path,data):
    raw=(json.dumps(data,ensure_ascii=True,indent=2)+'\n').encode();path.write_bytes(raw)
    return dict(path=path.name,sha256=digest(raw))


class CandidateAssemblyTests(unittest.TestCase):
    def fixture(self,root):
        helper=font_fixtures.SupplementBundleTests();game,font,font_plan,alphas=helper.fixture(root)
        raw,_,_=text_fixture();resource='Game/Coalesced.int';(game/resource).write_bytes(raw)
        toc_path=game/font_plan['toc']['path'];toc=toc_path.read_bytes()+f'{len(raw)} 0 1 ..\\Game\\Coalesced.int 0\r\n'.encode()
        toc_path.write_bytes(toc);font_plan['toc']['sha256']=digest(toc)
        source=extract_entries(parse(raw),resource)[0]
        text_plan=dict(schema_version=1,source_mode='sha256-utf8',resource=resource,input_sha256=digest(raw),
                       entries=[dict(id=source['id'],source_sha256=digest(source['source'].encode('utf8')),
                                     translation='A'+chr(0x6587)+'{0}\\n')])
        text_ref=write_json(root/'text-plan.json',text_plan);font_ref=write_json(root/'font-plan.json',font_plan)
        font_root=root/'font-bundle';bundle=helper.run_build(root,game,font,font_plan,alphas,font_root)
        hashes=[dict(label=r['label'],sha256=r['files']['candidate']['sha256']) for r in bundle['sources']]
        text_candidate=rebuild(raw,text_plan)
        changes=list(bundle['toc_changes'])+[dict(path=resource,expected_size=len(raw),new_size=len(text_candidate))]
        expected_toc=update_sizes(toc,digest(toc),changes)
        plan=dict(schema_version=1,kind='offline-locale-candidate',game_rendering_verified=False,
                  font_plan=font_ref,text_plan=text_ref,text_resource=resource,
                  font_candidates=hashes,expected_text_sha256=digest(text_candidate),expected_toc_sha256=digest(expected_toc))
        return game,font_root,plan

    def build(self,root,game,fonts,plan,out=None):
        return assembler.build(plan,game,root,fonts,out or root/'assembled',stored_decoder)

    def test_five_resources_relative_manifest_and_variable_text_toc(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root);r=self.build(root,game,fonts,plan)
            self.assertEqual(len(r['resources']),5);self.assertEqual(len(r['toc_changes']),4)
            self.assertIn('Game/Coalesced.int',[v['path'] for v in r['toc_changes']])
            self.assertFalse(r['deployment_performed']);self.assertFalse(r['game_rendering_verified'])
            self.assertFalse(r['source_font_file_rechecked']);self.assertFalse(r['upstream_manifest_trusted'])
            self.assertEqual(json.loads((root/'assembled/manifest.json').read_text(encoding='utf8')),r)
            for row in r['resources']:
                original=(game/row['resource']).read_bytes()
                for key in ('control','candidate','restored'):
                    item=row[key];self.assertFalse(Path(item['path']).is_absolute())
                    self.assertEqual(digest((root/'assembled'/item['path']).read_bytes()),item['sha256'])
                self.assertEqual((root/'assembled'/row['restored']['path']).read_bytes(),original)
                self.assertEqual(row['control']['sha256'],digest(original))
            self.assertTrue(r['text_inverse_byte_identical']);self.assertTrue(r['toc_inverse_byte_identical'])
            self.build(root,game,fonts,plan,root/'repeat')
            one={p.relative_to(root/'assembled').as_posix():digest(p.read_bytes())
                 for p in (root/'assembled').rglob('*') if p.is_file()}
            two={p.relative_to(root/'repeat').as_posix():digest(p.read_bytes())
                 for p in (root/'repeat').rglob('*') if p.is_file()}
            self.assertEqual(one,two)

    def test_locked_candidates_all_required_and_expected_output_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root)
            cases=[]
            for field in ('expected_text_sha256','expected_toc_sha256'):
                p=copy.deepcopy(plan);p[field]='0'*64;cases.append(p)
            p=copy.deepcopy(plan);p['font_candidates'].pop();cases.append(p)
            p=copy.deepcopy(plan);p['font_candidates'][0]['sha256']='0'*64;cases.append(p)
            p=copy.deepcopy(plan);p['font_candidates'][1]['label']='ONE';cases.append(p)
            for p in cases:
                with self.subTest(p=p),self.assertRaises(ValueError):self.build(root,game,fonts,p)
                self.assertFalse((root/'assembled').exists())

    def test_locked_json_reference_and_payload_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root)
            for ref in (None,dict(path='../outside.json',sha256='0'*64),dict(path='font-plan.json',sha256='0'*64)):
                with self.subTest(ref=ref),self.assertRaises(ValueError):read_locked_json(root,ref)
            path=root/'list.json';path.write_text('[]',encoding='utf8')
            with self.assertRaisesRegex(ValueError,'payload'):read_locked_json(root,dict(path='list.json',sha256=digest(path.read_bytes())))
            for field in ('font_plan','text_plan'):
                p=copy.deepcopy(plan);p[field]['sha256']='0'*64
                with self.assertRaises(ValueError):self.build(root,game,fonts,p)

    def test_upstream_success_manifest_cannot_replace_or_skip_payloads(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root)
            (fonts/'manifest.json').write_text('{"sources":[],"deployment_performed":true}',encoding='utf8')
            r=self.build(root,game,fonts,plan);self.assertEqual(len(r['resources']),5)
            (fonts/'candidates/one.xxx').unlink()
            with self.assertRaises(OSError):self.build(root,game,fonts,plan,root/'missing')
            self.assertFalse((root/'missing').exists())

    def test_original_wrong_version_fails_without_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root)
            (game/'Xbox360TOC.txt').write_bytes(b'wrong disc synthetic TOC')
            with self.assertRaisesRegex(ValueError,'SHA256'):self.build(root,game,fonts,plan)
            self.assertFalse((root/'assembled').exists())

    def test_missing_glyph_and_protected_token_changes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root);path=root/'text-plan.json'
            text=json.loads(path.read_text(encoding='utf8'));base=copy.deepcopy(text)
            for target,message in [('B{0}\\n','not covered'),('A','protected token')]:
                p=copy.deepcopy(plan);text=copy.deepcopy(base);text['entries'][0]['translation']=target
                p['text_plan']=write_json(path,text)
                with self.assertRaisesRegex(ValueError,message):self.build(root,game,fonts,p)
                self.assertFalse((root/'assembled').exists())

    def test_toc_source_size_conflict_is_not_patched_blindly(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root);toc=game/'Xbox360TOC.txt';raw=toc.read_bytes()
            size=len((game/'Game/Coalesced.int').read_bytes())
            raw=raw.replace(f'{size} 0 1 ..\\Game\\Coalesced.int'.encode(),f'{size+1} 0 1 ..\\Game\\Coalesced.int'.encode())
            toc.write_bytes(raw);fp=root/'font-plan.json';p=json.loads(fp.read_text(encoding='utf8'));p['toc']['sha256']=digest(raw)
            plan['font_plan']=write_json(fp,p)
            with self.assertRaisesRegex(ValueError,'source size mismatch'):self.build(root,game,fonts,plan)
            self.assertFalse((root/'assembled').exists())

    def test_existing_and_input_subtree_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root)
            for out in (root,game/'new',fonts/'new'):
                with self.assertRaises(ValueError):self.build(root,game,fonts,plan,out)
            self.assertFalse((game/'new').exists());self.assertFalse((fonts/'new').exists())

    def test_resource_readback_failure_leaves_no_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root);read=Path.read_bytes;hits=[]
            target=(root/'assembled/candidate/Game/Coalesced.int').resolve()
            def altered(path):
                raw=read(path)
                if path.resolve()==target:hits.append(str(path));return raw+b'corrupt'
                return raw
            with patch.object(Path,'read_bytes',altered),self.assertRaises(ValueError):self.build(root,game,fonts,plan)
            self.assertEqual(len(hits),1);self.assertFalse((root/'assembled/manifest.json').exists())

    def test_late_input_and_output_mutation_are_detected(self):
        for kind in ('input','output'):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);game,fonts,plan=self.fixture(root)
                if kind=='input':
                    real=assembler.audit
                    def audit(*a,**kw):
                        r=real(*a,**kw);(game/'Game/Coalesced.int').write_bytes(b'changed synthetic input');return r
                    guard=patch.object(assembler,'audit',side_effect=audit)
                else:
                    real=assembler.save_report
                    def save(path,report):
                        r=real(path,report)
                        if path.name=='text-font-coverage.json':(root/'assembled/candidate/Game/one.xxx').write_bytes(b'changed synthetic output')
                        return r
                    guard=patch.object(assembler,'save_report',side_effect=save)
                with guard,self.assertRaises(ValueError):self.build(root,game,fonts,plan)
                self.assertFalse((root/'assembled/manifest.json').exists())

    def test_cli_and_schema_identity_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,fonts,plan=self.fixture(root);path=root/'candidate.json';write_json(path,plan)
            decoder=root/'decoder.bin';decoder.write_bytes(b'mocked decoder; never loaded')
            args=['--plan',str(path),'--game-root',str(game),'--project-root',str(root),'--font-bundle',str(fonts),
                  '--output-dir',str(root/'cli'),'--lzx-library',str(decoder)]
            with patch.object(assembler,'LzxDecoder',return_value=stored_decoder):
                self.assertEqual(assembler.main(args),0);self.assertEqual(assembler.main(args),2)
            manifest=json.loads((root/'cli/manifest.json').read_text(encoding='utf8'))
            self.assertEqual(manifest['additional_input_hashes'],[
                dict(name=path.name,sha256=digest(path.read_bytes())),
                dict(name=decoder.name,sha256=digest(decoder.read_bytes()))])
            for field,value in [('schema_version',True),('kind','release'),('game_rendering_verified',True),('text_resource','../escape')]:
                p=copy.deepcopy(plan);p[field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):assembler.validate_plan(p)
            p=copy.deepcopy(plan);p['text_resource']='Game/one.xxx'
            text=json.loads((root/'text-plan.json').read_text(encoding='utf8'));text['resource']=p['text_resource']
            p['text_plan']=write_json(root/'text-plan.json',text)
            with self.assertRaisesRegex(ValueError,'aliases'):self.build(root,game,fonts,p,root/'alias')

    def test_disc_candidate_plans_bind_actual_dependency_bytes(self):
        project=Path(__file__).resolve().parents[1];plans=[]
        for disc in (1,2):
            p=json.loads((project/f'locales/zh-Hans/candidate-disc{disc}.json').read_text(encoding='utf8'));assembler.validate_plan(p)
            font,_,_=read_locked_json(project,p['font_plan']);text,_,_=read_locked_json(project,p['text_plan'])
            self.assertEqual(text['resource'],p['text_resource'])
            self.assertEqual({s['label'].casefold() for s in font['sources']},{s['label'].casefold() for s in p['font_candidates']})
            plans.append(p)
        self.assertEqual(plans[0]['font_candidates'],plans[1]['font_candidates'])
        self.assertEqual(plans[0]['text_plan'],plans[1]['text_plan'])
        self.assertNotEqual(plans[0]['font_plan']['sha256'],plans[1]['font_plan']['sha256'])
        self.assertNotEqual(plans[0]['expected_toc_sha256'],plans[1]['expected_toc_sha256'])


if __name__ == '__main__':unittest.main()
