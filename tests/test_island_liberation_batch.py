"""Source-free contracts for split island battles and liberation aftermath."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_bytes())
class IslandLiberationTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-026.json')
        self.review=load('locales/zh-Hans/batch-026.review.json')
    def test_scope_and_classification(self):
        c=Counter()
        for row in self.review['coverage']:
            c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2CSMB.int':91,'MC2NpcTalk.int':31,'MC2Compose.int':45})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),{'dialogue':135,'quest_progress':19,'narrative':13})
        self.assertEqual(self.review['status'],'draft')
        self.assertFalse(self.review['preserved_functional_break_ids'])
    def test_disjoint_increment_and_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches']
        old={e['id'] for spec in b[:25] for e in load(spec['plan']['path'])['entries']}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual(len(old),3946)
        self.assertEqual(len(ids),167)
        self.assertFalse(ids & old)
        self.assertEqual(ids,{e['id'] for e in self.review['entries']})
        for row in self.plan['entries']:
            self.assertNotIn('source',row)
            self.assertRegex(row['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
    def test_progress_and_narrative_markers(self):
        kinds={e['id']:e['text_kind'] for e in self.review['entries']}
        progress=[e['translation'] for e in self.plan['entries'] if kinds[e['id']]=='quest_progress']
        self.assertEqual(progress,[f'击败北部军 ({i}/15)' for i in range(1,16)]+[f'摧毁北部军死亡弩炮 ({i}/4)' for i in range(1,5)])
        narratives=[e['translation'] for e in self.plan['entries'] if kinds[e['id']]=='narrative']
        self.assertEqual(sum(t.startswith('(') and t.endswith(')') for t in narratives),12)
        self.assertIn('与此同时，青灵森林的朱特一行人……',narratives)
        self.assertEqual(sum('line_break_policy' in e for e in self.plan['entries']),85)
        for e in self.plan['entries']:
            if 'line_break_policy' in e:
                self.assertGreater(e['line_break_policy']['source_count'],0)
                self.assertEqual(e['line_break_policy']['target_count'],0)
                self.assertNotIn('\\n',e['translation'])
    def test_candidate_and_distinct_villager_viewpoints(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertEqual(terms['제바사']['target'],'杰巴萨')
        self.assertEqual(terms['제바사']['review_status'],'candidate')
        self.assertEqual(terms['제바사']['relation'],'unverified')
        values=[e['translation'] for e in self.plan['entries']]
        self.assertTrue(any('[杰巴萨]' in t for t in values))
        self.assertTrue(any('共有4台' in t and '每1台' in t for t in values))
        self.assertIn('死去的丈夫也不会活着回来。你却要我高兴？',values)
        self.assertIn('谢谢各位帮助解放了岛屿。',values)
        self.assertTrue(any('梅莉莎……在阿巴泽特' in t and '到现在都还没好' in t for t in values))
    def test_movie_frozen_prefix(self):
        profile=load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']),19)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:19]),149)
        for spec in profile['plans'][:19]:
            self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
if __name__=='__main__':
    unittest.main()
