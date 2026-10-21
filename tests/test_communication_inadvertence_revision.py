from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class CommunicationInadvertenceRevisionTests(unittest.TestCase):
 def test_three_source_grounded_drafts_and_explicit_forgetting_controls(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/communication-inadvertence.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields'],d['new_context_entries']),(184,3,0,0));self.assertEqual(len(d['decisions']),3)
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  for e in d['decisions']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(p['translation'],e['translation']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertIn('疏忽',e['translation']);self.assertNotIn('忘',e['translation']);self.assertEqual(e['translation'].count(chr(92)+'n'),2)
  self.assertEqual(len(d['retained_explicit_forgetting']),2)
  for e in d['retained_explicit_forgetting']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(p['translation'],e['translation']);self.assertIn('忘',p['translation'])
  for plan in ['batch-113.review.json','batch-116.review.json']:self.assertEqual(L('locales/zh-Hans/'+plan)['status'],'draft')
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
