"""Source-free contracts for the laboratory exit and chapter-eight support text."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class LabExitTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-049.json');self.r=load('locales/zh-Hans/batch-049.review.json')
 def test_scope(self):
  c=Counter()
  for e in self.r['coverage']:c[e['document']]+=e['entries']
  self.assertEqual(c,{'MC2CSMB.int':67,'MC2Compose.int':4,'MC2Quest.int':28,'MC2QubeMail.int':2,'MC2Item.int':3});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':80,'narrative':7,'quest_progress':6,'name':5,'quest_description':3,'mail_subject':1,'mail_body':1,'item_description':1});self.assertEqual(self.r['status'],'draft')
 def test_disjoint_source_locks(self):
  batches=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for b in batches[:48] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
  self.assertEqual((len(old),len(ids)),(6341,104));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
  for e in self.p['entries']:
   self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_layout_and_source_differences(self):
  rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),4);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),59)
  values=[e['translation'] for e in self.p['entries']];self.assertIn('北部军保管箱钥匙 ',values);self.assertIn('制造室通行卡',values);self.assertTrue(any('[制造室钥匙]' in t for t in values));self.assertEqual(sum('QUEST%s' in t for t in values),2);self.assertTrue(any(t.startswith('在下到中央研究室之前') for t in values));self.assertTrue(any('先王陛下' in t and t.endswith('吗？') for t in values));mail=next(t for t in values if '刚得到消息' in t);self.assertEqual(mail.count('\\n'),6);self.assertIn('\\n\\n',mail)
 def test_candidates(self):
  ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
  for s,t in [('제조실','制造室'),('제조실 열쇠','制造室钥匙'),('제조실 출입카드','制造室通行卡'),('북부군 보관함 열쇠','北部军保管箱钥匙'),('레카스','雷卡斯'),('베카스','贝卡斯')]:
   self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),30);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:30]),203)
  for s in p['plans'][:30]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
