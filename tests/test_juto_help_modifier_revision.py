from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class JutoHelpModifierRevisionTests(unittest.TestCase):
 def test_four_source_grounded_draft_targets_without_recount(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/juto-help-modifier.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields'],d['new_context_entries']),(223,4,0,0));self.assertEqual(len(d['decisions']),4)
  batch={e['id']:e for e in L('locales/zh-Hans/batch-115.json')['entries']}
  for e in d['decisions']:
   self.assertEqual(batch[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(batch[e['id']]['translation'],'看来不需要我帮忙啊……');self.assertEqual(hashlib.sha256(batch[e['id']]['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertNotIn('这种人',e['translation'])
  self.assertEqual(L('locales/zh-Hans/batch-115.review.json')['status'],'draft')
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
  self.assertFalse(d['held_candidates'][0]['adopted'])
if __name__=='__main__':unittest.main()
