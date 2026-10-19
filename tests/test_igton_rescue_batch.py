"""Source-free contracts for Igton rescue, state NPCs and Rati follow-ups."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class IgtonRescueTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-032.json');self.r=load('locales/zh-Hans/batch-032.review.json')
    def test_scope_and_deletion_markers(self):
        c=Counter()
        for row in self.r['coverage']:c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2CSMB.int':69,'MC2NpcTalk.int':26,'MC2Quest.int':27,'MC2Item.int':2})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':112,'quest_description':2,'name':3,'quest_progress':3,'quest_objective':3,'item_description':1})
        self.assertEqual(self.r['status'],'draft');self.assertEqual(len(self.r['held_entries']),4)
        self.assertEqual([e['key'] for e in self.r['held_entries']],['233','234','2201','2207'])
    def test_disjoint_source_locked_increment(self):
        batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in batches[:31] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(4717,124));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        self.assertFalse({e['id'] for e in self.r['held_entries']}&(old|ids))
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_layout_and_quest_prefixes(self):
        values=[e['translation'] for e in self.p['entries']]
        self.assertIn('QUEST%s : 撒布拉提毒药',values);self.assertIn('QUEST%s: 拉提女王面具碎片 (%s / %s)',values)
        self.assertIn('拉提女王的面具碎片 ',values);self.assertIn('消灭拉提女王 ',values)
        ids=set(self.r['preserved_functional_break_ids']);self.assertEqual(len(ids),2)
        for e in self.p['entries']:
            if e['id'] in ids:self.assertEqual(e['translation'].count('\\n'),1);self.assertNotIn('line_break_policy',e)
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),80)
    def test_candidates_and_source_uncertainty(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('여왕 라티','拉提女王'),('여왕 라티의 가면조각','拉提女王的面具碎片')]:
            self.assertEqual(terms[s]['target'],t);self.assertEqual(terms[s]['review_status'],'candidate');self.assertEqual(terms[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']]
        self.assertTrue(any('似乎有办法从地面前往' in t for t in values));self.assertIn('传闻是真的吗？',''.join(values))
    def test_new_movie_lock(self):
        profile=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(profile['plans']),23)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:23]),161)
        spec=profile['plans'][22];self.assertEqual(spec['path'],'locales/zh-Hans/subtitles/batch-032-csm06-35.txt.json')
        self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
        rows=load(spec['path'])['entries'];self.assertEqual(len(rows),7)
        self.assertEqual([e['start'] for e in rows],[0,4293,8090,11871,16499,23712,41234])
        self.assertEqual([e['translation'].count('<br>') for e in rows],[1,1,1,1,0,0,1])
if __name__=='__main__':unittest.main()
