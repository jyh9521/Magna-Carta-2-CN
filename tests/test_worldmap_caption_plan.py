import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorldMapCaptionPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes())
        self.decision = json.loads((ROOT/'locales/zh-Hans/candidate-decisions/worldmap-caption-image-labels.json').read_bytes())

    def test_exact_reviewed_caption_and_bounded_progress(self):
        d = self.decision
        self.assertEqual((d['adopted_map_captions'], d['remaining_map_captions']), (1, 31))
        self.assertEqual(d['translation'], '兰兹海姆')
        self.assertEqual(d['term_id'], 'mc2-opening-047')
        self.assertFalse(d['full_map_labels_translated'])
        self.assertFalse(d['game_rendering_verified'])
        self.assertEqual(d['INT_drafts_added'], 0)
        self.assertTrue(d['manual_review'])
        self.assertEqual(d['label'], next(l for l in self.plan['labels'] if l['id'] == d['label']['id']))

    def test_prior_1082_layers_are_unchanged(self):
        raw = json.dumps(self.plan['labels'][:1082], ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '387f26a686786bddbbc63f144f963dd5feebe1cc9b6d187500f67f5ab0f73267')

    def test_sparse_opaque_masked_repair_has_no_rectangular_fill(self):
        from PIL import Image
        label = self.decision['label']
        repair = label['restoration']
        for key in ['patch', 'mask']:
            p = ROOT/repair[key]['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), repair[key]['sha256'])
        patch = Image.open(ROOT/repair['patch']['path']).tobytes()
        mask = Image.open(ROOT/repair['mask']['path']).tobytes()
        self.assertFalse(set(mask)-{0, 255})
        self.assertGreater(sum(bool(v) for v in mask), len(mask)//2)
        self.assertLess(sum(bool(v) for v in mask), len(mask)*4//5)
        self.assertTrue(all(patch[i*4+3] == 255 if v else patch[i*4:i*4+4] == bytes(4) for i,v in enumerate(mask)))
        self.assertNotIn('background_fill', label['style'])

    def test_both_original_disc_aliases_and_exact_unchanged_blocks(self):
        d = self.decision
        self.assertTrue(d['all_4145_headers_rechecked'])
        self.assertEqual(sorted(a['disc'] for a in d['all_source_aliases']), [1, 2])
        source = next(s for s in self.plan['sources'] if s['path'].endswith('/UI_WorldMap.xxx'))
        edit = next(e for e in source['textures'] if e['object'] == 'Textures.WorldMap_Whole')
        self.assertEqual(edit['regions'][:1], ['world_map_lanzheim'])
        self.assertEqual(edit['profile']['format'], 5)
        self.assertEqual(edit['channel_mode'], 'opaque-rgb')
        self.assertIs(edit['preserve_unchanged_blocks'], True)
        self.assertGreater(d['native_encoded_proof']['unchanged_region_blocks_preserved'], 0)
        for a in d['all_source_aliases']:
            self.assertEqual(a['source_sha256'], source['original']['sha256'])
            self.assertEqual(a['payload_sha256'], edit['payload_sha256'])
            self.assertEqual(a['tiled_sha256'], edit['tiled_sha256'])
