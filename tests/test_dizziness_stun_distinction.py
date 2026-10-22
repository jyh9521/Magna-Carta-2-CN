from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class DizzinessStunDistinctionTests(unittest.TestCase):
 def test_linked_dizziness_drafts_and_distinct_stun_controls(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/dizziness-stun-distinction.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields']),(233,26,0));self.assertEqual(len(d['decisions']),26)
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  for e in d['decisions']:
   p=entries[e['id']];self.assertIn('어지러움',e['source']);self.assertEqual(hashlib.sha256(e['source'].encode()).hexdigest(),p['source_sha256']);self.assertEqual(p['translation'],e['translation']);self.assertEqual(e['translation'],e['before_translation'].replace('眩晕','晕眩'));self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertEqual(e['translation'].count(chr(92)+'n'),e['before_translation'].count(chr(92)+'n'))
  self.assertEqual(len(d['retained_controls']),14)
  for e in d['retained_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  terms={e['id']:e for e in L('locales/zh-Hans/terms.json')['terms']}
  for e in d['term_target_supersessions']:self.assertEqual(terms[e['id']],e['after']);self.assertEqual(e['after']['review_status'],'candidate');self.assertEqual(e['after']['relation'],'unverified')
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
