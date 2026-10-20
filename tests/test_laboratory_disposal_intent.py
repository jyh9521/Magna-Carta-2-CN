"""Source-only regression for the draft disposal intention, not game acceptance."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCALE = ROOT / 'locales/zh-Hans'
IDENTITY = 'coalesced:8cb6b1c94bea8488b17445ad760c1974bae197f22896754a9c72a2b642dda8c9'


def load(path):
    return json.loads(path.read_bytes())


class LaboratoryDisposalIntentTests(unittest.TestCase):
    def test_originating_batch_retains_draft_and_intention(self):
        plan = load(LOCALE / 'batch-047.json')
        entry = next(e for e in plan['entries'] if e['id'] == IDENTITY)
        self.assertEqual(entry['translation'], '这里的资料，现在看来都得销毁才行。')
        self.assertEqual(entry['source_sha256'],
                         'f9dec4db48887ec41d2af4ab710b8a18bab3eba202b187f1bd229c17a06c4f39')
        self.assertEqual(entry['line_break_policy'], {'source_count': 1, 'target_count': 0})
        review = load(LOCALE / 'batch-047.review.json')
        self.assertEqual(review['status'], 'draft')
        self.assertEqual(next(e for e in review['entries'] if e['id'] == IDENTITY)['text_kind'],
                         'dialogue')

    def test_workflow_reuses_unique_original_batch_not_an_overlapping_append(self):
        workflow = load(LOCALE / 'translation-workflow.json')
        owners = []
        for batch in workflow['batches']:
            ref = batch['plan']
            path = ROOT / ref['path']
            if any(e['id'] == IDENTITY for e in load(path)['entries']):
                owners.append(ref['path'])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ref['sha256'])
        self.assertEqual(owners, ['locales/zh-Hans/batch-047.json'])

    def test_context_and_literal_control_relocks_match_current_draft(self):
        profiles = [load(p) for p in (LOCALE / 'context-reviews').glob('*.json')]
        identities = {p['plan_canonical_sha256'] for p in profiles}
        self.assertEqual(len(identities), 1)
        self.assertEqual(identities, {load(LOCALE / 'literal-control-retention.json')
                                     ['changes_canonical_sha256']})
        locks = [e for p in profiles for e in p['entries'] if e['id'] == IDENTITY]
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0]['translation_sha256'],
                         hashlib.sha256('这里的资料，现在看来都得销毁才行。'.encode()).hexdigest())
        self.assertTrue(all(p['human_finalized'] is False and
                            p['runtime_layout_approved'] is False for p in profiles))


if __name__ == '__main__':
    unittest.main()
