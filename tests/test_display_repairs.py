import copy,json,unittest
from pathlib import Path
from tools.validate_catalog import token_errors
from tools import supplement_font as s
from tools.subtitle_text import parse,rebuild,digest
from tools.font_ink import ink_records
from tools.build_font_supplement import context
from tools.ue3_fonts import parse_font_payload
from test_supplement_font import plan,package_fixture,stored_decoder,NAMES,font_payload

class DisplayRepairTests(unittest.TestCase):
    def test_public_batch_reflows_dialogue_and_pins_all_subtitle_sources(self):
        root=Path(__file__).resolve().parents[1]
        load=lambda p:json.loads((root/p).read_bytes())
        p=load('locales/zh-Hans/display-fix.json');review=load('locales/zh-Hans/display-fix.review.json')
        kinds={e['id']:e['text_kind'] for e in review['entries']}
        self.assertEqual(len(p['entries']),262)
        self.assertEqual(sum(kinds[e['id']]=='dialogue' for e in p['entries']),66)
        for e in p['entries']:
            if kinds[e['id']]=='dialogue':
                self.assertNotIn('\\n',e['translation'])
                self.assertFalse(any(c.isspace() for c in e['translation']))
                if 'line_break_policy' in e:self.assertEqual(e['line_break_policy']['target_count'],0)
        route=load('locales/zh-Hans/display-fonts/route.json')
        self.assertTrue(route['verify_glyph_ink'])
        self.assertEqual(len(route['additional_text_plans']),4)
        self.assertEqual(sum(len(load(r['path'])['entries']) for r in route['additional_text_plans']),49)
        for ref in [route['text_plan'],*route['font_plans'],*route['additional_text_plans']]:
            self.assertEqual(digest((root/ref['path']).read_bytes()),ref['sha256'])
        for ref in route['font_plans']:
            f=load(ref['path']);self.assertEqual(digest((root/f['supplement']['path']).read_bytes()),f['supplement']['sha256'])
            gp=load(f['supplement']['path'])
            self.assertTrue(all(1<=g['metric_width']<=g['width'] for g in gp['glyphs']))
    def test_break_reflow_is_opt_in_count_locked_and_other_tokens_stay_protected(self):
        src='a\\n{0}<b>z</b>'
        self.assertTrue(token_errors(src,'a{0}<b>z</b>'))
        self.assertFalse(token_errors(src,'a{0}<b>z</b>',dict(source_count=1,target_count=0)))
        self.assertTrue(token_errors(src,'a<b>z</b>',dict(source_count=1,target_count=0)))
        self.assertTrue(token_errors(src,'a{0}<b>z</b>',dict(source_count=2,target_count=0)))

    def test_subtitle_preserves_bom_timing_class_clear_and_markup(self):
        raw=('1\r\n<SYNC Start=10><P Class=KRCC>a<br>b<SYNC Start=20><P Class=KRCC>&nbsp;').encode('utf-16-le')
        raw=b'\xff\xfe'+raw
        p=dict(schema_version=1,kind='timed-subtitle-text',input_sha256=digest(raw),entries=[dict(start=10,end=20,source_sha256=digest(b'a<br>b'),translation='甲<br>乙')])
        out=rebuild(raw,p);self.assertTrue(out.startswith(b'\xff\xfe'))
        self.assertEqual(parse(out)[1][0][4],'甲<br>乙')
        for key,value in [('source_sha256','0'*64),('start',11),('end',21),('translation','甲乙'),('translation','甲\n乙')]:
            bad=copy.deepcopy(p);bad['entries'][0][key]=value
            with self.assertRaises(ValueError):rebuild(raw,bad)

    def test_blank_mapping_is_not_ink_and_visible_mapping_cannot_be_replaced(self):
        raw=package_fixture();ctx=context(raw,stored_decoder);e=ctx['tables']['exports'][0]
        f=parse_font_payload(ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']],ctx['tables']['names'])
        records=ink_records(ctx,f,[65],stored_decoder)
        self.assertEqual(records[0]['status'],'ink')
        p=plan();p['glyphs'][0]['character']='A';p['replace_blank_codepoints']=[65]
        with self.assertRaisesRegex(ValueError,'transparent'):
            s.supplement_package(raw,digest(raw),'General',p,{65:bytes([255])*576},stored_decoder,True)

    def test_redirect_preserves_old_glyphs_and_does_not_duplicate_remap_key(self):
        a=dict(codepoint=65,StartU=8,StartV=8,USize=8,VSize=24,TextureIndex=0)
        out=s.append_font_payload(font_payload(),NAMES,[a],replace_blank_codepoints=[65])
        f=parse_font_payload(out,NAMES)
        self.assertEqual(len(f['characters']),2)
        self.assertEqual([(r['codepoint'],r['glyph_index']) for r in f['remap']],[(65,1)])

    def test_transparent_glyph_repair_has_real_pixels_after_remap_redirect(self):
        raw=package_fixture();ctx=context(raw,stored_decoder);e=ctx['tables']['exports'][1]
        texture=s.parse_atlas_payload(raw[e['serial_offset']:e['serial_offset']+e['serial_size']],NAMES,e['serial_offset'])
        b=texture['mips'][0]['bulk'];start=e['serial_offset']+b['payload_offset']
        raw=bytearray(raw);raw[start:start+b['size_on_disk']]=bytes(b['size_on_disk']);raw=bytes(raw)
        ctx=context(raw,stored_decoder);fexp=ctx['tables']['exports'][0]
        font=parse_font_payload(raw[fexp['serial_offset']:fexp['serial_offset']+fexp['serial_size']],NAMES)
        self.assertEqual(ink_records(ctx,font,[65],stored_decoder)[0]['status'],'transparent')
        p=plan();p['glyphs'][0]['character']='A';p['replace_blank_codepoints']=[65]
        out,report=s.supplement_package(raw,digest(raw),'General',p,{65:bytes([255])*576},stored_decoder,True)
        ctx=context(out,stored_decoder);fexp=ctx['tables']['exports'][0]
        font=parse_font_payload(ctx['logical'][fexp['serial_offset']:fexp['serial_offset']+fexp['serial_size']],NAMES)
        self.assertEqual(ink_records(ctx,font,[65],stored_decoder)[0]['status'],'ink')
        self.assertTrue(report['original_glyphs_and_unselected_remap_preserved'])
        self.assertFalse(report['original_glyphs_and_remap_preserved'])

    def test_reflow_audit_reverses_break_policy_not_just_visible_text(self):
        from test_text_font_coverage import fixture
        from tools.audit_text_font_coverage import audit
        raw,p,fonts=fixture('A{0}')
        p['entries'][0]['line_break_policy']=dict(source_count=1,target_count=0)
        r=audit(raw,p,fonts)
        self.assertTrue(r['inverse_rebuild_byte_identical'])
        self.assertTrue(r['non_layout_protected_tokens_preserved'])
        self.assertFalse(r['protected_token_sequences_preserved'])

if __name__=='__main__':unittest.main()
