from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class WeaponSuppressionAndIllusionTests(unittest.TestCase):
 def test_two_neutral_drafts_and_disc_separate_parallel_sources(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/weapon-suppression-and-illusion.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields']),(213,2,0))
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  for e in d['decisions']:
   self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertIn('压制敌人',e['translation']);self.assertNotIn('倒下',e['translation']);self.assertEqual(e['translation'].count(chr(92)+'n'),1)
   if '로드' in e['source']:self.assertNotIn('一击',e['translation'])
  self.assertEqual(len(d['retained_family_controls']),7)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertEqual(len(d['parallel_locale_sources']),8)
  for disc in [1,2]:
   rows=[e for e in d['parallel_locale_sources'] if e['disc']==disc];self.assertEqual(len(rows),4);self.assertEqual(next(e['source'] for e in rows if e['key']=='323_ham'),'イリュージョン')
   for e in rows:self.assertEqual(hashlib.sha256(e['source'].encode()).hexdigest(),e['source_sha256'])
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
