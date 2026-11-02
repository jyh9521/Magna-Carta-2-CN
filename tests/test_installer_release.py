"""Source-only player-guide and single-file payload integrity regressions."""
import json
import copy
from pathlib import Path
import tempfile
import unittest
from tools.installer_singlefile import verify_payload, extract_payload, sha_file
from tools.installer_usage import render_usage

ROOT = Path(__file__).resolve().parents[1]


class CurrentReleaseTests(unittest.TestCase):
    def test_display_version_and_numeric_quad_have_no_build_one(self):
        from tools.package_installer import single_file_version_info
        version=single_file_version_info()
        self.assertIn('filevers=(1,0,0,0)',version)
        self.assertIn('prodvers=(1,0,0,0)',version)
        for key in ('FileVersion','ProductVersion'):
            self.assertIn(f"StringStruct('{key}','v1.0')",version)
        self.assertNotIn('1.0.0.1',version)
        self.assertIn('version: 1.0.0+0',(ROOT/'src/installer/pubspec.yaml').read_text())
        self.assertIn('#define VERSION_AS_STRING "v1.0"',
                      (ROOT/'src/installer/windows/runner/Runner.rc').read_text(encoding='utf8'))

    def fixture(self):
        recipe=dict(version='v1.0',title_id='owned',output_name='owned',dlc=[],discs=[
            dict(sha256=str(n)*64,resources=[dict(path='art.xxx',sha256='a'*64)])for n in (1,2)])
        manifest=dict(version='v1.0',title_id='owned',output_name='owned',dlc=[],discs=[
            dict(sha256=str(n)*64,files=[dict(path='art.xxx',sha256='b'*64,output_sha256='a'*64)])for n in (1,2)])
        return manifest,recipe

    def test_recipe_checks_both_disc_outputs_not_just_version_text(self):
        from tools.audit_installer_release import compare_manifest
        manifest,recipe=self.fixture();self.assertTrue(compare_manifest(manifest,recipe)['passed'])
        manifest['discs'][1]['files'][0]['output_sha256']='c'*64
        result=compare_manifest(manifest,recipe)
        self.assertEqual(result['resources'],2)
        self.assertEqual(result['failures'],['disc2:art.xxx'])

    def test_wrong_disc_identity_and_duplicate_or_missing_overlay_fail(self):
        from tools.audit_installer_release import compare_manifest
        manifest,recipe=self.fixture();bad=copy.deepcopy(manifest)
        bad['discs'].reverse();self.assertFalse(compare_manifest(bad,recipe)['passed'])
        bad=copy.deepcopy(manifest);bad['discs'][0]['files']=[]
        self.assertFalse(compare_manifest(bad,recipe)['passed'])
        bad=copy.deepcopy(manifest);bad['discs'][0]['files']*=2
        with self.assertRaises(ValueError):compare_manifest(bad,recipe)

    def test_dlc_and_version_are_part_of_current_payload_identity(self):
        from tools.audit_installer_release import compare_manifest
        manifest,recipe=self.fixture();recipe['dlc']=[dict(name='owned',sha256='d'*64,output_sha256='e'*64)]
        self.assertFalse(compare_manifest(manifest,recipe)['passed'])
        manifest['dlc']=copy.deepcopy(recipe['dlc']);self.assertTrue(compare_manifest(manifest,recipe)['passed'])
        manifest['version']='stale';self.assertFalse(compare_manifest(manifest,recipe)['passed'])


