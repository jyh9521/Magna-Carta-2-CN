"""Source-free fourth-stage tactical mail contracts."""
from collections import Counter
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_bytes())
class TacticalMailTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-024.json')
        self.review=load('locales/zh-Hans/batch-024.review.json')
    def test_scope(self):
        self.assertEqual(len(self.plan['entries']),13)
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),{'mail_body':6,'mail_subject':6,'name':1})
        self.assertEqual([e['section'] for e in self.review['coverage']],['B04_001','B04_002','B04_003','B04_004','B04_005','Q04_QUBE_0','Default'])
        self.assertEqual(self.review['status'],'draft')
    def test_disjoint_locked_increment(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches']
        old={e['id'] for spec in b[:23] for e in load(spec['plan']['path'])['entries']}
        ids={e['id'] for e in self.plan['entries']}
        self.assertEqual(len(old),3834)
        self.assertEqual(len(ids),13)
        self.assertFalse(ids & old)
        self.assertEqual(ids,{e['id'] for e in self.review['entries']})
        for e in self.plan['entries']:
            self.assertNotIn('source',e)
            self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_conservative_layout_and_markers(self):
        functional=set(self.review['preserved_functional_break_ids'])
        rows=[e for e in self.plan['entries'] if e['id'] in functional]
        self.assertEqual([e['translation'].count('\\n') for e in rows],[4,8,8,7,7])
        self.assertTrue(all('line_break_policy' not in e for e in self.plan['entries']))
        self.assertTrue(rows[3]['translation'].endswith('　'))
        self.assertIn('[地面效果]',rows[3]['translation'])
        self.assertIn('[烧伤]',rows[3]['translation'])
        self.assertIn('HP',rows[1]['translation'])
        self.assertIn('3根',rows[1]['translation'])
        self.assertIn('2阶段',rows[1]['translation'])
    def test_incomplete_source_not_completed(self):
        values=[e['translation'] for e in self.plan['entries']]
        self.assertIn('在阿巴泽特附近发现了北部军哨所，这意味着',values)
        self.assertIn('请摧毁北部军哨所',values)
    def test_candidate_consistency(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('레비아탄','利维坦'),('저글론','泽格隆'),('지면효과','地面效果'),('화상','烧伤')]:
            self.assertEqual(terms[s]['target'],t)
            self.assertEqual(terms[s]['review_status'],'candidate')
            self.assertEqual(terms[s]['relation'],'unverified')
        self.assertEqual(terms['베카스']['target'],'贝卡斯')
        self.assertEqual(terms['레카스']['target'],'雷卡斯')
if __name__=='__main__':
    unittest.main()
