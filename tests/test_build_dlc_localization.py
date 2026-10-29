import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_stfs_package import fixture as stfs_fixture
from test_xdbf_strings import fixture as spa_fixture,plan as spa_plan
from tools.build_dlc_localization import build,json_bytes,validate_strings
from tools.stfs_package import StfsPackage
from tools.xdbf_strings import sha,Xdbf


class BuildDlcTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'original';self.source.mkdir();self.name='A'*42
        self.spa=spa_fixture();self.data=stfs_fixture([('spa.bin',self.spa),('marker.DLC',b'unchanged')])
        (self.source/self.name).write_bytes(self.data)
        self.shared=dict(schema_version=1,kind='shared-xdbf-string-translations',source_language_id=7,
            entries=spa_plan()['entries'],preserved_ids=[dict(id=2,source_sha256=sha(b'another')),dict(id=3,source_sha256=sha(b''))])
        (self.root/'strings.json').write_bytes(json_bytes(self.shared))
        self.assets=dict(schema_version=1,kind='ue3-subtitle-reference-revision',container=self.name,packages=[])
        (self.root/'assets.json').write_bytes(json_bytes(self.assets))
        self.profile=dict(schema_version=1,kind='stfs-dlc-localization',title_id='12345678',content_type=2,
            strings='strings.json',strings_sha256=sha((self.root/'strings.json').read_bytes()),assets='assets.json',
            assets_sha256=sha((self.root/'assets.json').read_bytes()),packages=[dict(name=self.name,input_sha256=sha(self.data),
                input_size=len(self.data),spa_sha256=sha(self.spa),metadata={'display_name:0':'本地化内容包'})])
        self.p=self.root/'profile.json';self.save();self.out=self.root/'output'
    def save(self):self.p.write_bytes(json_bytes(self.profile))
    def run_build(self):return build(self.source,self.p,self.root,self.out)
    def test_actual_container_and_xdbf_composition_reproducible(self):
        result=self.run_build();row=result['packages'][0];output=(self.out/row['path']).read_bytes()
        package=StfsPackage(output);self.assertEqual(package.read_member('marker.DLC'),b'unchanged')
        self.assertEqual(Xdbf(package.read_member('spa.bin')).strings()[7][0]['text'],'译文 {0}')
        self.assertEqual((self.source/self.name).read_bytes(),self.data)
        again=build(self.source,self.p,self.root,self.root/'again');self.assertEqual(result,again)
    def test_source_hash_guard_and_no_output_on_failure(self):
        (self.source/self.name).write_bytes(self.data+b'!')
        with self.assertRaisesRegex(ValueError,'identity'):self.run_build()
        self.assertFalse(self.out.exists())
    def test_dependency_hash_guard(self):
        (self.root/'strings.json').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'dependency'):self.run_build()
        self.assertFalse(self.out.exists())
    def test_existing_or_source_output_rejected(self):
        self.out.mkdir()
        with self.assertRaisesRegex(ValueError,'new output'):self.run_build()
        with self.assertRaisesRegex(ValueError,'new output'):build(self.source,self.p,self.root,self.source/'child')
    def test_unknown_source_files(self):
        (self.source/'unexpected').write_bytes(b'!')
        with self.assertRaisesRegex(ValueError,'inventory'):self.run_build()
    def test_complete_string_coverage_and_preserved_hashes(self):
        for change in ('missing','duplicate','preserved'):
            p=copy.deepcopy(self.shared)
            if change=='missing':p['preserved_ids'].pop()
            if change=='duplicate':p['entries']*=2
            if change=='preserved':p['preserved_ids'][0]['source_sha256']='0'*64
            with self.subTest(change=change),self.assertRaises(ValueError):validate_strings(self.spa,p)
    def test_wrong_title_identity(self):
        self.profile['title_id']='FFFFFFFF';self.save()
        with self.assertRaisesRegex(ValueError,'title/content'):self.run_build()
    def test_strict_profile(self):
        self.profile['schema_version']=True;self.save()
        with self.assertRaisesRegex(ValueError,'profile'):self.run_build()
    def test_wrong_spa_identity(self):
        self.profile['packages'][0]['spa_sha256']='0'*64;self.save()
        with self.assertRaisesRegex(ValueError,'SPA'):self.run_build()
    def test_dependency_path_escape(self):
        self.profile['strings']='../outside.json';self.save()
        with self.assertRaisesRegex(ValueError,'path'):self.run_build()

if __name__=='__main__':unittest.main()
