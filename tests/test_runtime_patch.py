"""Self-authored PPC snippets, patch guards and per-run launcher isolation."""
import copy
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from tools.runtime_patch import digest,apply_image,build,read_bundle,patch_toml
from tools.replay_wrap_width import replay,check
from tools.replay_wrap_width import main as replay_main
from tools import launch_xenia
from tools import prepare_oneclick_probe as ready
import test_oneclick_probe


def fixture_plan(image,game=b'game',exe=b'exe'):
    return dict(schema_version=1,kind='ppc-runtime-patch',image_base=0x1000,image_sha256=digest(image),
        game_sha256=digest(game),emulator_sha256=digest(exe),title_id='12345678',module_hash='0123456789ABCDEF',
        title_name='Synthetic Fixture',name='Correct forced-wrap line extent',
        windows=[dict(address=0x1020,size=4,sha256=digest(image[32:36]))],
        writes=[dict(address=0x1020,expected='ef40f77c',replacement='48000060'),
                dict(address=0x1080,expected='000000000000000000000000',replacement='ef40f77cef5ac8284bffff9c')],
        replay=dict(entry=0x1020,exit=0x1024,cave=0x1080))


def image_fixture():
    image=bytearray(256);image[32:36]=bytes.fromhex('ef40f77c');return bytes(image)


