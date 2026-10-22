from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class GenderQuestionPerspectiveTests(unittest.TestCase):
 def test_only_explicit_gender_question_loses_premature_gender_prefix(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/gender-question-perspective.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['known_originals_retained']),(155,1,0))
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  self.assertEqual(len(d['decisions']),1)
  for e in d['decisions']:
   self.assertEqual(e['source'],'어떤 사람이야? 남자? 여자?');self.assertEqual(e['before_translation'],'她是个什么样的人？男的？女的？');self.assertEqual(e['translation'],'是个什么样的人？男的？女的？');self.assertEqual(e['translation'].count(chr(92)+'n'),0)
   self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256'])
  self.assertEqual(len(d['retained_family_controls']),7)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertTrue(any('她' in e['translation'] for e in d['retained_family_controls']));self.assertTrue(any('姑娘' in e['translation'] for e in d['retained_family_controls']));self.assertTrue(any('姐姐' in e['translation'] for e in d['retained_family_controls']))
  self.assertEqual(d['new_primary_consistency_fields'],0)
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
