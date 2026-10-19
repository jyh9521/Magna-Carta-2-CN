"""Source-free contracts for the checkpoint dispute and Loud's report."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RoadVelfortTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-041.json');self.r=load('locales/zh-Hans/batch-041.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':67,'MC2Compose.int':26,'MC2FieldName.int':1});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':86,'narrative':5,'system_message':2,'name':1});self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:40] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5597,94));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_system_layout_and_reported_suspicion(self):
        functional=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in functional];self.assertEqual(len(rows),2);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual([e['translation'].count('\\n') for e in rows],[1,1]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),60)
        values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('恐怕是亚历克斯大人' in t for t in values));self.assertTrue(any('我亲眼看见' in t for t in values));self.assertTrue(any('开始怀疑亚历克斯大人' in t for t in values));self.assertTrue(any('亲自向他说明' in t for t in values));self.assertTrue(any('市民和公主殿下的安全' in t for t in values));self.assertEqual(sum(t.startswith('(') and t.endswith(')') for t in values),5)
    def test_candidate_linked_place(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']};t=ts['별빛 평원'];self.assertEqual(t['target'],'星光平原');self.assertEqual(t['review_status'],'candidate');self.assertEqual(t['relation'],'unverified');self.assertIn('星光平原',[e['translation'] for e in self.p['entries']])
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
