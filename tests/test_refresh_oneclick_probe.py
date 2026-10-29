import copy,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_oneclick_probe as fixtures
from tools import refresh_oneclick_probe as update
from tools.verify_resource_phase import sha

class RefreshTests(unittest.TestCase):
    def fixture(self,root):
        helper=fixtures.OneclickTests();f,project,exe,config,out=helper.fixture(root)
        helper.run_prepare(f,project,exe,config,out)
        packet=root/'new-packet';shutil.copytree(f.packet,packet);m=copy.deepcopy(f.manifest)
        raw=b'new candidate bytes';(packet/'candidate/Game/A.dat').write_bytes(raw)
        m['resources'][0].update(candidate_sha256=sha(raw),candidate_size=len(raw))
        m['member_sha256']['candidate/Game/A.dat']=sha(raw)
        data=json.dumps(m).encode();(packet/'manifest.json').write_bytes(data)
        args=[out,sha((out/'PREPARED.json').read_bytes()),packet,sha(data),exe,config,root/'backup',project]
        return f,args

    def test_refresh_preserves_runs_raw_controls_originals_and_config(self):
        with tempfile.TemporaryDirectory() as d:
            f,a=self.fixture(Path(d));out=a[0];save=out/'runs/storage/save.bin';save.parent.mkdir(parents=True);save.write_bytes(b'user save')
            raw=(out/'raw-controls/Game/A.dat').read_bytes();source=(f.game/'Game/A.dat').read_bytes();cfg=a[5].read_bytes()
            result=update.refresh(*a)
            self.assertFalse(result['game_started']);self.assertEqual(save.read_bytes(),b'user save')
            self.assertEqual((out/'candidate/Game/A.dat').read_bytes(),b'new candidate bytes')
            self.assertEqual((out/'raw-controls/Game/A.dat').read_bytes(),raw)
            self.assertEqual((f.game/'Game/A.dat').read_bytes(),source);self.assertEqual(a[5].read_bytes(),cfg)
            self.assertEqual((a[6]/'candidate/Game/A.dat').read_bytes(),b'candidate:Game/A.dat')

    def test_changed_old_resource_or_bad_report_hash_rejects_before_backup(self):
        for changed in (True,False):
            with tempfile.TemporaryDirectory() as d:
                _,a=self.fixture(Path(d))
                if changed:(a[0]/'candidate/Game/A.dat').write_bytes(b'user modified')
                else:a[1]='0'*64
                with self.assertRaises(ValueError):update.refresh(*a)
                self.assertFalse(a[6].exists())

    def test_raw_control_change_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,a=self.fixture(Path(d));p=a[2]/'raw-controls/Game/A.dat';p.write_bytes(b'changed raw')
            m=json.loads((a[2]/'manifest.json').read_bytes());m['member_sha256']['raw-controls/Game/A.dat']=sha(p.read_bytes())
            data=json.dumps(m).encode();(a[2]/'manifest.json').write_bytes(data);a[3]=sha(data)
            with self.assertRaisesRegex(ValueError,'raw controls'):update.refresh(*a)
            self.assertFalse(a[6].exists())

    def test_interrupted_commit_restores_every_written_file(self):
        with tempfile.TemporaryDirectory() as d:
            _,a=self.fixture(Path(d));before={p:p.read_bytes() for p in a[0].rglob('*') if p.is_file()}
            real=update.atomic_write;calls=[]
            def fail_once(path,data):
                calls.append(path)
                if len(calls)==2:raise OSError('synthetic interruption')
                return real(path,data)
            with patch.object(update,'atomic_write',side_effect=fail_once),self.assertRaisesRegex(OSError,'synthetic'):
                update.refresh(*a)
            for p,data in before.items():self.assertEqual(p.read_bytes(),data)

    def test_refresh_retains_verified_optional_dlc_in_candidate_only(self):
        from test_content_bundle import make_bundle
        with tempfile.TemporaryDirectory() as d:
            _,a=self.fixture(Path(d));bundle=a[0]/'dlc-content';_,h=make_bundle(bundle)
            p=a[0]/'PREPARED.json';record=json.loads(p.read_bytes())
            record['content_bundle']=dict(bundle=str(bundle),manifest_sha256=h);p.write_bytes(json.dumps(record).encode());a[1]=sha(p.read_bytes())
            update.refresh(*a)
            self.assertIn(b'--content-bundle',(a[0]/'开始中文测试.cmd').read_bytes())
            self.assertNotIn(b'--content-bundle',(a[0]/'开始原文对照.cmd').read_bytes())
            self.assertEqual(json.loads(p.read_bytes())['content_bundle'],record['content_bundle'])

    def test_changed_retained_bundle_rejects_before_refresh(self):
        from test_content_bundle import make_bundle,REL
        with tempfile.TemporaryDirectory() as d:
            _,a=self.fixture(Path(d));bundle=a[0]/'dlc-content';_,h=make_bundle(bundle)
            p=a[0]/'PREPARED.json';record=json.loads(p.read_bytes())
            record['content_bundle']=dict(bundle=str(bundle),manifest_sha256=h);p.write_bytes(json.dumps(record).encode());a[1]=sha(p.read_bytes())
            (bundle/'files'/REL).write_bytes(b'changed')
            with self.assertRaises(ValueError):update.refresh(*a)
            self.assertFalse(a[6].exists())

if __name__=='__main__':unittest.main()
