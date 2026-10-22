from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class MerchantAccidentSympathyTests(unittest.TestCase):
 def test_accident_reaction_is_sympathetic_without_global_replacement(self):
  L=lambda p:json.loads((R/p).read_bytes());d=L('locales/zh-Hans/candidate-decisions/merchant-accident-sympathy.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['known_originals_retained']),(216,1,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['decisions']),1)
  for e in d['decisions']:
   self.assertIn('사고를 당하셨다구요',e['source']);self.assertIn('저런',e['source']);self.assertEqual(e['before_translation'],'啊，是遭遇了意外啊……真是的……');self.assertEqual(e['translation'],'啊，是遭遇了意外啊……哎呀……');self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertEqual(e['translation'].count(chr(92)+'n'),0)
  self.assertEqual(len(d['retained_family_controls']),7)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertTrue(any('真是的' in e['translation'] for e in d['retained_family_controls']));self.assertTrue(any('内斯汀'==e['translation'] for e in d['retained_family_controls']));self.assertTrue(any('问好' in e['translation'] for e in d['retained_family_controls']))
  self.assertEqual(d['new_primary_consistency_fields'],0)
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
