from pathlib import Path
import json,unittest
R=Path(__file__).resolve().parents[1]
class FollowupRegisterTests(unittest.TestCase):
 def test_historical_snapshots_do_not_become_active_untranslated_counts(self):
  L=lambda p:json.loads((R/p).read_bytes());d=L('locales/zh-Hans/followup-register.json');self.assertEqual(d['inventory_records'],27);self.assertEqual(len(d['records']),27);self.assertEqual(d['translation_edits'],0);self.assertEqual(d['translation_context_fields'],0);self.assertFalse(d['historical_paths_required_for_clean_checkout']);entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len({r['record'] for r in d['records']}),27)
  for r in d['records']:
   for e in r['entries']:
    if e['planned']:self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256'])
    else:
     adopted={a['id']:a for a in L('locales/zh-Hans/candidate-decisions/held-original-adoptions.json')['entries']}
     if e['id'] in entries:
      self.assertIn(e['id'],adopted);self.assertEqual(adopted[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256'])
     else:self.assertNotIn(e['id'],adopted)
   for p in r['evidence']:self.assertTrue((R/p).is_file())
  by={r['record']:r for r in d['records']};self.assertEqual(by['candidate-revision-followups.json']['classification'],'resolved-revision');self.assertIn('merchant-accident-sympathy.json',str(by['candidate-revision-followups.json']['evidence']));self.assertEqual(by['skill-status-naming-followup.json']['classification'],'skill-name-source-review-next');self.assertEqual(by['original-exclusion-followup.json']['classification'],'source-context-review-next');self.assertEqual(by['skill-original-fragments-followup.json']['classification'],'concatenation-evidence-gate')
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
