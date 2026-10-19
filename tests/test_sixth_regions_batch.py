"""Source-free contracts for chapter-six city and regional NPC closure."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class SixthRegionsTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-035.json');self.r=load('locales/zh-Hans/batch-035.review.json')
    def test_scope_and_held_markers(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2NpcTalk.int':129,'MC2CharacterName.int':1,'MC2FieldName.int':2})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':129,'name':3})
        self.assertEqual(len(self.r['held_entries']),12);self.assertEqual(self.r['status'],'draft')
        self.assertIn('2254_1',[e['key'] for e in self.r['held_entries']])
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:34] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5068,132));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse({e['id'] for e in self.r['held_entries']}&(old|ids))
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_regions_numeric_and_split_sentences(self):
        cov={e['section']:e['entries'] for e in self.r['coverage']};self.assertEqual([cov[s] for s in ('06_Abajet','06_oldfox','06_chinook','06_dunanhill','06_dunanfield')],[59,7,24,18,21])
        values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('150年前' in t for t in values));self.assertTrue(any('[寂静荒野]' in t for t in values))
        self.assertIn('我会竭尽全力，守护这座岛。',values);self.assertTrue(any('难道是变异吗？？' in t for t in values));self.assertTrue(any('没有留下确切的记录' in t for t in values))
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),77);self.assertFalse(self.r['preserved_functional_break_ids'])
    def test_candidate_names(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('헤인겔','海因格尔'),('라노아라 호수','拉诺阿拉湖'),('레인폴트','雷恩波尔特'),('레인폴트 폐허','雷恩波尔特废墟')]:
            self.assertEqual(terms[s]['target'],t);self.assertEqual(terms[s]['review_status'],'candidate');self.assertEqual(terms[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']];self.assertIn('海因格尔',values);self.assertIn('拉诺阿拉湖',values);self.assertIn('雷恩波尔特废墟',values)
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        for s in p['plans'][:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
