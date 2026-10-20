import copy,json,tempfile,unittest
from pathlib import Path
from test_translation_variant_audit import fixture
from tools.coalesced import parse,extract_entries
from tools.audit_line_context import audit,digest,canonical,lock,atoms,main


def setup():
    b,p=fixture('[Scene]\nA=one\\ntwo\nB=A button 3\n[Menu]\nA=X one\\nY two\n')
    p['entries'][0].update(translation='draft',line_break_policy=dict(source_count=1,target_count=0))
    p['entries'][1]['translation']='A 键 3';p['entries'][2]['translation']='X 是\\nY 否'
    rows=extract_entries(parse(b),'fixture')
    profile=dict(schema_version=1,kind='source-locked-context-observations',resource='fixture',input_sha256=digest(b),
      plan_canonical_sha256=canonical(p),human_finalized=False,runtime_layout_approved=False,
      scopes=[dict(document='fixture.int',section='Scene',complete_section=True,reason='Complete synthetic scene'),
              dict(document='fixture.int',section='Menu',complete_section=True,reason='Menu control')],
      entries=[lock(r,p['entries'][i]['translation']) for i,r in enumerate(rows)],
      protected_breaks=[dict(id=rows[2]['id'],reason='Separate choices')])
    return b,p,profile


class LineContextAuditTests(unittest.TestCase):
    def test_context_observation_never_approves_runtime_or_edits(self):
        b,p,r=setup();before=copy.deepcopy(p);a=audit(b,p);m=audit(b,p,r)
        self.assertEqual((a['pending_context_policies'],m['pending_context_policies']),(1,0))
        self.assertEqual(m['pending_runtime_layout_policies'],1);self.assertFalse(m['runtime_layout_approved'])
        self.assertEqual(m['context_entries'],3);self.assertEqual(m['translation_edits'],0);self.assertEqual(p,before)
        self.assertNotIn('one\\ntwo',json.dumps(m));self.assertEqual(m['context'][0]['next_id'],p['entries'][1]['id'])

    def test_plan_source_hash_and_approval_state_drift_rejected(self):
        for k,v in [('schema_version',True),('input_sha256','0'*64),('plan_canonical_sha256','0'*64),('human_finalized',True),('runtime_layout_approved',True)]:
            b,p,r=setup();r[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):audit(b,p,r)

    def test_exact_membership_order_and_draft_hash_required(self):
        for mode in ('missing','duplicate','order','hash'):
            b,p,r=setup()
            if mode=='missing':r['entries'].pop()
            if mode=='duplicate':r['entries'].append(r['entries'][0])
            if mode=='order':r['entries'].reverse()
            if mode=='hash':r['entries'][0]['translation_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'membership/order/hash'):audit(b,p,r)

    def test_complete_section_cannot_be_silently_narrowed(self):
        b,p,r=setup();r['scopes'][0]['keys']=['A']
        with self.assertRaisesRegex(ValueError,'complete section'):audit(b,p,r)
        b,p,r=setup();r['scopes'].append(r['scopes'][0])
        with self.assertRaisesRegex(ValueError,'overlapping'):audit(b,p,r)

    def test_filtered_keys_must_all_exist(self):
        b,p,r=setup();r['scopes'][0].update(complete_section=False,keys=['A','absent'])
        with self.assertRaisesRegex(ValueError,'stale context'):audit(b,p,r)

    def test_unplanned_original_not_counted_as_reviewed_draft(self):
        b,p,r=setup();p['entries'].pop(1);r['plan_canonical_sha256']=canonical(p)
        with self.assertRaisesRegex(ValueError,'unplanned original'):audit(b,p,r)

    def test_key_and_numeric_changes_not_silently_accepted(self):
        b,p,r=setup();p['entries'][1]['translation']='X 键 4';r['plan_canonical_sha256']=canonical(p)
        rows=extract_entries(parse(b),'fixture');r['entries'][1]=lock(rows[1],p['entries'][1]['translation'])
        with self.assertRaisesRegex(ValueError,'key/numeric'):audit(b,p,r)

    def test_known_escape_cannot_hide_adjacent_button(self):
        self.assertEqual(atoms('KR\\nX단추 3'),['X','3']);self.assertEqual(atoms('nX word'),[])
        self.assertEqual(atoms('<Styles:Font_0>X<Styles:/> 3'),['X','3'])

    def test_functional_menu_break_removal_rejected_even_if_layout_policy_exists(self):
        b,p,r=setup();p['entries'][2].update(translation='X 是 Y 否',line_break_policy=dict(source_count=1,target_count=0))
        r['plan_canonical_sha256']=canonical(p);rows=extract_entries(parse(b),'fixture');r['entries'][2]=lock(rows[2],p['entries'][2]['translation'])
        with self.assertRaisesRegex(ValueError,'functional break'):audit(b,p,r)

    def test_cli_refuses_existing_output(self):
        b,p,r=setup()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'source').write_bytes(b);(root/'plan').write_text(json.dumps(p));out=root/'report';out.write_bytes(b'user file')
            self.assertEqual(main(['--source',str(root/'source'),'--plan',str(root/'plan'),'--output',str(out)]),2)
            self.assertEqual(out.read_bytes(),b'user file')
