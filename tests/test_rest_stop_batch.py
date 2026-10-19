"""Source-free contracts for chapter-six rest-stop quests and diary link."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RestStopTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-036.json');self.r=load('locales/zh-Hans/batch-036.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Quest.int':67,'MC2CSMB.int':2,'MC2Item.int':4})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':55,'name':6,'quest_description':4,'quest_progress':3,'quest_objective':3,'item_description':2})
        self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:35] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5200,73));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_breaks_and_held(self):
        functional=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in functional]
        self.assertEqual(len(rows),4);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertTrue(all(e['translation'].count('\\n')==1 for e in rows))
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),36)
        held=self.r['held_entries'];self.assertEqual(len(held),1);self.assertEqual((held[0]['section'],held[0]['key']),('06_603_0','603_0'));self.assertNotIn(held[0]['id'],{e['id'] for e in self.p['entries']})
        values=[e['translation'] for e in self.p['entries']];self.assertIn('QUEST : 获得日记',values);self.assertIn('破旧的日记 ',values);self.assertIn('拜……泽恩……拜泽恩？',values)
    def test_candidates_and_associated_fields(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('일기장','日记'),('낡은 일기장','破旧的日记'),('작은 주머니','小袋子'),('바이젠','拜泽恩')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']];self.assertIn('难道是银白的拜泽恩？',values);self.assertIn('小袋子',values)
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        for s in p['plans'][:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
