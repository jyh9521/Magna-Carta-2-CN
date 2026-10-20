"""Synthetic additive inventories and transaction interruption; no game execution."""
from pathlib import Path
import json,os,tempfile,unittest
from unittest.mock import patch
import test_refresh_oneclick_probe as base
from tools import refresh_oneclick_probe as update
from tools.verify_resource_phase import sha


def fixture(root):
    f,a=base.RefreshTests().fixture(root);packet=a[2]
    m=json.loads((packet/'manifest.json').read_bytes())
    m.update(kind='offline-disc-locale-raw-comparison',disc=1,composition_manifest_sha256='1'*64,
             comparison_plan_canonical_sha256='2'*64,unknown_control_syntax_resolved=False,
             raw_control_method='source-derived-uncompressed-fonts-original-text-disc-toc')
    path='Game/added.txt';original=b'original extra subtitle';candidate=b'translated extra subtitle'
    for phase in ('controls','raw-controls','candidate'):
        data=candidate if phase=='candidate' else original;p=packet/phase/path;p.write_bytes(data)
        m['member_sha256'][phase+'/'+path]=sha(data)
    for phase in ('candidate','raw-controls'):(a[0]/phase/path).write_bytes(original)
    m['resources'].append(dict(path=path,original_sha256=sha(original),original_size=len(original),
                              candidate_sha256=sha(candidate),candidate_size=len(candidate)))
    for r in m['resources']:
        r.update(raw_sha256=m['member_sha256']['raw-controls/'+r['path']],raw_size=(packet/'raw-controls'/r['path']).stat().st_size)
    data=json.dumps(m).encode();(packet/'manifest.json').write_bytes(data);a[3]=sha(data)
    plan=dict(schema_version=1,kind='explicit-resource-enrollment',disc=1,prepared_sha256=a[1],
              old_packet_manifest_sha256=f.hash,new_packet_manifest_sha256=a[3],game_rendering_verified=False,
              additions=[dict(path=path,original_sha256=sha(original),original_size=len(original))])
    p=root/'enrollment.json';p.write_bytes(json.dumps(plan).encode());return f,a,p,plan


def save_plan(p,plan):p.write_bytes(json.dumps(plan).encode());return sha(p.read_bytes())
def run(a,p):return update.refresh(*a,enrollment=p,enrollment_sha256=sha(p.read_bytes()))
def tree(root):return {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}


