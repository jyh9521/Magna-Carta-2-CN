from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class MaterialRequestAndHideRevisionTests(unittest.TestCase):
 def test_two_source_grounded_drafts_and_full_delivery_quest_retained(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/material-request-and-hide.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields']),(212,2,0));self.assertEqual(len(d['decisions']),2)
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  self.assertEqual({e['translation'] for e in d['decisions']},{'比尔特大叔要的工具','可从有皮的怪物身上取得'})
  for e in d['decisions']:
   p=entries[e['id']];self.assertEqual(hashlib.sha256(e['source'].encode()).hexdigest(),p['source_sha256']);self.assertEqual(p['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertEqual(e['translation'].count(chr(92)+'n'),0)
  self.assertEqual(len(d['retained_delivery_quest']),20)
  for e in d['retained_delivery_quest']:self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256'])
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
