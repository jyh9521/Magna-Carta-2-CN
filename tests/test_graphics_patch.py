"""Synthetic whole-image/section guards and the checked-in offline contract."""
import contextlib
import copy
import io
import itertools
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from tools.inspect_graphics_patch import main,recover_original,summary_line
from tools.runtime_patch import digest,patch_toml


def fixture():
    image=bytearray(128)
    values=[(0x10,'39600002','39600001'),(0x20,'00000001','00000000'),
            (0x30,'00000001','00000000'),(0x40,'419a0008','48000008')]
    for at,old,_ in values:image[at:at+4]=bytes.fromhex(old)
    image=bytes(image)
    p=dict(schema_version=1,kind='ppc-runtime-patch',image_base=0x1000,image_sha256=digest(image),
        title_name='Synthetic Graphics',title_id='12345678',module_hash='0123456789ABCDEF',name='Synthetic set',
        windows=[dict(address=0x1000,size=len(image),sha256=digest(image))],
        writes=[dict(address=0x1000+a,expected=o,replacement=n) for a,o,n in values],
        patch_sections=[dict(name='Interval',is_enabled=False,write_addresses=[0x1010]),
                        dict(name='Tiling',is_enabled=False,write_addresses=[0x1020,0x1030]),
                        dict(name='Post',is_enabled=False,write_addresses=[0x1040])])
    return image,p


class GraphicsPatchTests(unittest.TestCase):
    def test_all_independent_section_combinations_restore_same_original(self):
        original,p=fixture()
        for choices in itertools.product((False,True),repeat=3):
            image=bytearray(original)
            for active,section in zip(choices,p['patch_sections']):
                if active:
                    for w in p['writes']:
                        if w['address'] in section['write_addresses']:
                            a=w['address']-p['image_base'];image[a:a+4]=bytes.fromhex(w['replacement'])
            with self.subTest(choices=choices):self.assertEqual(recover_original(bytes(image),p),original)

    def test_partial_tiling_unknown_words_and_unrelated_tamper_fail(self):
        original,p=fixture()
        for label,at,value in [('partial',0x20,b'\0'*4),('word',0x10,b'1234'),('hash',120,b'1234')]:
            image=bytearray(original);image[at:at+4]=value
            with self.subTest(label=label),self.assertRaises(ValueError):recover_original(bytes(image),p)

    def test_source_hash_context_bounds_and_schema_guards(self):
        original,p=fixture()
        for label in ['hash','window','bounds','schema']:
            q=copy.deepcopy(p)
            if label=='hash':q['image_sha256']='0'*64
            if label=='window':q['windows'][0]['sha256']='0'*64
            if label=='bounds':q['writes'][0]['address']=0
            if label=='schema':q['schema_version']=0
            with self.subTest(label=label),self.assertRaises(ValueError):recover_original(original,q)

    def test_checked_in_candidates_are_separate_disabled_and_explicitly_scoped(self):
        root=Path(__file__).resolve().parents[1]
        p=json.loads((root/'references/probes/mc2-graphics-offline.json').read_bytes())
        t=tomllib.loads(patch_toml(p).decode());sections=t['patch']
        self.assertEqual(t['title_id'],'4E4D0811');self.assertEqual(len(sections),3)
        self.assertTrue(all(s['is_enabled'] is False for s in sections))
        self.assertEqual(sections[0]['be32'],[dict(address=0x8237c264,value=0x39600001)])
        self.assertEqual(sections[1]['be32'],[dict(address=0x8320ad30,value=0),dict(address=0x8320ad98,value=0)])
        self.assertEqual(sections[2]['be32'],[dict(address=0x8249b3c4,value=0x480001bc)])
        self.assertFalse(p['evidence']['postprocess_equivalence_to_upstream_verified'])
        self.assertFalse(p['evidence']['runtime_verified'])

    def test_cli_rejects_unrelated_image_before_fragment_execution(self):
        b,p=fixture()
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()) as output:
            root=Path(d);f=root/'image.bin';f.write_bytes(b+b'x');j=root/'plan.json';j.write_text(json.dumps(p))
            self.assertEqual(main([str(f),'--plan',str(j),'--brief']),2)
            self.assertIn('SHA256 mismatch',output.getvalue())

    def test_brief_summary_states_are_explicitly_static(self):
        s=dict(frame_interval=1,tiling_enabled=0,tiling_mode=0,postprocess_chain='bypassed',replay_fragments=214)
        self.assertEqual(summary_line(s),'interval=1; tiling=0/0; post=bypassed; fragments=214; static_only=true')


if __name__=='__main__':unittest.main()
