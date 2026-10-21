from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class ArgoRecoveryExpectationRevisionTests(unittest.TestCase):
 def test_source_expected_recovery_and_independent_promise_controls(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/argo-recovery-expectation.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields'],d['new_context_entries']),(205,1,0,0));self.assertEqual(len(d['decisions']),1)
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  e=d['decisions'][0];p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(p['translation'],e['translation']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertEqual(e['translation'],e['before_translation'].replace('就会恢复正常。','应该会恢复正常。'));self.assertEqual(e['translation'].count(chr(92)+'n'),2)
  self.assertEqual(len(d['retained_direct_promises']),5)
  for e in d['retained_direct_promises']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(p['translation'],e['translation']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
  for r in L('locales/zh-Hans/translation-workflow.json')['batches'][111:]:self.assertEqual(L(r['plan']['path'].replace('.json','.review.json'))['status'],'draft')
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
