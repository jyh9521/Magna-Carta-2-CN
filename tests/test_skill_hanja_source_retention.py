from pathlib import Path
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1]
class SkillHanjaSourceRetentionTests(unittest.TestCase):
 def test_aligned_hanja_evidence_does_not_override_korean_leg_name(self):
  L=lambda p:json.loads((R/p).read_bytes());H=lambda s:hashlib.sha256(s.encode()).hexdigest();d=L('locales/zh-Hans/candidate-decisions/skill-hanja-source-retention.json');self.assertEqual((d['context_fields'],d['source_physical'],d['retained_original_count'],d['translation_edits']),(324,334,10,0));entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['retained_entries']),324)
  for e in d['retained_entries']:
   self.assertEqual(H(e['source']),e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(H(e['translation']),e['translation_sha256'])
  for e in d['retained_originals']:self.assertNotIn(e['id'],entries)
  self.assertEqual(len(d['name_controls']),6);self.assertEqual(len(d['parallel_locale_sources']),30)
  by={(e['section'],e['key']):e for e in d['name_controls']};self.assertEqual(by['Crocell_Style1','Crocell_Skill04']['translation'],'镇炎螺旋腿');self.assertIn('퇴',by['Crocell_Style1','Crocell_Skill04']['source'])
  for disc in [1,2]:
   rows={(e['section'],e['key']):e for e in d['parallel_locale_sources'] if e['disc']==disc};self.assertEqual(len(rows),15);self.assertEqual(rows['Juto_Style2','Juto_Skill03']['source'],'破鎖乱閃');self.assertEqual(rows['Crocell_Style1','Crocell_Skill02']['source'],'爆鎖陣');self.assertEqual(rows['Crocell_Style1','Crocell_Skill03']['source'],'鎮炎怒号脚');self.assertEqual(rows['Crocell_Style1','Crocell_Skill04']['source'],'鎮炎螺旋槌');self.assertEqual(rows['Crocell_Style2','Crocell_Normal']['source'],'玉炎旋風')
   for e in rows.values():self.assertEqual(H(e['source']),e['source_sha256'])
  rec=next(e for e in L('locales/zh-Hans/followup-register.json')['records'] if e['record']=='skill-status-naming-followup.json');self.assertEqual(rec['latest_resolution']['phase'],279)
  for f in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[f])
if __name__=='__main__':unittest.main()
