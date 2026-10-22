"""Self-authored byte inventories only. No game assets or optional dependencies."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import verify_resource_phase as phase


class Fixture:
    def __init__(self,root):
        self.packet=root/'packet';self.game=root/'resources';self.output=root/'report.json';self.data={}
        rows=[];members={}
        for name in ['Game/A.dat','Game/TOC.txt']:
            for kind in phase.PHASES:
                raw=(kind+':'+name).encode();self.data[kind,name]=raw
                path=self.packet/kind/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);members[kind+'/'+name]=phase.sha(raw)
            rows.append(dict(path=name,original_sha256=members['controls/'+name],original_size=len(self.data['controls',name]),
                candidate_sha256=members['candidate/'+name],candidate_size=len(self.data['candidate',name])))
            target=self.game/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(self.data['candidate',name])
        self.manifest=dict(schema_version=1,kind='offline-font-route-probe',game_rendering_verified=False,deployment_performed=False,
            raw_package_outputs=True,resources=rows,member_sha256=members);self.refresh()

    def refresh(self):
        raw=json.dumps(self.manifest).encode();(self.packet/'manifest.json').write_bytes(raw);self.hash=phase.sha(raw)

    def args(self):return ['--packet-root',str(self.packet),'--manifest-sha256',self.hash,'--resource-root',str(self.game),'--phase','candidate','--output',str(self.output)]
    def run(self,kind='candidate'):return phase.inspect(self.packet,self.hash,self.game,kind)[0]


class ResourcePhaseTests(unittest.TestCase):
    def test_exact_candidate_bytes_and_immutable_roots(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));before={str(p):p.read_bytes() for root in [f.packet,f.game] for p in root.rglob('*') if p.is_file()};r=f.run()
            self.assertTrue(r['all_resources_match']);self.assertEqual(r['matched_count'],2)
            for path,raw in before.items():self.assertEqual(Path(path).read_bytes(),raw)

    def test_all_three_phases_require_their_own_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d))
            for kind in phase.PHASES:
                for row in f.manifest['resources']:(f.game/row['path']).write_bytes(f.data[kind,row['path']])
                self.assertTrue(f.run(kind)['all_resources_match'])

    def test_wrong_phase_and_wrong_toc_are_distinct_mismatches(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));self.assertEqual(f.run('controls')['matched_count'],0)
            (f.game/'Game/TOC.txt').write_bytes(f.data['raw-controls','Game/TOC.txt']);r=f.run()
            self.assertEqual(r['matched_count'],1);self.assertEqual(r['resources'][1]['status'],'mismatch')

    def test_missing_file_is_not_a_match(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));(f.game/'Game/A.dat').unlink();r=f.run()
            self.assertEqual(r['resources'][0]['status'],'missing');self.assertIsNone(r['resources'][0]['actual']);self.assertFalse(r['all_resources_match'])

    def test_same_size_changed_byte_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));p=f.game/'Game/A.dat';raw=p.read_bytes();p.write_bytes(bytes([raw[0]^1])+raw[1:]);self.assertEqual(f.run()['matched_count'],1)

    def test_runtime_and_write_claims_are_always_false(self):
        with tempfile.TemporaryDirectory() as d:
            r=Fixture(Path(d)).run()
            for key in ['game_rendering_verified','game_started','resource_writes_performed','deployment_performed']:self.assertIs(r[key],False)
            self.assertIn('not execution',r['scope'])

    def test_unrelated_files_are_not_enumerated_or_read(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));config=f.game/'user-config.toml';config.write_bytes(b'unchanged configuration')
            with patch.object(Path,'rglob',side_effect=AssertionError('no recursive root scan')):self.assertTrue(f.run()['all_resources_match'])
            self.assertEqual(config.read_bytes(),b'unchanged configuration')

    def test_manifest_hash_and_member_hash_guards_are_independent(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));f.hash='0'*64
            with self.assertRaisesRegex(ValueError,'manifest SHA256'):f.run()
            f.refresh();(f.packet/'candidate/Game/A.dat').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'phase member SHA256'):f.run()

    def test_duplicate_json_and_nonfinite_rejected_even_with_new_hash(self):
        for raw in [b'{"schema_version":1,"schema_version":1}',b'{"a":NaN}']:
            with tempfile.TemporaryDirectory() as d:
                f=Fixture(Path(d));(f.packet/'manifest.json').write_bytes(raw);f.hash=phase.sha(raw)
                with self.assertRaises(ValueError):f.run()

    def test_path_escape_duplicate_case_and_row_contract_rejected(self):
        changes=[lambda m:m['resources'][0].update(path='../outside'),lambda m:m['resources'].append(copy.deepcopy(m['resources'][0])),
            lambda m:m['resources'][0].update(candidate_size=True),lambda m:m['resources'][0].update(candidate_sha256='0'*64)]
        for change in changes:
            with tempfile.TemporaryDirectory() as d:
                f=Fixture(Path(d));change(f.manifest);f.refresh()
                with self.assertRaises(ValueError):f.run()

    def test_phase_absence_invalid_schema_and_inventory_bounds(self):
        changes=[lambda m:m.update(raw_package_outputs=False),lambda m:m.update(schema_version=True),lambda m:m.update(resources=[]),
            lambda m:m.update(game_rendering_verified=0),lambda m:m.update(deployment_performed=True)]
        for change in changes:
            with tempfile.TemporaryDirectory() as d:
                f=Fixture(Path(d));change(f.manifest);f.refresh()
                with self.assertRaises(ValueError):f.run('raw-controls')

    def test_directory_in_place_of_file_and_size_bound(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));p=f.game/'Game/A.dat';p.unlink();p.mkdir()
            with self.assertRaisesRegex(ValueError,'bounded regular'):f.run()
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d))
            with patch.object(phase,'MAX_FILE',1),self.assertRaises(ValueError):f.run()

    def test_changed_and_newly_appeared_files_reject_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));_,snap=phase.inspect(f.packet,f.hash,f.game,'candidate');(f.game/'Game/A.dat').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed during'):phase.stable(snap)
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));p=f.game/'Game/A.dat';p.unlink();_,snap=phase.inspect(f.packet,f.hash,f.game,'candidate');p.write_bytes(b'new')
            with self.assertRaisesRegex(ValueError,'changed during'):phase.stable(snap)

    def test_cli_zero_and_one_write_readonly_reports(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));self.assertEqual(phase.main(f.args()),0);self.assertTrue(json.loads(f.output.read_bytes())['all_resources_match'])
            f.output=Path(d)/'mismatch.json';(f.game/'Game/A.dat').write_bytes(b'changed');self.assertEqual(phase.main(f.args()),1)
            self.assertFalse(json.loads(f.output.read_bytes())['all_resources_match'])

    def test_cli_does_not_overwrite_or_publish_inside_input_roots(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));f.output.write_bytes(b'retain');self.assertEqual(phase.main(f.args()),2);self.assertEqual(f.output.read_bytes(),b'retain')
            for root in [f.packet,f.game]:
                f.output=root/'new.json';self.assertEqual(phase.main(f.args()),2);self.assertFalse(f.output.exists())

    def test_cli_postpublication_mutation_removes_own_report_only(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));original=phase.stable;calls=0
            def changed(rows):
                nonlocal calls
                calls+=1
                if calls==2:(f.game/'Game/A.dat').write_bytes(b'changed')
                original(rows)
            with patch.object(phase,'stable',side_effect=changed):self.assertEqual(phase.main(f.args()),2)
            self.assertFalse(f.output.exists())

    def test_cli_preserves_externally_changed_output_on_error(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d));original=phase.stable;calls=0
            def changed(rows):
                nonlocal calls
                calls+=1
                if calls==2:
                    f.output.write_bytes(b'external output');raise ValueError('external mutation')
                original(rows)
            with patch.object(phase,'stable',side_effect=changed):self.assertEqual(phase.main(f.args()),2)
            self.assertEqual(f.output.read_bytes(),b'external output')


if __name__=='__main__':unittest.main()

class ExpandedResourceInventoryTests(unittest.TestCase):
    def test_five_hundred_twelve_resources_and_next_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            f=Fixture(Path(d))
            for i in range(510):
                name=f'Extra/{i}.dat';data=str(i).encode();h=phase.sha(data)
                for kind in phase.PHASES:
                    p=f.packet/kind/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);f.manifest['member_sha256'][kind+'/'+name]=h
                p=f.game/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                f.manifest['resources'].append(dict(path=name,original_size=len(data),original_sha256=h,candidate_size=len(data),candidate_sha256=h))
            f.refresh();self.assertEqual(f.run()['matched_count'],512)
            f.manifest['resources'].append(dict(f.manifest['resources'][-1]));f.refresh()
            with self.assertRaisesRegex(ValueError,'inventory'):f.run()
