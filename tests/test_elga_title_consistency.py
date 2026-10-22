from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class ElgaTitleConsistencyTests(unittest.TestCase):
 def test_same_title_reuses_shared_candidate_without_changing_perspectives(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/elga-title-consistency.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['known_originals_retained']),(178,2,0))
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  term=next(e for e in L('locales/zh-Hans/terms.json')['terms'] if e['id']=='mc2-island-075')
  self.assertEqual(d['shared_title_candidate'],term);self.assertEqual((term['source'],term['target'],term['review_status'],term['relation']),('학살자 엘가','屠杀者艾尔加','candidate','unverified'))
  self.assertEqual(len({e['id'] for e in d['decisions']}),2)
  for e in d['decisions']:
   self.assertIn(term['source'],e['source']);self.assertIn(term['target'],e['translation']);self.assertEqual(e['before_translation'].replace('屠夫艾尔加','屠杀者艾尔加'),e['translation']);self.assertEqual(e['translation'].count(chr(92)+'n'),0)
   self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256'])
  self.assertEqual(len(d['retained_family_controls']),6)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertEqual(d['new_primary_consistency_fields'],0)
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
