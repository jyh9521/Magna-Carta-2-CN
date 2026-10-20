"""Synthetic refresh journals, interruption states and isolated restoration."""
from pathlib import Path
import json,os,tempfile,unittest
from unittest.mock import patch
from test_refresh_enrollment import fixture,run,tree
from tools import restore_probe_refresh as undo
from tools.verify_resource_phase import sha


def setup(root):
    _,args,p,_=fixture(root);before=tree(args[0]);run(args,p)
    return args,before,sha((args[6]/'REFRESH.json').read_bytes())


def edit(args,change):
    p=args[6]/'REFRESH.json';m=json.loads(p.read_bytes());change(m);p.write_bytes(json.dumps(m).encode());return sha(p.read_bytes())


class RestoreRefreshTests(unittest.TestCase):
    def test_committed_audit_readonly_and_restore_exact_before(self):
        with tempfile.TemporaryDirectory() as d:
            a,before,h=setup(Path(d));after=tree(a[0]);backup=tree(a[6]);r,_,_=undo.audit(a[0],a[6],h)
            self.assertTrue(r['restorable']);self.assertGreater(r['after_count'],0);self.assertEqual(tree(a[0]),after)
            receipt=Path(d)/'receipt.json';result=undo.restore(a[0],a[6],h,receipt)
            self.assertTrue(result['all_journal_targets_before']);self.assertEqual(tree(a[0]),before);self.assertEqual(tree(a[6]),backup)
            self.assertEqual(json.loads(receipt.read_bytes()),result)
            again=undo.restore(a[0],a[6],h,Path(d)/'again.json');self.assertEqual(again['restored_files'],0)

    def test_interrupted_prepared_mixed_before_after_restores(self):
        with tempfile.TemporaryDirectory() as d:
            a,before,h=setup(Path(d));m=json.loads((a[6]/'REFRESH.json').read_bytes())
            row=m['files'][0];(a[0]/row['path']).write_bytes((a[6]/row['path']).read_bytes())
            h=edit(a,lambda m:m.update(status='prepared'));r,_,_=undo.audit(a[0],a[6],h)
            self.assertGreater(r['before_count'],0);self.assertGreater(r['after_count'],0)
            undo.restore(a[0],a[6],h,Path(d)/'receipt.json');self.assertEqual(tree(a[0]),before)

    def test_rolled_back_audit_and_noop_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            a,before,h=setup(Path(d));undo.restore(a[0],a[6],h,Path(d)/'first.json')
            h=edit(a,lambda m:m.update(status='rolled-back'));r,_,_=undo.audit(a[0],a[6],h)
            self.assertEqual(r['after_count'],0);self.assertTrue(r['restorable'])

    def test_conflict_and_missing_targets_refuse_all_writes(self):
        for missing in (True,False):
            with tempfile.TemporaryDirectory() as d:
                a,_,h=setup(Path(d));p=a[0]/'candidate/Game/A.dat'
                if missing:p.unlink()
                else:p.write_bytes(b'user edit')
                before=tree(a[0]);r,_,_=undo.audit(a[0],a[6],h);self.assertEqual(r['conflict_count'],1)
                with self.assertRaisesRegex(ValueError,'target conflict'):undo.restore(a[0],a[6],h,Path(d)/'receipt.json')
                self.assertEqual(tree(a[0]),before)

    def test_wrong_hash_root_status_or_count_rejected(self):
        for change in [lambda m:m.update(root=str(Path.cwd())),lambda m:m.update(status='unknown'),lambda m:m.update(changed_files=True),
                       lambda m:m.update(game_started=True),lambda m:m.update(raw_controls_unchanged=False)]:
            with tempfile.TemporaryDirectory() as d:
                a,_,h=setup(Path(d));h=edit(a,change)
                with self.assertRaises(ValueError):undo.audit(a[0],a[6],h)
        with tempfile.TemporaryDirectory() as d:
            a,_,_=setup(Path(d))
            with self.assertRaisesRegex(ValueError,'SHA256'):undo.audit(a[0],a[6],'0'*64)

    def test_bad_backup_hash_or_missing_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d));(a[6]/'candidate/Game/A.dat').write_bytes(b'bad backup')
            with self.assertRaisesRegex(ValueError,'before-hash'):undo.audit(a[0],a[6],h)
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d))
            def remove(m):m['files']=[r for r in m['files'] if r['path']!='PREPARED.json'];m['changed_files']=len(m['files'])
            h=edit(a,remove)
            with self.assertRaisesRegex(ValueError,'required entry metadata'):undo.audit(a[0],a[6],h)

    def test_protected_traversal_and_duplicate_paths_rejected(self):
        for name in ['raw-controls/Game/A.dat','candidate/default.xex','candidate/runs/file.bin','candidate/Game/user.toml',
                     'candidate/Game/start.cmd','../escape','candidate/Game/A.dat ']:
            with tempfile.TemporaryDirectory() as d:
                a,_,h=setup(Path(d));h=edit(a,lambda m:m['files'][0].update(path=name))
                with self.subTest(name=name),self.assertRaises(ValueError):undo.audit(a[0],a[6],h)
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d))
            def duplicate(m):m['files'].append(dict(m['files'][0]));m['changed_files']=len(m['files'])
            h=edit(a,duplicate)
            with self.assertRaisesRegex(ValueError,'duplicate'):undo.audit(a[0],a[6],h)

    def test_linked_target_and_backup_rejected(self):
        for backup in (True,False):
            with tempfile.TemporaryDirectory() as d:
                a,_,h=setup(Path(d));p=(a[6] if backup else a[0])/'candidate/Game/A.dat';os.link(p,Path(d)/'alias')
                with self.assertRaisesRegex(ValueError,'hardlinked'):undo.audit(a[0],a[6],h)

    def test_receipt_must_be_new_and_outside_roots(self):
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d));before=tree(a[0])
            for p in [a[0]/'report.json',a[6]/'report.json',a[0]/'PREPARED.json']:
                with self.assertRaises(ValueError):undo.restore(a[0],a[6],h,p)
                self.assertEqual(tree(a[0]),before)

    def test_interruption_before_and_after_replace_restores_observed_state(self):
        for after_replace in (True,False):
            with tempfile.TemporaryDirectory() as d:
                a,_,h=setup(Path(d));before=tree(a[0]);real=undo.atomic_write;calls=[]
                def fail_once(p,b):
                    calls.append(p)
                    if len(calls)==2:
                        if after_replace:real(p,b)
                        raise OSError('synthetic restore interruption')
                    return real(p,b)
                with patch.object(undo,'atomic_write',side_effect=fail_once),self.assertRaisesRegex(OSError,'synthetic'):undo.restore(a[0],a[6],h,Path(d)/'receipt.json')
                self.assertEqual(tree(a[0]),before)

    def test_receipt_failure_reverses_restore(self):
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d));before=tree(a[0])
            with patch.object(undo,'emit_new',side_effect=OSError('receipt failure')),self.assertRaisesRegex(OSError,'receipt failure'):
                undo.restore(a[0],a[6],h,Path(d)/'receipt.json')
            self.assertEqual(tree(a[0]),before)

    def test_original_source_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d));p=a[6]/'PREPARED.json';old=json.loads(p.read_bytes());old['source_root']=str(a[0]);p.write_bytes(json.dumps(old).encode())
            def update(m):next(r for r in m['files'] if r['path']=='PREPARED.json')['before']=sha(p.read_bytes())
            h=edit(a,update)
            with self.assertRaisesRegex(ValueError,'original source'):undo.audit(a[0],a[6],h)

    def test_cli_audit_conflict_exit_one_without_game_writes(self):
        with tempfile.TemporaryDirectory() as d:
            a,_,h=setup(Path(d));(a[0]/'candidate/Game/A.dat').write_bytes(b'user edit');before=tree(a[0])
            code=undo.main(['--mode','audit','--root',str(a[0]),'--backup',str(a[6]),'--journal-sha256',h,'--output',str(Path(d)/'audit.json')])
            self.assertEqual(code,1);self.assertEqual(tree(a[0]),before)
