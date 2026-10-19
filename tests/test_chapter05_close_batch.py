"""Source-free contracts for fifth-stage story close and rescue quest states."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_bytes())
class Chapter05CloseTests(unittest.TestCase):
    def setUp(self):
        self.p=load('locales/zh-Hans/batch-029.json');self.r=load('locales/zh-Hans/batch-029.review.json')
    def test_scope(self):
        c=Counter()
        for row in self.r['coverage']:c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2CSMB.int':64,'MC2Quest.int':50,'MC2Item.int':2})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':103,'narrative':3,'quest_progress':1,'quest_objective':1,'name':4,'quest_description':3,'item_description':1})
        self.assertEqual(self.r['status'],'draft')
    def test_disjoint_and_old_held_entry(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches']
        old={e['id'] for spec in b[:28] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(4345,116));self.assertFalse(ids&old)
        self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        self.assertNotIn(load('locales/zh-Hans/batch-027.review.json')['held_entries'][0]['id'],ids|old)
        for row in self.p['entries']:
            self.assertNotIn('source',row);self.assertRegex(row['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
    def test_layout_and_quest_state_tokens(self):
        v=[e['translation'] for e in self.p['entries']]
        self.assertIn('QUEST%s : 获得幻之根',v);self.assertIn('幻之根 ',v)
        self.assertIn('风息守备队(森林)',v);self.assertIn('风息守备队(海岸)',v)
        ids=set(self.r['preserved_functional_break_ids']);self.assertEqual(len(ids),1)
        des=next(e for e in self.p['entries'] if e['id'] in ids)
        self.assertEqual(des['translation'].count('\\n'),1);self.assertNotIn('line_break_policy',des)
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),67)
        self.assertTrue(any('喵' in t and '[幻之根]' in t for t in v))
    def test_candidate_and_legend(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']};t=terms['환상의 뿌리']
        self.assertEqual(t['target'],'幻之根');self.assertEqual(t['review_status'],'candidate');self.assertEqual(t['relation'],'unverified')
        v=[e['translation'] for e in self.p['entries']]
        self.assertIn('传说能让死人复生的根',v)
        self.assertTrue(any('没能向爷爷说出真相' in t for t in v))
    def test_fifth_stage_movie_complete(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),22)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:22]),154)
        movies=[load(s['path']) for s in p['plans'][:22] if 'csm05-' in s['path']]
        self.assertEqual(len(movies),4);self.assertEqual(sum(len(m['entries']) for m in movies),13)
        spec=p['plans'][21];self.assertEqual(spec['path'],'locales/zh-Hans/subtitles/batch-029-csm05-90.txt.json')
        self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
        cue=load(spec['path'])['entries'];self.assertEqual([e['start'] for e in cue],[8969,11347])
        self.assertEqual([e['translation'].count('哈啊') for e in cue],[4,4])
        self.assertEqual([e['translation'].count('<br>') for e in cue],[0,1])
if __name__=='__main__':unittest.main()
