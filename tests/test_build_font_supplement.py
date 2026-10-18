"""Synthetic multi-alias font bundles; no native DLL/font/game dependency."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_font_binding_audit import alias_package
from test_supplement_font import stored_decoder
from tools import build_font_supplement as bundle
from tools.font_binding_audit import fingerprint
from tools.lzx_stored import wrap_ue3_chunk
from tools.supplement_font import supplement_package
from tools.ue3_ui_styles import StyleGraph


def compressed_alias():
    raw = alias_package(1); header = struct.unpack_from('>I',raw,8)[0]
    first, second = wrap_ue3_chunk(raw[101:header]), wrap_ue3_chunk(raw[header:])
    prefix = bytearray(raw[:101]); struct.pack_into('>II',prefix,93,4,2)
    table = struct.pack('>IIII',101,header-101,133,len(first))
    table += struct.pack('>IIII',header,len(raw)-header,133+len(first),len(second))
    return bytes(prefix)+table+first+second+b'SYNTHETIC-TAIL'


class SupplementBundleTests(unittest.TestCase):
    def fixture(self, root):
        game = root/'original'; game.mkdir(); (game/'Game').mkdir()
        sources, lines = [], []
        raws = [alias_package(), compressed_alias(), alias_package(2,compressed_atlas=True)]
        for label,raw in zip(('one','two','three'),raws):
            path='Game/'+label+'.xxx'; (game/path).write_bytes(raw)
            sources.append(dict(label=label,path=path,sha256=bundle.digest(raw),font_object='Assets.General'))
            lines.append(f'{len(raw)} 0 1 ..\\Game\\{label}.xxx 0\r\n')
        toc=''.join(lines).encode();(game/'Xbox360TOC.txt').write_bytes(toc)
        glyph_plan=dict(schema_version=1,in_game_verified=False,font_size=22,
            glyphs=[dict(character=chr(0x6587),texture_index=0,x=32,y=32,width=24,height=24)])
        glyph_bytes=json.dumps(glyph_plan).encode();(root/'glyphs.json').write_bytes(glyph_bytes)
        font=root/'font.bin';font.write_bytes(b'self-authored font input; mocked raster only')
        alphas={0x6587:bytes([255])*576}
        before=fingerprint(StyleGraph(dict(one=bundle.context(raws[0],stored_decoder))),('one',1),stored_decoder)
        candidate,_=supplement_package(raws[0],bundle.digest(raws[0]),'Assets.General',glyph_plan,alphas,stored_decoder)
        after=fingerprint(StyleGraph(dict(one=bundle.context(candidate,stored_decoder))),('one',1),stored_decoder)
        plan=dict(schema_version=1,game_rendering_verified=False,required_source_count=3,
            canonical_font_path='assets.general',expected_namespace_guid='a'*32,
            expected_semantic_sha256=before['semantic_sha256'],expected_supplement_semantic_sha256=after['semantic_sha256'],
            font_source_sha256=bundle.digest(font.read_bytes()),supplement=dict(path='glyphs.json',sha256=bundle.digest(glyph_bytes)),
            sources=sources,toc=dict(path='Xbox360TOC.txt',sha256=bundle.digest(toc)))
        return game,font,plan,alphas

    def run_build(self,root,game,font,plan,alphas,out=None):
        with patch.object(bundle,'rasterize_plan',return_value=(alphas,[dict(bbox=(0,0,24,24))])):
            return bundle.build(plan,game,root,font,out or root/'output',stored_decoder)

    def test_three_aliases_mixed_compression_restore_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root)
            report=self.run_build(root,game,font,plan,alphas)
            self.assertFalse(report['deployment_performed']);self.assertFalse(report['text_resources_changed'])
            self.assertTrue(report['toc_inverse_byte_identical']);self.assertEqual(len(report['toc_changes']),3)
            self.assertEqual(report['added_codepoints'],[0x6587])
            self.assertEqual(len({v['semantic_after'] for v in report['sources']}),1)
            self.assertEqual(report,json.loads((root/'output/manifest.json').read_text()))
            for source,row in zip(plan['sources'],report['sources']):
                files=row['files'];original=(game/source['path']).read_bytes()
                self.assertEqual(Path(files['control']['path']).read_bytes(),original)
                self.assertEqual(Path(files['restored']['path']).read_bytes(),original)
                self.assertEqual(bundle.digest(original),source['sha256'])
                self.assertNotEqual(files['candidate']['sha256'],source['sha256'])
            self.assertEqual((root/'output/rollback-check/Xbox360TOC.txt').read_bytes(),(game/'Xbox360TOC.txt').read_bytes())

    def test_version_identity_semantics_and_font_hash_fail_before_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root)
            for field in ('expected_semantic_sha256','expected_supplement_semantic_sha256','expected_namespace_guid','font_source_sha256','canonical_font_path','package'):
                p=copy.deepcopy(plan)
                if field=='package':p['sources'][2]['sha256']='0'*64
                elif field=='canonical_font_path':p[field]='other.general'
                else:p[field]='b'*32 if field=='expected_namespace_guid' else '0'*64
                output=root/field
                with self.subTest(field=field),self.assertRaises(ValueError):self.run_build(root,game,font,p,alphas,output)
                self.assertFalse(output.exists())

    def test_locale_plan_hash_and_escaping_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root)
            for value in ('../glyphs.json','/glyphs.json','C:/glyphs.json','glyphs.json'):
                p=copy.deepcopy(plan);p['supplement']['path']=value;p['supplement']['sha256']='0'*64
                with self.subTest(value=value),self.assertRaises(ValueError):self.run_build(root,game,font,p,alphas)
                self.assertFalse((root/'output').exists())

    def test_output_existing_or_inside_game_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root)
            for out in (root,game/'new-output'):
                with self.assertRaises(ValueError):self.run_build(root,game,font,plan,alphas,out)
            self.assertFalse((game/'new-output').exists())

    def test_output_readback_failure_leaves_no_completion_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root);read=Path.read_bytes
            target=(root/'output/candidates/one.xxx').resolve()
            hits=[]
            def altered(path):
                result=read(path)
                if path.resolve()==target:
                    hits.append(str(path))
                    return result+b'corrupt'
                return result
            with patch.object(Path,'read_bytes',altered),self.assertRaisesRegex(ValueError,'reopening'):
                self.run_build(root,game,font,plan,alphas)
            self.assertEqual(len(hits),1)
            self.assertFalse((root/'output/manifest.json').exists())

    def test_late_source_change_detected_before_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root)
            def raster(*args):
                (game/'Game/one.xxx').write_bytes(b'changed synthetic fixture')
                return alphas,[]
            with patch.object(bundle,'rasterize_plan',side_effect=raster),self.assertRaisesRegex(ValueError,'input changed'):
                bundle.build(plan,game,root,font,root/'output',stored_decoder)
            self.assertFalse((root/'output').exists())

    def test_restore_copy_requires_both_hashes_and_new_destination(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/'candidate';b=root/'backup';a.write_bytes(b'changed');b.write_bytes(b'original')
            for ah,bh in [('0'*64,bundle.digest(b.read_bytes())),(bundle.digest(a.read_bytes()),'0'*64)]:
                with self.assertRaisesRegex(ValueError,'input hash'):
                    bundle.restore_copy(a,b,root/'out',ah,bh)
                self.assertFalse((root/'out').exists())
            with self.assertRaisesRegex(ValueError,'must be new'):
                bundle.restore_copy(a,b,a,bundle.digest(a.read_bytes()),bundle.digest(b.read_bytes()))

    def test_plan_guards_include_bool_version_and_wrong_types(self):
        with tempfile.TemporaryDirectory() as d:
            _,_,plan,_=self.fixture(Path(d))
            cases=[]
            for field,value in [('schema_version',True),('supplement',[]),('expected_namespace_guid',3),
                                ('font_source_sha256',None),('expected_supplement_semantic_sha256',plan['expected_semantic_sha256'])]:
                p=copy.deepcopy(plan);p[field]=value;cases.append(p)
            p=copy.deepcopy(plan);p['sources'][0]['label']=1;cases.append(p)
            p=copy.deepcopy(plan);p['sources'][0]['label']='CON';cases.append(p)
            for p in cases:
                with self.subTest(p=p),self.assertRaises(ValueError):bundle.validate_plan(p)

    def test_locked_disc_plans_share_font_inputs_and_distinct_tocs(self):
        root=Path(__file__).resolve().parents[1]/'locales/zh-Hans'
        plans=[json.loads((root/f'font-build-disc{i}.json').read_text()) for i in (1,2)]
        for p in plans:bundle.validate_plan(p)
        for field in ('sources','supplement','font_source_sha256','expected_supplement_semantic_sha256'):
            self.assertEqual(plans[0][field],plans[1][field])
        self.assertNotEqual(plans[0]['toc']['sha256'],plans[1]['toc']['sha256'])

    def test_cli_fixture_build_without_external_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game,font,plan,alphas=self.fixture(root);p=root/'build-plan.json';p.write_text(json.dumps(plan))
            args=['--plan',str(p),'--game-root',str(game),'--project-root',str(root),'--font-file',str(font),
                  '--output-dir',str(root/'output'),'--lzx-library','mock.dll']
            with patch.object(bundle,'LzxDecoder',return_value=stored_decoder),patch.object(bundle,'rasterize_plan',return_value=(alphas,[])):
                self.assertEqual(bundle.main(args),0)
                self.assertEqual(bundle.main(args),2)


if __name__ == '__main__':unittest.main()
