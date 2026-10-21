from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class StoryFinalTrialsEpilogueConsistencyTests(unittest.TestCase):
 def test_existing_drafts_locked_without_context_recount(self):
  def load(p):return json.loads((R/p).read_bytes())
  r=load('locales/zh-Hans/consistency-reviews/story-final-trials-epilogue.json')
  self.assertEqual((len(r['entries']),len(r['scopes'])),(226,23))
  self.assertEqual((sum(s['physical'] for s in r['scopes']),sum(s['planned'] for s in r['scopes'])),(227,226))
  self.assertEqual((r['new_translations'],r['new_context_entries']),(0,0))
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(r[flag])
  entries={}
  for ref in load('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in load(ref['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in r['entries']}),226)
  for e in r['entries']:
   p=entries[e['id']];self.assertEqual(p['source_sha256'],e['source_sha256']);self.assertEqual(hashlib.sha256(p['translation'].encode()).hexdigest(),e['translation_sha256'])
 def test_chapter_twelve_complete_disjoint_coverage(self):
  load=lambda n:json.loads((R/'locales/zh-Hans/consistency-reviews'/n).read_bytes())
  a=load('story-ch12-departure-ascent.json');b=load('story-final-trials-epilogue.json');old={e['id'] for e in a['entries']};new=set(b['group_entry_ids']['CSMB12']);self.assertFalse(old&new);self.assertEqual(len(old|new),304)
  scopes=[s for d in [a,b] for s in d['scopes'] if s['section'].startswith('CSMB12_')];self.assertEqual((len(scopes),sum(s['physical'] for s in scopes),sum(s['planned'] for s in scopes),sum(s['original_retained'] for s in scopes)),(27,305,304,1));self.assertEqual(len({s['section'] for s in scopes}),27)
 def test_chapter_thirteen_and_epilogue_group_partition(self):
  b=json.loads((R/'locales/zh-Hans/consistency-reviews/story-final-trials-epilogue.json').read_bytes());seen=set()
  for group,n,sections in [('CSMB12',135,16),('CSMB13',40,3),('CSMBE',51,4)]:
   ids=b['group_entry_ids'][group];self.assertEqual(len(ids),n);self.assertFalse(set(ids)&seen);seen.update(ids);scopes=[s for s in b['scopes'] if s['section'].startswith(group+'_')];self.assertEqual((len(scopes),sum(s['planned'] for s in scopes)),(sections,n))
  self.assertEqual(seen,{e['id'] for e in b['entries']})
if __name__=='__main__':unittest.main()
