from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class ChapterExclusionReasonTests(unittest.TestCase):
 def test_recovered_term_holds_do_not_become_unused_or_translated(self):
  L=lambda p:json.loads((R/p).read_bytes());H=lambda s:hashlib.sha256(s.encode()).hexdigest();d=L('locales/zh-Hans/candidate-decisions/chapter-exclusion-reasons.json');self.assertEqual((d['context_fields'],d['source_physical'],d['retained_original_count'],d['translation_edits']),(156,158,2,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['retained_entries']),156)
  for e in d['retained_entries']:
   self.assertEqual(H(e['source']),e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(H(e['translation']),e['translation_sha256'])
  self.assertEqual(len(d['retained_originals']),2)
  for e in d['retained_originals']:
   adopted={a['id']:a for a in L('locales/zh-Hans/candidate-decisions/chapter-term-adoption.json')['entries']}
   if e['id'] in entries:
    self.assertIn(e['id'],adopted);self.assertEqual(H(entries[e['id']]['translation']),adopted[e['id']]['translation_sha256'])
   else:self.assertNotIn(e['id'],adopted)
   r=next(x for x in L(e['review'])['held_entries'] if x['id']==e['id']);self.assertEqual(r['source_sha256'],e['source_sha256']);self.assertEqual(r['reason'],e['held_reason'])
  self.assertTrue(any('성쇄' in e['held_reason'] for e in d['retained_originals']));self.assertTrue(any('영병' in e['held_reason'] for e in d['retained_originals']));self.assertEqual(len(d['parallel_locale_sources']),20)
  for disc in [1,2]:
   rows={(e['section'],e['key']):e for e in d['parallel_locale_sources'] if e['disc']==disc};self.assertIn('隆盛',rows['Chapter11','Chapter11_27']['source']);self.assertIn('王の霊廟',rows['Chapter12','Chapter12_37']['source'])
   for e in rows.values():self.assertEqual(H(e['source']),e['source_sha256'])
  rec=next(e for e in L('locales/zh-Hans/followup-register.json')['records'] if e['record']=='original-exclusion-followup.json');self.assertEqual(rec['latest_resolution']['phase'],285)
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
