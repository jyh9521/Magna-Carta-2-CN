"""Source-free contracts for leave-taking, villagers' relics and state-specific NPCs."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_bytes())
class VillagerRelicTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-027.json')
        self.review=load('locales/zh-Hans/batch-027.review.json')
    def test_scope_classification_and_held_note(self):
        c=Counter()
        for row in self.review['coverage']:
            c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2CSMB.int':79,'MC2NpcTalk.int':8,'MC2Quest.int':7,'MC2Compose.int':26,'MC2Item.int':2})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),{'dialogue':96,'narrative':18,'quest_description':1,'name':2,'quest_progress':1,'quest_objective':1,'editor_note':2,'item_description':1})
        self.assertEqual(self.review['status'],'draft')
        held=self.review['held_entries'];self.assertEqual(len(held),1)
        self.assertEqual((held[0]['section'],held[0]['key']),('CSMB05_070','voc_csmb_05070_27'))
        self.assertNotIn(held[0]['id'],{e['id'] for e in self.plan['entries']})
    def test_disjoint_source_locked_increment(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches']
        old={e['id'] for spec in b[:26] for e in load(spec['plan']['path'])['entries']}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual((len(old),len(ids)),(4113,122))
        self.assertFalse(old & ids)
        self.assertEqual(ids,{e['id'] for e in self.review['entries']})
        for row in self.plan['entries']:
            self.assertNotIn('source',row)
            self.assertRegex(row['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
    def test_quest_tokens_and_layout(self):
        values=[e['translation'] for e in self.plan['entries']]
        self.assertIn('QUEST%s : 收集遗物 (%s / %s)',values)
        self.assertIn('村民的遗物 ',values)
        ids=set(self.review['preserved_functional_break_ids']);self.assertEqual(len(ids),1)
        des=next(e for e in self.plan['entries'] if e['id'] in ids)
        self.assertEqual(des['translation'].count('\\n'),1)
        self.assertNotIn('line_break_policy',des)
        self.assertEqual(sum('line_break_policy' in e for e in self.plan['entries']),60)
        self.assertEqual(sum(t.startswith('(') and t.endswith(')') for t in values),16)
        for e in self.plan['entries']:
            if 'line_break_policy' in e:
                self.assertEqual(e['line_break_policy']['target_count'],0)
                self.assertNotIn('\\n',e['translation'])
    def test_candidate_and_viewpoints(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        t=terms['마을사람의 유품'];self.assertEqual(t['target'],'村民的遗物')
        self.assertEqual(t['review_status'],'candidate');self.assertEqual(t['relation'],'unverified')
        values=[e['translation'] for e in self.plan['entries']]
        self.assertIn('朱特……我希望你从今天起，退出反哨兵部队。',values)
        self.assertTrue(any('恐怕已经不在人世' in t for t in values))
        self.assertTrue(any('我竟然一点也不知道' in t for t in values))
        self.assertIn('洁菲说明之后',values);self.assertIn('会议结束之后',values)
    def test_movie_frozen_prefix(self):
        profile=load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']),19)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:19]),149)
        for spec in profile['plans'][:19]:
            self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
if __name__=='__main__':
    unittest.main()
