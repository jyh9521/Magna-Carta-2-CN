from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class ThermalDomainDistinctionTests(unittest.TestCase):
 def test_retained_status_story_and_weapon_domains(self):
  L=lambda p:json.loads((R/p).read_bytes());H=lambda s:hashlib.sha256(s.encode()).hexdigest();d=L('locales/zh-Hans/candidate-decisions/thermal-domain-distinction.json');self.assertEqual((d['core_context_fields'],d['context_fields'],d['source_physical'],d['translation_edits']),(269,357,358,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['retained_entries']),357)
  for e in d['retained_entries']:
   self.assertEqual(H(e['source']),e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(H(e['translation']),e['translation_sha256'])
  self.assertEqual(len(d['retained_originals']),1)
  for e in d['retained_originals']:self.assertNotIn(e['id'],entries);self.assertEqual(H(e['source']),e['source_sha256']);self.assertIn('게임에 안 나오는 대사',e['source'])
  hits={i for i,e in entries.items() if '灼热' in e['translation'] or '灼伤' in e['translation']};self.assertEqual(hits,set(d['canonical_alias_search']['ids']));self.assertEqual(len(hits),3)
  rows={(e['section'],e['key']):e for e in d['retained_entries']}
  for section,n in [('Recover',207),('Zephie_Style1',36),('CSMB10_20',10),('CSMB10_80',75)]:self.assertEqual(sum(s==section for s,k in rows),n)
  self.assertIn('灼伤',rows['CSMB10_20','voc_csmb_1020_08']['translation']);self.assertIn('灼伤',rows['CSMB10_80','voc_csmb_1080_27']['translation']);self.assertEqual(rows['Weapon_fireball_crocell','426_fireball']['source'],'작열');self.assertEqual(rows['Weapon_fireball_crocell','426_fireball']['translation'],'灼热');self.assertIn('精神+140',rows['Weapon_fireball_crocell','426_fireball_D']['translation'])
  rec=next(e for e in L('locales/zh-Hans/followup-register.json')['records'] if e['record']=='status-terminology-followups.json');self.assertEqual(rec['latest_resolution']['phase'],281)
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified','runtime_status_identity_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
