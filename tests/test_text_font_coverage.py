"""Self-authored Coalesced/Font coverage fixtures; never execute game code."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_build_font_supplement import compressed_alias
from test_font_binding_audit import alias_package
from test_supplement_font import stored_decoder
from tools import audit_text_font_coverage as coverage
from tools import build_coalesced
from tools.build_coalesced import rebuild
from tools.coalesced import EmbeddedFile, SerializedString, serialize, parse, extract_entries


def fixture(translation='A{0}\\n', source='source {0}\\n'):
    raw=serialize([EmbeddedFile(SerializedString('fixture.int','ascii',0),
                  SerializedString('[Test]\r\nText='+source+'\r\nOther=keep\n','utf-16-le',0))])
    row=extract_entries(parse(raw),'synthetic')[0]
    plan=dict(schema_version=1,input_sha256=coverage.digest(raw),resource='synthetic',
              entries=[dict(id=row['id'],source=row['source'],translation=translation)])
    font=alias_package()
    fonts=[dict(label='one',data=font,sha256=coverage.digest(font),font_object='Assets.General')]
    return raw,plan,fonts


class TextFontCoverageTests(unittest.TestCase):
    def test_literal_tokens_and_source_identity_without_dumping_text(self):
        raw,plan,fonts=fixture()
        report=coverage.audit(raw,plan,fonts)
        self.assertTrue(report['all_supplied_fonts_cover_literals'])
        self.assertTrue(report['source_identity_and_reextraction_verified'])
        self.assertTrue(report['inverse_rebuild_byte_identical'])
        self.assertEqual(report['literal_codepoints'],[65])
        self.assertEqual(report['entries'][0]['protected_token_count'],2)
        self.assertNotIn('source {0}',json.dumps(report))
        self.assertFalse(report['game_rendering_verified'])
        self.assertFalse(report['dynamic_expansion_coverage_verified'])
        self.assertFalse(report['atlas_bounds_verified'])

    def test_all_fonts_are_required_no_winner_or_missing_font_skip(self):
        raw,plan,fonts=fixture('B{0}\\n')
        raw2=compressed_alias();fonts.append(dict(label='two',data=raw2,sha256=coverage.digest(raw2),font_object='Assets.General'))
        report=coverage.audit(raw,plan,fonts,stored_decoder)
        self.assertFalse(report['all_supplied_fonts_cover_literals'])
        self.assertEqual(len(report['fonts']),2)
        for f in report['fonts']:
            self.assertEqual(f['failures'],[dict(codepoint=66,status='missing-remap')])
            self.assertEqual(f['entries'][0]['failed_codepoints'],[66])

    def test_compressed_and_uncompressed_alias_coverage_agrees(self):
        raw,plan,fonts=fixture(chr(0x4e2d)+'{0}\\n')
        data=compressed_alias();fonts.append(dict(label='two',data=data,sha256=coverage.digest(data),font_object='Assets.General'))
        report=coverage.audit(raw,plan,fonts,stored_decoder)
        self.assertTrue(report['all_supplied_fonts_cover_literals'])
        self.assertEqual(report['fonts'][0]['codepoints'],report['fonts'][1]['codepoints'])
        with self.assertRaises(ValueError):coverage.audit(raw,plan,fonts)

    def test_source_id_hash_and_tokens_are_guarded(self):
        raw,plan,fonts=fixture()
        cases=[]
        for key,value in [('input_sha256','0'*64),('schema_version',True),('resource','other')]:
            p=copy.deepcopy(plan);p[key]=value;cases.append(p)
        for key,value in [('id','unknown'),('source','wrong'),('translation','A\\n{0}')]:
            p=copy.deepcopy(plan);p['entries'][0][key]=value;cases.append(p)
        for p in cases:
            with self.subTest(p=p),self.assertRaises(ValueError):coverage.audit(raw,p,fonts)

    def test_malformed_coalesced_envelope_is_a_value_error(self):
        raw,_,_=fixture()
        for plan in ([],None,True,dict(schema_version=True),dict(schema_version=1.0)):
            with self.subTest(plan=plan),self.assertRaisesRegex(ValueError,'schema'):rebuild(raw,plan)

    def test_full_inverse_text_equality_is_required(self):
        raw,plan,fonts=fixture();rebuilt=rebuild(raw,plan)
        with patch.object(coverage,'rebuild',side_effect=[rebuilt,b'not original']),self.assertRaisesRegex(ValueError,'inverse'):
            coverage.audit(raw,plan,fonts)

    def test_source_hash_plan_rebuild_and_coverage_match_literal_plan(self):
        raw,plan,fonts=fixture();hashed=copy.deepcopy(plan);hashed['source_mode']='sha256-utf8'
        for e in hashed['entries']:e['source_sha256']=coverage.digest(e.pop('source').encode('utf-8'))
        original=copy.deepcopy(hashed)
        self.assertEqual(rebuild(raw,hashed),rebuild(raw,plan))
        report=coverage.audit(raw,hashed,fonts)
        self.assertTrue(report['all_supplied_fonts_cover_literals'])
        self.assertEqual(report['source_verification_mode'],'sha256-utf8')
        self.assertEqual(hashed,original)

    def test_source_hash_plan_never_falls_back_on_unknown_mode_or_source(self):
        raw,plan,_=fixture();plan['source_mode']='sha256-utf8'
        e=plan['entries'][0];e['source_sha256']=coverage.digest(e.pop('source').encode('utf8'))
        bad=[]
        for mode in ('unknown',True,1):p=copy.deepcopy(plan);p['source_mode']=mode;bad.append(p)
        for key,value in [('source_sha256','0'*64),('source_sha256',None),('id','unknown'),('source','ambiguous')]:
            p=copy.deepcopy(plan);p['entries'][0][key]=value;bad.append(p)
        p=copy.deepcopy(plan);p['entries']*=2;bad.append(p)
        for p in bad:
            with self.subTest(p=p),self.assertRaises(ValueError):rebuild(raw,p)

    def test_font_hash_object_class_and_duplicate_label_guards(self):
        raw,plan,fonts=fixture()
        for key,value in [('sha256','0'*64),('font_object','missing'),('font_object','Assets.General.Atlas'),('label','../bad')]:
            f=copy.deepcopy(fonts);f[0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):coverage.audit(raw,plan,f)
        with self.assertRaises(ValueError):coverage.audit(raw,plan,fonts+[dict(fonts[0],label='ONE')])
        with self.assertRaises(ValueError):coverage.audit(raw,plan,[])

    def test_local_font_class_coverage_matches_imported_font(self):
        raw,plan,fonts=fixture();source=fonts[0]
        logical,tables=coverage._tables(source['data'],source['sha256'],None)
        tables['exports'].append(dict(path='Font',class_path='Class'))
        tables['exports'][0].update(class_path='Font',**{'class':len(tables['exports'])})
        expected=coverage.audit(raw,plan,fonts)
        with patch.object(coverage,'_tables',return_value=(logical,tables)):
            self.assertEqual(coverage.audit(raw,plan,fonts),expected)

    def test_local_font_class_must_resolve_to_exact_class_definition(self):
        raw,plan,fonts=fixture();source=fonts[0]
        logical,tables=coverage._tables(source['data'],source['sha256'],None)
        for path,kind,ref in [('Other.Font','Class',4),('Font','Engine.Font',4),('Font','Class',True),
                               ('Font','Class',0),('Font','Class',99),('Font','Class',-2)]:
            t=copy.deepcopy(tables);t['exports'].append(dict(path=path,class_path=kind))
            t['exports'][0].update(class_path='Font',**{'class':ref})
            with self.subTest(path=path,kind=kind,ref=ref),patch.object(coverage,'_tables',return_value=(logical,t)):
                with self.assertRaisesRegex(ValueError,'locally defined Font'):coverage.audit(raw,plan,fonts)

    def test_imported_font_class_identity_is_not_only_a_display_path(self):
        raw,plan,fonts=fixture();source=fonts[0];logical,tables=coverage._tables(source['data'],source['sha256'],None)
        for change in ['path','kind','local-ref']:
            t=copy.deepcopy(tables);e=t['exports'][0]
            if change=='local-ref':e['class']=1
            else:
                imp=t['imports'][-e['class']-1]
                if change=='path':imp['path']='Other.Font'
                else:imp['class_name']['name']='Font'
            with self.subTest(change=change),patch.object(coverage,'_tables',return_value=(logical,t)):
                with self.assertRaisesRegex(ValueError,'imported Engine.Font'):coverage.audit(raw,plan,fonts)

    def test_zero_area_visible_glyph_fails_without_assuming_tofu_identity(self):
        raw,plan,fonts=fixture();data=alias_package(height=0)
        fonts[0].update(data=data,sha256=coverage.digest(data))
        r=coverage.audit(raw,plan,fonts)
        self.assertFalse(r['all_supplied_fonts_cover_literals'])
        self.assertEqual(r['fonts'][0]['failures'][0]['status'],'zero-area-visible-glyph')

    def test_non_remapped_control_non_bmp_and_space_boundaries(self):
        font=dict(is_remapped=True,characters=[dict(USize=0,VSize=0,TextureIndex=0)],
                  remap=[dict(codepoint=32,glyph_index=0)])
        records=coverage.font_coverage(font,[9,32,0x200b,0x10000])
        self.assertEqual([r['status'] for r in records],['control-or-format-literal-unverified','mapped',
                         'control-or-format-literal-unverified','outside-bmp-remap'])
        font['is_remapped']=False
        self.assertEqual(coverage.font_coverage(font,[32])[0]['status'],'non-remapped-font-mode-unverified')

    def test_token_only_or_empty_edit_does_not_claim_literal_coverage(self):
        raw,plan,fonts=fixture('{0}\\n')
        report=coverage.audit(raw,plan,fonts)
        self.assertEqual(report['literal_codepoints'],[])
        self.assertFalse(report['all_supplied_fonts_cover_literals'])
        plan['entries']=[]
        with self.assertRaises(ValueError):coverage.audit(raw,plan,fonts)
        raw,plan,fonts=fixture('',source='source')
        with self.assertRaisesRegex(ValueError,'empty'):coverage.audit(raw,plan,fonts)

    def test_only_known_tokens_are_excluded_not_unrecognized_braces(self):
        self.assertEqual(coverage.literal_codepoints('A{0}\\n^FF<tag>%2$s$n'),[65])
        self.assertIn(ord('{'),coverage.literal_codepoints('A{?}'))

    def cli_fixture(self,root,translation='A{0}\\n'):
        raw,plan,fonts=fixture(translation)
        coalesced=root/'original.int';coalesced.write_bytes(raw)
        changes=root/'changes.json';changes.write_text(json.dumps(plan),encoding='utf8')
        font=root/'font.xxx';font.write_bytes(fonts[0]['data'])
        args=[str(coalesced),str(changes),'--font-package','one',str(font),fonts[0]['sha256'],
              fonts[0]['font_object'],'--output',str(root/'report.json')]
        return args,raw,coalesced

    def test_cli_success_missing_coverage_and_no_overwrite(self):
        for target,code in [('A{0}\\n',0),('B{0}\\n',1)]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);args,raw,original=self.cli_fixture(root,target)
                self.assertEqual(coverage.main(args),code)
                report=json.loads((root/'report.json').read_text(encoding='utf8'))
                self.assertEqual(report['all_supplied_fonts_cover_literals'],code==0)
                self.assertTrue(report['input_hashes_rechecked'])
                self.assertEqual(coverage.main(args),2)
                self.assertEqual(original.read_bytes(),raw)

    def test_cli_source_hash_plan_rebuilds_without_original_text_in_plan(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,raw,_=self.cli_fixture(root);p=root/'changes.json'
            literal=json.loads(p.read_text(encoding='utf8'));hashed=copy.deepcopy(literal)
            hashed['source_mode']='sha256-utf8'
            for e in hashed['entries']:e['source_sha256']=coverage.digest(e.pop('source').encode('utf8'))
            p.write_text(json.dumps(hashed),encoding='utf8')
            self.assertEqual(coverage.main(args),0)
            target=root/'rebuilt.int'
            self.assertEqual(build_coalesced.main([args[0],args[1],'--output',str(target)]),0)
            self.assertEqual(target.read_bytes(),rebuild(raw,literal))

    def test_locked_locale_probe_uses_hash_only_source_and_planned_glyphs(self):
        root=Path(__file__).resolve().parents[1]/'locales/zh-Hans'
        plan=json.loads((root/'text-probe.json').read_text(encoding='utf8'))
        glyphs=json.loads((root/'font-supplement.json').read_text(encoding='utf8'))
        self.assertEqual(plan['source_mode'],'sha256-utf8')
        self.assertEqual(plan['review_status'],'technical-prototype')
        self.assertFalse(plan['game_rendering_verified']);self.assertEqual(len(plan['entries']),1)
        planned={ord(g['character']) for g in glyphs['glyphs']}
        for e in plan['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertEqual({cp for cp in coverage.literal_codepoints(e['translation']) if cp>127},planned)

    def test_cli_report_readback_failure_and_input_alias(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,_,original=self.cli_fixture(root)
            target=(root/'report.json').resolve();read=Path.read_text;hits=[]
            def altered(path,*a,**kw):
                text=read(path,*a,**kw)
                if path.resolve()==target:hits.append(str(path));return '{}'
                return text
            with patch.object(Path,'read_text',altered):self.assertEqual(coverage.main(args),2)
            self.assertEqual(len(hits),1)
            args[-1]=str(original)
            self.assertEqual(coverage.main(args),2)

    def test_cli_input_mutation_before_publication_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,_,original=self.cli_fixture(root);audit=coverage.audit
            def changed(*a,**kw):
                report=audit(*a,**kw);original.write_bytes(b'changed synthetic input');return report
            with patch.object(coverage,'audit',side_effect=changed):self.assertEqual(coverage.main(args),2)
            self.assertFalse((root/'report.json').exists())


if __name__ == '__main__':unittest.main()
