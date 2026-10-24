"""Source-data guards for skill sprites and transparent world-map header captions."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillWorldMapPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((ROOT / 'locales/zh-Hans/texture-overlays/ui-labels.json').read_bytes())
        cls.decision = json.loads((ROOT / 'locales/zh-Hans/candidate-decisions/skill-worldmap-image-labels.json').read_bytes())
        cls.labels = {l['id']: l for l in cls.plan['labels']}

    def test_complete_selected_inventory_and_original_disc_provenance(self):
        d = self.decision
        self.assertEqual((d['image_groups'], d['text_layers'], len(d['all_source_aliases'])), (38, 39, 80))
        self.assertEqual([sum(a['disc'] == dn for a in d['all_source_aliases']) for dn in (1, 2)], [40, 40])
        self.assertTrue(d['all_4145_headers_rechecked'])
        sources = {s['path']: s for s in self.plan['sources']}
        for a in d['all_source_aliases']:
            s = sources[a['resource_path']]
            self.assertIn(a['disc'], s['discs'])
            self.assertEqual(s['original']['sha256'], a['source_sha256'])
            e = next(e for e in s['textures'] if e['object'] == a['path'])
            self.assertEqual(e['payload_sha256'], a['payload_sha256'])
            self.assertEqual(e['tiled_sha256'], a['tiled_sha256'])

    def test_visible_wording_and_locked_language_layers(self):
        for g in self.decision['entries']:
            self.assertTrue(g['manual_review'])
            for l, cell in zip(g['labels'], g['source_group']['cells']):
                self.assertEqual(l, self.labels[l['id']])
                self.assertEqual(l['text'], cell['candidate_translation'])
                self.assertEqual(l['source_text_sha256'], hashlib.sha256(cell['visible_source'].encode()).hexdigest())
                self.assertNotIn('background_fill', l.get('style', {}))

    def test_original_1043_layers_are_unchanged(self):
        raw = json.dumps(self.plan['labels'][:1043], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'a118f3fefa5321e206d9c5803e0f39b66b7659e5bee7538a72c98f98a1bc82c8')

    def test_current_field_anchors_and_literal_only_names_are_distinguished(self):
        anchored = [c for g in self.decision['entries'] for c in g['source_group']['cells'] if c.get('evidence')]
        self.assertEqual(len(anchored), 29)
        workflow = json.loads((ROOT / 'locales/zh-Hans/translation-workflow.json').read_bytes())
        entries = {}
        for batch in workflow['batches']:
            entries.update({e['id']: e for e in json.loads((ROOT / batch['plan']['path']).read_bytes())['entries']})
        for c in anchored:
            e = c['evidence']
            self.assertEqual(entries[e['source_id']]['source_sha256'], e['source_sha256'])
            self.assertEqual(entries[e['source_id']]['translation'], c['candidate_translation'])
        self.assertEqual(self.labels['skill_caption_025']['text'], '凌空震踢')
        self.assertEqual(self.labels['skill_caption_034']['text'], '神圣波动')

    def test_native_header_preserves_emblem_marker_and_true_transparency(self):
        from PIL import Image
        for lid in ['world_map_header_title', 'world_map_location_list']:
            l = self.labels[lid]
            r = l['restoration']
            im = Image.open(ROOT / r['patch']['path'])
            mask = Image.open(ROOT / r['mask']['path'])
            self.assertIsNone(im.getbbox())  # Erase glyphs into transparency, never an opaque plate.
            self.assertIsNotNone(mask.getbbox())
            self.assertEqual(mask.mode, 'L')
            self.assertFalse(set(mask.tobytes()) - {0, 255})
            for key in ('patch', 'mask'):
                self.assertEqual(hashlib.sha256((ROOT / r[key]['path']).read_bytes()).hexdigest(), r[key]['sha256'])
        mask = Image.open(ROOT / self.labels['world_map_header_title']['restoration']['mask']['path'])
        self.assertFalse(any(mask.crop((0, 0, 2, mask.height)).tobytes()))
        g = next(g for g in self.decision['entries'] if g['image_id'] == 'img_world_map_header')
        self.assertEqual(len(g['native_encoded_proof']['protected_regions']), 2)

    def test_uncertain_sprite_full_map_and_boss_are_not_silently_adopted(self):
        self.assertNotIn('skill_caption_042', self.labels)
        self.assertEqual({r['export'] for r in self.decision['retained']}, {42, 284})
        self.assertFalse(self.decision['full_world_map_labels_translated'])
        self.assertFalse(self.decision['game_rendering_verified'])
        self.assertEqual(self.decision['INT_drafts_added'], 0)
        self.assertNotIn('hud_complete_16_00', self.labels)
