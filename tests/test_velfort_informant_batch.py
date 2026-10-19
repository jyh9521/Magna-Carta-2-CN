"""Source-free contracts for Velfort civilians and informant search."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class VelfortInformantTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-042.json');self.r=load('locales/zh-Hans/batch-042.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':65,'MC2Quest.int':20,'MC2NpcTalk.int':37,'MC2Compose.int':5,'MC2CharacterName.int':2,'MC2FieldName.int':1});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':114,'narrative':10,'name':4,'system_message':1,'quest_description':1});self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:41] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5691,130));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_layout_conditions_and_numbers(self):
        rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),2);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum(e['translation'].count('\\n') for e in rows),1);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),80)
        values=[e['translation'] for e in self.p['entries']];self.assertIn('发现了北部军的库布',values);self.assertTrue(any('3倍' in t and '4倍' in t for t in values));self.assertTrue(any('2个月' in t for t in values));self.assertTrue(any('爸爸妈妈也不见了' in t for t in values));self.assertTrue(any('或者仍在遭到追捕' in t for t in values));self.assertTrue(any('这里受到灾祸种影响，没法使用连环术' in t for t in values));self.assertEqual(sum(t.startswith('(') and t.endswith(')') for t in values),5)
    def test_candidate_associated_names(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('제로하','泽罗哈'),('쿡스','库克斯'),('센티넬 연구소','哨兵研究所')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified');self.assertIn(t,[e['translation'] for e in self.p['entries']])
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