class EnrollmentRefreshTests(unittest.TestCase):
    def test_default_still_refuses_expansion_before_backup(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,_,_=fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'resource sets differ'):update.refresh(*a)
            self.assertFalse(a[6].exists())

    def test_explicit_enrollment_refreshes_only_candidate_and_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,_=fixture(Path(d));before=tree(a[0]);raw=tree(a[0]/'raw-controls')
            save=a[0]/'runs/save.bin';save.parent.mkdir();save.write_bytes(b'user save')
            r=run(a,p);self.assertEqual(r['enrolled_resource_count'],1);self.assertEqual(r['status'],'committed')
            self.assertEqual(tree(a[0]/'raw-controls'),raw);self.assertEqual(save.read_bytes(),b'user save')
            self.assertEqual((a[0]/'candidate/Game/added.txt').read_bytes(),b'translated extra subtitle')
            report=json.loads((a[0]/'PREPARED.json').read_bytes())
            self.assertEqual([r['resource_count'] for r in report['phases']],[3,3]);self.assertFalse(report['game_started'])
            for row in r['files']:self.assertEqual((a[6]/row['path']).read_bytes(),before[Path(row['path'])])

    def test_wrong_plan_hash_before_backup(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,_=fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'SHA256'):update.refresh(*a,enrollment=p,enrollment_sha256='0'*64)
            self.assertFalse(a[6].exists())

    def test_stale_identity_or_wrong_disc_rejected(self):
        for k,v in [('schema_version',True),('kind','implicit'),('prepared_sha256','0'*64),('old_packet_manifest_sha256','0'*64),
                    ('new_packet_manifest_sha256','0'*64),('disc',2),('disc',True),('game_rendering_verified',True)]:
            with tempfile.TemporaryDirectory() as d:
                _,a,p,plan=fixture(Path(d));plan[k]=v;save_plan(p,plan)
                with self.subTest(k=k),self.assertRaises(ValueError):run(a,p)
                self.assertFalse(a[6].exists())

    def test_partial_extra_duplicate_addition_sets_rejected(self):
        for mode in ['empty','duplicate','foreign','old']:
            with tempfile.TemporaryDirectory() as d:
                _,a,p,plan=fixture(Path(d))
                if mode=='empty':plan['additions']=[]
                if mode=='duplicate':plan['additions']*=2
                if mode=='foreign':plan['additions'][0]['path']='Game/foreign.txt'
                if mode=='old':plan['additions'].append(dict(plan['additions'][0],path='Game/A.dat'))
                save_plan(p,plan)
                with self.subTest(mode=mode),self.assertRaises(ValueError):run(a,p)
                self.assertFalse(a[6].exists())

    def test_original_size_or_hash_mismatch_rejected(self):
        for k,v in [('original_size',True),('original_size',1),('original_sha256','0'*64)]:
            with tempfile.TemporaryDirectory() as d:
                _,a,p,plan=fixture(Path(d));plan['additions'][0][k]=v;save_plan(p,plan)
                with self.assertRaisesRegex(ValueError,'original identity'):run(a,p)

    def test_live_extra_modified_or_missing_rejected(self):
        for phase in ('candidate','raw-controls'):
            for missing in (True,False):
                with tempfile.TemporaryDirectory() as d:
                    _,a,p,_=fixture(Path(d));target=a[0]/phase/'Game/added.txt'
                    if missing:target.unlink()
                    else:target.write_bytes(b'user edit')
                    with self.assertRaisesRegex(ValueError,'not original'):run(a,p)
                    self.assertFalse(a[6].exists())

    def test_raw_extra_translated_even_with_matching_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,plan=fixture(Path(d));target=a[2]/'raw-controls/Game/added.txt';target.write_bytes(b'translated raw')
            m=json.loads((a[2]/'manifest.json').read_bytes());m['member_sha256']['raw-controls/Game/added.txt']=sha(target.read_bytes())
            m['resources'][-1].update(raw_sha256=sha(target.read_bytes()),raw_size=target.stat().st_size)
            data=json.dumps(m).encode();(a[2]/'manifest.json').write_bytes(data);a[3]=sha(data)
            plan['new_packet_manifest_sha256']=a[3];save_plan(p,plan)
            with self.assertRaisesRegex(ValueError,'not original'):run(a,p)

    def test_interrupted_write_restores_complete_existing_tree(self):
        for after_replace in (True,False):
            with tempfile.TemporaryDirectory() as d:
                _,a,p,_=fixture(Path(d));before=tree(a[0]);real=update.atomic_write;calls=[]
                def fail_once(path,data):
                    calls.append(path)
                    if len(calls)==2:
                        if after_replace:real(path,data)
                        raise OSError('synthetic interruption')
                    return real(path,data)
                with patch.object(update,'atomic_write',side_effect=fail_once),self.assertRaisesRegex(OSError,'synthetic'):run(a,p)
                self.assertEqual(tree(a[0]),before)
                self.assertEqual(json.loads((a[6]/'REFRESH.json').read_bytes())['status'],'rolled-back')

    def test_final_journal_failure_also_restores_tree(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,_=fixture(Path(d));before=tree(a[0]);real=update.atomic_write;failed=[]
            def fail_once(path,data):
                if path.name=='REFRESH.json' and not failed:failed.append(True);raise OSError('journal failure')
                return real(path,data)
            with patch.object(update,'atomic_write',side_effect=fail_once),self.assertRaisesRegex(OSError,'journal failure'):run(a,p)
            self.assertEqual(tree(a[0]),before)

    def test_xex_changed_during_write_triggers_rollback(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,_=fixture(Path(d));before=tree(a[0]);real=update.atomic_write;changed=[]
            def mutate(path,data):
                result=real(path,data)
                if not changed:changed.append(True);(a[0]/'candidate/default.xex').write_bytes(b'external change')
                return result
            with patch.object(update,'atomic_write',side_effect=mutate),self.assertRaisesRegex(ValueError,'changed during check'):run(a,p)
            for path,data in before.items():
                if path!=Path('candidate/default.xex'):self.assertEqual((a[0]/path).read_bytes(),data)
            self.assertEqual((a[0]/'candidate/default.xex').read_bytes(),b'external change')

    def test_hardlinked_target_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,_=fixture(Path(d));target=a[0]/'candidate/Game/added.txt';link=Path(d)/'outside.txt'
            os.link(target,link)
            with self.assertRaisesRegex(ValueError,'linked refresh target'):run(a,p)
            self.assertFalse(a[6].exists())

    def test_enrollment_requires_hash_and_actual_additions(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,_=fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'trusted SHA256'):update.refresh(*a,enrollment=p)
        with tempfile.TemporaryDirectory() as d:
            _,a=base.RefreshTests().fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'without resource additions'):update.refresh(*a,enrollment=Path(d)/'unused',enrollment_sha256='0'*64)

    def test_legacy_packet_cannot_be_used_for_enrollment(self):
        with tempfile.TemporaryDirectory() as d:
            _,a,p,plan=fixture(Path(d));m=json.loads((a[2]/'manifest.json').read_bytes());m['kind']='offline-font-route-probe'
            data=json.dumps(m).encode();(a[2]/'manifest.json').write_bytes(data);a[3]=sha(data)
            plan['new_packet_manifest_sha256']=a[3];save_plan(p,plan)
            with self.assertRaisesRegex(ValueError,'matching disc comparison'):run(a,p)
