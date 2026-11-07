"""Synthetic disc reader exercises text-only preparation without a game image."""
import copy
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from tools.audit_text_residuals import digest,screen
from tools.coalesced import serialize
from tools.prepare_text_screen_inputs import prepare
from test_coalesced import fixture
from test_audit_text_residuals import policy


class PrepareTextScreenTests(unittest.TestCase):
    def setup_inputs(self,root,second_same=True):
        a=serialize(fixture('[Demo]\nText=원본\n'));b=serialize(fixture('[Demo]\nText=另一个原文\n'))
        images=[];inventories={};payloads={}
        for d,raw in [(1,a),(2,a if second_same else b)]:
            image=root/f'disc{d}.bin';image.write_bytes(raw);images.append(dict(iso=str(image),sha256=digest(raw),resources=[]))
            row=dict(path='Texts/demo.int',offset=0,size=len(raw),sha256=digest(raw),directory=False)
            inventories[d]=dict(image_size=len(raw),sha256=digest(raw),entries=[row]);payloads[str(image.resolve())]=row
        def factory(path):
            path=Path(path).resolve();return SimpleNamespace(
                inventory=lambda:[payloads[str(path)]],read=lambda off,size:path.read_bytes()[off:off+size])
        selectors=dict(schema_version=1,kind='text-screen-resource-selectors',selectors=[
            dict(pattern='Texts/*',kind='coalesced',role='primary')])
        return dict(discs=images),selectors,inventories,factory

    def test_identical_memberships_share_only_hash_verified_text_work(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);r,s,i,f=self.setup_inputs(root);out=root/'prepared';v=prepare(r,s,i,root,out,f)
            self.assertEqual(len(v['resources']),1);self.assertEqual(v['resources'][0]['discs'],[1,2])
            self.assertEqual(v['resource_memberships'],2);self.assertFalse(v['full_game_copy_created'])
            result=screen(v,policy(),root);self.assertEqual(result['summary']['script_residuals'],1)
            self.assertEqual(len(list(out.rglob('*.int'))),1)

    def test_same_member_path_with_distinct_disc_bytes_is_never_merged(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);r,s,i,f=self.setup_inputs(root,False);v=prepare(r,s,i,root,root/'out',f)
            self.assertEqual(len(v['resources']),2);self.assertEqual([x['discs'] for x in v['resources']],[[1],[2]])
            self.assertNotEqual(v['resources'][0]['original']['sha256'],v['resources'][1]['original']['sha256'])

    def test_effective_recipe_is_independently_read_not_assumed_shared(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);r,s,i,f=self.setup_inputs(root);target=root/'current.bin'
            raw=serialize(fixture('[Demo]\nText=已译\n'));target.write_bytes(raw)
            r['discs'][0]['resources']=[dict(path='Texts/demo.int',file=str(target),sha256=digest(raw))]
            v=prepare(r,s,i,root,root/'out',f);self.assertEqual(len(v['resources']),2)
            self.assertEqual(target.read_bytes(),raw)
            self.assertEqual(v['resources'][0]['effective']['sha256'],digest(raw))

    def test_bad_hash_directory_and_ambiguous_selector_fail_before_output(self):
        for variant in ('image','resource','directory','selector'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);r,s,i,f=self.setup_inputs(root);out=root/'out'
                if variant=='image':r['discs'][0]['sha256']='0'*64
                if variant=='resource':i[1]['entries'][0]['sha256']='0'*64
                if variant=='directory':i[1]['entries'][0]['offset']=1
                if variant=='selector':s['selectors']*=2
                # Freeze the actual fake directory separately from the altered declaration.
                if variant=='directory':
                    actual=copy.deepcopy(i[1]['entries']);actual[0]['offset']=0
                    f=lambda path:SimpleNamespace(inventory=lambda:actual,read=lambda a,b:b'')
                with self.assertRaises(ValueError):prepare(r,s,i,root,out,f)
                self.assertFalse(out.exists())

    def test_existing_output_and_unknown_locale_role_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);r,s,i,f=self.setup_inputs(root);out=root/'out';out.mkdir()
            with self.assertRaises(ValueError):prepare(r,s,i,root,out,f)
            s['selectors'][0].pop('role');s['selectors'][0]['role_by_suffix']={'.other':'primary'}
            with self.assertRaises(ValueError):prepare(r,s,i,root,root/'other',f)
            self.assertFalse((root/'other').exists())
            s['selectors'][0]['role_by_suffix']=None
            with self.assertRaises(ValueError):prepare(r,s,i,root,root/'other',f)
