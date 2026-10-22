from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class EscortSpeechRetentionTests(unittest.TestCase):
 def test_contextual_escort_urge_retained_without_added_participants(self):
  L=lambda p:json.loads((R/p).read_bytes());H=lambda s:hashlib.sha256(s.encode()).hexdigest();d=L('locales/zh-Hans/candidate-decisions/escort-speech-retention.json');self.assertEqual((d['context_fields'],d['translation_edits'],d['new_primary_consistency_fields']),(173,0,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['retained_entries']),173)
  for e in d['retained_entries']:
   self.assertEqual(H(e['source']),e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(H(e['translation']),e['translation_sha256'])
  by={e['key']:e for e in d['retained_entries']};self.assertEqual(by['voc_csmb_03126_04']['translation'],'朱特，过去护卫她。');self.assertIn('호위해야겠다',by['voc_csmb_03126_04']['source']);self.assertEqual(by['voc_csmb_03126_05']['translation'],'嗯，知道了。');self.assertIn('洁菲',by['voc_csmb_03126_03']['translation'])
  self.assertEqual(len(d['parallel_locale_sources']),16)
  for disc in [1,2]:
   rows={e['key']:e for e in d['parallel_locale_sources'] if e['disc']==disc};self.assertEqual(len(rows),8);self.assertIn('援護しよう',rows['voc_csmb_03126_05']['source']);self.assertIn('行こう',rows['voc_csmb_03126_06']['source']);self.assertIn('包囲',rows['voc_csmb_03126_04']['source'])
   for e in rows.values():self.assertEqual(H(e['source']),e['source_sha256'])
  self.assertTrue(d['alignment']['offset_is_local_observation_not_general_rule'])
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
