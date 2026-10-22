from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class JutoBurnoutMetaphorTests(unittest.TestCase):
 def test_two_independent_keys_keep_burnout_metaphor_and_layout(self):
  def L(p):return json.loads((R/p).read_bytes())
  d=L('locales/zh-Hans/candidate-decisions/juto-burnout-metaphor.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['known_originals_retained']),(223,2,9))
  entries={}
  for r in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(r['plan']['path'])['entries']})
  self.assertEqual(len({e['id'] for e in d['decisions']}),2)
  for e in d['decisions']:
   self.assertIn('燃え尽きたかよ',e['source']);self.assertIn('燃尽了吗',e['translation']);self.assertEqual(e['before_translation'].replace('烧光了吗','燃尽了吗'),e['translation']);self.assertEqual(e['source'].count(chr(92)+'n'),2);self.assertEqual(e['translation'].count(chr(92)+'n'),2)
   self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256'])
  self.assertEqual(len(d['retained_family_controls']),6)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertEqual(d['new_primary_consistency_fields'],0)
  for flag in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[flag])
if __name__=='__main__':unittest.main()
