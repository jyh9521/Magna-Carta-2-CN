"""Consumer-window regressions must not confuse an atlas cell with its sampler."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.texture_sampling_probe import evaluate, sampled_bounds


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT/'locales/zh-Hans/texture-overlays/gameplay-consumer-contracts-v7.json'


class SamplingProbeTests(unittest.TestCase):
    def test_bounds_use_source_and_consumer_offsets_without_resizing(self):
        pixels = bytearray(120*24*4)
        for y in range(5,10):
            for x in range(20,30):pixels[(y*120+x)*4+3] = 255
        label = dict(rect=[124,28,120,24])
        self.assertEqual(sampled_bounds(label,bytes(pixels),[122,27,121,26]),[22,6,32,11])
        self.assertEqual(sampled_bounds(label,bytes(pixels),[124,28,120,24]),[20,5,30,10])

    def test_invalid_and_empty_sample_inputs_are_rejected(self):
        label = dict(rect=[0,0,4,4]); pixels = bytes([255]*64)
        for window in ([0,0,0,4],[0,0,4,-1],[0,0,float('nan'),4],[0,0,4],None):
            with self.subTest(window=window), self.assertRaises(ValueError):
                sampled_bounds(label,pixels,window)
        with self.assertRaisesRegex(ValueError,'pixel length'):
            sampled_bounds(label,bytes(63),[0,0,4,4])
        with self.assertRaisesRegex(ValueError,'empty glyph'):
            sampled_bounds(label,bytes(64),[0,0,4,4])

    def fixture(self,root):
        from test_texture_render_windows import owned_font
        data=owned_font();(root/'fixture.ttf').write_bytes(data)
        font=dict(path='fixture.ttf',sha256=hashlib.sha256(data).hexdigest())
        appearance=dict(kind='source-style-v1',ink_box=[2,5,60,18],align='center',
                        gradient=[[0,[255]*4],[1000,[255]*4]],outline=[0]*4,
                        outline_width=0,glow=[0]*4,glow_radius=0,shadow=[0]*4,
                        shadow_offset=[0,0],shadow_radius=0,italic=0,tracking=0,
                        weight=0,motion=0)
        a=dict(id='a',text='AB',rect=[0,0,64,32],font_size=20,appearance=appearance)
        b=copy.deepcopy(a);b.update(id='b',rect=[124,0,64,32]);b['appearance']['ink_box'][0]=0
        plan=dict(font=font,labels=[a,b])
        contracts=dict(schema_version=1,kind='texture-consumer-probe-contracts',
                       game_rendering_verified=False,cases=[dict(
                           name='paired sample',mode='registration',samples=[
                               dict(label='a',window=[0,0,64,32]),
                               dict(label='b',window=[122,0,64,32])])])
        return plan,contracts

    def test_actual_geometry_failure_is_reported_not_silently_recentered(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan,contracts=self.fixture(root)
            frozen=copy.deepcopy(plan)
            self.assertTrue(evaluate(plan,contracts,root)['passed'])
            self.assertEqual(plan,frozen)
            plan['labels'][1]['rect'][0]+=2
            result=evaluate(plan,contracts,root)
            self.assertFalse(result['passed'])
            a,b=result['checks'][0]['measured']
            self.assertEqual(b[0]-a[0],2)
            self.assertFalse(result['game_started'])

    def test_font_hash_and_project_root_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan,contracts=self.fixture(root)
            plan['font']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                evaluate(plan,contracts,root)
            plan['font']['path']='../fixture.ttf'
            with self.assertRaisesRegex(ValueError,'outside project'):
                evaluate(plan,contracts,root)

    def test_unknown_contract_and_duplicate_names_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan,contracts=self.fixture(root)
            contracts['cases'].append(copy.deepcopy(contracts['cases'][0]))
            with self.assertRaisesRegex(ValueError,'duplicate consumer'):
                evaluate(plan,contracts,root)
            contracts['cases']=contracts['cases'][:1];contracts['cases'][0]['mode']='guess'
            with self.assertRaisesRegex(ValueError,'unknown consumer'):
                evaluate(plan,contracts,root)


class GameplayConsumerContractTests(unittest.TestCase):
    def test_original_identity_and_field_evidence_are_versioned(self):
        contract=json.loads(CONTRACTS.read_text(encoding='utf-8'))
        self.assertEqual(contract['source_profile'],'UE3 446/25')
        self.assertEqual(len(contract['source_packages']),4)
        self.assertTrue(all(len(p['sha256'])==64 and p['size']>0 for p in contract['source_packages']))
        self.assertEqual(len(contract['cases']),64)
        cases={case['name']:case for case in contract['cases']}
        self.assertEqual(len(cases),64)
        added={
            'back title: pulse registration': ('registration', ['ui_menu_tex_back_0_normal','ui_menu_tex_back_0_hover']),
            'back title: shadow registration': ('same-field', ['ui_menu_tex_back_0_normal','ui_menu_tex_back_0_hover']),
            'Reverse: paired glyph shape': ('equal-core', ['img_ui_name_jpn_176_0','img_ui_name_jpn_177_0']),
        }
        for name,(mode,labels) in added.items():
            self.assertIn(name,cases)
            self.assertEqual(cases[name]['mode'],mode)
            self.assertEqual(cases[name].get('labels',[s['label'] for s in cases[name].get('samples',[])]),labels)
        self.assertEqual([s['window'] for s in cases['back title: pulse registration']['samples']],
                         [[0,0,121,30],[122,0,121,30]])
        self.assertEqual(cases['back title: shadow registration']['field'],['appearance','shadow_offset'])
        self.assertTrue(all(c['evidence'] for c in contract['cases']))
        self.assertFalse(contract['coordinate_defaults']['missing_values_assumed_zero'])
        self.assertEqual(contract['coordinate_defaults']['missing_default_slots'],[])
        self.assertTrue(all('deduction' in c['evidence']['classification']
                            for c in contract['cases'] if c['name'].endswith('destination sampling')))

    def test_native_consumer_contracts_reject_v6_and_accept_v7(self):
        contract=json.loads(CONTRACTS.read_text(encoding='utf-8'))
        plans=[json.loads((ROOT/('locales/zh-Hans/texture-overlays/'+name)).read_text(encoding='utf-8'))
               for name in ['ui-labels-reviewed-v6.json','ui-labels-gameplay-v7.json']]
        used=set()
        for case in contract['cases']:
            if 'label' in case:used.add(case['label'])
            used.update(case.get('labels',[]))
            if 'sample' in case:used.add(case['sample']['label'])
            used.update(x['label'] for x in case.get('samples',[]))
        for plan in plans:
            for label in plan['labels']:
                if label['id'] in used and not (ROOT/label.get('font',plan['font'])['path']).is_file():
                    self.skipTest('Hash-locked source fonts must be materialized for native consumer checks')
        baseline,modified=[evaluate(plan,contract,ROOT) for plan in plans]
        self.assertFalse(baseline['passed'])
        self.assertLess(baseline['passed_checks'],10)
        self.assertTrue(modified['passed'],json.dumps([r for r in modified['checks'] if not r['passed']]))
        self.assertEqual(modified['passed_checks'],64)


if __name__=='__main__':unittest.main()
