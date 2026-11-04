"""Synthetic sampler fixtures; no game image or graphics runtime is required."""
import copy
import json
from pathlib import Path
import struct
import tomllib
import unittest

from tools.runtime_patch import apply_image,digest,patch_toml
from tools.inspect_sampler_patch import inspect


def fixture():
    b=bytearray(256)
    struct.pack_into('>I',b,16,0x38a00004)
    struct.pack_into('>I',b,32,0x2f040010)
    table=[0,0,2,2,3,3,3,4,4,4,4,4,4,5,5,5,5]
    struct.pack_into('>17I',b,64,*table)
    b=bytes(b)
    plan=dict(schema_version=1,kind='ppc-runtime-patch',image_base=0x1000,
        image_sha256=digest(b),title_name='Synthetic',title_id='12345678',
        module_hash='0123456789ABCDEF',name='Sampler test',
        windows=[dict(address=0x1010,size=4,sha256=digest(b[16:20])),
                 dict(address=0x1040,size=68,sha256=digest(b[64:132]))],
        writes=[dict(address=0x1010,expected='38a00004',replacement='38a00010')],
        sampler_probe=dict(argument_address=0x1010,loop_compare_address=0x1020,
                           table_address=0x1040,table_entries=17))
    return b,plan


class SamplerPatchTests(unittest.TestCase):
    def test_checked_in_korean_candidate_is_disabled_and_relocated(self):
        root=Path(__file__).resolve().parents[1]
        p=json.loads((root/'references/probes/mc2-sampler-anisotropy.json').read_bytes())
        t=tomllib.loads(patch_toml(p).decode())
        self.assertEqual(t['title_id'],'4E4D0811')
        self.assertEqual(t['hash'],'0FAA852250B131D1')
        self.assertIs(t['patch'][0]['is_enabled'],False)
        self.assertEqual(t['patch'][0]['be32'],[dict(address=0x8244a2b0,value=0x38a00010)])
        self.assertEqual(p['writes'][0]['expected'],'38a00004')
        self.assertEqual(len(p['windows']),3)
        self.assertEqual(len(p['supported_disc_sources']),2)

    def test_baseline_modified_and_restored_static_states(self):
        b,p=fixture();m=apply_image(b,p)
        self.assertEqual(inspect(b,p)['max_ratio'],'4x')
        self.assertEqual(inspect(m,p)['max_ratio'],'16x')
        self.assertEqual(inspect(m,p)['model_cases'],256)
        self.assertEqual(inspect(apply_image(m,p,True),p),inspect(b,p))
        self.assertEqual([i for i,(a,c) in enumerate(zip(b,m)) if a!=c],[19])

    def test_unrelated_image_mutation_is_rejected(self):
        b,p=fixture()
        for data in (b,apply_image(b,p)):
            changed=bytearray(data);changed[-1]^=1
            with self.assertRaises(ValueError):inspect(bytes(changed),p)

    def test_argument_opcode_table_bounds_and_loop_guards(self):
        b,p=fixture()
        for key,value in [('argument_address',0x1020),('table_address',0x1044),
                          ('loop_compare_address',0x1010),('table_entries',18),
                          ('argument_address',0x0ffc),('argument_address',0x1011)]:
            q=copy.deepcopy(p);q['sampler_probe'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):inspect(b,q)
        q=copy.deepcopy(p);q['writes'][0]['replacement']='38a00008'
        with self.assertRaisesRegex(ValueError,'unreviewed'):inspect(apply_image(b,q),q)

    def test_default_patch_metadata_stays_backward_compatible(self):
        _,p=fixture();t=tomllib.loads(patch_toml(p).decode())['patch'][0]
        self.assertTrue(t['is_enabled']);self.assertNotIn('author',t)
        self.assertEqual(t['desc'],'Subtract the line origin from forced intra-token wrap extents')

    def test_candidate_metadata_is_disabled_and_attributed(self):
        _,p=fixture();p.update(description='Offline "candidate"\nNo game QA',is_enabled=False,author='Original author')
        t=tomllib.loads(patch_toml(p).decode())['patch'][0]
        self.assertIs(t['is_enabled'],False)
        self.assertEqual(t['desc'],p['description']);self.assertEqual(t['author'],p['author'])

    def test_invalid_metadata_is_rejected(self):
        for key,value in [('is_enabled','false'),('is_enabled',0),('description',''),
                          ('description',False),('author',42),('author','')]:
            _,p=fixture();p[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):patch_toml(p)


if __name__=='__main__':unittest.main()
