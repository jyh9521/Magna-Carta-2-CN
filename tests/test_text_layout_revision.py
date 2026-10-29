import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import shutil
from unittest.mock import patch

from tools.build_text_layout_revision import run, main, json_bytes
from tools.coalesced import EmbeddedFile, SerializedString, serialize, parse, extract_entries
from tools.build_coalesced import rebuild
from tools.reface_font import sha
from tools.rollback_text_layout_revision import restore


class TextLayoutRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'input'
        self.source.mkdir()
        self.raw = serialize([EmbeddedFile(SerializedString('fixture.int', 'ascii', 0),
            SerializedString('[Fixture]\r\nText=甲乙丙丁。\r\nDynamic=测试%s\r\n', 'utf-16-le', 0))])
        (self.source/'text.int').write_bytes(self.raw)
        self.rows = extract_entries(parse(self.raw), 'text.int')
        self.profile = dict(schema_version=1, kind='metric-text-layout-revision', fonts={},
            consumer_contracts=[], icon_styles={},
            rules=dict(atomic_pairs={'[':']'}, no_line_start='，。！？]', no_line_end='[',
                       repeat_pairs='…—', preferred_break_after='，。！？', natural_break_min_fraction=.7),
            coalesced=dict(resource='text.int', sha256=sha(self.raw), entry_count=2, discs=[1,2],
                source_by_disc=[dict(disc=i,sha256=sha(self.raw),size=len(self.raw)) for i in (1,2)]),
            families=[dict(id='test',entry_ids=[self.rows[0]['id']],width=40,max_lines=3,fonts=['test'])],
            literal_edits=[], reflow_options=[], held_fields=[], subtitles=[])
        self.widths = {ord(c):10 for c in '甲乙丙丁。测试%s'}
        self.addCleanup(patch.stopall)
        patch('tools.build_text_layout_revision.font_metrics', return_value={'test':self.widths}).start()
        patch('tools.build_text_layout_revision.verify_consumers', return_value=dict(packages=0,contracts=0)).start()

    def call(self, output, mode='modified'):
        return run(self.profile, self.source, self.root/'fonts', self.root/'consumers', self.root/output, mode)

    def test_baseline_modified_and_inverse_exact(self):
        before = self.call('baseline', 'baseline')
        self.assertEqual(before['failures'], 1)
        after = self.call('modified')
        self.assertEqual(after['failures'], 0)
        self.assertEqual(after['changed_fields'], 1)
        out = (self.root/'modified/candidate/text.int').read_bytes()
        reverse = json.loads((self.root/'modified/coalesced-rollback-plan.json').read_bytes())
        self.assertEqual(rebuild(out, reverse), self.raw)
        self.assertEqual((self.source/'text.int').read_bytes(), self.raw)
        self.assertEqual(after['resources'][0]['discs'], [1,2])
        self.assertEqual(after['global_explicit_break_scan']['findings'], [])

    def test_unknown_assigned_markup_is_a_failure_not_a_skip(self):
        self.profile['families'][0]['entry_ids'].append(self.rows[1]['id'])
        report = self.call('unknown')
        self.assertEqual(report['failures'], 1)
        self.assertEqual(len(report['unsupported']), 1)
        self.assertEqual(report['held_fields'], [])

    def test_exact_explicit_hold_has_separate_accounting(self):
        self.profile['families'][0]['entry_ids'].append(self.rows[1]['id'])
        self.profile['held_fields'] = [dict(id=self.rows[1]['id'],
            source_sha256=sha(self.rows[1]['source'].encode()), reason='Unknown dynamic replacement width.')]
        report = self.call('held')
        self.assertEqual(report['failures'], 0)
        self.assertEqual(report['layout_checked'], 1)
        self.assertEqual(len(report['held_fields']), 1)
        output_rows = extract_entries(parse((self.root/'held/candidate/text.int').read_bytes()),'text.int')
        self.assertEqual(output_rows[1]['source'], self.rows[1]['source'])

    def test_hold_source_drift_is_rejected(self):
        self.profile['held_fields'] = [dict(id=self.rows[0]['id'],source_sha256='0'*64,reason='Expected.')]
        with self.assertRaisesRegex(ValueError,'held field identity'): self.call('bad')

    def test_source_drift_is_rejected(self):
        self.profile['coalesced']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source identity'): self.call('bad')

    def test_output_cannot_alias_any_source_tree(self):
        for out in (self.source/'nested', self.root/'fonts/nested', self.root/'consumers/nested'):
            with self.subTest(out=out), self.assertRaisesRegex(ValueError,'disjoint'):
                run(self.profile,self.source,self.root/'fonts',self.root/'consumers',out)

    def test_cli_unknown_is_nonzero(self):
        self.profile['families'][0]['entry_ids'].append(self.rows[1]['id'])
        p = self.root/'profile.json';p.write_bytes(json_bytes(self.profile))
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(['--profile',str(p),'--text-root',str(self.source),'--font-root',str(self.root/'fonts'),
                '--consumer-root',str(self.root/'consumers'),'--output',str(self.root/'cli')])
        self.assertEqual(result,1)

    def test_rollback_copy_restores_original_and_retains_candidate(self):
        self.call('modified')
        target = self.root/'rollback-copy';shutil.copytree(self.root/'modified/candidate',target)
        result = restore(self.root/'modified',self.source,target)
        self.assertTrue(result['retained_candidate_unchanged'])
        self.assertEqual((target/'text.int').read_bytes(),self.raw)
        self.assertNotEqual((self.root/'modified/candidate/text.int').read_bytes(),self.raw)

    def test_rollback_unknown_bytes_rejected_before_writes(self):
        self.call('modified')
        target = self.root/'rollback-copy';shutil.copytree(self.root/'modified/candidate',target)
        (target/'text.int').write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError,'identity mismatch'): restore(self.root/'modified',self.source,target)
        self.assertEqual((target/'text.int').read_bytes(),b'unknown')

    def test_rollback_cannot_restore_retained_candidate_itself(self):
        self.call('modified')
        with self.assertRaisesRegex(ValueError,'disjoint'): restore(self.root/'modified',self.source,self.root/'modified/candidate')


if __name__ == '__main__': unittest.main()
