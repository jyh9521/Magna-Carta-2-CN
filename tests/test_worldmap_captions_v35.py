"""Final source-only contracts; original movies/fonts are not CI inputs."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from tools.build_video_captions import frame_repair_metadata, load_mask_asset, prepare_frame_repairs

ROOT = Path(__file__).resolve().parents[1]


class WorldMapCaptionV35Tests(unittest.TestCase):
    def plans(self):
        path = ROOT/'locales/zh-Hans/worldmap-captions-v35.catalog.json'
        catalog = json.loads(path.read_bytes())
        self.assertEqual(len(catalog['entries']), 11)
        seen = set()
        for row in catalog['entries']:
            path = ROOT/row['plan']['path']
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['plan']['sha256'])
            plan = json.loads(raw)
            entry, = plan['entries']
            self.assertNotIn(entry['source']['member'], seen)
            seen.add(entry['source']['member'])
            yield row, plan, entry

    def test_exact_eleven_original_members_and_sixteen_disc_memberships(self):
        register = json.loads((ROOT/'locales/zh-Hans/omission-findings-v34.json').read_bytes())
        findings = {r['member']: r for r in register['findings']
                    if r['id'].startswith('ANIM-364-WM')}
        observed = set()
        memberships = 0
        for _, _, entry in self.plans():
            source = entry['source']
            old = findings[source['member']]
            self.assertEqual(source['sha256'], old['original_sha256'])
            self.assertEqual(source['discs'], old['discs'])
            observed.add(source['member'])
            memberships += len(source['discs'])
            self.assertEqual(entry['expected_header'], dict(width=1280, height=720, frames=360,
                numerator=10000000, denominator=333333, magic='BIKi', audio_tracks=6))
            self.assertEqual(entry['encoder_guard_frames'], 1)
            self.assertGreaterEqual(entry['minimum_start_free_bytes'], 16*2**30)
            self.assertGreaterEqual(entry['scratch_reserve_bytes'], 8*2**30)
        self.assertEqual(observed, set(findings))
        self.assertEqual(memberships, 16)

    def test_reviewed_serif_family_natural_width_and_native_bounds(self):
        for _, plan, entry in self.plans():
            self.assertFalse(plan['game_rendering_verified'])
            self.assertFalse(plan['source_font_identity_recovered'])
            font = plan['fonts']['caption']
            self.assertEqual(font, dict(path='build/font-source/NotoSerifCJKsc-SemiBold.otf',
                sha256='d627b53dbcde61e07de1498d2623a8b287f78585ffbc90cc0618d0caaa2ed6b0'))
            caption, = entry['captions']
            self.assertEqual(caption['role'], 'worldmap-destination-title')
            appearance = caption['appearance']
            self.assertEqual(appearance['align'], 'left')
            self.assertEqual(appearance.get('width_scale', 1), 1)
            x, y, w, h = appearance['ink_box']
            self.assertGreaterEqual(x, 255)
            self.assertLess(x, 280)
            self.assertGreaterEqual(y, 338)
            self.assertLess(y, 355)
            self.assertGreaterEqual(h, 24)
            self.assertLessEqual(h, 40)
            self.assertLessEqual(x+w, 620)

    def test_all3960_sparse_repairs_load_through_production_hash_guards(self):
        total = 0
        for _, _, entry in self.plans():
            caption, = entry['captions']
            self.assertEqual(caption['frame_alpha'], [255]*360)
            erase = caption['erase']
            rect = erase['rect']
            mask = load_mask_asset(erase['mask_asset'], rect, ROOT)
            self.assertTrue(erase['mask_asset']['path'].startswith(
                'locales/zh-Hans/video-repairs/worldmap-v35/'))
            metadata = frame_repair_metadata(caption, 360, (1280, 720), ROOT)
            operation = prepare_frame_repairs(metadata, caption, mask, 360, (1280, 720))
            self.assertEqual(operation.active_frames, tuple(range(360)))
            self.assertEqual(len(metadata), 360)
            for record in erase['frame_repairs']['records']:
                self.assertTrue(record['patch']['path'].startswith(
                    'locales/zh-Hans/video-repairs/worldmap-v35/'))
            total += len(metadata)
        self.assertEqual(total, 3960)

    def test_native_compass_is_never_owned_by_source_letter_mask(self):
        for _, _, entry in self.plans():
            caption, = entry['captions']
            erase = caption['erase']
            x, y, w, h = erase['rect']
            mask = load_mask_asset(erase['mask_asset'], erase['rect'], ROOT)
            # The original compass/arrow guard is x184..251, y326..393.
            xs = (np.arange(w)+x >= 184) & (np.arange(w)+x < 252)
            ys = (np.arange(h)+y >= 326) & (np.arange(h)+y < 394)
            self.assertFalse(mask[np.ix_(ys, xs)].any())

    def test_per_clip_source_geometry_and_only_reviewed_optical_delta(self):
        for row, _, entry in self.plans():
            geometry = row['native_geometry']
            source = geometry['source_ink_box']
            chinese = geometry['Chinese_ink_box']
            self.assertEqual(chinese, entry['captions'][0]['appearance']['ink_box'])
            self.assertEqual(geometry['x_delta'], chinese[0]-source[0])
            self.assertEqual(geometry['y_delta'], chinese[1]-source[1])
            self.assertEqual(geometry['height_delta'], chinese[3]-source[3])
            self.assertIs(geometry['natural_advance'], True)
            self.assertIs(geometry['width_stretch'], False)
            self.assertTrue(geometry['basis'])
            self.assertEqual(geometry['x_delta'], 0)
            self.assertEqual(geometry['y_delta'], 0)
            if entry['source']['member'].endswith('worldmapmovie_01_village.bik'):
                self.assertEqual(source, [256, 345, 157, 33])
                self.assertEqual(chinese, [256, 345, 300, 32])
                self.assertEqual(geometry['height_delta'], -1)
            else:
                self.assertEqual(geometry['height_delta'], 0)


if __name__ == '__main__':
    unittest.main()
