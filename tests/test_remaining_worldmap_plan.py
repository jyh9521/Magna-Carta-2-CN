import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RemainingWorldMapTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes())
        self.decision = json.loads((ROOT/'locales/zh-Hans/candidate-decisions/remaining-worldmap-image-labels.json').read_bytes())

    def test_exact_21_followup_captions_complete_only_this_map(self):
        d = self.decision
        self.assertEqual((len(d['entries']), d['new_text_layers']), (21, 21))
        self.assertEqual((d['current_map_captions'], d['remaining_map_captions']), (32, 0))
        self.assertTrue(d['full_map_labels_translated'])
        self.assertFalse(d['all_game_image_text_translated'])
        self.assertFalse(d['game_rendering_verified'])
        self.assertEqual((d['new_image_groups'], d['new_aliases'], d['INT_drafts_added']), (0, 0, 0))
        labels = {l['id']: l for l in self.plan['labels']}
        for row in d['entries']:
            self.assertTrue(row['manual_review'])
            self.assertEqual(row['label'], labels[row['label']['id']])

    def test_prior_1093_layers_are_unchanged(self):
        data = json.dumps(self.plan['labels'][:1093], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(data).hexdigest(), '292401cee05259e4e31220ce3c1855aa59446ae4520e796621fc5125cb398e0a')

    def test_all_corresponding_fields_remain_source_locked(self):
        workflow = json.loads((ROOT/'locales/zh-Hans/translation-workflow.json').read_bytes())
        entries = {}
        for batch in workflow['batches']:
            entries.update({e['id']: e for e in json.loads((ROOT/batch['plan']['path']).read_bytes())['entries']})
        for row in self.decision['entries']:
            e = row['active_field_anchor']
            self.assertEqual(entries[e['source_id']]['source_sha256'], e['source_sha256'])
            self.assertEqual(entries[e['source_id']]['translation'], e['translation'])

    def test_32_regions_fit_existing_bound_and_marker_controls_are_explicit(self):
        edit = next(e for s in self.plan['sources'] for e in s['textures'] if e['object'] == 'Textures.WorldMap_Whole')
        self.assertEqual(len(edit['regions']), 32)
        self.assertEqual(len(set(edit['regions'])), 32)
        self.assertIs(edit['preserve_unchanged_blocks'], True)
        markers = self.decision['nineteen_marker_regions']
        self.assertEqual(len(markers), 19)
        self.assertEqual(len({p['id'] for p in markers}), 19)
        self.assertTrue(all(p['unchanged'] and len(p['rgba_sha256']) == 64 for p in markers))
        self.assertEqual(sorted(a['disc'] for a in self.decision['all_source_aliases']), [1, 2])

    def test_repair_pngs_are_sparse_and_hash_guarded(self):
        from PIL import Image
        for row in self.decision['entries']:
            repair = row['label']['restoration']
            for key in ['patch', 'mask']:
                p = ROOT/repair[key]['path']
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), repair[key]['sha256'])
            mask = Image.open(ROOT/repair['mask']['path']).tobytes()
            pixels = Image.open(ROOT/repair['patch']['path']).tobytes()
            self.assertFalse(set(mask)-{0,255})
            self.assertGreater(sum(bool(v) for v in mask), 0)
            self.assertLess(sum(bool(v) for v in mask), len(mask))
            self.assertTrue(all(pixels[i*4+3] == 255 if v else pixels[i*4:i*4+4] == bytes(4) for i,v in enumerate(mask)))
            self.assertNotIn('background_fill', row['label']['style'])
