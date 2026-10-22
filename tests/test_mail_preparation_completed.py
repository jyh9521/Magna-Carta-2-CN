from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class MailPreparationCompletedTests(unittest.TestCase):
 def test_ceremony_mail_preparation_completed_not_future_and_controls_retained(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/mail-preparation-completed.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['known_originals_retained']),(237,1,2))
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  self.assertEqual(len(d['decisions']),1)
  for e in d['decisions']:
   self.assertIn('준비를 해 놓고 기다리고 있단다',e['source']);self.assertEqual(e['before_translation'].replace('我会做好一切准备，等你回来。','我已经做好一切准备，正等你回来。'),e['translation']);self.assertEqual(e['translation'].count(chr(92)+'n'),3)
   self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256'])
  self.assertEqual(len(d['retained_family_controls']),7)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertEqual(d['new_primary_consistency_fields'],0)
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
