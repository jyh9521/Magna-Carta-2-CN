"""Pure merge/TOC and independently decoded pixel fixtures; no game assets."""
import unittest
from tools.compose_locale_resources import merge_resources,pixel_proof,prepare
from tools.update_resource_sizes import update_sizes_reversible
from tools.subtitle_text import digest
from tools.build_font_supplement import context
from tools.ue3_fonts import parse_font_payload
from tools import supplement_font as s
from test_literal_control_retention import setup
from test_supplement_font import package_fixture,plan,stored_decoder
from test_blank_advance import blank,build as build_blank


def inputs():
    raw,p,ledger,_=setup();font={'Fonts/f.xxx':b'newfont'};subs={'Movies/d1.txt':b'new subtitles'}
    toc=(f'4 1 2 ../Fonts/f.xxx 0\r\n1 3 4 ../Movies/d1.txt 0\r\n{len(raw)} 5 6 ../synthetic 0\r\n'
         '0 0 99 ../Game/TOC.txt 0\r\n').encode()
    originals={'Fonts/f.xxx':b'font','Movies/d1.txt':b'x','synthetic':raw,'Game/TOC.txt':toc}
    return originals,font,subs,p,ledger,dict(path='Game/TOC.txt',sha256=digest(toc))


def font_context(raw):
    ctx=context(raw,stored_decoder);e=ctx['tables']['exports'][0]
    f=parse_font_payload(ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']],ctx['tables']['names'])
    return ctx,f


class ResourceCompositionTests(unittest.TestCase):
    def test_invalid_offline_plan_flags_rejected_before_io(self):
        for field,value in [('schema_version',True),('kind','install'),('disc',True),('game_rendering_verified',True)]:
            p=dict(schema_version=1,kind='offline-disc-locale-composition',disc=1,game_rendering_verified=False)
            p[field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'offline disc composition'):prepare(p,'.')

    def test_combines_all_size_changes_once_and_retains_unknown_controls(self):
        args=inputs();current,r,toc,changes=merge_resources(*args)
        self.assertEqual(set(current),set(args[0]));self.assertEqual(len(changes),3)
        self.assertTrue(toc['inverse_byte_identical'])
        self.assertEqual(r['retained_literal_codepoints'],[9]);self.assertFalse(r['font_coverage_verified'])
        self.assertIn(b'0 0 99 ../Game/TOC.txt 0\r\n',current['Game/TOC.txt'])

    def test_partial_toc_cannot_overwrite_combined_table(self):
        o,f,sub,p,l,toc=inputs();sub['Game/TOC.txt']=b'partial TOC'
        with self.assertRaisesRegex(ValueError,'roles overlap'):merge_resources(o,f,sub,p,l,toc)

    def test_overlapping_component_resources_rejected(self):
        o,f,sub,p,l,toc=inputs();sub['Fonts/f.xxx']=b'overlap'
        with self.assertRaisesRegex(ValueError,'roles overlap'):merge_resources(o,f,sub,p,l,toc)

    def test_other_disc_originals_are_not_silently_copied(self):
        o,f,sub,p,l,toc=inputs();o['Movies/d2.txt']=b'foreign'
        with self.assertRaisesRegex(ValueError,'this disc'):merge_resources(o,f,sub,p,l,toc)

    def test_source_identity_and_retention_evidence_required(self):
        o,f,sub,p,l,toc=inputs()
        with self.assertRaisesRegex(ValueError,'retention evidence'):merge_resources(o,f,sub,p,None,toc)
        o['synthetic']+=b'junk'
        with self.assertRaises(ValueError):merge_resources(o,f,sub,p,l,toc)

    def test_wrong_original_toc_and_stale_plan_rejected(self):
        o,f,sub,p,l,toc=inputs();toc['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'TOC SHA256'):merge_resources(o,f,sub,p,l,toc)
        o,f,sub,p,l,toc=inputs();p['entries'][0]['translation']='stale\t'
        with self.assertRaises(ValueError):merge_resources(o,f,sub,p,l,toc)

    def test_reversible_toc_noop_still_checks_hash_and_ascii(self):
        raw=b'0 0 99 ../Game/TOC.txt 0\r\n';out,r=update_sizes_reversible(raw,digest(raw),[])
        self.assertEqual(out,raw);self.assertTrue(r['inverse_byte_identical'])
        with self.assertRaises(ValueError):update_sizes_reversible(raw,'0'*64,[])
        with self.assertRaises(ValueError):update_sizes_reversible(raw,digest(raw),None)
        with self.assertRaises(ValueError):update_sizes_reversible(b'\xff',digest(b'\xff'),[])

    def test_pixel_proof_reads_real_decoded_ink(self):
        p=plan();p['metric_height']=23;raw=package_fixture()
        out,_=s.supplement_package(raw,digest(raw),'General',p,{0x4e2d:bytes([255])*24*23+bytes(24)},stored_decoder)
        ctx,f=font_context(out);proof=pixel_proof(ctx,f,{0x4e2d},stored_decoder)
        self.assertEqual(proof['ink_glyphs'],1)

    def test_zero_ink_visible_glyph_is_rejected_independently(self):
        p=plan();p['metric_height']=23;raw=package_fixture()
        out,_=s.supplement_package(raw,digest(raw),'General',p,{0x4e2d:bytes(576)},stored_decoder)
        ctx,f=font_context(out)
        with self.assertRaisesRegex(ValueError,'no ink'):pixel_proof(ctx,f,{0x4e2d},stored_decoder)

    def test_blank_layout_requires_exact_zero_and_supported_separator(self):
        raw,_=build_blank(blank());ctx,f=font_context(raw)
        self.assertEqual(pixel_proof(ctx,f,{12288},stored_decoder)['blank_layout_codepoints'],[12288])
        f['remap'][-1]['codepoint']=0x2028
        with self.assertRaisesRegex(ValueError,'layout literal'):pixel_proof(ctx,f,{0x2028},stored_decoder)

    def test_visible_pixels_cannot_masquerade_as_blank_space(self):
        p=plan();p['metric_height']=23;raw=package_fixture()
        out,_=s.supplement_package(raw,digest(raw),'General',p,{0x4e2d:bytes([255])*24*23+bytes(24)},stored_decoder)
        ctx,f=font_context(out);f['remap'][-1]['codepoint']=12288
        with self.assertRaisesRegex(ValueError,'visible layout literal'):pixel_proof(ctx,f,{12288},stored_decoder)

    def test_bad_pixel_rectangle_rejected(self):
        raw,_=build_blank(blank());ctx,f=font_context(raw);f['characters'][-1]['StartU']=99999
        with self.assertRaisesRegex(ValueError,'outside atlas'):pixel_proof(ctx,f,{12288},stored_decoder)

class TextureCompositionChainTests(unittest.TestCase):
 def test_font_then_texture_exact_chain(self):
  args=inputs();before=dict(args[0]);out,*_=merge_resources(*args,texture_updates={'Fonts/f.xxx':dict(base_sha256=digest(b'newfont'),data=b'font plus title')});self.assertEqual(out['Fonts/f.xxx'],b'font plus title');self.assertEqual(args[0],before)
 def test_original_font_is_not_accepted_as_overlay_base(self):
  with self.assertRaisesRegex(ValueError,'base chain'):merge_resources(*inputs(),texture_updates={'Fonts/f.xxx':dict(base_sha256=digest(b'font'),data=b'title')})
 def test_new_texture_resource_and_unified_toc(self):
  o,f,s,p,l,t=inputs();o['Title.xxx']=b'old';o[t['path']]+=b'3 7 8 ../Title.xxx 0\r\n';t['sha256']=digest(o[t['path']]);out,*_=merge_resources(o,f,s,p,l,t,{'Title.xxx':dict(base_sha256=digest(b'old'),data=b'new title')});self.assertEqual(out['Title.xxx'],b'new title');self.assertIn(b'9 7 8 ../Title.xxx',out[t['path']])
 def test_texture_role_conflicts_remain_rejected(self):
  args=inputs()
  for path in ['Movies/d1.txt','synthetic','Game/TOC.txt','fonts/f.xxx']:
   with self.subTest(path=path),self.assertRaises(ValueError):merge_resources(*args,texture_updates={path:dict(base_sha256=digest(b'x'),data=b'x')})
