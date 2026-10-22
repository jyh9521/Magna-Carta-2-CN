from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class HusbandRevengeEllipsisTests(unittest.TestCase):
 def test_unfinished_revenge_object_does_not_become_killer_noun(self):
  L=lambda p:json.loads((R/p).read_bytes());d=L('locales/zh-Hans/candidate-decisions/husband-revenge-ellipsis.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['known_originals_retained']),(242,1,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['decisions']),1)
  for e in d['decisions']:
   self.assertIn('제 남편의 원수를...',e['source']);self.assertEqual(e['before_translation'],'我实在没法原谅拉提族。杀害我丈夫的仇人……');self.assertEqual(e['translation'],'我实在没法原谅拉提族。我丈夫的仇……');self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(hashlib.sha256(e['translation'].encode()).hexdigest(),e['translation_sha256']);self.assertEqual(e['translation'].count(chr(92)+'n'),0)
  self.assertEqual(len(d['retained_family_controls']),7)
  for e in d['retained_family_controls']:self.assertEqual(entries[e['id']]['translation'],e['translation'])
  self.assertTrue(any('杀害' in e['translation'] for e in d['retained_family_controls']));self.assertTrue(any('不知道怎么样' in e['translation'] for e in d['retained_family_controls']));self.assertEqual(len(d['parallel_locale_sources']),4)
  for disc in [1,2]:
   rows={x['key']:x for x in d['parallel_locale_sources'] if x['disc']==disc};self.assertIn('夫の仇を討ちます',rows['04_202_00']['source'])
   for x in rows.values():self.assertEqual(hashlib.sha256(x['source'].encode()).hexdigest(),x['source_sha256'])
  self.assertEqual(d['new_primary_consistency_fields'],0)
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
