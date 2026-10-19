"""Source-free contracts for Rue return and fifth-stage opening."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_bytes())
class RueReturnTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-025.json')
        self.review=load('locales/zh-Hans/batch-025.review.json')
    def test_scope_and_classification(self):
        c=Counter()
        for row in self.review['coverage']:
            c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2CSMB.int':88,'MC2NpcTalk.int':7,'MC2Compose.int':4})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),{'dialogue':98,'menu':1})
        self.assertEqual(self.review['status'],'draft')
    def test_disjoint_increment(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches']
        old={e['id'] for spec in b[:24] for e in load(spec['plan']['path'])['entries']}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual(len(old),3847)
        self.assertEqual(len(ids),99)
        self.assertFalse(old & ids)
        self.assertEqual(ids,{e['id'] for e in self.review['entries']})
        for row in self.plan['entries']:
            self.assertNotIn('source',row)
            self.assertRegex(row['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
    def test_menu_and_explicit_dialogue_dewrap(self):
        ids=set(self.review['preserved_functional_break_ids'])
        self.assertEqual(len(ids),1)
        menu=next(e for e in self.plan['entries'] if e['id'] in ids)
        self.assertEqual(menu['translation'],'<Styles:MC2_StyleFont_0>X<Styles:/> 准备好了\\n<Styles:MC2_StyleFont_0>Y<Styles:/> 还没准备好')
        self.assertNotIn('line_break_policy',menu)
        for e in self.plan['entries']:
            if 'line_break_policy' in e:
                self.assertGreater(e['line_break_policy']['source_count'],0)
                self.assertEqual(e['line_break_policy']['target_count'],0)
                self.assertNotIn('\\n',e['translation'])
    def test_candidates_and_in_scene_uncertainty(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for source,target in [('피의 계약','血之契约'),('마스터','主人')]:
            self.assertEqual(terms[source]['target'],target)
            self.assertEqual(terms[source]['review_status'],'candidate')
            self.assertEqual(terms[source]['relation'],'unverified')
        vals=[e['translation'] for e in self.plan['entries']]
        self.assertTrue(any('似乎' in t and '强化型哨兵' in t for t in vals))
        self.assertTrue(any('我也对此存疑' in t for t in vals))
        self.assertIn('传闻她出身风息岛，公主殿下也认识她吗？',vals)
    def test_adjacent_movie_cues_locked(self):
        profile=load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']),19)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:19]),149)
        spec=profile['plans'][18];self.assertEqual(spec['path'],'locales/zh-Hans/subtitles/batch-025-csm05-10.txt.json')
        self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
        plan=load(spec['path']);self.assertEqual(plan['resource'],'MC2Game/Movies/csm05-10.txt')
        self.assertEqual(len(plan['entries']),8)
        self.assertEqual([e['start'] for e in plan['entries']],[0,2391,5388,8986,9864,16669,22296,26800])
        self.assertEqual([e['translation'].count('<br>') for e in plan['entries']],[0,0,0,0,1,0,1,1])
        self.assertTrue(all('source' not in e for e in plan['entries']))
if __name__=='__main__':
    unittest.main()
