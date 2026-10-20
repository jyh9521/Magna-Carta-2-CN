"""Self-authored two-disc fixtures; never combine subtitle source identities."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import build_subtitle_bundle as b
from tools.subtitle_text import digest, rebuild_reversible, parse


def fixture():
    raw = b'\xff\xfe'+('1\r\n<SYNC Start=10><P Class=KRCC>source<br>text'
        '<SYNC Start=20><P Class=KRCC>&nbsp;\r\n').encode('utf-16-le')
    plans=[];sources=[]
    for disc in (1,2):
        resource=f'Movies/disc{disc}.txt'
        plans.append(dict(schema_version=1,kind='timed-subtitle-text',resource=resource,
            input_sha256=digest(raw),entries=[dict(start=10,end=20,
                source_sha256=digest(b'source<br>text'),translation='localized<br>text')]))
        image=f'image{disc}'.encode()
        sources.append(dict(disc=disc,path=f'disc{disc}.iso',size=len(image),sha256=digest(image),
            members=[dict(resource=resource,sha256=digest(raw),size=len(raw))]))
    toc=(f'{len(raw)} 7 9 ../Movies/disc1.txt 0\r\n'+'0 0 123 ../Game/TOC.txt 0\r\n').encode()
    plan=dict(schema_version=1,kind='offline-disc-subtitle-bundle',disc=1,
        game_rendering_verified=False,toc=dict(path='Game/TOC.txt',sha256=digest(toc)))
    profile=dict(schema_version=1,sources=sources)
    return plan,profile,plans,{'Movies/disc1.txt':raw,'Game/TOC.txt':toc}


class SubtitleBundleTests(unittest.TestCase):
    def test_cue_inverse_and_toc_inverse_are_byte_identical(self):
        plan,profile,plans,originals=fixture();files,r=b.prepare(plan,profile,plans,originals)
        self.assertEqual((r['disc'],r['subtitle_resources'],r['translated_cues']),(1,1,1))
        self.assertTrue(r['toc_inverse_byte_identical'])
        for path,raw in originals.items():
            self.assertEqual(files['rollback-check/'+path],raw)
            self.assertEqual(files['controls/'+path],raw)
        self.assertFalse(r['game_rendering_verified']);self.assertFalse(r['fonts_verified'])
        self.assertFalse(r['cumulative_INT_included'])
        self.assertNotEqual(files['candidate/Game/TOC.txt'],originals['Game/TOC.txt'])

    def test_other_disc_inputs_rejected(self):
        p,f,ps,originals=fixture();originals['Movies/disc2.txt']=originals['Movies/disc1.txt']
        with self.assertRaisesRegex(ValueError,'this disc exactly'):b.prepare(p,f,ps,originals)

    def test_zero_self_size_and_other_toc_fields_are_not_invented(self):
        p,f,ps,o=fixture();ps[0]['entries'][0]['translation']='Z'*5000+'<br>text'
        files,_=b.prepare(p,f,ps,o)
        self.assertNotEqual(len(files['candidate/Game/TOC.txt']),len(o['Game/TOC.txt']))
        self.assertIn(b'0 0 123 ../Game/TOC.txt 0\r\n',files['candidate/Game/TOC.txt'])

    def test_second_disc_requires_its_own_toc_and_stays_separate(self):
        p,f,ps,o=fixture();p['disc']=2
        o['Movies/disc2.txt']=o.pop('Movies/disc1.txt')
        with self.assertRaises(ValueError):b.prepare(p,f,ps,o)
        o['Game/TOC.txt']=o['Game/TOC.txt'].replace(b'disc1.txt',b'disc2.txt')
        p['toc']['sha256']=digest(o['Game/TOC.txt'])
        files,r=b.prepare(p,f,ps,o)
        self.assertEqual(r['disc'],2)
        self.assertEqual(r['source_image_sha256'],f['sources'][1]['sha256'])
        self.assertFalse(any('disc1.txt' in path for path in files))

    def test_disc_bool_unknown_and_duplicate_id_rejected(self):
        for disc in (True,0,3):
            p,f,ps,_=fixture();p['disc']=disc
            with self.subTest(disc=disc),self.assertRaises(ValueError):b.select_inputs(p,f,ps)
        p,f,ps,_=fixture();f['sources'][1]['disc']=1
        with self.assertRaisesRegex(ValueError,'ambiguous'):b.select_inputs(p,f,ps)

    def test_unknown_plan_or_missing_disc_plan_rejected(self):
        p,f,ps,_=fixture();ps[0]['resource']='Movies/foreign.txt'
        with self.assertRaisesRegex(ValueError,'provenance'):b.select_inputs(p,f,ps)
        p,f,ps,_=fixture()
        with self.assertRaisesRegex(ValueError,'unplanned'):b.select_inputs(p,f,ps[1:])

    def test_duplicate_case_paths_and_member_bound(self):
        p,f,ps,_=fixture();m=copy.deepcopy(f['sources'][0]['members'][0]);m['resource']='MOVIES/DISC1.TXT';f['sources'][0]['members'].append(m)
        with self.assertRaisesRegex(ValueError,'duplicate'):b.select_inputs(p,f,ps)
        p,f,ps,_=fixture();f['sources'][0]['members']*=65
        with self.assertRaisesRegex(ValueError,'1..64'):b.select_inputs(p,f,ps)

    def test_toc_role_overlap_and_bad_hash_rejected(self):
        p,f,ps,o=fixture();p['toc']['path']='Movies/disc1.txt'
        with self.assertRaisesRegex(ValueError,'overlaps'):b.prepare(p,f,ps,o)
        p,f,ps,o=fixture();p['toc']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'TOC identity'):b.prepare(p,f,ps,o)

    def test_source_size_hash_and_toc_expected_size_rejected(self):
        p,f,ps,o=fixture();o['Movies/disc1.txt']+=b'\0\0'
        with self.assertRaisesRegex(ValueError,'member identity'):b.prepare(p,f,ps,o)
        p,f,ps,o=fixture();o['Game/TOC.txt']=o['Game/TOC.txt'].replace(str(len(o['Movies/disc1.txt'])).encode(),b'999');p['toc']['sha256']=digest(o['Game/TOC.txt'])
        with self.assertRaises(ValueError):b.prepare(p,f,ps,o)

    def test_overlapping_cue_plans_and_timing_drift_rejected(self):
        p,f,ps,o=fixture()
        with self.assertRaises(ValueError):b.prepare(p,f,ps+[copy.deepcopy(ps[0])],o)
        p,f,ps,o=fixture();ps[0]['entries'][0]['end']=21
        with self.assertRaisesRegex(ValueError,'timing'):b.prepare(p,f,ps,o)

    def test_reversible_helper_accepts_string_start_and_noop(self):
        _,_,ps,o=fixture();p=ps[0];p['entries'][0]['start']='10'
        output,r=rebuild_reversible(o['Movies/disc1.txt'],p)
        self.assertTrue(r['inverse_rebuild_byte_identical'])
        p['entries']=[];output,r=rebuild_reversible(o['Movies/disc1.txt'],p)
        self.assertEqual(output,o['Movies/disc1.txt']);self.assertEqual(r['edited_cues'],0)

    def test_bundle_build_verify_tamper_and_original_image_guard(self):
        p,profile,plans,o=fixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'disc1.iso').write_bytes(b'image1')
            refs=[]
            for i,plan in enumerate(plans):
                path=root/f'p{i}.json';path.write_bytes(b.encoded(plan));refs.append(dict(path=path.name,sha256=digest(path.read_bytes())))
            profile['plans']=refs;path=root/'profile.json';path.write_bytes(b.encoded(profile));p['profile']=dict(path=path.name,sha256=digest(path.read_bytes()))
            paths=list(o);records=[dict(path=v,directory=False,offset=i,size=len(o[v])) for i,v in enumerate(paths)]
            with patch.object(b,'Disc') as disc:
                disc.return_value.inventory.return_value=records
                disc.return_value.read.side_effect=lambda offset,size:o[paths[offset]]
                out=root/'bundle';b.build(p,root,out);b.verify(p,root,out)
                self.assertEqual((out/'rollback-check/Movies/disc1.txt').read_bytes(),o['Movies/disc1.txt'])
                with self.assertRaisesRegex(ValueError,'must be new'):b.build(p,root,out)
                target=out/'candidate/Movies/disc1.txt';target.write_bytes(target.read_bytes()+b'xx')
                with self.assertRaisesRegex(ValueError,'replay mismatch'):b.verify(p,root,out)
                (root/'disc1.iso').write_bytes(b'wrong')
                with self.assertRaisesRegex(ValueError,'source image'):b.build(p,root,root/'other')
