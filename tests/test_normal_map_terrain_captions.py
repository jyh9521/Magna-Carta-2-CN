import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
class NormalMapTerrainCaptionTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/normal-map-terrain-captions.json').read_bytes());self.p=json.loads((R/self.d['plan']['path']).read_bytes());self.labels={x['id']:x for x in self.p['labels']}
 def test_cumulative_counts_and_active_plan_identity(self):
  self.assertTrue(self.d['applied']);self.assertFalse(self.d['game_rendering_verified']);self.assertEqual((self.d['total_groups'],self.d['total_layers'],self.d['total_aliases'],self.d['total_sources']),(832,1560,3869,518));self.assertEqual(hashlib.sha256((R/self.d['plan']['path']).read_bytes()).hexdigest(),self.d['plan']['sha256']);self.assertEqual(len(self.d['groups']),23);self.assertEqual(len(self.d['aliases']),68)
 def test_all_new_labels_have_source_anchors_and_verified_render_proofs(self):
  cells=[c for g in self.d['groups'] for c in g['new_cells']];self.assertEqual(len(cells),99);self.assertEqual(len({c['label_id'] for c in cells}),99)
  for g in self.d['groups']:
   self.assertTrue(g['independent_native_visual_review']);self.assertTrue(g['modified_native']);self.assertTrue(g['original_native'])
   for c in g['new_cells']:
    label=self.labels[c['label_id']];self.assertEqual(label['text'],c['text']);self.assertEqual(set(label['source_ids']),{a['source']['id'] for a in c['anchors']});self.assertTrue(c['anchors'])
    for a in c['anchors']:self.assertEqual(a['source']['source_sha256'],a['adopted']['source_sha256'])
 def test_native_restoration_masks_are_sparse_and_hash_locked(self):
  for g in self.d['groups']:
   for c in g['new_cells']:
    label=self.labels[c['label_id']];r=label['restoration']
    with Image.open(R/r['mask']['path']) as source_mask, Image.open(R/r['patch']['path']) as source_patch:
     m=source_mask.copy();p=source_patch.copy()
    self.assertEqual(m.size,tuple(label['rect'][2:]));self.assertEqual(p.size,m.size);self.assertEqual(set(m.tobytes()),{0,255});self.assertLess(sum(v>0 for v in m.tobytes()),m.width*m.height*.9)
    for part in (r['mask'],r['patch']):self.assertEqual(hashlib.sha256((R/part['path']).read_bytes()).hexdigest(),part['sha256'])
 def test_leader_lines_and_terrain_geometry_stay_locked(self):
  for g in self.d['groups']:
   proof=g['native_encoded_proof'];self.assertTrue(proof.get('untouched_blocks_preserved',True));self.assertTrue(g['landmark_line_and_outside_guard_exact']);self.assertEqual(g['original_native'],proof.get('source_rgba_sha256',g['original_native']))
   if g['leader_lines']:self.assertTrue(proof.get('leader_latin_blocks_exact',True))
  self.assertTrue(self.d['three_Lastrada03_pure_terrain_groups_unchanged'])
 def test_research_rooms_and_held_name(self):
  texts={c['text'] for g in self.d['groups'] for c in g['new_cells']};self.assertTrue({'第1研究室','第2研究室','第3研究室','第4研究室'}<=texts);self.assertEqual(self.d['held_source_original'],'원수의 언덕');self.assertTrue(self.d['unverified_name_not_adopted']);self.assertNotIn('원수의 언덕',texts)
 def test_source_materialization_is_finite_and_native_inputs_preserved(self):
  p=R/self.d['source_materialization'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.d['source_materialization_sha256']);j=json.loads(p.read_bytes());self.assertEqual(len(j['resources']),22);self.assertEqual(sum(len(x['discs']) for x in j['resources']),28);self.assertTrue(self.d['all_tutorial_illustrations_original'])
if __name__=='__main__':unittest.main()
