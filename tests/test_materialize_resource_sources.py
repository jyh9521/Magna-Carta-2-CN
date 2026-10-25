import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.materialize_resource_sources import materialize

class MaterializeSourceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.r=Path(self.temp.name);self.data=b'abc';self.sha=hashlib.sha256(self.data).hexdigest();self.d=dict(schema_version=1,kind='locked-resource-source-subset',resources=[dict(resource='Game/one.bin',destination='build/originals/one.bin',discs=[1],expected_sha256=self.sha)]);self.inv={1:dict(image='original-disc',entries=[dict(path='Game/one.bin',directory=False,sha256=self.sha,offset=0,size=3)])}
 def reader(self,path):
  data=self.data
  class Reader:
   def read(self,offset,size):return data[offset:offset+size]
  return Reader()
 def test_copy_hash_reopen_and_idempotent_reuse(self):
  a=materialize(self.d,self.r,self.inv,self.reader);self.assertEqual(a['materialized'],1);self.assertEqual((self.r/'build/originals/one.bin').read_bytes(),b'abc');b=materialize(self.d,self.r,self.inv,self.reader);self.assertEqual(b['materialized'],0);self.assertEqual(b['verified_existing'],1);self.assertFalse(b['full_game_copy_created'])
 def test_different_existing_original_never_overwritten(self):
  p=self.r/'build/originals/one.bin';p.parent.mkdir(parents=True);p.write_bytes(b'old')
  with self.assertRaisesRegex(ValueError,'never overwrite'):materialize(self.d,self.r,self.inv,self.reader)
  self.assertEqual(p.read_bytes(),b'old')
 def test_no_cross_disc_fallback_or_unknown_resource_version(self):
  with self.assertRaises(ValueError):materialize(self.d,self.r,{2:self.inv[1]},self.reader)
  self.inv[1]['entries'][0]['sha256']='0'*64
  with self.assertRaises(ValueError):materialize(self.d,self.r,self.inv,self.reader)
 def test_actual_source_bytes_not_trusted_from_inventory(self):
  self.data=b'bad'
  with self.assertRaisesRegex(ValueError,'actual original'):materialize(self.d,self.r,self.inv,self.reader)
  self.assertFalse((self.r/'build/originals/one.bin').exists())
 def test_destination_escape_is_rejected(self):
  self.d['resources'][0]['destination']='../escape.bin'
  with self.assertRaises(ValueError):materialize(self.d,self.r,self.inv,self.reader)
 def test_duplicate_destinations_and_inventory_paths_fail(self):
  self.d['resources']*=2
  with self.assertRaises(ValueError):materialize(self.d,self.r,self.inv,self.reader)
  self.inv[1]['entries']*=2
  with self.assertRaises(ValueError):materialize(self.d,self.r,self.inv,self.reader)
if __name__=='__main__':unittest.main()
