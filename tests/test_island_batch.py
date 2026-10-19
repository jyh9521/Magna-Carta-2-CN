"""Public source-free checks for the cave and coastal-defense translation batch."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_bytes())


class IslandBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-004.json')
        self.review=load('locales/zh-Hans/batch-004.review.json')

    def test_exact_new_scope_and_disjoint_prior_ids(self):
        previous={e['id'] for name in ('readability-fix','batch-002','batch-003')
                  for e in load('locales/zh-Hans/'+name+'.json')['entries']}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual((len(ids),len(previous)),(308,533))
        self.assertFalse(ids & previous)
        self.assertEqual(sum(e['entries'] for e in self.review['coverage']),308)
        counts=Counter()
        for row in self.review['coverage']:counts[row['document']]+=row['entries']
        self.assertEqual(counts,{'MC2CSMB.int':235,'MC2NpcTalk.int':68,'linked-name-fields':5})

    def test_scene_and_npc_groups_are_contiguous(self):
        scenes={e['section'] for e in self.review['coverage'] if e['document']=='MC2CSMB.int'}
        self.assertEqual(scenes,{'CSMB00_21','CSMB00_22','CSMB00_25','CSMB00_31','CSMB00_50',
            'CSMB01_05','CSMB01_07','CSMB01_11','CSMB01_15','CSMB01_17','CSMB01_21',
            'CSMB01_25','CSMB01_31','CSMB01_47','CSMB01_48'})
        self.assertEqual({e['section'] for e in self.review['coverage'] if e['document']=='MC2NpcTalk.int'},
                         {'Ch01_0','Ch01_1'})

    def test_draft_classification_and_per_entry_linebreaks(self):
        self.assertEqual(self.review['status'],'draft')
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue':300,'narrative':3,'name':5})
        self.assertEqual({e['id'] for e in self.review['entries']},{e['id'] for e in self.plan['entries']})
        for entry in self.plan['entries']:
            self.assertNotIn('source',entry)
            self.assertRegex(entry['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertTrue(entry['translation'].strip())
            self.assertFalse(any(c in entry['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in entry:
                p=entry['line_break_policy']
                self.assertIs(type(p['source_count']),int)
                self.assertGreater(p['source_count'],0)
                self.assertEqual(p['target_count'],0)

    def test_terms_and_name_title_forms_remain_separate(self):
        terms=load('locales/zh-Hans/terms.json')['terms'];by_source={e['source']:e for e in terms}
        self.assertGreaterEqual(len(terms),75)
        self.assertEqual(by_source['엘가']['form'],'short-name')
        self.assertEqual(by_source['학살자 엘가']['form'],'title')
        self.assertNotEqual(by_source['엘가']['id'],by_source['학살자 엘가']['id'])
        index={e['id']:e['translation'] for e in self.plan['entries']}
        for source in ('엘가','슈엔자이트','청령의 숲','목캔디'):
            term=by_source[source]
            self.assertEqual(term['review_status'],'candidate')
            self.assertEqual(index[term['source_string_id']],term['target'])
        self.assertEqual(sum(e['translation']=='艾尔加' for e in self.plan['entries']),2)

    def test_workflow_preserves_frozen_prior_batches(self):
        workflow=load('locales/zh-Hans/translation-workflow.json')
        paths=[e['plan']['path'] for e in workflow['batches']]
        self.assertEqual(paths[:4],['locales/zh-Hans/'+n+'.json' for n in
            ('readability-fix','batch-002','batch-003','batch-004')])
        ids=[e['id'] for ref in workflow['batches'] for e in load(ref['plan']['path'])['entries']]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),841)


if __name__=='__main__':unittest.main()
