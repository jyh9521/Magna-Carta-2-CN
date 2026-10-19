"""Source-free contracts for Argo and Drago's rebuilding request."""
from pathlib import Path
import unittest,json,hashlib
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class BlueMoonReturnTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-081.json');self.r=L('locales/zh-Hans/batch-081.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMBQ10_30':5,'CSMBQ10_35':17});self.assertEqual(len(self.p['entries']),22);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),15);self.assertFalse(self.r['held_entries']);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertTrue(all(e['text_kind']=='dialogue' for e in self.r['entries']));self.assertEqual(self.r['status'],'draft')
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:80] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8753);self.assertEqual(len(ids),22);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_speakers_and_legacy_terms(self):
  t=''.join(e['translation'] for e in self.p['entries']);self.assertIn('德雷戈',t);self.assertIn('青月特雷瓦',t);self.assertIn('黑角特雷瓦',t);self.assertIn('鲁哈尔特高原',t);self.assertNotIn('德拉戈',t);self.assertNotIn('阿尔贝多',t);self.assertNotIn('鲁坦',t)
 def test_request_not_completed_reconstruction(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('已经在鲁哈尔特高原聚集了' in t for t in ts));self.assertTrue(any('我真的还能' in t for t in ts));self.assertTrue(any('这会花些时间' in t for t in ts));self.assertFalse(any('故乡已经重建完成' in t or '全族一致推举' in t for t in ts));self.assertIn('为什么……？',ts)
 def test_merchant_guild_candidate(self):
  terms=L('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),410);e=terms[409];self.assertEqual((e['source'],e['target']),('상인조합','商人公会'));self.assertEqual(e['review_status'],'candidate');self.assertEqual(e['relation'],'unverified');self.assertIn(e['source_string_id'],{e['id'] for e in self.p['entries']})
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,81) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
