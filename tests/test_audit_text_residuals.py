"""Self-authored source/target resources; no original game text fixtures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.audit_text_residuals import digest,locked,main,paired_rows,policy_tables,prefix_matches,screen
from tools.coalesced import serialize,extract_entries,parse
from test_coalesced import fixture


def policy():
    return dict(schema_version=1,kind='text-residual-screen-policy',
        script_ranges=dict(source_script=[[0xac00,0xd7a3]]),known_dispositions=[],
        prefix_rules=[dict(id='prefix',literal='Quest',document_suffix='demo.int',case_sensitive=False)])


class ResidualScreenTests(unittest.TestCase):
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
                classified_residuals=0,prefix_gaps=1,unclassified=1))
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

