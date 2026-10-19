"""Source-free contracts for poisoning aftermath and the firefly conversation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_bytes())
class FirefliesBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-028.json')
        self.review=load('locales/zh-Hans/batch-028.review.json')
    def test_scope_and_classification(self):
        self.assertEqual([(e['section'],e['entries']) for e in self.review['coverage']],[('CSMB05_086',63),('CSMB05_087_1',36),('CSMB05_088',11)])
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),{'dialogue':104,'narrative':6})
        self.assertEqual(self.review['status'],'draft')
        self.assertFalse(self.review['held_entries'])
    def test_disjoint_source_locked_increment(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches']
        old={e['id'] for spec in b[:27] for e in load(spec['plan']['path'])['entries']}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual((len(old),len(ids)),(4235,110))
        self.assertFalse(old & ids)
        self.assertEqual(ids,{e['id'] for e in self.review['entries']})
        held=load('locales/zh-Hans/batch-027.review.json')['held_entries'][0]
        self.assertNotIn(held['id'],ids|old)
        for row in self.plan['entries']:
            self.assertNotIn('source',row)
            self.assertRegex(row['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
    def test_explicit_dewrap_and_narrative_viewpoint(self):
        self.assertEqual(sum('line_break_policy' in e for e in self.plan['entries']),48)
        self.assertFalse(self.review['preserved_functional_break_ids'])
        kinds={e['id']:e['text_kind'] for e in self.review['entries']}
        narratives=[e['translation'] for e in self.plan['entries'] if kinds[e['id']]=='narrative']
        self.assertEqual(len(narratives),6)
        self.assertIn('原来，我想要保护她……',narratives)
        self.assertTrue(any('至今仍在我耳边回响' in t for t in narratives))
        for row in self.plan['entries']:
            if 'line_break_policy' in row:
                self.assertEqual(row['line_break_policy']['target_count'],0)
                self.assertNotIn('\\n',row['translation'])
    def test_formality_shift_and_conditional_promise(self):
        v=[e['translation'] for e in self.plan['entries']]
        self.assertEqual(v[0],'公主殿下，您没事吧？')
        self.assertIn('对不起，公主殿下……',v)
        self.assertTrue(any('突然不再用敬语' in t for t in v))
        self.assertIn('那……那个……洁菲。',v)
        self.assertTrue(any('只要说服了梅莉莎' in t for t in v))
        self.assertIn('我背你。',v)
    def test_adjacent_movie_cues_locked(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),21)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:21]),152)
        specs=p['plans'][19:21]
        self.assertEqual([s['path'] for s in specs],['locales/zh-Hans/subtitles/batch-028-csm05-82.txt.json','locales/zh-Hans/subtitles/batch-028-csm05-85.txt.json'])
        for spec in specs:
            self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
        plans=[load(s['path']) for s in specs]
        self.assertEqual([len(p['entries']) for p in plans],[1,2])
        self.assertEqual([[e['start'] for e in p['entries']] for p in plans],[[19705],[1234,29187]])
        self.assertEqual([[e['translation'].count('<br>') for e in p['entries']] for p in plans],[[0],[0,1]])
if __name__=='__main__':
    unittest.main()
