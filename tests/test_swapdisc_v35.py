"""Frozen swap prompts retain native emphasis and strictly sparse ownership."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

from tools.build_video_captions import load_mask_asset, frame_repair_metadata, prepare_frame_repairs

ROOT = Path(__file__).resolve().parents[1]


class SwapDiscRepairTests(unittest.TestCase):
    def plans(self):
        catalog = json.loads((ROOT/'locales/zh-Hans/swapdisc-captions-v35.catalog.json').read_bytes())
        self.assertEqual(len(catalog['entries']), 2)
        for row in catalog['entries']:
            path = ROOT/row['plan']['path']
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['plan']['sha256'])
            yield row, json.loads(raw)

    def test_original_members_and_headers_match_dated_omission_evidence(self):
        old = json.loads((ROOT/'locales/zh-Hans/omission-findings-v34.json').read_bytes())
        sources = {r['member']: r for r in old['findings'] if r['id'].startswith('ANIM-364-SD')}
        descriptor = json.loads((ROOT/'locales/zh-Hans/source-resources/swapdisc-movies-v35.json').read_bytes())
        self.assertEqual(descriptor['kind'], 'locked-resource-source-subset')
        originals = {r['resource']: r for r in descriptor['resources']}
        self.assertEqual(originals.keys(), sources.keys())
        for row, plan in self.plans():
            entry, = plan['entries']
            source = sources[entry['source']['member']]
            self.assertEqual(entry['source']['sha256'], source['original_sha256'])
            self.assertEqual(entry['source']['discs'], [1, 2])
            original = originals[entry['source']['member']]
            self.assertEqual(original['expected_sha256'], entry['source']['sha256'])
            self.assertEqual(original['discs'], entry['source']['discs'])
            self.assertEqual(original['destination'], 'build/phase-365-swapdisc/original/'+entry['source']['file'])
            self.assertEqual(entry['expected_header'], dict(width=1280, height=720, frames=30,
                numerator=10000000, denominator=333333, magic='BIKi', audio_tracks=0))
            self.assertEqual(entry['encoder_guard_frames'], 1)
            self.assertFalse(plan['game_rendering_verified'])

    def test_each_prompt_preserves_separate_white_and_yellow_runs(self):
        for number, (_, plan) in enumerate(self.plans(), 1):
            caption, = plan['entries'][0]['captions']
            self.assertEqual(caption['text'], f'请放入《真名法典2》第{number}张光盘')
            self.assertEqual(''.join(p['text'] for p in caption['parts']), caption['text'])
            self.assertEqual(len(caption['parts']), 2)
            white, yellow = caption['parts']
            self.assertEqual(white['appearance']['gradient'][0][1], [239, 239, 239, 255])
            self.assertEqual(yellow['text'], f'第{number}张光盘')
            self.assertEqual(yellow['appearance']['gradient'][0][1], [243, 203, 28, 255])
            self.assertEqual(caption['frame_alpha'], [255]*30)
            self.assertFalse({'appearance', 'style', 'font_size'} & caption.keys())

    def test_native_mask_and_every_patch_load_through_production_guards(self):
        for _, plan in self.plans():
            caption, = plan['entries'][0]['captions']
            rect = caption['erase']['rect']
            self.assertEqual(rect, [438, 338, 404, 47])
            mask = load_mask_asset(caption['erase']['mask_asset'], rect, ROOT)
            records = frame_repair_metadata(caption, 30, (1280, 720), ROOT)
            operation = prepare_frame_repairs(records, caption, mask, 30, (1280, 720))
            self.assertEqual(operation.active_frames, tuple(range(30)))
            self.assertEqual(len(records), 30)
            self.assertLess(mask.sum(), mask.size//2)
            for ref in caption['erase']['frame_repairs']['records']:
                with Image.open(ROOT/ref['patch']['path']) as image:
                    rgba = np.asarray(image)
                    np.testing.assert_array_equal(rgba[:, :, 3], mask.astype('uint8')*255)
                    self.assertFalse(rgba[~mask].any())

    def test_card_border_and_corner_coordinates_are_never_owned(self):
        for _, plan in self.plans():
            caption, = plan['entries'][0]['captions']
            x, y, w, h = caption['erase']['rect']
            self.assertGreater(x, 335)
            self.assertLess(x+w, 945)
            self.assertGreater(y, 310)
            self.assertLess(y+h, 410)
            for part in caption['parts']:
                px, py, pw, ph = part['rect']
                self.assertGreater(px, 335)
                self.assertLess(px+pw, 945)
                self.assertGreater(py, 310)
                self.assertLess(py+ph, 410)


if __name__ == '__main__':
    unittest.main()
