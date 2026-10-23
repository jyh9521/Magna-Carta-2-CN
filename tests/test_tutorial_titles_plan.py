import json,unittest,hashlib
from pathlib import Path
from tools.texture_overlay import image_id,render_area
R=Path(__file__).resolve().parents[1]
class CompleteTutorialTitleTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.p=json.loads((R/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes());c.d=json.loads((R/'locales/zh-Hans/candidate-decisions/tutorial-title-image-labels.json').read_bytes());c.l={l['id']:l for l in c.p['labels']};c.s={s['path']:s for s in c.p['sources']}
 def test_cohort_counts_and_inventory_floor(self):
  self.assertGreaterEqual(len(self.p['sources']),325);self.assertGreaterEqual(len(self.l),988);self.assertGreaterEqual(len({image_id(e) for s in self.p['sources'] for e in s['textures']}),548);self.assertEqual((self.d['image_groups'],self.d['text_layers'],len(self.d['new_source_aliases'])),(28,28,102));self.assertEqual(len({a['resource_path'] for a in self.d['new_source_aliases']}),48)
 def test_all_actual_aliases_enrolled_with_independent_disc_provenance(self):
  self.assertEqual(len(self.d['all_title_aliases']),108)
  for d in [1,2]:self.assertEqual(sum(a['disc']==d for a in self.d['all_title_aliases']),54)
  for a in self.d['all_title_aliases']:
   s=self.s[a['resource_path']];e=next(e for e in s['textures'] if e['object']==a['path']);self.assertIn(a['disc'],s['discs']);self.assertEqual(s['original']['sha256'],a['source_sha256']);self.assertEqual(e['payload_sha256'],a['payload_sha256']);self.assertEqual(e['tiled_sha256'],a['tiled_sha256'])
 def test_visible_reading_and_field_hashes_are_not_confused(self):
  for g in self.d['entries']:
   l=self.l[g['label']['id']];e=g['evidence'];self.assertEqual(l['text'],e['candidate_translation']);self.assertEqual(l['source_text_sha256'],hashlib.sha256(e['visible_source'].encode()).hexdigest());self.assertEqual(e['source_text_sha256'],hashlib.sha256(e['source_text'].encode()).hexdigest());self.assertEqual(l['source_ids'],[e['source_id']]);self.assertEqual(l['translation_basis'],e['basis'])
 def test_japanese_assets_use_explicit_semantic_or_fragment_basis(self):
  gs=[g for g in self.d['entries'] if any('\u3040'<=c<='\u30ff' for c in g['evidence']['visible_source'])];self.assertEqual(len(gs),5);self.assertTrue(all('High-confidence' in g['evidence']['basis'] for g in gs));self.assertEqual({g['label']['text'] for g in gs},{'注视模式','角色切换提示','交流','（其一）救援请求','（其二）协同请求'})
 def test_chain_drive_does_not_copy_the_whole_field(self):
  g=next(g for g in self.d['entries'] if g['evidence']['visible_source']=='체인 드라이브');self.assertEqual(g['label']['text'],'连锁超限');self.assertEqual(g['evidence']['applied_translation'],'连锁超限与连锁终结');self.assertIn('fragment',g['evidence']['basis'])
 def test_all_masks_and_protected_strips_are_disjoint(self):
  for a in self.d['new_source_aliases']:
   self.assertTrue(a['atlas_supported'])
   e=next(e for e in self.s[a['resource_path']]['textures'] if e['object']==a['path']);w,h=e['dimensions'];self.assertEqual(h,64);self.assertEqual(self.l[e['regions'][0]]['rect'],[0,4,w,56]);self.assertEqual([p['rect'] for p in e['protected_regions']],[[0,0,w,4],[0,60,w,4]]);self.assertNotIn('profile',e);self.assertNotIn('channel_mode',e)
 def test_numeral_only_exports_are_preserved(self):
  self.assertEqual(len(self.d['retained_numerals']),4)
  for a in self.d['retained_numerals']:self.assertNotIn(a['object'],[e['object'] for e in self.s[a['resource_path']]['textures']])
 def test_alias_namespace_and_full_resource_identity_are_explicit(self):
  self.assertTrue(self.d['all_4145_headers_rechecked']);self.assertEqual(self.d['prefilter_contract'],'include numbered FName base names;exact parsed path and canonical namespace select aliases')
  for a in self.d['all_title_aliases']:self.assertTrue(a['identity']['canonical_path']);self.assertEqual(len(a['payload_sha256']),64);self.assertEqual(len(a['source_sha256']),64)
 def test_actual_render_bounds_and_review_state(self):
  self.assertLessEqual(sum(render_area(l) for l in self.p['labels']),16*1024*1024);self.assertTrue(all(g['manual_review'] for g in self.d['entries']));self.assertFalse(self.d['game_rendering_verified'])
if __name__=='__main__':unittest.main()
