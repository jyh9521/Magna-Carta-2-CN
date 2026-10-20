"""Synthetic, source-free contracts for context-sensitive variant dispositions."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.audit_translation_variants import audit, digest, main
from tools.coalesced import EmbeddedFile, SerializedString, extract_entries, parse, serialize


def fixture(text='[Scene]\nA=ack\nB=ack\nC=other\n'):
    data = serialize([EmbeddedFile(SerializedString('fixture.int', 'ascii', 0),
                                   SerializedString(text, 'utf-16-le', 0))])
    rows = extract_entries(parse(data), 'fixture')
    plan = dict(schema_version=1, resource='fixture', input_sha256=digest(data),
                source_mode='sha256-utf8', entries=[dict(id=r['id'],
                    source_sha256=digest(r['source'].encode()), translation=f'draft{i}')
                    for i, r in enumerate(rows)])
    return data, plan


def decision(data, plan):
    group = audit(data, plan)['groups'][0]
    return dict(schema_version=1, resource='fixture', input_sha256=digest(data), groups=[
        dict(group, disposition='context-variant-retained', reason='Different display roles')])


class TranslationVariantAuditTests(unittest.TestCase):
    def test_grouping_keeps_ids_and_no_source_text(self):
        data, plan = fixture(); r = audit(data, plan)
        self.assertEqual((len(r['groups']), r['pending_groups']), (1, 1))
        self.assertEqual(len(r['groups'][0]['entries']), 2)
        self.assertNotIn('source', json.dumps(r['groups'][0]['entries']))

    def test_sections_are_not_blindly_merged(self):
        data, plan = fixture('[First]\nA=ack\n[Second]\nB=ack\n')
        self.assertEqual(audit(data, plan)['groups'], [])

    def test_disposition_preserves_plan_and_source(self):
        data, plan = fixture(); before = copy.deepcopy(plan)
        r = audit(data, plan, decision(data, plan))
        self.assertEqual((r['pending_groups'], r['context_variant_groups']), (0, 1))
        self.assertEqual(plan, before); self.assertEqual(serialize(parse(data)), data)
        self.assertIn('no reviewer/status upgrade', r['policy'])

    def test_source_envelope_mismatch_and_bool_schema_rejected(self):
        data, plan = fixture(); p = decision(data, plan)
        for key, value in [('input_sha256', '0' * 64), ('resource', 'other'), ('schema_version', True)]:
            bad = copy.deepcopy(p); bad[key] = value
            with self.assertRaises(ValueError): audit(data, plan, bad)

    def test_stale_draft_hash_rejected(self):
        data, plan = fixture(); p = decision(data, plan)
        p['groups'][0]['entries'][0]['translation_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'membership/hash'): audit(data, plan, p)

    def test_group_membership_and_duplicates_rejected(self):
        data, plan = fixture(); p = decision(data, plan)
        p['groups'][0]['entries'].pop()
        with self.assertRaises(ValueError): audit(data, plan, p)
        p = decision(data, plan); p['groups'].append(copy.deepcopy(p['groups'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate or stale'): audit(data, plan, p)

    def test_human_final_upgrade_not_a_disposition(self):
        data, plan = fixture(); p = decision(data, plan)
        p['groups'][0]['disposition'] = 'human-final'
        with self.assertRaisesRegex(ValueError, 'invalid context'): audit(data, plan, p)

    def test_existing_output_cannot_replace_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, plan = fixture(); source = Path(tmp) / 'source'; source.write_bytes(data)
            p = Path(tmp) / 'plan.json'; p.write_text(json.dumps(plan), encoding='utf8')
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(['--source', str(source), '--plan', str(p), '--output', str(source)])
            self.assertEqual(code, 1); self.assertEqual(source.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
