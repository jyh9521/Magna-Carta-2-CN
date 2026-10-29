import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from test_content_bundle import make_bundle,REL
import test_oneclick_probe as probe_fixtures
from tools import install_dlc_bundle as transaction
from tools.xdbf_strings import sha


class DlcInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        helper=probe_fixtures.OneclickTests();f,project,exe,config,test=helper.fixture(self.root)
        helper.run_prepare(f,project,exe,config,test)
        self.test=test;self.content=self.root/'content';self.content.mkdir();(self.content/'save.bin').write_bytes(b'preserve user save')
        self.bundle=self.root/'bundle';_,h=make_bundle(self.bundle);self.backup=self.root/'install-journal'
        self.args=dict(bundle=self.bundle,manifest_sha256=h,content_root=self.content,test_root=test,backup=self.backup,
            prepared_sha256=sha((test/'PREPARED.json').read_bytes()),project=project,exe=exe,config=config)
        self.before={p.relative_to(test).as_posix():p.read_bytes()for p in test.rglob('*')if p.is_file()}
    def check_restored(self):
        self.assertEqual({p.relative_to(self.test).as_posix():p.read_bytes()for p in self.test.rglob('*')if p.is_file()},self.before)
        self.assertEqual([p.name for p in self.content.iterdir()],['save.bin'])
        self.assertEqual((self.content/'save.bin').read_bytes(),b'preserve user save')
    def test_install_and_idempotent_exact_rollback(self):
        r=transaction.install(**self.args);self.assertEqual(r['files'],5)
        self.assertEqual((self.content/REL).read_bytes(),(self.bundle/'files'/REL).read_bytes())
        self.assertIn(b'--content-bundle',(self.test/'开始中文测试.cmd').read_bytes())
        for _ in range(2):
            result=transaction.rollback(self.backup,r['journal_sha256']);self.assertTrue(result['restored_pre_dlc_status'])
            self.check_restored()
    def test_independent_copy_rollback_does_not_revert_live_modified_files(self):
        r=transaction.install(**self.args);test=self.root/'isolated-test';content=self.root/'isolated-content'
        shutil.copytree(self.test,test);shutil.copytree(self.content,content)
        transaction.rollback(self.backup,r['journal_sha256'],content,test)
        self.assertFalse((content/REL).exists());self.assertTrue((self.content/REL).exists())
        self.assertEqual((test/'PREPARED.json').read_bytes(),self.before['PREPARED.json'])
    def test_conflicting_package_is_preserved_before_any_write(self):
        path=self.content/REL;path.parent.mkdir(parents=True);path.write_bytes(b'user package')
        with self.assertRaisesRegex(ValueError,'already exists'):transaction.install(**self.args)
        self.assertEqual(path.read_bytes(),b'user package');self.assertFalse(self.backup.exists())
    def test_partial_write_failure_restores_entry(self):
        real=transaction.atomic_write;calls=[]
        def fail(path,data):
            calls.append(path)
            if len(calls)==3:raise OSError('synthetic interruption')
            return real(path,data)
        with patch.object(transaction,'atomic_write',side_effect=fail),self.assertRaisesRegex(OSError,'interruption'):
            transaction.install(**self.args)
        self.check_restored()
    def test_foreign_modification_refuses_rollback_without_partial_writes(self):
        r=transaction.install(**self.args);(self.content/REL).write_bytes(b'new writer')
        before=(self.test/'PREPARED.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'another writer'):transaction.rollback(self.backup,r['journal_sha256'])
        self.assertEqual((self.test/'PREPARED.json').read_bytes(),before)
    def test_modified_launcher_or_prepared_hash_rejects(self):
        (self.test/'开始中文测试.cmd').write_bytes(b'user change')
        with self.assertRaisesRegex(ValueError,'template'):transaction.install(**self.args)
        self.assertFalse(self.backup.exists())
    def test_journal_hash_and_target_scope(self):
        r=transaction.install(**self.args)
        with self.assertRaisesRegex(ValueError,'SHA256'):transaction.rollback(self.backup,'0'*64)
        jp=self.backup/'INSTALL.json';j=json.loads(jp.read_bytes());j['files'][0]['path']='../../outside'
        jp.write_bytes(json.dumps(j).encode())
        with self.assertRaisesRegex(ValueError,'inventory'):transaction.rollback(self.backup,sha(jp.read_bytes()))

    def test_backup_must_not_modify_source_bundle(self):
        self.args['backup']=self.bundle/'journal'
        with self.assertRaisesRegex(ValueError,'disjoint'):transaction.install(**self.args)
        self.assertFalse((self.bundle/'journal').exists())

if __name__=='__main__':unittest.main()
