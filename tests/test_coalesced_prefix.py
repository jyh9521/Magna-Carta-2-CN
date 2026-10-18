"""Synthetic prefix probes/publication guards; no original game text or fonts."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import build_coalesced as builder
from tools import audit_text_font_coverage as coverage
from tools import verify_locale_candidate as independent
from tools.coalesced import EmbeddedFile,SerializedString,serialize,parse,extract_entries
from tools.font_binding_plan import read_locked_json
from tools.validate_catalog import TOKEN
from test_text_font_coverage import fixture as coverage_fixture
import test_locale_candidate as candidate_fixtures
from test_supplement_font import stored_decoder


def fixture(source='XYZ tail {0}\\n',replacement='ABC',count=3,preserve=True):
    raw=serialize([EmbeddedFile(SerializedString('fixture.int','ascii',0),
                  SerializedString('[Test]\r\nText='+source+'\r\nOther=retained\n','utf-16-le',0))])
    row=extract_entries(parse(raw),'synthetic')[0]
    edit=dict(id=row['id'],source_sha256=builder.sha256(source.encode()),source_prefix_codepoints=count,
              replacement=replacement,preserve_utf16_units=preserve,
              selector={k:row[k] for k in ('embedded_path','section','key','occurrence')})
    return raw,dict(schema_version=1,source_mode='sha256-utf8-prefix',input_sha256=builder.sha256(raw),resource='synthetic',entries=[edit])


class PrefixProbeTests(unittest.TestCase):
    def test_prefix_retains_suffix_tokens_and_source_selector_without_plan_mutation(self):
        raw,plan=fixture();before=copy.deepcopy(plan);resolved=builder.resolve_changes(raw,plan);edit=resolved['entries'][0]
        self.assertEqual(edit['translation'],'ABC tail {0}\\n');self.assertEqual(edit['prefix_scope']['source_selector'],plan['entries'][0]['selector'])
        self.assertEqual(edit['prefix_scope']['preserved_suffix_sha256'],builder.sha256(' tail {0}\\n'.encode()))
        out=builder.rebuild(raw,plan);rows=extract_entries(parse(out),'synthetic');self.assertEqual(rows[0]['source'],edit['translation'])
        self.assertEqual(rows[1]['source'],'retained');self.assertEqual(TOKEN.findall(rows[0]['source']),['{0}','\\n'])
        self.assertEqual(len(out),len(raw));self.assertEqual(plan,before)

    def test_utf16_units_are_distinct_from_codepoint_count(self):
        raw,plan=fixture(source='😀suffix',replacement='AB',count=1);resolved=builder.resolve_changes(raw,plan)['entries'][0]
        self.assertEqual(resolved['prefix_scope']['source_prefix_utf16_units'],2);self.assertEqual(resolved['prefix_scope']['replacement_utf16_units'],2)
        self.assertEqual(len(builder.rebuild(raw,plan)),len(raw));self.assertEqual(resolved['translation'],'ABsuffix')
        plan['entries'][0]['replacement']='A'
        with self.assertRaisesRegex(ValueError,'UTF16 length'):builder.rebuild(raw,plan)

    def test_explicit_variable_length_prefix_and_empty_prefix_insert(self):
        raw,plan=fixture(replacement='A',preserve=False);out=builder.rebuild(raw,plan);self.assertLess(len(out),len(raw))
        self.assertEqual(extract_entries(parse(out),'synthetic')[0]['source'],'A tail {0}\\n')
        raw,plan=fixture(replacement='A',count=0,preserve=False)
        self.assertEqual(extract_entries(parse(builder.rebuild(raw,plan)),'synthetic')[0]['source'],'AXYZ tail {0}\\n')

    def test_prefix_must_not_split_recognized_token_boundaries(self):
        for source,n in [('X{0}tail',2),('X\\ntail',2)]:
            raw,plan=fixture(source=source,count=n,replacement='A'*n)
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'splits a protected'):builder.rebuild(raw,plan)

    def test_complete_tokens_are_preserved_and_new_or_reordered_tokens_fail(self):
        raw,plan=fixture(source='X{0}tail',count=4,replacement='A{0}')
        self.assertEqual(extract_entries(parse(builder.rebuild(raw,plan)),'synthetic')[0]['source'],'A{0}tail')
        for replacement in ['ABCD','A{1}','{0}\\n']:
            p=copy.deepcopy(plan);p['entries'][0]['replacement']=replacement;p['entries'][0]['preserve_utf16_units']=False
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):builder.rebuild(raw,p)

    def test_count_flag_replacement_and_unknown_fields_fail_closed(self):
        for key,value in [('source_prefix_codepoints',True),('source_prefix_codepoints',-1),('source_prefix_codepoints',999),
                          ('source_prefix_codepoints',3.0),('preserve_utf16_units',1),('replacement',None),('unexpected','field')]:
            raw,p=fixture();p['entries'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):builder.rebuild(raw,p)
        for key in ['source_prefix_codepoints','preserve_utf16_units','replacement']:
            raw,p=fixture();del p['entries'][0][key]
            with self.subTest(key=key),self.assertRaises(ValueError):builder.rebuild(raw,p)

    def test_mixed_literal_full_value_and_prefix_modes_are_not_guessed(self):
        for mode in ['literal','sha256-utf8']:
            raw,p=fixture();p['source_mode']=mode
            with self.subTest(mode=mode),self.assertRaises(ValueError):builder.rebuild(raw,p)
        for key,value in [('source','XYZ tail {0}\\n'),('translation','ABC tail {0}\\n')]:
            raw,p=fixture();p['entries'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):builder.rebuild(raw,p)
        raw,p=fixture();p['source_mode']='literal';p['entries'][0].update(source='XYZ tail {0}\\n',translation='ABC tail {0}\\n')
        with self.assertRaisesRegex(ValueError,'require explicit prefix'):builder.rebuild(raw,p)

    def test_selector_types_exact_case_occurrence_and_path_identity(self):
        for key,value in [('embedded_path','other.int'),('section','test'),('key','Other'),('occurrence',True),('occurrence',2)]:
            raw,p=fixture();p['entries'][0]['selector'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'selector'):builder.rebuild(raw,p)
        raw,p=fixture();p['entries'][0]['selector']['extra']='x'
        with self.assertRaises(ValueError):builder.rebuild(raw,p)
        raw,p=fixture();del p['entries'][0]['selector'];self.assertTrue(builder.rebuild(raw,p))

    def test_source_container_hash_id_duplicates_and_exact_utf8_source_hash(self):
        for key,value in [('input_sha256','0'*64),('resource','different')]:
            raw,p=fixture();p[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):builder.rebuild(raw,p)
        for key,value in [('source_sha256','0'*64),('id','unknown')]:
            raw,p=fixture();p['entries'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):builder.rebuild(raw,p)
        raw,p=fixture();p['entries']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):builder.rebuild(raw,p)

    def test_physical_line_controls_and_lone_surrogates_are_rejected(self):
        for value in ['A\n','A\r','A\0','\ud800']:
            raw,p=fixture(replacement=value,preserve=False)
            with self.subTest(value=repr(value)),self.assertRaises(ValueError):builder.rebuild(raw,p)

    def test_prefix_coverage_audits_full_retained_value_and_reports_verified_scope(self):
        raw,old,fonts=coverage_fixture(source='XA{0}\\n');row=extract_entries(parse(raw),'synthetic')[0]
        p=dict(schema_version=1,source_mode='sha256-utf8-prefix',resource='synthetic',input_sha256=builder.sha256(raw),
               entries=[dict(id=row['id'],source_sha256=builder.sha256(row['source'].encode()),source_prefix_codepoints=1,replacement='A',preserve_utf16_units=True)])
        r=coverage.audit(raw,p,fonts);self.assertTrue(r['all_supplied_fonts_cover_literals']);self.assertEqual(r['literal_codepoints'],[65])
        self.assertEqual(r['entries'][0]['edit_scope']['source_selector']['key'],'Text');self.assertTrue(r['inverse_rebuild_byte_identical'])
        self.assertFalse(r['font_runtime_selection_verified']);self.assertNotIn('XA{0}',json.dumps(r))
        raw2,_,fonts2=coverage_fixture(source='XB{0}\\n');p['input_sha256']=builder.sha256(raw2)
        p['entries'][0]['source_sha256']=builder.sha256('XB{0}\\n'.encode())
        r=coverage.audit(raw2,p,fonts2);self.assertFalse(r['all_supplied_fonts_cover_literals']);self.assertIn(66,r['literal_codepoints'])

    def test_literal_inverse_restores_original_complete_container(self):
        raw,p=fixture();resolved=builder.resolve_changes(raw,p);out=builder.rebuild(raw,p)
        reverse=dict(schema_version=1,input_sha256=builder.sha256(out),resource='synthetic',
                     entries=[dict(id=e['id'],source=e['translation'],translation=e['source']) for e in resolved['entries']])
        self.assertEqual(builder.rebuild(out,reverse),raw)

    def cli(self,root):
        raw,p=fixture();src=root/'source';plan=root/'plan.json';out=root/'out';src.write_bytes(raw);plan.write_bytes(json.dumps(p).encode())
        return [str(src),str(plan),'--output',str(out)],raw,p

    def test_cli_ambiguous_or_nonfinite_json_fails_without_output(self):
        for suffix in [b',"schema_version":1}',b',"value":NaN}']:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);args,_,_=self.cli(root);p=root/'plan.json';p.write_bytes(p.read_bytes()[:-1]+suffix)
                self.assertEqual(builder.main(args),2);self.assertFalse((root/'out').exists())

    def test_cli_mutation_before_publication_leaves_no_output(self):
        for field in ['source','plan.json']:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);args,_,_=self.cli(root);real=builder.rebuild
                def altered(*a,**kw):
                    result=real(*a,**kw);(root/field).write_bytes(b'changed synthetic input');return result
                with patch.object(builder,'rebuild',side_effect=altered):self.assertEqual(builder.main(args),2)
                self.assertFalse((root/'out').exists())

    def test_cli_mutation_after_publication_removes_only_own_unchanged_output(self):
        for field in ['source','plan.json']:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);args,_,_=self.cli(root);read=Path.read_bytes;trigger=[]
                def altered(path):
                    value=read(path)
                    if path==root/'out' and not trigger:trigger.append(True);(root/field).write_bytes(b'changed synthetic input')
                    return value
                with patch.object(Path,'read_bytes',altered):self.assertEqual(builder.main(args),2)
                self.assertFalse((root/'out').exists());self.assertEqual((root/field).read_bytes(),b'changed synthetic input')

    def test_cli_reopening_detects_corruption_without_deleting_external_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,_,_=self.cli(root);read=Path.read_bytes;hit=[]
            def altered(path):
                if path==root/'out' and not hit:hit.append(True);path.write_bytes(b'external changed output')
                return read(path)
            with patch.object(Path,'read_bytes',altered):self.assertEqual(builder.main(args),2)
            self.assertEqual((root/'out').read_bytes(),b'external changed output')

    def test_cli_old_formats_keep_stdout_contract_and_all_inputs_immutable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,raw,p=self.cli(root);before=(root/'plan.json').read_bytes();stream=io.StringIO()
            with contextlib.redirect_stdout(stream):self.assertEqual(builder.main(args),0)
            r=json.loads(stream.getvalue());self.assertEqual(set(r),{'input_sha256','output_sha256','input_size','output_size','reextract_equal','deployed'})
            self.assertEqual((root/'source').read_bytes(),raw);self.assertEqual((root/'plan.json').read_bytes(),before)
            self.assertEqual(builder.main(args),2)
            target=builder.resolve_changes(raw,p)['entries'][0]['translation']
            literal=dict(schema_version=1,input_sha256=builder.sha256(raw),resource='synthetic',entries=[dict(id=p['entries'][0]['id'],source='XYZ tail {0}\\n',translation=target)])
            full=copy.deepcopy(literal);full['source_mode']='sha256-utf8';full['entries'][0]['source_sha256']=builder.sha256(full['entries'][0].pop('source').encode())
            self.assertEqual(builder.rebuild(raw,literal),builder.rebuild(raw,full));self.assertEqual(builder.rebuild(raw,p),builder.rebuild(raw,full))

    def test_current_candidate_plans_bind_login_scope_and_only_planned_probe_glyphs(self):
        root=Path(__file__).resolve().parents[1];old=json.loads((root/'locales/zh-Hans/text-probe.json').read_bytes())
        for disc in [1,2]:
            plan=json.loads((root/f'locales/zh-Hans/candidate-disc{disc}.json').read_bytes());p,_,raw=read_locked_json(root,plan['text_plan']);entry=p['entries'][0]
            self.assertEqual(p['source_mode'],'sha256-utf8-prefix');self.assertEqual(entry['selector']['section'],'GameStart')
            self.assertEqual(entry['selector']['key'],'LogIn_NewGame');self.assertEqual(entry['selector']['occurrence'],1)
            self.assertNotEqual(entry['id'],old['entries'][0]['id']);self.assertEqual(entry['source_prefix_codepoints'],3)
            self.assertTrue(entry['preserve_utf16_units']);self.assertNotIn('source',entry);self.assertNotIn('translation',entry)
            glyphs=json.loads((root/'locales/zh-Hans/font-supplement.json').read_bytes())
            self.assertEqual({ord(c) for c in entry['replacement'] if ord(c)>127},{ord(g['character']) for g in glyphs['glyphs']})
            self.assertNotIn(b'\r',raw);self.assertEqual(plan['expected_text_sha256'],'349968ee05e4199e7aa7c557fe6cab86720f9e872813d6885ae2d98d928f05f7')

    def test_prefix_plan_integrates_with_candidate_builder_and_independent_verifier(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);helper=candidate_fixtures.CandidateAssemblyTests();game,fonts,plan=helper.fixture(root)
            text_path=root/'text-plan.json';old=json.loads(text_path.read_bytes());e=old['entries'][0]
            p=dict(old,source_mode='sha256-utf8-prefix',entries=[dict(id=e['id'],source_sha256=e['source_sha256'],source_prefix_codepoints=7,replacement='A文',preserve_utf16_units=False)])
            plan['text_plan']=candidate_fixtures.write_json(text_path,p);report=helper.build(root,game,fonts,plan)
            self.assertTrue(report['text_inverse_byte_identical']);self.assertFalse(report['deployment_performed'])
            r=independent.verify(plan,root/'assembled',root,stored_decoder,builder.sha256((root/'assembled/manifest.json').read_bytes()))
            self.assertEqual(r['verified_resources'],5);self.assertTrue(r['reports_match_independent_replay']);self.assertFalse(r['game_rendering_verified'])

    def test_coverage_cli_rejects_duplicate_json_and_preserves_font_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw,p,fonts=coverage_fixture();src=root/'text';src.write_bytes(raw);plan=root/'plan.json';plan.write_bytes((json.dumps(p)[:-1]+',"schema_version":1}').encode());font=root/'font';font.write_bytes(fonts[0]['data'])
            args=[str(src),str(plan),'--font-package','one',str(font),fonts[0]['sha256'],'Assets.General','--output',str(root/'report.json')]
            self.assertEqual(coverage.main(args),2);self.assertFalse((root/'report.json').exists());self.assertEqual(src.read_bytes(),raw);self.assertEqual(font.read_bytes(),fonts[0]['data'])


if __name__=='__main__':unittest.main()
