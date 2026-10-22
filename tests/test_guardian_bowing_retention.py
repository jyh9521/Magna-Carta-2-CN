from pathlib import Path
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
class GuardianBowingRetentionTests(unittest.TestCase):
 def test_contextual_antecedent_and_original_participant_preserved(self):
  L=lambda p:json.loads((R/p).read_bytes());H=lambda s:hashlib.sha256(s.encode()).hexdigest()
  d=L('locales/zh-Hans/candidate-decisions/guardian-bowing-retention.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields']),(168,0,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['retained_entries']),168)
  for e in d['retained_entries']:
   self.assertEqual(H(e['source']),e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(H(e['translation']),e['translation_sha256'])
  by={e['key']:e for e in d['retained_entries']};self.assertIn('守护者',by['voc_csmb_0231_14']['translation']);self.assertIn('怎么打赢',by['voc_csmb_0231_15']['translation']);self.assertEqual(by['voc_csmb_0238_13']['translation'],'可是，你也不想向亚历克斯低头，不是吗？');self.assertIn('넌',by['voc_csmb_0238_13']['source'])
  self.assertEqual(len(d['parallel_locale_sources']),44)
  for disc in [1,2]:
   rows={e['key']:e for e in d['parallel_locale_sources'] if e['disc']==disc};self.assertEqual(len(rows),22);self.assertIn('俺です',rows['voc_csmb_0238_13']['source']);self.assertIn('軍には入らなかった',rows['voc_csmb_0238_14']['source'])
   for e in rows.values():self.assertEqual(H(e['source']),e['source_sha256'])
  self.assertTrue(d['alignment']['offset_is_local_observation_not_general_rule'])
  for k in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[k])
if __name__=='__main__':unittest.main()
