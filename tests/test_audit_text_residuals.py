"""Self-authored source/target resources; no original game text fixtures."""
import copy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.audit_text_residuals import digest,locked,main,paired_rows,policy_tables,prefix_matches,screen
from tools.coalesced import EmbeddedFile,SerializedString,serialize,extract_entries,parse
from test_coalesced import fixture


def policy():
    return dict(schema_version=1,kind='text-residual-screen-policy',
        script_ranges=dict(source_script=[[0xac00,0xd7a3]]),known_dispositions=[],
        prefix_rules=[dict(id='prefix',literal='Quest',document_suffix='demo.int',case_sensitive=False)])


class ResidualScreenTests(unittest.TestCase):
    def opaque_inputs(self, root):
        files=fixture('[Demo]\nText=own\n');old=files[0]
        payload=b'[Demo]\nText=own\xa9\n'
        files[0]=EmbeddedFile(old.path,SerializedString(payload.decode('latin1'),'opaque-8bit',0))
        raw=serialize(files);(root/'a.bin').write_bytes(raw);(root/'b.bin').write_bytes(raw)
        inputs=dict(schema_version=1,kind='effective-text-screen-inputs',resources=[dict(
            resource='fixture.int',kind='coalesced',role='primary',discs=[1,2],
            original=dict(file='a.bin',sha256=digest(raw)),effective=dict(file='b.bin',sha256=digest(raw)))])
        p=policy();p['document_decoders']=[dict(resource='fixture.int',embedded_path=old.path.text,
            discs=[1,2],payload_sha256=digest(payload),decoder='unsigned-byte-to-u16',evidence='authored-native-loop')]
        return inputs,p,raw

    def test_bound_decoder_adds_real_fields_without_changing_storage_or_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs,p,raw=self.opaque_inputs(root)
            baseline=screen(inputs,policy(),root);self.assertEqual(baseline['summary']['opaque_primary_documents'],1)
            result=screen(inputs,p,root);self.assertEqual(result['summary']['opaque_primary_documents'],0)
            self.assertEqual(result['summary']['primary_fields'],baseline['summary']['primary_fields']+1)
            self.assertEqual(result['resources'][0]['source_bound_document_decoders'],p['document_decoders'])
            self.assertEqual((root/'a.bin').read_bytes(),raw);self.assertEqual((root/'b.bin').read_bytes(),raw)
            self.assertEqual(parse(raw)[0].content.encoding,'opaque-8bit')

    def test_bound_decoder_rejects_drift_partial_absent_unknown_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs,p,raw=self.opaque_inputs(root)
            for changes in (dict(payload_sha256='0'*64),dict(discs=[1]),dict(discs=[True]),
                            dict(embedded_path='missing'),dict(resource='missing'),dict(decoder='cp949'),
                            dict(evidence=''),dict(payload_sha256=True)):
                bad=copy.deepcopy(p);bad['document_decoders'][0].update(changes)
                with self.subTest(changes=changes),self.assertRaises(ValueError):screen(inputs,bad,root)
            bad=copy.deepcopy(p);bad['document_decoders']*=2
            with self.assertRaisesRegex(ValueError,'Duplicate'):screen(inputs,bad,root)
            plain=serialize(fixture('[Demo]\nText=own\n'));(root/'b.bin').write_bytes(plain)
            inputs['resources'][0]['effective']['sha256']=digest(plain)
            with self.assertRaisesRegex(ValueError,'opaque storage'):screen(inputs,p,root)

    def inputs(self,root,before='[Demo]\nText=원본\nPrefix=Quest%s: 自制\n',after=None):
        after=before if after is None else after
        a=serialize(fixture(before));b=serialize(fixture(after))
        (root/'a.bin').write_bytes(a);(root/'b.bin').write_bytes(b)
        return dict(schema_version=1,kind='effective-text-screen-inputs',resources=[dict(
            resource='fixture.int',kind='coalesced',role='primary',discs=[1,2],
            original=dict(file='a.bin',sha256=digest(a)),effective=dict(file='b.bin',sha256=digest(b)))])

    def test_source_script_and_case_insensitive_prompt_prefix_are_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            r=screen(self.inputs(Path(temp)),policy(),temp)
            self.assertEqual(r['summary'],dict(primary_fields=2,subtitle_cues=0,script_residuals=1,
                classified_residuals=0,prefix_gaps=1,unclassified=1,pending=0,excluded=0,
                confirmed_player_gaps=0,unresolved=2,opaque_primary_documents=0))
            self.assertFalse(r['game_rendering_verified'])
            self.assertFalse(r['complete_language_coverage_claimed'])

    def test_classifying_a_hold_does_not_remove_confirmed_gaps_or_mutate_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root);p=policy();raw=(root/'b.bin').read_bytes()
            row=extract_entries(parse(raw),'fixture.int')[0]
            p['known_dispositions']=[dict(resource='fixture.int',id=row['id'],discs=[1,2],value_sha256=digest(row['source'].encode()),
                classification='composition-unverified',status='pending',evidence='self-authored-test')]
            r=screen(inputs,p,temp);self.assertEqual(r['summary']['unclassified'],0)
            self.assertEqual(r['summary']['classified_residuals'],1);self.assertEqual(r['summary']['prefix_gaps'],1)
            self.assertEqual((root/'b.bin').read_bytes(),raw)
            self.assertEqual(r['findings'][0]['status'],'pending')
            self.assertEqual(r['findings'][1]['status'],'confirmed-resource-gap')

    def test_known_disposition_drift_and_absence_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root);p=policy();row=extract_entries(parse((root/'a.bin').read_bytes()),'fixture.int')[0]
            decision=dict(resource='fixture.int',id=row['id'],discs=[1,2],value_sha256='0'*64,classification='hold',status='pending',evidence='fixture')
            p['known_dispositions']=[decision]
            with self.assertRaisesRegex(ValueError,'source drift'):screen(inputs,p,temp)
            decision['id']='not-present'
            with self.assertRaisesRegex(ValueError,'absent'):screen(inputs,p,temp)

    def test_alternate_locale_is_counted_without_becoming_a_primary_runtime_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            inputs=self.inputs(Path(temp));inputs['resources'][0]['role']='alternate-locale'
            r=screen(inputs,policy(),temp);self.assertEqual(r['resources'][0]['script_fields'],dict(source_script=1))
            self.assertEqual(r['findings'],[]);self.assertEqual(r['summary']['primary_fields'],0)

    def test_prefix_cases_do_not_match_longer_machine_identifiers(self):
        rule=policy()['prefix_rules'][0]
        for text in ['Quest: sample','QUEST%s: sample','  quest: sample','Quest']:
            with self.subTest(text=text):self.assertTrue(prefix_matches(text,rule))
        for text in ['MC2Quest.Title','QuestName','Quest_001','Quest02','not Quest: sample']:
            with self.subTest(text=text):self.assertFalse(prefix_matches(text,rule))

    def test_a_confirmed_prefix_gap_also_classifies_the_same_fields_script_residual(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);result=screen(self.inputs(root,'[Demo]\nText=Quest: 원본\n'),policy(),root)
            self.assertEqual(result['summary']['script_residuals'],1)
            self.assertEqual(result['summary']['classified_residuals'],1)
            self.assertEqual(result['summary']['prefix_gaps'],1)
            self.assertEqual(result['summary']['unclassified'],0)

    def test_no_field_identity_or_subtitle_timing_changes_are_hidden(self):
        a=serialize(fixture('[Demo]\nText=source\n'));b=serialize(fixture('[Demo]\nOther=target\n'))
        with self.assertRaisesRegex(ValueError,'identities'):paired_rows(a,b,'fixture.int','coalesced')
        cue=lambda end:b'\xff\xfe'+('1\r\n<SYNC Start=0><P Class=KRCC>自制<SYNC Start='+str(end)+'><P Class=KRCC>&nbsp;\r\n').encode('utf-16-le')
        with self.assertRaisesRegex(ValueError,'timing'):paired_rows(cue(100),cue(101),'movie.txt','timed-cues')
        rows,opaque=paired_rows(cue(100),cue(100),'movie.txt','timed-cues');self.assertEqual(len(rows),1)
        self.assertEqual(opaque,0)

    def test_invalid_range_boolean_and_duplicate_dispositions_fail(self):
        with self.assertRaises(ValueError):policy_tables([])
        for spans in [[[True,10]],[[30,20]],[[-1,20]],[[0,0x110000]]]:
            p=policy();p['script_ranges']={'x':spans}
            with self.subTest(spans=spans),self.assertRaises(ValueError):policy_tables(p)
        p=policy();p['schema_version']=True
        with self.assertRaises(ValueError):policy_tables(p)
        row=dict(resource='x',id='y',discs=[1],value_sha256='0'*64,classification='held',status='pending',evidence='fixture')
        p=policy();p['known_dispositions']=[row,row]
        with self.assertRaises(ValueError):policy_tables(p)

    def test_duplicate_memberships_and_escaping_files_are_rejected(self):
        with self.assertRaises(ValueError):screen([],policy(),'.')
        with tempfile.TemporaryDirectory() as temp:
            inputs=self.inputs(Path(temp));inputs['resources'][0]['discs']=[True]
            with self.assertRaises(ValueError):screen(inputs,policy(),temp)
            inputs['resources'][0]['discs']=[1];inputs['resources'][0]['effective']['file']='../escape.bin'
            with self.assertRaises(ValueError):screen(inputs,policy(),temp)

    def test_shared_reader_is_bounded_and_source_hash_locked(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'data';p.write_bytes(b'abc')
            self.assertEqual(locked(p,digest(b'abc'),3),b'abc')
            for sha,limit in [(digest(b'abc'),2),('0'*64,3)]:
                with self.assertRaises(ValueError):locked(p,sha,limit)

    def test_same_path_on_distinct_discs_is_not_merged_or_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root);a=inputs['resources'][0];a['discs']=[1]
            b=copy.deepcopy(a);b['discs']=[2];b['role']='configuration';inputs['resources'].append(b)
            result=screen(inputs,policy(),root)
            self.assertEqual([r['discs'] for r in result['resources']],[[1],[2]])
            self.assertEqual(result['summary']['script_residuals'],1)

    def test_disposition_never_leaks_from_one_disc_to_another(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root);r=extract_entries(parse((root/'a.bin').read_bytes()),'fixture.int')[0]
            p=policy();p['known_dispositions']=[dict(resource='fixture.int',id=r['id'],discs=[1],
                value_sha256=digest(r['source'].encode()),classification='hold',status='pending',evidence='fixture')]
            with self.assertRaisesRegex(ValueError,'Partially classified'):screen(inputs,p,root)

    def test_cli_is_red_capable_and_never_overwrites_a_prior_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root);p=policy()
            for name,value in [('inputs.json',inputs),('policy.json',p)]:
                (root/name).write_text(json.dumps(value),encoding='utf8')
            args=['--inputs',str(root/'inputs.json'),'--inputs-sha256',digest((root/'inputs.json').read_bytes()),
                '--policy',str(root/'policy.json'),'--policy-sha256',digest((root/'policy.json').read_bytes()),
                '--project-root',str(root),'--output',str(root/'report.json'),'--require-classified']
            self.assertEqual(main(args),1);self.assertTrue((root/'report.json').is_file())
            before=(root/'report.json').read_bytes();self.assertEqual(main(args),2)
            self.assertEqual((root/'report.json').read_bytes(),before)

    def disposition(self,root,status='pending'):
        row=extract_entries(parse((root/'a.bin').read_bytes()),'fixture.int')[0]
        result=dict(resource='fixture.int',id=row['id'],discs=[1,2],
            value_sha256=digest(row['source'].encode()),classification='self-authored-review',
            status=status,evidence='self-authored-test')
        if status=='confirmed-player-gap':
            result['runtime_observation']=dict(kind='user-supplied-screenshot',
                source_path='external/self-authored-capture.png',sha256='a'*64)
        return result

    def test_known_pending_is_unresolved_even_when_every_residual_is_classified(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root,'[Demo]\nText=원본\n');p=policy()
            p['known_dispositions']=[self.disposition(root)]
            result=screen(inputs,p,root)
            self.assertEqual(result['summary']['unclassified'],0)
            self.assertEqual(result['summary']['pending'],1)
            self.assertEqual(result['summary']['excluded'],0)
            self.assertEqual(result['summary']['unresolved'],1)

    def test_observed_player_gap_keeps_external_evidence_without_claiming_image_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root,'[Demo]\nText=원본\n');p=policy()
            d=self.disposition(root,'confirmed-player-gap');p['known_dispositions']=[d]
            original_open=Path.open
            def guarded_open(path,*args,**kwargs):
                self.assertNotEqual(path.as_posix(),d['runtime_observation']['source_path'])
                return original_open(path,*args,**kwargs)
            with patch.object(Path,'open',guarded_open):result=screen(inputs,p,root)
            finding=result['findings'][0]
            self.assertEqual(result['summary']['confirmed_player_gaps'],1)
            self.assertEqual(result['summary']['unresolved'],1)
            self.assertTrue(finding['runtime_display_observed'])
            self.assertEqual(finding['runtime_observation'],d['runtime_observation'])
            self.assertFalse(finding['runtime_observation_semantics_verified'])
            self.assertFalse(result['game_rendering_verified'])
            self.assertFalse(result['game_started'])

    def test_confirmed_gap_requires_valid_observation_metadata_and_disc_evidence_agreement(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root,'[Demo]\nText=원본\n')
            d=self.disposition(root,'confirmed-player-gap')
            variants=[None,{},dict(d['runtime_observation'],sha256='0'*63),
                dict(d['runtime_observation'],source_path=''),
                dict(d['runtime_observation'],source_path='bad\x00path'),
                dict(d['runtime_observation'],kind='')]
            for observation in variants:
                p=policy();bad=copy.deepcopy(d)
                if observation is None:bad.pop('runtime_observation')
                else:bad['runtime_observation']=observation
                p['known_dispositions']=[bad]
                with self.subTest(observation=observation),self.assertRaises(ValueError):screen(inputs,p,root)
            a=copy.deepcopy(d);b=copy.deepcopy(d);a['discs']=[1];b['discs']=[2]
            b['runtime_observation']['sha256']='b'*64;p=policy();p['known_dispositions']=[a,b]
            with self.assertRaisesRegex(ValueError,'Conflicting grouped dispositions'):screen(inputs,p,root)

    def test_unresolved_counts_unique_findings_not_script_and_prefix_twice(self):
        with tempfile.TemporaryDirectory() as temp:
            result=screen(self.inputs(Path(temp),'[Demo]\nText=Quest: 원본\n'),policy(),temp)
            self.assertEqual(result['summary']['script_residuals'],1)
            self.assertEqual(result['summary']['prefix_gaps'],1)
            self.assertEqual(result['summary']['unresolved'],1)

    def test_explicit_observed_gap_is_not_hidden_by_script_ranges_or_prefix_overlap(self):
        for value,prefix in [('self-authored foreign text',0),('Quest: 원본',1)]:
            with self.subTest(value=value),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);inputs=self.inputs(root,'[Demo]\nText='+value+'\n');p=policy()
                p['known_dispositions']=[self.disposition(root,'confirmed-player-gap')]
                result=screen(inputs,p,root)
                self.assertEqual(result['summary']['confirmed_player_gaps'],1)
                self.assertEqual(result['summary']['prefix_gaps'],prefix)
                self.assertEqual(result['summary']['unresolved'],1)

    def test_observation_metadata_does_not_silently_promote_a_pending_decision(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root,'[Demo]\nText=원본\n');p=policy()
            d=self.disposition(root,'confirmed-player-gap');d['status']='pending'
            p['known_dispositions']=[d];result=screen(inputs,p,root)
            self.assertEqual(result['summary']['pending'],1)
            self.assertEqual(result['summary']['confirmed_player_gaps'],0)
            self.assertEqual(result['summary']['unresolved'],1)

    def test_legacy_runtime_display_flag_is_boolean_and_matches_observation(self):
        cases=[(False,False,True),(True,True,True),(False,True,False),(True,False,False),
               (None,False,False),(0,False,False),(1,True,False),
               ('false',False,False),([],False,False),({},False,False)]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=self.inputs(root,'[Demo]\nText=원본\n')
            for flag,observed,valid in cases:
                with self.subTest(flag=flag,observed=observed):
                    d=self.disposition(root,'confirmed-player-gap' if observed else 'pending')
                    d['runtime_display_observed']=flag;p=policy();p['known_dispositions']=[d]
                    if valid:
                        result=screen(inputs,p,root)
                        self.assertIs(result['findings'][0]['runtime_display_observed'],observed)
                    else:
                        with self.assertRaisesRegex(ValueError,'Runtime display flag'):
                            screen(inputs,p,root)

    def test_no_script_dispositions_still_report_pending_or_preserved_status(self):
        for status in ('pending','excluded'):
            with self.subTest(status=status),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);inputs=self.inputs(root,'[Demo]\nText=ASCII source\n');p=policy()
                p['known_dispositions']=[self.disposition(root,status)];result=screen(inputs,p,root)
                self.assertEqual(result['summary']['script_residuals'],0)
                self.assertEqual(result['summary'][status],1)
                self.assertEqual(result['summary']['unresolved'],int(status=='pending'))
                self.assertEqual(result['findings'][0]['status'],status)

    def test_opaque_primary_document_blocks_resolution_not_legacy_classification(self):
        for role,flag,expected in [('primary','--require-resolved',1),
                ('primary','--require-classified',0),('alternate-locale','--require-resolved',0)]:
            with self.subTest(role=role,flag=flag),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);inputs=self.inputs(root);raw=serialize(fixture('\xa9','opaque-8bit'))
                for phase,name in [('original','a.bin'),('effective','b.bin')]:
                    (root/name).write_bytes(raw);inputs['resources'][0][phase]['sha256']=digest(raw)
                inputs['resources'][0]['role']=role;p=policy();result=screen(inputs,p,root)
                self.assertEqual(result['summary']['unresolved'],0)
                self.assertEqual(result['summary']['opaque_primary_documents'],int(role=='primary'))
                for name,value in [('inputs.json',inputs),('policy.json',p)]:
                    (root/name).write_text(json.dumps(value),encoding='utf8')
                args=['--inputs',str(root/'inputs.json'),'--inputs-sha256',digest((root/'inputs.json').read_bytes()),
                    '--policy',str(root/'policy.json'),'--policy-sha256',digest((root/'policy.json').read_bytes()),
                    '--project-root',str(root),'--output',str(root/'report.json'),flag]
                output=StringIO()
                with redirect_stdout(output):self.assertEqual(main(args),expected)
                verdict='CLASSIFIED' if flag=='--require-classified' else 'UNRESOLVED' if expected else 'RESOLVED'
                self.assertIn('RESULT='+verdict,output.getvalue())

    def test_resolution_gate_exit_codes_and_classification_compatibility(self):
        cases=[('unclassified',True,1),('pending',True,1),('confirmed-player-gap',True,1),
               ('prefix',True,1),('excluded',True,0),('clean',True,0),
               ('pending',False,0),('confirmed-player-gap',False,0)]
        for status,resolution_gate,expected in cases:
            with self.subTest(status=status,resolution_gate=resolution_gate),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);text='Quest: 自制' if status=='prefix' else '自制' if status=='clean' else '원본'
                inputs=self.inputs(root,'[Demo]\nText='+text+'\n');p=policy()
                if status in ('pending','excluded','confirmed-player-gap'):
                    p['known_dispositions']=[self.disposition(root,status)]
                for name,value in [('inputs.json',inputs),('policy.json',p)]:
                    (root/name).write_text(json.dumps(value),encoding='utf8')
                args=['--inputs',str(root/'inputs.json'),'--inputs-sha256',digest((root/'inputs.json').read_bytes()),
                    '--policy',str(root/'policy.json'),'--policy-sha256',digest((root/'policy.json').read_bytes()),
                    '--project-root',str(root),'--output',str(root/'report.json'),
                    '--require-resolved' if resolution_gate else '--require-classified']
                output=StringIO()
                with redirect_stdout(output):self.assertEqual(main(args),expected)
                if resolution_gate:
                    self.assertIn('RESULT='+('UNRESOLVED' if expected else 'RESOLVED'),output.getvalue())
                else:self.assertIn('RESULT=CLASSIFIED',output.getvalue())

