"""Source-free contracts for Ruhalt preparations and linked game mechanics."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RuhaltOpeningTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-031.json');self.r=load('locales/zh-Hans/batch-031.review.json')
    def test_scope(self):
        c=Counter()
        for row in self.r['coverage']:c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2CSMB.int':90,'MC2Quest.int':20,'MC2NpcTalk.int':20,'MC2CharacterName.int':1,'MC2FieldName.int':2,'MC2Item.int':4})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':124,'narrative':2,'quest_description':1,'name':6,'quest_progress':1,'quest_objective':1,'item_description':2})
        self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in batches[:30] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(4580,137));self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_game_controls_counts_and_layout(self):
        values=[e['translation'] for e in self.p['entries']]
        self.assertTrue(any('各自积累5个KAN' in t and '力量KAN' in t and '风之KAN' in t for t in values))
        self.assertTrue(any('方向键右' in t for t in values));self.assertTrue(any('AI设置' in t for t in values))
        self.assertIn('QUEST%s : 尝试制作雷电炸弹 (%s / %s)',values)
        self.assertIn('未完成的雷电炸弹 ',values);self.assertEqual(values.count('鲁哈尔特盆地'),2)
        ids=set(self.r['preserved_functional_break_ids']);self.assertEqual(len(ids),1)
        row=next(e for e in self.p['entries'] if e['id'] in ids);self.assertEqual(row['translation'].count('\\n'),3);self.assertNotIn('line_break_policy',row)
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),79)
    def test_candidates_and_npc_uncertainty(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('칸 지뢰','KAN地雷'),('번개 폭탄','雷电炸弹'),('파이어와인','法伊尔瓦因'),('루할트 분지','鲁哈尔特盆地'),('연계오의','连携奥义'),('번개의 칸','雷之KAN')]:
            self.assertEqual(terms[s]['target'],t);self.assertEqual(terms[s]['review_status'],'candidate');self.assertEqual(terms[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('我想，也许' in t and 'KAN' in t for t in values))
        self.assertIn('把它当作一场梦，是我的失误。那个噩梦，其实是我失去的记忆发出的警告。',values)
    def test_movie_frozen_prefix(self):
        profile=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(profile['plans']),22)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:22]),154)
        for spec in profile['plans'][:22]:self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
if __name__=='__main__':unittest.main()