class RuntimePatchTests(unittest.TestCase):
    def test_original_forced_split_reproduces_origin_leak(self):
        image=image_fixture();plan=fixture_plan(image);r=check(image,plan)
        self.assertEqual((r['cases'],r['failures']),(216,180))
        got,_=replay(image,0x1000,0x1020,0x1024,0x1080,640,928,1,16)
        self.assertEqual(got,912)  # actual 17*16=272; spurious origin640

    def test_fix_executes_original_then_subtracts_origin_and_returns(self):
        image=image_fixture();plan=fixture_plan(image);modified=apply_image(image,plan)
        got,trace=replay(modified,0x1000,0x1020,0x1024,0x1080,640,928,1,16)
        self.assertEqual(got,272);self.assertEqual(trace,[0x1020,0x1080,0x1084,0x1088])
        self.assertEqual(check(modified,plan)['failures'],0)
        self.assertEqual(apply_image(modified,plan,True),image)
        changes={i for i,(a,b) in enumerate(zip(image,modified)) if a!=b}
        self.assertTrue(changes <= set(range(32,36))|set(range(128,140)))

    def test_zero_origin_unchanged_and_midword_start_handled(self):
        image=image_fixture();plan=fixture_plan(image);modified=apply_image(image,plan)
        a,_=replay(image,0x1000,0x1020,0x1024,0x1080,0,288,1,16)
        b,_=replay(modified,0x1000,0x1020,0x1024,0x1080,0,288,1,16)
        self.assertEqual((a,b),(272,272))
        c,_=replay(modified,0x1000,0x1020,0x1024,0x1080,267,555,1,16)
        self.assertEqual(c,272)

    def test_patch_rejects_unknown_image_bad_window_and_wrong_expected_bytes(self):
        image=image_fixture();plan=fixture_plan(image)
        with self.assertRaisesRegex(ValueError,'SHA256'):apply_image(image+b'x',plan)
        for edit in ['window','expected','overlap','bounds']:
            p=copy.deepcopy(plan)
            if edit=='window':p['windows'][0]['sha256']='0'*64
            if edit=='expected':p['writes'][0]['expected']='00000000'
            if edit=='overlap':p['writes'].append(copy.deepcopy(p['writes'][0]))
            if edit=='bounds':p['writes'][0]['address']=0xfffffffc
            with self.subTest(edit=edit),self.assertRaises(ValueError):apply_image(image,p)

    def test_rollback_rejects_unrelated_modified_image(self):
        image=image_fixture();p=fixture_plan(image);m=bytearray(apply_image(image,p));m[-1]=1
        with self.assertRaisesRegex(ValueError,'restoration'):apply_image(bytes(m),p,True)

    def test_replay_rejects_unsupported_instruction_and_escape(self):
        image=bytearray(image_fixture());image[32:36]=bytes.fromhex('60000000')
        with self.assertRaisesRegex(ValueError,'unsupported'):replay(bytes(image),0x1000,0x1020,0x1024,0x1080,1,5,1,1)
        image[32:36]=bytes.fromhex('48000004')
        # A direct branch to exit performs no arithmetic and fails width checks.
        self.assertGreater(check(bytes(image),fixture_plan(bytes(image)))['failures'],0)
        with self.assertRaisesRegex(ValueError,'finite'):replay(bytes(image),0x1000,0x1020,0x1024,0x1080,float('nan'),5,1,1)

    def test_replay_cli_checks_full_input_image_not_only_selected_instruction(self):
        import contextlib,io
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stdout(io.StringIO()):
            root=Path(d);image=image_fixture();plan=fixture_plan(image);p=root/'plan.json';p.write_text(json.dumps(plan));f=root/'image.bin'
            args=[str(f),'--plan',str(p)]
            f.write_bytes(image);self.assertEqual(replay_main(args),1)
            f.write_bytes(apply_image(image,plan));self.assertEqual(replay_main(args),0)
            changed=bytearray(image);changed[-1]=1;f.write_bytes(changed)
            self.assertEqual(replay_main(args),2)

    def make_bundle(self,root,game=b'game',exe=b'exe'):
        g=root/'game/default.xex';g.parent.mkdir();g.write_bytes(game);e=root/'emu.exe';e.write_bytes(exe)
        p=fixture_plan(image_fixture(),game,exe);out=root/'bundle';build(image_fixture(),p,g,e,out)
        return g,e,p,out,digest((out/'manifest.json').read_bytes())

    def test_toml_words_replay_exactly_to_modified_image(self):
        image=image_fixture();p=fixture_plan(image);t=tomllib.loads(patch_toml(p).decode())
        self.assertTrue(t['patch'][0]['is_enabled']);out=bytearray(image)
        for w in t['patch'][0]['be32']:out[w['address']-0x1000:w['address']-0x1000+4]=w['value'].to_bytes(4,'big')
        self.assertEqual(bytes(out),apply_image(image,p))

    def test_bundle_identity_hashes_and_existing_config_gate(self):
        with tempfile.TemporaryDirectory() as d:
            g,e,p,b,h=self.make_bundle(Path(d));m,files=read_bundle(b,h,g,e,b'[General]\napply_patches=true\n')
            self.assertEqual(len(files),1);self.assertFalse(m['game_started'])
            with self.assertRaisesRegex(ValueError,'manifest SHA256'):read_bundle(b,'0'*64,g,e,b'')
            with self.assertRaisesRegex(ValueError,'apply_patches'):read_bundle(b,h,g,e,b'[General]\napply_patches=false\n')
            g.write_bytes(b'unsupported game')
            with self.assertRaisesRegex(ValueError,'game_sha256'):read_bundle(b,h,g,e,b'')

    def test_bundle_payload_tamper_and_filename_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            g,e,p,b,h=self.make_bundle(Path(d));m=json.loads((b/'manifest.json').read_bytes());name=next(iter(m['patches']))
            (b/name).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'file SHA256'):read_bundle(b,h,g,e,b'')
            m['patches']={'../escape.patch.toml':'0'*64};raw=json.dumps(m).encode();(b/'manifest.json').write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'filename'):read_bundle(b,digest(raw),g,e,b'')

    def test_launcher_copies_patch_only_to_unique_storage_and_preserves_config(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();g,e,p,b,h=self.make_bundle(root);config=root/'user.toml';raw=b'[General]\napply_patches=true\n[GPU]\ngpu="d3d12"\n';config.write_bytes(raw)
            run=root/'run';r=launch_xenia.prepare(e,config,g,run,patch_bundle=b,patch_manifest_sha256=h)
            self.assertEqual(config.read_bytes(),raw);self.assertEqual(Path(r['config_snapshot']).read_bytes(),raw)
            self.assertEqual(r['tuning_overrides'],[]);self.assertEqual(len(r['command']),7)
            copied=next((run/'storage/patches').iterdir());self.assertIn(str(copied),r['runtime_patch']['files'])
            with patch.object(launch_xenia.subprocess,'Popen') as popen:
                copied.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError,'copy changed'):launch_xenia.launch(run,r)
                popen.assert_not_called()

    def test_launcher_extra_patch_and_incomplete_arguments_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();g,e,p,b,h=self.make_bundle(root);c=root/'user.toml';c.write_bytes(b'')
            with self.assertRaisesRegex(ValueError,'together'):launch_xenia.prepare(e,c,g,root/'bad',patch_bundle=b)
            self.assertFalse((root/'bad').exists())
            r=launch_xenia.prepare(e,c,g,root/'run',patch_bundle=b,patch_manifest_sha256=h)
            (root/'run/storage/patches/unrelated.patch.toml').write_text('')
            with patch.object(launch_xenia.subprocess,'Popen') as popen:
                with self.assertRaisesRegex(ValueError,'inventory'):launch_xenia.launch(root/'run',r)
                popen.assert_not_called()

    def test_launch_accepts_relative_run_directory_without_false_inventory_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();g,e,p,b,h=self.make_bundle(root);c=root/'user.toml';c.write_bytes(b'')
            r=launch_xenia.prepare(e,c,g,root/'run',patch_bundle=b,patch_manifest_sha256=h)
            # Hosted Windows uses D: for the checkout and C: for TEMP. Resolve
            # the relative fixture from its own root, not the ambient checkout.
            with patch('os.getcwd',return_value=str(root)), patch.object(launch_xenia.subprocess,'Popen',return_value=type('FakeProcess',(),{'pid':123})()) as popen:
                launch_xenia.launch(Path('run'),r)
                popen.assert_called_once()
            self.assertEqual(r['status'],'started')  # Mock process only, never a native executable.

    def test_oneclick_has_same_resource_unfixed_control_and_patched_candidate_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();f,project,e,c,out=test_oneclick_probe.OneclickTests().fixture(root)
            sub=root/'runtime';sub.mkdir();g,other,p,b,h=self.make_bundle(sub,(f.game/'default.xex').read_bytes(),e.read_bytes())
            r=ready.prepare(f.game,f.packet,f.hash,digest(g.read_bytes()),e,c,out,project,patch_bundle=b,patch_manifest_sha256=h)
            self.assertTrue(r['runtime_patch']['per_run_storage_only']);self.assertFalse(r['game_started'])
            fixed=(out/'开始中文测试.cmd').read_text('utf8');unfixed=(out/'开始未修复对照.cmd').read_text('utf8')
            self.assertIn('--patch-bundle',fixed);self.assertNotIn('--patch-bundle',unfixed)
            self.assertIn('--phase candidate',fixed);self.assertIn('--phase candidate',unfixed)
            self.assertNotIn('--patch-bundle',(out/'开始原文对照.cmd').read_text('utf8'))


if __name__=='__main__':unittest.main()
