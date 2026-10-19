"""Source-free contracts for chapter-seven identity dispute and transport."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class IdentityTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-040.json');self.r=load('locales/zh-Hans/batch-040.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2CSMB.int':86,'MC2Compose.int':7,'MC2CharacterName.int':1,'MC2Item.int':2,'MC2UI_Pillar.int':2,'MC2QubeMail.int':2})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':85,'narrative':8,'name':2,'menu':2,'item_description':1,'mail_subject':1,'mail_body':1})
        self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:39] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5497,100));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_mail_and_identity(self):
        functional=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in functional]
        self.assertEqual(len(rows),1);self.assertNotIn('line_break_policy',rows[0]);self.assertEqual(rows[0]['translation'].count('\\n'),7)
        self.assertEqual([i for i,t in enumerate(rows[0]['translation'].split('\\n')) if not t],[3]);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),70)
        values=[e['translation'] for e in self.p['entries']];self.assertTrue(any('另一个' in t or '一模一样' in t for t in values));self.assertTrue(any('绝对不能杀死洁菲' in t for t in values));self.assertTrue(any('“血之契约”的烙印无法抹去' in t for t in values));self.assertTrue(any('终身免费' in t for t in values));self.assertTrue(any('交战地区' in t and '去不了' in t for t in values))
    def test_transport_candidates(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('아비스 수송대','阿维斯运输队'),('아비스 수송대 이용권','阿维斯运输队乘车券'),('아비스 상점','阿维斯商店')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
    def test_subtitle_locked_prefix_and_new_cues(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
        s=load('locales/zh-Hans/subtitles/batch-040-csm07-10.txt.json');self.assertEqual(len(s['entries']),7);self.assertEqual(s['resource'],'MC2Game/Movies/csm07-10.txt');self.assertEqual([(e['start'],e['end']) for e in s['entries']],[(3327,5634),(6314,7006),(7006,9655),(10044,11284),(12359,14279),(14675,21523),(22163,25569)])
        self.assertEqual(sum(e['translation'].count('<br>') for e in s['entries']),1)
if __name__=='__main__':unittest.main()
