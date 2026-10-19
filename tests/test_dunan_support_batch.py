"""Source-free contracts for Dunan bandits, surrendering soldiers and mail."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class DunanSupportTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-037.json');self.r=load('locales/zh-Hans/batch-037.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Quest.int':46,'MC2QubeMail.int':10,'MC2CharacterName.int':1,'MC2FieldName.int':1})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':38,'name':5,'mail_subject':5,'mail_body':5,'quest_description':3,'quest_progress':1,'quest_objective':1})
        self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:36] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5273,58));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_mail_and_tactics(self):
        functional=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in functional]
        self.assertEqual(len(rows),8);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum(e['translation'].count('\\n') for e in rows),37)
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),32)
        kinds={e['id']:e['text_kind'] for e in self.r['entries']};mail=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='mail_body']
        self.assertEqual([t.count('\\n') for t in mail],[3,8,8,9,6]);self.assertEqual([[i for i,v in enumerate(t.split('\\n')) if not v] for t in mail],[[2],[4],[4],[5],[1,4]])
        tactic=mail[3];self.assertIn('至少5个',tactic);self.assertIn('双手剑',tactic);self.assertIn('扇子',tactic);self.assertIn('两人进入连锁状态',tactic);self.assertEqual(tactic.count('方向键右'),2)
        values=[e['translation'] for e in self.p['entries']];self.assertIn('杜南平原的麻烦(2)',values);self.assertIn('QUEST : 消灭杜南盗贼头目',values)
    def test_candidates_and_associated_fields(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('매드맥','麦德麦克'),('듀난 도적','杜南盗贼'),('듀난 도적의 아지트','杜南盗贼窝点')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']];self.assertIn('麦德麦克',values);self.assertIn('杜南盗贼窝点',values)
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        for s in p['plans'][:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
