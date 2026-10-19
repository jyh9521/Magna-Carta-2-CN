"""Source-free contracts for chapter-six story and movie closure."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RuhaltCloseTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-033.json');self.r=load('locales/zh-Hans/batch-033.review.json')
    def test_scope_and_held_markers(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':42,'MC2NpcTalk.int':27,'MC2Compose.int':32,'MC2FieldName.int':1})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':92,'narrative':8,'menu':1,'name':1})
        self.assertEqual([e['key'] for e in self.r['held_entries']],['2268','2273_0','2216']);self.assertEqual(self.r['status'],'draft')
    def test_disjoint_and_protected_ids(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:32] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(4841,102));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        self.assertFalse({e['id'] for e in self.r['held_entries']}&(old|ids))
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_menu_narrative_and_dewrap(self):
        ids=set(self.r['preserved_functional_break_ids']);self.assertEqual(len(ids),1)
        e=next(e for e in self.p['entries'] if e['id'] in ids);self.assertEqual(e['translation'].count('\\n'),1);self.assertNotIn('line_break_policy',e)
        self.assertIn('X<Styles:/>',e['translation']);self.assertIn('Y<Styles:/>',e['translation'])
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),58)
        v=[e['translation'] for e in self.p['entries']];self.assertEqual(sum(t.startswith('(') and t.endswith(')') for t in v),6)
        self.assertIn('你说我是艾尔加？别开玩笑了。……这不可能！',v)
    def test_location_and_subtitle_only_candidate(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertEqual(terms['루할트 고원']['target'],'鲁哈尔特高原');self.assertEqual(terms['트레와 사막']['target'],'特雷瓦沙漠')
        c=self.r['subtitle_term_candidates'];self.assertEqual(len(c),1);self.assertEqual((c[0]['source'],c[0]['target']),('퍼스트','一号'))
        self.assertEqual(c[0]['resource'],'MC2Game/Movies/csm06-120.txt');self.assertTrue(c[0]['source_string_id'].startswith('subtitle:'))
        self.assertEqual(c[0]['review_status'],'candidate');self.assertEqual(c[0]['relation'],'unverified')
        self.assertRegex(c[0]['anchor_source_sha256'],r'^[0-9a-f]{64}$')
        # Batch033 only had a Movies anchor; later genuine Coalesced occurrences
        # may join shared terms without altering this immutable subtitle record.
        if '퍼스트' in terms:
            shared=terms['퍼스트'];self.assertEqual(shared['target'],c[0]['target'])
            self.assertEqual(shared['resource'],'MC2Game/Localization/Coalesced.int')
            self.assertEqual((shared['review_status'],shared['relation']),('candidate','unverified'))
            batches=load('locales/zh-Hans/translation-workflow.json')['batches']
            early={e['id'] for spec in batches[:33] for e in load(spec['plan']['path'])['entries']}
            later={e['id']:e for spec in batches[33:] for e in load(spec['plan']['path'])['entries']}
            self.assertNotIn(shared['source_string_id'],early);self.assertIn(shared['source_string_id'],later)
            self.assertIn(c[0]['target'],later[shared['source_string_id']]['translation'])
            self.assertNotEqual(shared['source_string_id'],c[0]['source_string_id'])
    def test_full_chapter_six_movie_locks(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        movies=[load(s['path']) for s in p['plans'][:27] if 'csm06-' in s['path']]
        self.assertEqual(len(movies),5);self.assertEqual(sum(len(m['entries']) for m in movies),33)
        for s in p['plans'][23:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
        c=self.r['subtitle_term_candidates'][0];m=next(m for m in movies if m['resource']==c['resource']);self.assertTrue(any(e['source_sha256']==c['anchor_source_sha256'] and '一号' in e['translation'] for e in m['entries']))
if __name__=='__main__':unittest.main()
