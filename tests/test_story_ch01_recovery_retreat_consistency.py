from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryCh01RecoveryRetreatConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-ch01-recovery-retreat.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(151,10))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(151,151))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),151)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_complete_chapter_one_scope_inventory(self):
  r=json.loads((R/'locales/zh-Hans/consistency-reviews/story-ch01-recovery-retreat.json').read_bytes())
  expected={'CSMB01_05':27,'CSMB01_07':2,'CSMB01_11':23,'CSMB01_15':22,'CSMB01_17':1,'CSMB01_21':16,'CSMB01_25':18,'CSMB01_31':24,'CSMB01_47':12,'CSMB01_48':6}
  self.assertEqual(len(r['scopes']),len(expected));self.assertEqual({s['section']:s['planned'] for s in r['scopes']},expected)
  for s in r['scopes']:self.assertEqual((s['physical'],s['planned'],s['original_retained']),(expected[s['section']],expected[s['section']],0))
  self.assertEqual(sum(expected.values()),151)
if __name__=='__main__':unittest.main()
