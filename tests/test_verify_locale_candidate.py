"""Independent candidate replay fixtures, including forged producer metadata."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import test_locale_candidate as candidate_fixtures
from test_supplement_font import stored_decoder
from tools import verify_locale_candidate as verifier
from tools.font_binding_plan import digest, confined_path


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf8')


class IndependentCandidateTests(unittest.TestCase):
    def fixture(self,root):
        helper=candidate_fixtures.CandidateAssemblyTests();game,fonts,plan=helper.fixture(root)
        helper.build(root,game,fonts,plan)
        return root/'assembled',plan

    def verify(self,root,tree,plan,anchor=None):
        return verifier.verify(plan,tree,root,stored_decoder,anchor)

    def test_relocated_tree_with_only_trusted_jsons_and_no_producer_build(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            root,new=Path(d),Path(other);tree,plan=self.fixture(root)
            moved=new/'moved';shutil.copytree(tree,moved)
            for name in ('font-plan.json','text-plan.json','glyphs.json'):(new/name).write_bytes((root/name).read_bytes())
            anchor=digest((tree/'manifest.json').read_bytes());before={p.relative_to(moved).as_posix():digest(p.read_bytes()) for p in moved.rglob('*') if p.is_file()}
            with patch('tools.build_locale_candidate.build',side_effect=AssertionError('producer build must not run')):
                report=self.verify(new,moved,plan,anchor)
            self.assertEqual(report['verified_resources'],5);self.assertEqual(report['verified_member_files'],18)
            self.assertTrue(report['trusted_manifest_sha256_verified']);self.assertTrue(report['reports_match_independent_replay'])
            self.assertFalse(report['producer_success_flags_used_as_proof']);self.assertFalse(report['producer_additional_inputs_reopened'])
            self.assertFalse(report['raster_source_font_file_reopened']);self.assertFalse(report['game_rendering_verified'])
            self.assertEqual(before,{p.relative_to(moved).as_posix():digest(p.read_bytes()) for p in moved.rglob('*') if p.is_file()})

    def test_wrong_manifest_anchor_rejects_before_asset_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root)
            with patch.object(verifier,'context',side_effect=AssertionError('must fail before Font parse')):
                with self.assertRaisesRegex(ValueError,'SHA256'):self.verify(root,tree,plan,'0'*64)

    def test_payload_hash_forgery_cannot_be_hidden_by_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);path=tree/'candidate/Game/one.xxx'
            path.write_bytes(path.read_bytes()+b'changed isolated payload')
            manifest=json.loads((tree/'manifest.json').read_text(encoding='utf8'))
            manifest['resources'][0]['candidate']['sha256']=digest(path.read_bytes())
            write_json(tree/'manifest.json',manifest)
            with self.assertRaisesRegex(ValueError,'SHA256'):self.verify(root,tree,plan)

    def test_missing_extra_and_unknown_directory_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root)
            (tree/'unexpected.exe').write_bytes(b'self-authored marker, never executed')
            with self.assertRaisesRegex(ValueError,'member set'):self.verify(root,tree,plan)
            (tree/'unexpected.exe').unlink();(tree/'unused').mkdir()
            with self.assertRaisesRegex(ValueError,'directory'):self.verify(root,tree,plan)
            (tree/'unused').rmdir();(tree/'rollback-check/Game/one.xxx').unlink()
            with self.assertRaisesRegex(ValueError,'member set'):self.verify(root,tree,plan)

    def test_declared_escape_paths_duplicates_and_sizes_are_not_trusted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);path=tree/'manifest.json';original=json.loads(path.read_text(encoding='utf8'))
            cases=[]
            p=copy.deepcopy(original);p['resources'][0]['candidate']['path']='../outside';cases.append(p)
            p=copy.deepcopy(original);p['resources'][0]['control']['size']+=1;cases.append(p)
            p=copy.deepcopy(original);p['resources'].append(p['resources'][0]);cases.append(p)
            for value in cases:
                write_json(path,value)
                with self.assertRaisesRegex(ValueError,'manifest contract'):self.verify(root,tree,plan)

    def test_typed_flags_do_not_equate_false_to_zero_or_int_to_float(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);path=tree/'manifest.json';original=json.loads(path.read_text(encoding='utf8'))
            for key,value in [('schema_version',True),('game_rendering_verified',0),('deployment_performed',True),('all_resource_hashes_rechecked',1)]:
                p=copy.deepcopy(original);p[key]=value;write_json(path,p)
                with self.subTest(key=key),self.assertRaises(ValueError):self.verify(root,tree,plan)
            self.assertNotEqual(verifier.canonical_json(dict(value=1)),verifier.canonical_json(dict(value=1.0)))

    def test_ambiguous_duplicate_keys_and_non_finite_json_are_rejected(self):
        from tools.font_binding_plan import parse_json_object
        for raw in (b'{"a":1,"a":1}',b'{"outer":{"a":0,"a":1}}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):parse_json_object(raw)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);path=tree/'manifest.json'
            raw=path.read_text(encoding='utf8').replace('"schema_version": 1','"schema_version": 0, "schema_version": 1')
            path.write_text(raw,encoding='utf8')
            with self.assertRaisesRegex(ValueError,'duplicate JSON key'):self.verify(root,tree,plan)

    def test_consistent_report_hash_forgery_still_fails_replayed_values(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);report_path=tree/'reports/text-font-coverage.json'
            report=json.loads(report_path.read_text(encoding='utf8'));report['glyph_pixels_verified']=True;write_json(report_path,report)
            manifest=json.loads((tree/'manifest.json').read_text(encoding='utf8'));manifest['reports'][0]['sha256']=digest(report_path.read_bytes());write_json(tree/'manifest.json',manifest)
            with self.assertRaisesRegex(ValueError,'report does not match'):self.verify(root,tree,plan)

    def test_producer_extra_declarations_remain_unproven_without_trusted_anchor(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);path=tree/'manifest.json';anchor=digest(path.read_bytes())
            manifest=json.loads(path.read_text(encoding='utf8'));manifest['additional_input_hashes']=[dict(name='old-decoder.dll',sha256='0'*64)];write_json(path,manifest)
            report=self.verify(root,tree,plan)
            self.assertFalse(report['trusted_manifest_sha256_verified']);self.assertFalse(report['producer_additional_inputs_reopened'])
            with self.assertRaisesRegex(ValueError,'SHA256'):self.verify(root,tree,plan,anchor)
            manifest['additional_input_hashes'][0]['name']='../decoder';write_json(path,manifest)
            with self.assertRaisesRegex(ValueError,'additional input'):self.verify(root,tree,plan)

    def test_descendant_links_and_confined_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);real=Path.is_symlink;target=(tree/'candidate').resolve()
            def linked(path):return path.resolve()==target or real(path)
            with patch.object(Path,'is_symlink',linked),self.assertRaisesRegex(ValueError,'linked candidate'):self.verify(root,tree,plan)
            with self.assertRaises(ValueError):confined_path(tree,'../outside')

    def test_wrong_trusted_dependency_and_candidate_plans_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root)
            for field in ('font_plan','text_plan'):
                p=copy.deepcopy(plan);p[field]['sha256']='0'*64
                with self.assertRaisesRegex(ValueError,'SHA256'):self.verify(root,tree,p)
            p=copy.deepcopy(plan);p['font_candidates'].pop()
            with self.assertRaises(ValueError):self.verify(root,tree,p)

    def test_late_member_mutation_is_caught_by_final_rehash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,plan=self.fixture(root);real=verifier.audit
            def changed(*a,**kw):
                report=real(*a,**kw);(tree/'candidate/Game/one.xxx').write_bytes(b'changed isolated member');return report
            with patch.object(verifier,'audit',side_effect=changed),self.assertRaisesRegex(ValueError,'dependency changed'):
                self.verify(root,tree,plan)

    def cli_fixture(self,root):
        tree,plan=self.fixture(root);path=root/'candidate.json';write_json(path,plan)
        decoder=root/'decoder.bin';decoder.write_bytes(b'mocked decoder, never loaded')
        args=['--plan',str(path),'--candidate-root',str(tree),'--project-root',str(root),
              '--manifest-sha256',digest((tree/'manifest.json').read_bytes()),'--lzx-library',str(decoder),'--output',str(root/'audit.json')]
        return tree,args

    def test_cli_no_overwrite_and_no_report_inside_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tree,args=self.cli_fixture(root)
            with patch.object(verifier,'LzxDecoder',return_value=stored_decoder):
                self.assertEqual(verifier.main(args),0);self.assertEqual(verifier.main(args),2)
                args[-1]=str(tree/'new-report.json');self.assertEqual(verifier.main(args),2)
            report=json.loads((root/'audit.json').read_text(encoding='utf8'))
            self.assertTrue(report['trusted_manifest_sha256_verified'])
            self.assertEqual(len(report['verifier_additional_input_hashes']),2)
            self.assertFalse((tree/'new-report.json').exists())

    def test_cli_readback_and_post_publication_mutations_are_errors(self):
        for mode in ('readback','member'):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);tree,args=self.cli_fixture(root);read=Path.read_bytes;target=(root/'audit.json').resolve();hits=[]
                def altered(path):
                    value=read(path)
                    if path.resolve()==target:
                        hits.append(str(path))
                        if mode=='readback':return b'{}'
                        (tree/'candidate/Game/one.xxx').write_bytes(b'changed after external report')
                    return value
                with patch.object(verifier,'LzxDecoder',return_value=stored_decoder),patch.object(Path,'read_bytes',altered):
                    self.assertEqual(verifier.main(args),2)
                self.assertEqual(len(hits),1)


if __name__ == '__main__':unittest.main()
