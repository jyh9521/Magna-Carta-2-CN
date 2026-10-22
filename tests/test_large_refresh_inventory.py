import json,tempfile,unittest
from pathlib import Path
from tools import refresh_oneclick_probe as update,restore_probe_refresh as undo
from tools.verify_resource_phase import sha
import test_refresh_enrollment as fixture
class LargeRefreshInventoryTests(unittest.TestCase):
 def test_full_512_packet_enrollment_and_515_journal_isolated_restore(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);_,a,p,plan=fixture.fixture(root);m=json.loads((a[2]/'manifest.json').read_bytes())
   for i in range(509):
    name=f'Game/large{i}.dat';original=b'owned original '+str(i).encode();candidate=b'owned localized '+str(i).encode()
    for phase in ['controls','raw-controls','candidate']:
     data=candidate if phase=='candidate' else original;f=a[2]/phase/name;f.write_bytes(data);m['member_sha256'][phase+'/'+name]=sha(data)
    for phase in ['candidate','raw-controls']:(a[0]/phase/name).write_bytes(original)
    m['resources'].append(dict(path=name,original_size=len(original),original_sha256=sha(original),candidate_size=len(candidate),candidate_sha256=sha(candidate),raw_size=len(original),raw_sha256=sha(original)));plan['additions'].append(dict(path=name,original_size=len(original),original_sha256=sha(original)))
   # Change the second old resource as well, reaching exactly all512 candidate files +3 metadata.
   row=m['resources'][1];data=b'owned changed second control';(a[2]/'candidate'/row['path']).write_bytes(data);row.update(candidate_size=len(data),candidate_sha256=sha(data));m['member_sha256']['candidate/'+row['path']]=sha(data)
   b=json.dumps(m).encode();(a[2]/'manifest.json').write_bytes(b);a[3]=sha(b);plan['new_packet_manifest_sha256']=a[3];fixture.save_plan(p,plan);before=fixture.tree(a[0]);result=fixture.run(a,p);self.assertEqual(result['changed_files'],515);self.assertEqual(result['enrolled_resource_count'],510)
   h=sha((a[6]/'REFRESH.json').read_bytes());r,_,_=undo.audit(a[0],a[6],h);self.assertTrue(r['restorable']);undo.restore(a[0],a[6],h,root/'receipt.json');self.assertEqual(fixture.tree(a[0]),before)
 def test_513_enrollment_entries_fail_before_backup(self):
  with tempfile.TemporaryDirectory() as td:
   _,a,p,plan=fixture.fixture(Path(td));plan['additions']*=513;fixture.save_plan(p,plan)
   with self.assertRaisesRegex(ValueError,'bounded'):fixture.run(a,p)
   self.assertFalse(a[6].exists())
 def test_516_journal_entries_fail_before_any_restore(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);_,a,p,_=fixture.fixture(root);fixture.run(a,p);j=a[6]/'REFRESH.json';m=json.loads(j.read_bytes());m['files']=[m['files'][0]]*516;m['changed_files']=516;j.write_bytes(json.dumps(m).encode());before=fixture.tree(a[0])
   with self.assertRaisesRegex(ValueError,'inventory outside bound'):undo.restore(a[0],a[6],sha(j.read_bytes()),root/'receipt.json')
   self.assertEqual(fixture.tree(a[0]),before)
if __name__=='__main__':unittest.main()
