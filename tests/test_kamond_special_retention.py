from pathlib import Path
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
class KamondSpecialRetentionTests(unittest.TestCase):
 def test_complete_families_retained_without_invented_mechanics(self):
  L=lambda p:json.loads((R/p).read_bytes());H=lambda s:hashlib.sha256(s.encode()).hexdigest()
  d=L('locales/zh-Hans/candidate-decisions/kamond-special-retention.json');self.assertEqual((d['context_fields'],d['selected_family_fields'],d['linked_fields'],d['translation_edits']),(174,165,9,0));self.assertFalse(d['full_section']);self.assertEqual(d['full_section_source_fields'],309)
  entries={}
  for b in L('locales/zh-Hans/translation-workflow.json')['batches']:entries.update({e['id']:e for e in L(b['plan']['path'])['entries']})
  self.assertEqual(len(d['retained_entries']),174)
  for e in d['retained_entries']:
   self.assertEqual(H(e['source']),e['source_sha256']);self.assertEqual(entries[e['id']]['source_sha256'],e['source_sha256']);self.assertEqual(entries[e['id']]['translation'],e['translation']);self.assertEqual(H(e['translation']),e['translation_sha256'])
  by={e['key']:e for e in d['retained_entries'] if e['section']=='Karmond'}
  self.assertEqual(len(by),165)
  self.assertEqual(by['1745_Karmond_S']['translation'],'普通攻击成功率提高 ');self.assertEqual(by['1746_Karmond_S']['translation'],'命中率+10%');self.assertEqual(by['1738_Karmond']['translation'],'黄金三叶草');self.assertEqual(by['1716_Karmond']['translation'],'晕眩一击');self.assertEqual(by['1720_Karmond']['translation'],'眩晕一击')
  for t in d['term_controls']:self.assertEqual(t['review_status'],'candidate');self.assertEqual(t['relation'],'unverified')
  self.assertEqual(len(d['term_controls']),5)
  for k in ['human_finalized','runtime_layout_approved','game_rendering_verified']:self.assertFalse(d[k])
if __name__=='__main__':unittest.main()
