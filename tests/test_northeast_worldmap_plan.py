import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NortheastWorldMapTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes())
        self.decision = json.loads((ROOT/'locales/zh-Hans/candidate-decisions/northeast-worldmap-image-labels.json').read_bytes())
        self.labels = {l['id']: l for l in self.plan['labels']}

    def test_coherent_ten_caption_inventory_and_honest_progress(self):
        d = self.decision
        self.assertEqual((d['new_text_layers'], len(d['entries'])), (10, 10))
        self.assertEqual((d['current_map_captions'], d['remaining_map_captions']), (11, 21))
        self.assertEqual((d['new_image_groups'], d['new_aliases'], d['INT_drafts_added']), (0, 0, 0))
        self.assertFalse(d['full_map_labels_translated'])
        self.assertFalse(d['game_rendering_verified'])
        for row in d['entries']:
            self.assertTrue(row['manual_review'])
            self.assertEqual(row['label'], self.labels[row['label']['id']])

    def test_previous_1083_language_layers_remain_identical(self):
        raw = json.dumps(self.plan['labels'][:1083], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '6b912a0cd3d7b31026ccf24fdee3f377efa767f3f2a7707cf8a3945a035d886e')

    def test_field_and_candidate_terminology_evidence_remain_explicit(self):
        wf = json.loads((ROOT/'locales/zh-Hans/translation-workflow.json').read_bytes())
        entries = {}
        for b in wf['batches']:
            entries.update({e['id']: e for e in json.loads((ROOT/b['plan']['path']).read_bytes())['entries']})
        for row in self.decision['entries']:
            for key in ['active_field_anchor', 'active_name_anchor']:
                if key in row:
                    e = row[key]
                    self.assertEqual(entries[e['source_id']]['source_sha256'], e['source_sha256'])
                    self.assertEqual(entries[e['source_id']]['translation'], e['translation'])
        town = next(r for r in self.decision['entries'] if r['name'] == 'belfort_region')
        self.assertEqual(town['active_term_anchor']['review_status'], 'candidate')

    def test_single_region_two_lines_preserves_text_and_native_points(self):
        l = self.labels['world_map_ruhalt_garrison']
        self.assertEqual(l['text'], '鲁哈尔特盆地南部军驻地')
        self.assertEqual(l['line_breaks'], [6])
        self.assertNotIn('\n', l['text'])
        edit = next(e for s in self.plan['sources'] for e in s['textures'] if e['object'] == 'Textures.WorldMap_Whole')
        self.assertEqual(edit['regions'][:11], ['world_map_lanzheim'] +
                         [r['label']['id'] for r in self.decision['entries']])
        self.assertLessEqual(len(edit['regions']), 32)
        self.assertIs(edit['preserve_unchanged_blocks'], True)
        self.assertEqual(len(self.decision['native_encoded_proof']['protected_regions']), 8)
        self.assertTrue(all(p['blocks_preserved'] for p in self.decision['native_encoded_proof']['protected_regions']))
        self.assertEqual(sorted(a['disc'] for a in self.decision['all_source_aliases']), [1, 2])
        self.assertTrue(self.decision['all_4145_headers_rechecked'])

    def test_repairs_are_hash_locked_sparse_masks_not_flat_plates(self):
        from PIL import Image
        for row in self.decision['entries']:
            l = row['label']
            repair = l['restoration']
            for key in ['mask', 'patch']:
                p = ROOT/repair[key]['path']
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), repair[key]['sha256'])
            mask = Image.open(ROOT/repair['mask']['path']).tobytes()
            patch = Image.open(ROOT/repair['patch']['path']).tobytes()
            self.assertFalse(set(mask)-{0,255})
            self.assertTrue(any(mask))
            self.assertLess(sum(bool(v) for v in mask), len(mask))
            self.assertTrue(all(patch[i*4+3] == 255 if v else patch[i*4:i*4+4] == bytes(4) for i,v in enumerate(mask)))
            self.assertNotIn('background_fill', l['style'])
