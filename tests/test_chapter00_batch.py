"""Source-free public contracts for the next contiguous opening translation batch."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT/name).read_bytes())


class Chapter00BatchTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-003.json')
        self.review=load('locales/zh-Hans/batch-003.review.json')

    def test_incremental_batch_has_exact_coverage_and_no_overlap(self):
        previous=[*load('locales/zh-Hans/readability-fix.json')['entries'],
                  *load('locales/zh-Hans/batch-002.json')['entries']]
        before={e['id'] for e in previous}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual(len(ids),217)
        self.assertFalse(ids & before)
        self.assertEqual(sum(r['entries'] for r in self.review['coverage']),217)
        scenes={r.get('section'):r['entries'] for r in self.review['coverage'] if r['document']=='MC2CSMB.int'}
        self.assertEqual(scenes,{'CSMB00_13':30,'CSMB00_14':19,'CSMB00_15':80,'CSMB00_18':42})

    def test_classification_and_review_states_remain_explicit_draft(self):
        self.assertEqual(self.review['status'],'draft')
        self.assertEqual(Counter(r['text_kind'] for r in self.review['entries']),
                         {'dialogue':210,'narrative':3,'name':4})
        self.assertEqual({r['id'] for r in self.review['entries']},{r['id'] for r in self.plan['entries']})

    def test_public_plan_contains_hashes_not_full_source_and_no_physical_newline(self):
        self.assertEqual(self.plan['source_mode'],'sha256-utf8')
        for entry in self.plan['entries']:
            self.assertNotIn('source',entry)
            self.assertRegex(entry['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertTrue(entry['translation'].strip())
            self.assertFalse(any(c in entry['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in entry:
                policy=entry['line_break_policy']
                self.assertIs(type(policy['source_count']),int)
                self.assertGreater(policy['source_count'],0)
                self.assertEqual(policy['target_count'],0)
                self.assertNotIn('\\n',entry['translation'])

    def test_unknown_escape_stays_held_back(self):
        self.assertEqual(len(self.review['held_entries']),1)
        held=self.review['held_entries'][0]
        self.assertEqual(held['reason'],'unverified-backslash-sequence')
        self.assertNotIn(held['id'],{e['id'] for e in self.plan['entries']})

    def test_linked_names_match_project_terms_without_promoting_candidates(self):
        terms=load('locales/zh-Hans/terms.json')['terms']
        by_source={t['source']:t for t in terms}
        self.assertEqual(len(terms),59)
        self.assertTrue(all(t['review_status']=='candidate' for t in terms))
        edits={e['id']:e['translation'] for e in self.plan['entries']}
        for source,target in [('라 스트라다','拉·斯特拉达'),('바람노래동굴','风歌洞窟'),
                              ('빌터','比尔特'),('이공진퇴','凌空震踢')]:
            term=by_source[source]
            self.assertEqual(term['target'],target)
            self.assertEqual(edits[term['source_string_id']],target)


if __name__=='__main__':
    unittest.main()
