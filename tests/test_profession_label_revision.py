"""The same source profession keeps one draft label across role and quest."""
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
IDENTITY='coalesced:7fda95fce79de7e56515da2f2f5dc803154a53d92f45f53a5383d0e94bf9ad99'
SOURCE='420763e723e97dcfbcdca2536b4aacbdc417f771d140e5f230a76a8961a36405'
def load(name):return json.loads((ROOT/name).read_bytes())
class ProfessionLabelRevisionTests(unittest.TestCase):
 def test_exact_role_identity_and_draft_status(self):
  p=load('locales/zh-Hans/batch-094.json');e=next(e for e in p['entries'] if e['id']==IDENTITY)
  self.assertEqual(e,dict(id=IDENTITY,source_sha256=SOURCE,translation='新手鞣皮匠'))
  self.assertEqual(load('locales/zh-Hans/batch-094.review.json')['status'],'draft')
 def test_single_source_plan_and_matching_quest_profession(self):
  w=load('locales/zh-Hans/translation-workflow.json');self.assertEqual(len(w['batches']),119)
  refs=[b['plan'] for b in w['batches']];r=next(r for r in refs if r['path']=='locales/zh-Hans/batch-094.json')
  self.assertEqual(r['sha256'],hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest())
  entries=[e for r in refs for e in load(r['path'])['entries']];ids=[e['id'] for e in entries]
  self.assertEqual(len(ids),14135);self.assertEqual(len(ids),len(set(ids)))
  matches=[e for e in entries if e['source_sha256']==SOURCE]
  self.assertEqual(len(matches),2);self.assertEqual({e['translation'] for e in matches},{'新手鞣皮匠'})
if __name__=='__main__':unittest.main()
