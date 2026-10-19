"""Source-free contracts for team combat, the werewolf base and escort quests."""
from collections import Counter
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())


class TeamBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-006.json');self.review=load('locales/zh-Hans/batch-006.review.json')

    def test_scope_and_categories(self):
        counts=Counter()
        for r in self.review['coverage']:counts[r['document']]+=r['entries']
        self.assertEqual(counts,{'MC2CSMB.int':180,'MC2NpcTalk.int':38,'MC2Quest.int':45,'linked-name-fields':9})
        self.assertEqual(Counter(r['text_kind'] for r in self.review['entries']),
            {'dialogue':247,'narrative':9,'name':11,'quest_description':2,'quest_progress':2,'menu':1})
        self.assertEqual(self.review['status'],'draft')

    def test_incremental_and_unique_ids(self):
        names=('readability-fix','batch-002','batch-003','batch-004','batch-005')
        before={e['id'] for n in names for e in load('locales/zh-Hans/'+n+'.json')['entries']}
        ids=[e['id'] for e in self.plan['entries']]
        self.assertEqual((len(before),len(ids),len(set(ids))),(1117,272,272))
        self.assertFalse(before & set(ids))
        self.assertEqual(set(ids),{e['id'] for e in self.review['entries']})

    def test_functional_breaks_and_progress_prefixes(self):
        ids=self.review['preserved_functional_break_ids'];self.assertEqual(len(set(ids)),3)
        rows=[e for e in self.plan['entries'] if e['id'] in ids]
        self.assertEqual(sorted(e['translation'].count('\\n') for e in rows),[1,2,2])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        progress=[e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress,['QUEST : 救出胡安','QUEST:抵达卡蒙德采掘场！'])
        choice=next(e['translation'] for e in rows if '<Styles:' in e['translation'])
        self.assertIn('>X<Styles:/>',choice);self.assertIn('>Y<Styles:/>',choice)

    def test_combat_quantities_and_linked_names(self):
        text='\n'.join(e['translation'] for e in self.plan['entries'])
        for phrase in ('1名队长','2名队员','1.5倍','2倍','2人同时过热','300SID','15分','20分'):
            self.assertIn(phrase,text)
        self.assertEqual(sum(e['translation']=='猫猫' for e in self.plan['entries']),2)
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms),124)
        for source,target in [('체인','连锁'),('체인드라이브','连锁超限'),('체인브레이크','连锁终结')]:
            self.assertEqual(terms[source]['target'],target);self.assertEqual(terms[source]['review_status'],'candidate')

    def test_public_plan_hash_only_and_explicit_breaks(self):
        for e in self.plan['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertTrue(e['translation'].strip());self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in e:
                self.assertGreater(e['line_break_policy']['source_count'],0)
                self.assertEqual(e['line_break_policy']['target_count'],0)

    def test_workflow_keeps_previous_batches(self):
        paths=[e['plan']['path'] for e in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(paths[:6],['locales/zh-Hans/'+n+'.json' for n in
            ('readability-fix','batch-002','batch-003','batch-004','batch-005','batch-006')])
        ids=[e['id'] for p in paths for e in load(p)['entries']]
        self.assertEqual(len(ids),len(set(ids)));self.assertGreaterEqual(len(ids),1389)


if __name__=='__main__':unittest.main()
