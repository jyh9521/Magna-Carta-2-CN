"""Source-free contracts for separate festival states and remaining field comments."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class MareFeastTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-034.json');self.r=load('locales/zh-Hans/batch-034.review.json')
    def test_scope_and_held_markers(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Compose.int':35,'MC2NpcTalk.int':85,'MC2Quest.int':3,'MC2Skill.int':1,'MC2CharacterName.int':1})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'narrative':24,'dialogue':93,'menu':2,'system_message':2,'quest_description':1,'name':3})
        self.assertEqual([e['key'] for e in self.r['held_entries']],['2219','2461','221','241','2229','2235']);self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:33] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(4943,125));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse({e['id'] for e in self.r['held_entries']}&(old|ids))
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_festival_menu_and_skill_identity(self):
        v=[e['translation'] for e in self.p['entries']];self.assertIn('天风一击闪',v);self.assertIn('朱特学会了天风一击闪',v);self.assertIn('洁菲学会了天风一击闪',v)
        self.assertEqual(sum(t.startswith('(') and t.endswith(')') for t in v),24)
        ids=set(self.r['preserved_functional_break_ids']);self.assertEqual(len(ids),1);menu=next(e for e in self.p['entries'] if e['id'] in ids)
        self.assertEqual(menu['translation'].count('\\n'),1);self.assertIn('X<Styles:/>',menu['translation']);self.assertIn('Y<Styles:/>',menu['translation']);self.assertNotIn('line_break_policy',menu)
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),58)
        self.assertIn('你在紧张吗？准备好了，随时告诉我。 ',v);self.assertTrue(any('再过3年' in t for t in v))
    def test_candidate_names_and_distinct_states(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('천풍일격섬','天风一击闪'),('킬로티','基洛蒂'),('세리아','塞莉娅'),('성인식','成人礼')]:
            self.assertEqual(terms[s]['target'],t);self.assertEqual(terms[s]['review_status'],'candidate');self.assertEqual(terms[s]['relation'],'unverified')
        cov={e['section']:e['entries'] for e in self.r['coverage']};self.assertEqual(cov['06_kotamare'],26);self.assertEqual(cov['06_kotamare_feast'],25)
        self.assertIn('塞莉娅若是能看到，不知该有多高兴……',[e['translation'] for e in self.p['entries']])
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        for s in p['plans'][:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
        self.assertEqual(load('locales/zh-Hans/batch-033.review.json')['subtitle_term_candidates'][0]['target'],'一号')
if __name__=='__main__':unittest.main()
