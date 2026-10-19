"""Source-free fifth-stage quest/mail gap closure contracts."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class Chapter05SupportTests(unittest.TestCase):
    def setUp(self):
        self.p=load('locales/zh-Hans/batch-030.json');self.r=load('locales/zh-Hans/batch-030.review.json')
    def test_scope(self):
        c=Counter()
        for row in self.r['coverage']:c[row['document']]+=row['entries']
        self.assertEqual(c,{'MC2Quest.int':100,'MC2QubeMail.int':16,'MC2Item.int':2,'MC2UI.int':1})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':79,'menu':1,'quest_description':6,'name':8,'quest_progress':5,'quest_objective':3,'mail_subject':8,'mail_body':8,'item_description':1})
        self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:29] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(4461,119));self.assertFalse(old&ids)
        self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_layout_and_literals(self):
        ids=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in ids]
        self.assertEqual(len(rows),14);self.assertEqual(sum(e['translation'].count('\\n') for e in rows),61)
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),54)
        kinds={e['id']:e['text_kind'] for e in self.r['entries']};mail=[e for e in self.p['entries'] if kinds[e['id']]=='mail_body']
        self.assertEqual([e['translation'].count('\\n') for e in mail],[4,5,7,8,10,8,5,6])
        values=[e['translation'] for e in self.p['entries']]
        self.assertIn('QUEST%s: 击败北部军 (%s / %s)',values);self.assertIn('QUEST%s : 摧毁死亡弩炮 (%s / %s)',values);self.assertIn('Quest: 护送完成',values)
        self.assertIn('利安达尔果实 ',values);self.assertTrue(any(t.endswith('。  ') for t in values))
        self.assertTrue(any('X<Styles:/>' in t and 'Y<Styles:/>' in t for t in values))
        self.assertTrue(any('LV2 卡蒙德' in t for t in values));self.assertTrue(any('15名以上' in t for t in values))
    def test_candidate_and_associated_fields(self):
        terms={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']};t=terms['리안달의 열매']
        self.assertEqual(t['target'],'利安达尔果实');self.assertEqual(t['review_status'],'candidate');self.assertEqual(t['relation'],'unverified')
        v=[e['translation'] for e in self.p['entries']];self.assertIn('利安达尔果实',v);self.assertIn('利安达尔 2',v)
        self.assertTrue(any('让露来对付，也许会有办法？' in t for t in v))
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),22)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:22]),154)
        for spec in p['plans'][:22]:self.assertEqual(hashlib.sha256((ROOT/spec['path']).read_bytes()).hexdigest(),spec['sha256'])
if __name__=='__main__':unittest.main()