class PlayerGuideTests(unittest.TestCase):
    def test_installed_xex_guide_matches_actual_dlc_choice(self):
        from test_installer import make_bundle
        from tools.installer_core import Bundle, Installer
        template=(ROOT/'src/installer/USAGE.txt').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);bundle,images,dlc=make_bundle(root)
            (bundle.root/'USAGE.txt').write_bytes(template)
            manifest=dict(bundle.data,usage_sha256=sha_file(bundle.root/'USAGE.txt'),version='v1.0')
            path=bundle.root/'manifest.json';path.write_text(json.dumps(manifest),encoding='utf-8')
            bundle=Bundle(bundle.root,sha_file(path))
            for selected in (False,True):
                output=root/str(selected)
                receipt=Installer(bundle).install(images,output,'xex',dlc if selected else None)
                text=(output/'使用说明.txt').read_text(encoding='utf-8')
                self.assertEqual(bool(receipt['dlc']),selected)
                self.assertEqual('Install Content' in text,selected)
                self.assertIn('Disc1/default.xex',text)
                self.assertNotIn('.zar',text)
                self.assertTrue(text.startswith('《真名法典2》简体中文汉化补丁 v1.0\n'))
    def test_all_four_output_variants(self):
        template = (ROOT / 'src/installer/USAGE.txt').read_text(encoding='utf-8')
        for mode in ('zar', 'xex'):
            for dlc in (False, True):
                with self.subTest(mode=mode, dlc=dlc):
                    guide = render_usage(template, mode, 'TestGame', dlc)
                    self.assertTrue(guide.startswith('《真名法典2》简体中文汉化补丁 v1.0\n'))
                    self.assertNotIn('{{', guide)
                    self.assertEqual('TestGame_Disc1.zar' in guide, mode == 'zar')
                    self.assertEqual('Disc1/default.xex' in guide, mode == 'xex')
                    self.assertEqual('Install Content' in guide, dlc)
                    self.assertEqual('本次未生成 DLC' in guide, not dlc)
                    self.assertNotIn('SHA256', guide)
                    self.assertNotIn('STFS', guide)
    def test_rejects_unknown_format_or_template_marker(self):
        with self.assertRaises(ValueError): render_usage('', 'unknown', 'name', False)
        with self.assertRaises(ValueError): render_usage('{{unknown}}', 'zar', 'name', False)


class SingleFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'payload'; self.root.mkdir()
        file = self.root / 'MC2Installer.exe'; file.write_bytes(b'synthetic-executable')
        self.manifest = dict(schema=1, files={file.name: dict(size=file.stat().st_size, sha256=sha_file(file))})
        self.digest = self.write_manifest()
    def write_manifest(self):
        path = self.root / 'release-files.json'
        path.write_text(json.dumps(self.manifest), encoding='utf-8')
        return sha_file(path)
    def test_payload_and_extract_are_verified(self):
        self.assertEqual(verify_payload(self.root, self.digest), self.manifest)
        dest = self.root.parent / 'extracted'
        self.assertEqual(extract_payload(self.root, dest, self.digest), self.manifest)
        with self.assertRaises(ValueError): extract_payload(self.root, dest, self.digest)
    def test_corruption_missing_or_extra_file_rejected(self):
        file = self.root / 'MC2Installer.exe'; original = file.read_bytes()
        file.write_bytes(b'x' * len(original))
        with self.assertRaises(ValueError): verify_payload(self.root, self.digest)
        file.unlink()
        with self.assertRaises(ValueError): verify_payload(self.root, self.digest)
        file.write_bytes(original); (self.root / 'extra.dll').write_bytes(b'x')
        with self.assertRaises(ValueError): verify_payload(self.root, self.digest)
    def test_manifest_mismatch_rejected(self):
        with self.assertRaises(ValueError): verify_payload(self.root, '0' * 64)
    def test_bad_paths_rejected_even_with_valid_manifest_digest(self):
        entry = self.manifest['files']['MC2Installer.exe']
        for name in ('../outside', '/outside', 'C:/outside', 'a\\b', './MC2Installer.exe'):
            with self.subTest(name=name):
                self.manifest['files'] = {name: entry}
                with self.assertRaises(ValueError): verify_payload(self.root, self.write_manifest())
    def test_casefold_alias_rejected(self):
        self.manifest['files']['mc2installer.exe'] = self.manifest['files']['MC2Installer.exe']
        with self.assertRaises(ValueError): verify_payload(self.root, self.write_manifest())
