import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools import prepare_translation_workspace as w
from tools.coalesced import EmbeddedFile, SerializedString, serialize, parse, extract_entries


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = serialize([EmbeddedFile(SerializedString('Game.int', 'ascii', 0),
            SerializedString('[Menu]\r\nA=shop {0}\r\nB=shop {0}\r\nCode=42\r\n', 'utf-16-le', 0))])
        for disc in (1, 2):
            (self.root / f'disc{disc}').write_bytes(self.data)
        self.rows = extract_entries(parse(self.data), 'Game/Coalesced.int')
        self.profile = dict(schema_version=1, sources=[dict(disc=d, path=f'disc{d}',
            resource='Game/Coalesced.int', sha256=w.digest(self.data), role='translation') for d in (1, 2)],
            domains={'Game':'ui'})
        self.plan = dict(schema_version=1, source_mode='sha256-utf8', resource='Game/Coalesced.int',
            input_sha256=w.digest(self.data), entries=[dict(id=self.rows[0]['id'],
                source_sha256=w.digest(self.rows[0]['source'].encode()), translation='商店 {0}')])
        self.review = dict(status='draft', entries=[dict(id=self.rows[0]['id'], text_kind='menu')])
        self.terms = dict(terms=[dict(id='shop', source='shop', resource='Game/Coalesced.int',
            source_string_id=self.rows[0]['id'], review_status='candidate')])
        self.workflow = dict(schema_version=1, primary_resource='Game/Coalesced.int',
            extraction_profile=self.lock('extraction.json', self.profile),
            style_rules=self.lock('style.json', {}), terms=self.lock('terms.json', self.terms),
            batches=[dict(plan=self.lock('plan.json', self.plan), review=self.lock('review.json', self.review))])

    def lock(self, path, value):
        raw = (json.dumps(value, ensure_ascii=False) + '\n').encode()
        (self.root / path).write_bytes(raw)
        return dict(path=path, sha256=w.digest(raw))

    def prepare(self):
        return w.prepare(self.root, self.workflow, self.root / 'output')

    def test_shared_discs_distinct_ids_and_draft_overlay(self):
        report = self.prepare()
        self.assertEqual((report['unique_entries'], report['physical_disc_entries']), (3, 6))
        self.assertEqual(report['groups'][0]['discs'], [1, 2])
        self.assertEqual(report['groups'][0]['queues'], {'translated-draft':1, 'translation-candidate':2})
        self.assertEqual(report['terms_reviewed'], 0)
        catalog = json.loads(next((self.root/'output/work').rglob('*.json')).read_bytes())
        self.assertEqual(catalog['entries'][1]['translation'], '')  # identical wording is not an ID merge
        original = json.loads((self.root/'output/source'/report['groups'][0]['catalogs'][0]['path']).read_bytes())
        self.assertEqual(original['entries'][0]['translation'], '')
        hits = json.loads((self.root/'output/term-concordance.json').read_bytes())['entries'][0]
        self.assertEqual(len(hits['substring_ids']), 2)
        self.assertEqual((self.root/'disc1').read_bytes(), self.data)
        self.assertEqual((self.root/'disc2').read_bytes(), self.data)

    def test_no_overwrite(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'new'):
            self.prepare()

    def test_different_container_hashes_never_share_work(self):
        other=self.data.replace('42'.encode('utf-16-le'),'43'.encode('utf-16-le'))
        (self.root/'disc2').write_bytes(other)
        self.profile['sources'][1]['sha256']=w.digest(other)
        self.workflow['extraction_profile']=self.lock('extraction.json',self.profile)
        report=self.prepare()
        self.assertEqual((report['unique_entries'],len(report['groups'])),(6,2))
        self.assertEqual([g['discs'] for g in report['groups']],[[1],[2]])
        self.assertEqual(report['groups'][1]['queues'].get('translated-draft',0),0)

    def test_alternate_resource_is_not_auto_translated(self):
        self.profile['sources'][1]['resource']='Game/Coalesced.jpn'
        self.workflow['extraction_profile']=self.lock('extraction.json',self.profile)
        report=self.prepare()
        self.assertEqual(report['groups'][1]['queues'],{'alternate-resource-review':3})

    def test_editor_documents_remain_reference_not_deleted(self):
        self.profile['domains']['Game']='editor'
        self.workflow['extraction_profile']=self.lock('extraction.json',self.profile)
        report=self.prepare()
        self.assertEqual(report['groups'][0]['queues'],{'editor-reference':2,'translated-draft':1})

    def test_stale_dependency_fails_without_output(self):
        (self.root/'plan.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'dependency SHA256'):
            self.prepare()
        self.assertFalse((self.root/'output').exists())

    def test_bad_binary_hash_fails_without_output(self):
        (self.root/'disc2').write_bytes(self.data + b'x')
        with self.assertRaisesRegex(ValueError, 'source SHA256'):
            self.prepare()
        self.assertFalse((self.root/'output').exists())

    def test_protected_marker_mismatch_fails_without_output(self):
        self.plan['entries'][0]['translation'] = '商店'
        self.workflow['batches'][0]['plan'] = self.lock('plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'token'):
            self.prepare()
        self.assertFalse((self.root/'output').exists())

    def test_review_exact_ids_required(self):
        self.review['entries'].append(dict(id='other', text_kind='menu'))
        self.workflow['batches'][0]['review'] = self.lock('review.json', self.review)
        with self.assertRaisesRegex(ValueError, 'review IDs'):
            self.prepare()

    def test_overlapping_batches_never_last_writer_wins(self):
        self.workflow['batches'] *= 2
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.prepare()

    def test_stale_value_hash_rejected(self):
        self.plan['entries'][0]['source_sha256'] = '0'*64
        self.workflow['batches'][0]['plan'] = self.lock('plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'source value'):
            self.prepare()

    def test_bad_term_source_id_rejected(self):
        self.terms['terms'][0]['source_string_id'] = 'missing'
        self.workflow['terms'] = self.lock('terms.json', self.terms)
        with self.assertRaisesRegex(ValueError, 'term source ID'):
            self.prepare()

    def test_primary_resource_must_exist(self):
        self.workflow['primary_resource'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'primary resource'):
            self.prepare()

    def test_source_equal_translation_rejected(self):
        self.plan['entries'][0]['translation'] = self.rows[0]['source']
        self.workflow['batches'][0]['plan'] = self.lock('plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'not a translation'):
            self.prepare()

    def test_cli(self):
        self.lock('workflow.json', self.workflow)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(w.main(['--source-root', str(self.root), '--workflow',
                str(self.root/'workflow.json'), '--output', str(self.root/'output')]), 0)
        self.assertIn('"physical_disc_entries": 6', output.getvalue())

    def test_path_escape_rejected(self):
        self.workflow['terms']['path'] = '../terms.json'
        with self.assertRaisesRegex(ValueError, 'dependency path'):
            self.prepare()


class PublicWorkflowTests(unittest.TestCase):
    root=Path(__file__).resolve().parents[1]

    def load(self,path):
        return json.loads((self.root/path).read_bytes())

    def test_public_workflow_dependencies_match_exact_bytes(self):
        workflow=self.load('locales/zh-Hans/translation-workflow.json')
        refs=[workflow[k] for k in ('extraction_profile','style_rules','terms')]
        refs += [ref for batch in workflow['batches'] for ref in batch.values()]
        for ref in refs:
            self.assertEqual(w.digest((self.root/ref['path']).read_bytes()),ref['sha256'])

    def test_batches_are_disjoint_and_preserve_current_baseline(self):
        workflow=self.load('locales/zh-Hans/translation-workflow.json')
        batches=[self.load(batch['plan']['path']) for batch in workflow['batches']]
        ids=[e['id'] for p in batches for e in p['entries']]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),533)
        self.assertEqual(batches[0],self.load('locales/zh-Hans/readability-revised.json'))
        self.assertEqual(len(batches[1]['entries']),54)
        self.assertEqual(len(batches[2]['entries']),217)
        for p in batches:
            self.assertTrue(all('source' not in e for e in p['entries']))

    def test_subtitle_profile_locks_all_known_sidecars_and_existing_plans(self):
        profile=self.load('locales/zh-Hans/subtitle-profile.json')
        self.assertEqual([len(s['members']) for s in profile['sources']],[21,23])
        names=[e['resource'] for s in profile['sources'] for e in s['members']]
        self.assertEqual((len(names),len(set(names))),(44,44))
        for ref in profile['plans']:
            self.assertEqual(w.digest((self.root/ref['path']).read_bytes()),ref['sha256'])
        baseline=['locales/zh-Hans/display-subtitles/'+name+'.txt.json' for name in
            ('csm00-10','csm00-12','csm00-20','csm_prologue')]
        self.assertEqual([p['path'] for p in profile['plans'][:4]],baseline)
        self.assertEqual(sum(len(self.load(p)['entries']) for p in baseline),49)
        identities=[]
        for ref in profile['plans']:
            plan=self.load(ref['path'])
            identities.extend((plan['resource'],plan['input_sha256'],e['start']) for e in plan['entries'])
        self.assertGreaterEqual(len(identities),49)
        self.assertEqual(len(identities),len(set(identities)))


if __name__ == '__main__':
    unittest.main()
