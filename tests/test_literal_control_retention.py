"""Synthetic retention evidence never converts an unknown control into coverage."""
import json
from pathlib import Path
import tempfile
import unittest
from tools import audit_text_font_coverage as c
from tools.audit_literal_control_retention import main
from test_text_font_coverage import fixture


def setup(source='source\t', translation='A\t'):
    raw, plan, fonts = fixture(translation, source)
    e = plan['entries'][0]
    sequence, segments = c.literal_control_shape(e['source'])
    row = dict(id=e['id'], source_sha256=c.digest(e['source'].encode()),
        translation_sha256=c.digest(e['translation'].encode()),
        control_sequence=sequence, segment_nonempty=segments)
    ledger = dict(schema_version=1, kind='source-locked-literal-control-retention',
        resource=plan['resource'], input_sha256=c.digest(raw),
        changes_canonical_sha256=c.digest(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()),entries=[row])
    return raw,plan,ledger,fonts


class LiteralControlRetentionTests(unittest.TestCase):
    def test_exact_trailing_tab_is_retention_not_coverage(self):
        raw,p,l,fonts=setup();r=c.audit_control_retention(raw,p,l)
        self.assertEqual(r['retained_literal_codepoints'],[9])
        self.assertTrue(r['exact_control_sequences_and_segment_shapes_retained'])
        self.assertFalse(r['font_coverage_verified'])
        self.assertFalse(r['unknown_control_syntax_resolved'])
        self.assertFalse(r['game_rendering_verified'])
        self.assertFalse(c.audit(raw,p,fonts)['all_supplied_fonts_cover_literals'])
        self.assertNotIn('source\t',json.dumps(r))

    def test_multiple_controls_keep_order_and_empty_segments(self):
        raw,p,l,_=setup('s\t\u200b','A\t\u200b')
        r=c.audit_control_retention(raw,p,l)
        self.assertEqual(r['entries'][0]['control_sequence'],[9,0x200b])
        self.assertEqual(r['entries'][0]['segment_nonempty'],[True,False,False])

    def test_added_removed_moved_reordered_controls_fail(self):
        for old,new in [('s\t','A'),('s','A\t'),('s\t','\tA'),('s\t\u200b','A\u200b\t'),('s\t','A\t\t')]:
            raw,p,l,_=setup(old,new)
            with self.subTest(old=repr(old),new=repr(new)),self.assertRaisesRegex(ValueError,'sequence or segment'):c.audit_control_retention(raw,p,l)

    def test_known_tokens_are_not_new_literal_controls(self):
        self.assertEqual(c.literal_control_shape('A\\n{0}$n\\t'),([], [True]))

    def test_ledger_top_identity_drift_fails(self):
        for key,value in [('schema_version',True),('kind','skip-controls'),('resource','elsewhere'),('input_sha256','0'*64),('changes_canonical_sha256','0'*64)]:
            raw,p,l,_=setup();l[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_source_translation_or_sequence_drift_fails(self):
        for key,value in [('source_sha256','0'*64),('translation_sha256','0'*64),('control_sequence',[0x200b]),('segment_nonempty',[False,True])]:
            raw,p,l,_=setup();l['entries'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_invalid_scalar_and_shape_types_fail(self):
        for seq in ([True],[65],[-1],[0xd800],[0x110000],[],[9]*4097):
            raw,p,l,_=setup();l['entries'][0]['control_sequence']=seq
            with self.subTest(seq=str(seq[:3])),self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)
        raw,p,l,_=setup();l['entries'][0]['segment_nonempty']=[1,0]
        with self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_duplicate_unrelated_and_empty_ledgers_fail(self):
        raw,p,l,_=setup();l['entries']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):c.audit_control_retention(raw,p,l)
        raw,p,l,_=setup();l['entries'][0]['id']='unrelated'
        with self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_unrelated_extra_row_and_oversize_ledger_fail(self):
        raw,p,l,_=setup();l['entries'].append(dict(l['entries'][0],id='extra'))
        with self.assertRaisesRegex(ValueError,'unrelated'):c.audit_control_retention(raw,p,l)
        raw,p,l,_=setup();l['entries']*=16385
        with self.assertRaisesRegex(ValueError,'entry count'):c.audit_control_retention(raw,p,l)
        raw,p,l,_=setup();l['entries']=[]
        with self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_extra_field_is_not_an_approval_switch(self):
        raw,p,l,_=setup();l['entries'][0]['allow']=True
        with self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_wrong_original_or_stale_plan_fails(self):
        raw,p,l,_=setup()
        with self.assertRaises(ValueError):c.audit_control_retention(raw+b'junk',p,l)
        p['entries'][0]['translation']='changed\t'
        with self.assertRaises(ValueError):c.audit_control_retention(raw,p,l)

    def test_cli_report_exit_is_not_coverage_and_existing_output_rejected(self):
        raw,p,l,_=setup()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'source').write_bytes(raw)
            (root/'plan').write_text(json.dumps(p),encoding='utf8');(root/'ledger').write_text(json.dumps(l),encoding='utf8')
            args=['--coalesced',str(root/'source'),'--plan',str(root/'plan'),'--ledger',str(root/'ledger'),'--output',str(root/'report')]
            self.assertEqual(main(args),0)
            self.assertFalse(json.loads((root/'report').read_bytes())['font_coverage_verified'])
            self.assertEqual(main(args),2)
