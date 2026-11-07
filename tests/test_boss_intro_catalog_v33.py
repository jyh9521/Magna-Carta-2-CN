"""Source-free contracts for all eleven frozen native title repair plans.

These tests read small versioned assets only; no original movie, font, neural
runtime, encoder, GPU, game installation or ignored research file is required.
"""
import hashlib
import json
from pathlib import Path
import unittest

from tools import build_video_captions as captions
from tools.video_frame_repairs import MAX_PATCH_BYTES, MAX_RECT_PIXELS
from tools.video_title_caption import active_frame_indices, frame_exposure_values
from tools.verify_resource_phase import hash_value, relative, unique


ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'locales/zh-Hans/boss-intro-captions-v33.catalog.json'
PLAN_ROOT = 'locales/zh-Hans/video-captions/boss-intro-v33/'
ASSET_ROOT = 'locales/zh-Hans/video-repairs/boss-intro-v33/'
# Independently verified original identities, not hashes derived from a candidate.
EXPECTED = {
    'csm00-35': (1, 354, '守护者阿蒙', '83432049889402cb79c970a63f3e1b35060dc2fbda4d3618023c65d7c188c447'),
    'csm02-52': (1, 242, '恸哭之门', 'a2cf0ecbd5f44757d8eb37ac1afb44aed91ffa3528dc8e42a2dfb62446c02199'),
    'csm02-54': (1, 178, '恸哭之门', '62d7e54850ff7d4f9dd21f07e0abb18e128de32068ceac925b65af7706fccb5c'),
    'csm02-61': (1, 2032, '阿斯塔罗斯', '147fd3d2df76714d7e32faf4acde1bb0785bfef4b45c4deed16b0a4b7a70e0a3'),
    'csm03-122': (1, 271, '修亚伦', 'b76becd06edf78e0b7e715d5f39bdaf2a43e2a68ae782536efc7967cedcf8825'),
    'csm03-185': (1, 546, '巨型安格勒', '445d96dfa4f2d39aed2951b56c6672ae731784788e169046ff27be2f629810e9'),
    'csm04-111': (1, 630, '利维坦', '086a09aafb11320f834ad960764ceb73c5e763872561adbfa581ea1b968b6ad7'),
    'csm05-82': (1, 638, '贝里艾尔', '36dcf7b64e7ccf48bfab31e58eb235313e069a53c8dc1062bbcbc50d2434060d'),
    'csm06-80': (2, 1111, '阿斯莫德乌斯', '76306364d1d75dc245f33688a1c31b3e33cd1e7efc9a6eda701462332bcc5d0f'),
    'csm11-50': (2, 1622, '普尔森', 'bf0ecc00f6479d6354a05095a37a29cf035c38cfe9f87eccbc6e4d66ceac0a75'),
    'csm13-40': (2, 1930, '斯特拉斯', 'b44deb9b088b4bef7d5135682187015a4b7373cbd8edb2342b2894684052c609'),
}


def canonical_json(name):
    raw = captions.member(ROOT, relative(name)).read_bytes()
    value = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    if raw != captions.encoded(value):
        raise ValueError('Versioned title metadata must be canonical UTF-8 with LF')
    return value, raw


class BossIntroCatalogV33Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.catalog_raw = canonical_json(CATALOG)
        cls.plans = {}
        for row in cls.catalog['entries']:
            plan, raw = canonical_json(row['plan']['path'])
            cls.plans[row['id']] = (row, plan, raw)

    def test_exact_family_and_explicit_offline_status(self):
        c = self.catalog
        self.assertIs(type(c['schema_version']), int)
        self.assertEqual(c['schema_version'], 1)
        self.assertEqual(c['kind'], 'source-locked-video-caption-catalog')
        self.assertEqual(c['locale'], 'zh-Hans')
        self.assertEqual(c['status'], 'offline-native-candidate-not-game-acceptance')
        self.assertEqual(len(c['entries']), 11)
        self.assertEqual({r['id'] for r in c['entries']}, set(EXPECTED))
        self.assertEqual(len(self.plans), 11)
        self.assertEqual(len({r['plan']['path'].casefold() for r in c['entries']}), 11)
        self.assertEqual(len({r['source_member'].casefold() for r in c['entries']}), 11)

    def test_descriptor_preserves_original_disc_member_and_hash(self):
        self.assertEqual(self.catalog['source_inventory'],
                         'locales/zh-Hans/source-resources/boss-intro-movies.json')
        descriptor, _ = canonical_json(self.catalog['source_inventory'])
        self.assertEqual(set(descriptor), {'schema_version', 'kind', 'resources'})
        self.assertIs(type(descriptor['schema_version']), int)
        self.assertEqual(descriptor['schema_version'], 1)
        self.assertEqual(descriptor['kind'], 'locked-resource-source-subset')
        resources = descriptor['resources']
        self.assertEqual(len(resources), 11)
        by_member = {r['resource']: r for r in resources}
        self.assertEqual(len(by_member), 11)
        self.assertEqual(set(by_member), {f'MC2Game/Movies/{name}.bik' for name in EXPECTED})
        destinations = set()
        for name, (disc, _, _, source_sha) in EXPECTED.items():
            row = by_member[f'MC2Game/Movies/{name}.bik']
            self.assertEqual(set(row), {'resource', 'destination', 'discs', 'expected_sha256'})
            self.assertEqual(row['discs'], [disc])
            self.assertTrue(all(type(d) is int for d in row['discs']))
            self.assertEqual(hash_value(row['expected_sha256']), source_sha)
            self.assertEqual(relative(row['destination']), f'build/boss-intro-source-originals/{name}.bik')
            destinations.add(row['destination'].casefold())
        self.assertEqual(len(destinations), 11)

    def test_plan_hashes_canonical_lf_and_source_identities(self):
        for name, (row, plan, raw) in self.plans.items():
            with self.subTest(movie=name):
                disc, frames, text, source_sha = EXPECTED[name]
                self.assertEqual(row['plan']['path'], PLAN_ROOT + name + '.json')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), hash_value(row['plan']['sha256']))
                self.assertNotIn(b'\r', raw)
                self.assertEqual(row['source_member'], f'MC2Game/Movies/{name}.bik')
                self.assertEqual(row['source_sha256'], source_sha)
                self.assertEqual((row['disc'], row['text']), (disc, text))
                self.assertEqual(plan['kind'], 'bink-audio-caption-plan')
                self.assertIs(type(plan['schema_version']), int)
                self.assertEqual(plan['schema_version'], 1)
                self.assertEqual(plan['locale'], 'zh-Hans')
                self.assertIs(plan['game_rendering_verified'], False)
                self.assertIs(plan['source_font_identity_recovered'], False)
                self.assertEqual(len(plan['entries']), 1)
                entry = plan['entries'][0]
                self.assertEqual(entry['id'], name)
                source = entry['source']
                self.assertEqual(source['file'], name + '.bik')
                self.assertEqual(source['member'], row['source_member'])
                self.assertEqual(source['sha256'], source_sha)
                self.assertEqual(source['discs'], [disc])
                self.assertIs(type(source['size']), int)
                self.assertGreater(source['size'], 0)
                self.assertLessEqual(source['size'], 512 * 1024 * 1024)
                hash_value(source['first_rgb_sha256'])
                numerator, denominator = (1000000, 33333) if name == 'csm05-82' else (10000000, 333333)
                self.assertEqual(entry['expected_header'], dict(width=1280, height=720,
                    frames=frames, numerator=numerator, denominator=denominator, magic='BIKi', audio_tracks=6))

    def test_every_plan_keeps_explicit_frame_size_time_and_tail_caps(self):
        for name, (_, plan, _) in self.plans.items():
            with self.subTest(movie=name):
                entry = plan['entries'][0]
                frames = entry['expected_header']['frames']
                self.assertIn('maximum_frames', entry)
                self.assertGreaterEqual(captions.frame_count_limit(entry), frames)
                self.assertLessEqual(captions.frame_count_limit(entry), 6144)
                self.assertIn('maximum_encoded_bytes', entry)
                self.assertLessEqual(captions.encoded_size_limit(entry), 512 * 1024 * 1024)
                self.assertLessEqual(captions.encoder_time_limit(entry), 1800)
                self.assertLessEqual(captions.encoding_guard_frames(entry, frames), 2)
                first = captions.encoding_first_frame(entry, frames)
                indices = [r['index'] for r in entry['captions'][0]['erase']['frame_repairs']['records']]
                self.assertEqual(first, min(indices))
                self.assertTrue(all(index >= first for index in indices))
                self.assertGreaterEqual(captions.scratch_space_required(entry['expected_header'], entry),
                                        128 * 1024 * 1024)

    def test_font_identity_and_light_source_style_are_explicit_not_host_dependent(self):
        for name, (row, plan, _) in self.plans.items():
            with self.subTest(movie=name):
                self.assertEqual(plan['fonts'], dict(caption=dict(
                    path='build/font-source/NotoSansCJKsc-Regular.otf',
                    sha256='2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b')))
                self.assertEqual(plan['rasterizer_versions'],
                                 dict(Pillow='12.2.0', numpy='2.5.1', fontTools='4.63.0'))
                self.assertEqual(len(plan['entries'][0]['captions']), 1)
                caption = plan['entries'][0]['captions'][0]
                self.assertEqual(caption['text'], EXPECTED[name][2])
                self.assertEqual(caption['font'], 'caption')
                self.assertEqual(caption['font_size'], row['font_size'])
                self.assertLessEqual(caption['font_size'], 36)
                self.assertEqual(caption['appearance']['kind'], 'source-style-v1')
                self.assertNotIn('style', caption)
                self.assertNotIn('native_screen', caption['erase'])
                self.assertNotIn('background_fill', caption['erase'])

    def test_all_mask_and_patch_assets_are_distinct_confined_and_hash_locked(self):
        paths = set()
        for name, (row, plan, _) in self.plans.items():
            with self.subTest(movie=name):
                entry = plan['entries'][0]
                caption = entry['captions'][0]
                rect = caption['erase']['rect']
                self.assertLessEqual(rect[2] * rect[3], MAX_RECT_PIXELS)
                mask_ref = caption['erase']['mask_asset']
                self.assertEqual(mask_ref['path'], ASSET_ROOT + 'masks/' + name + '.png')
                mask = captions.load_mask_asset(mask_ref, rect, ROOT)
                self.assertEqual(int(mask.sum()), mask_ref['pixels'])
                metadata = captions.frame_repair_metadata(caption, entry['expected_header']['frames'],
                                                          (1280, 720), ROOT)
                self.assertEqual(len(metadata), row['cleanup_frames'])
                operation = captions.prepare_frame_repairs(metadata, caption, mask,
                                                           entry['expected_header']['frames'], (1280, 720))
                proof = operation.proof()
                self.assertEqual(proof['record_count'], row['cleanup_frames'])
                self.assertEqual(proof['mask_sha256'], mask_ref['pixels_sha256'])
                self.assertLessEqual(proof['total_patch_bytes'], MAX_PATCH_BYTES)
                self.assertIs(proof['artistic_acceptance'], False)
                self.assertIs(proof['outside_mask_retained'], True)
                references = [mask_ref] + [r['patch'] for r in caption['erase']['frame_repairs']['records']]
                for ref in references:
                    path = captions.member(ROOT, ref['path'])
                    self.assertEqual(path.relative_to(ROOT).as_posix(), ref['path'])
                    self.assertNotIn(ref['path'].casefold(), paths)
                    paths.add(ref['path'].casefold())
                for record in caption['erase']['frame_repairs']['records']:
                    self.assertEqual(record['patch']['path'], ASSET_ROOT + name + f"/{record['index']:04}.png")
                    hash_value(record['source_crop_sha256'])

    def test_alpha_exposure_and_cleanup_timeline_are_separate_and_complete(self):
        background_only = {}
        exposures = set()
        for name, (_, plan, _) in self.plans.items():
            with self.subTest(movie=name):
                entry = plan['entries'][0]
                caption = entry['captions'][0]
                count = entry['expected_header']['frames']
                text_active = set(active_frame_indices(caption['frame_alpha'], count))
                cleanup = [r['index'] for r in caption['erase']['frame_repairs']['records']]
                self.assertEqual(len(set(cleanup)), len(cleanup))
                self.assertTrue(all(type(index) is int and 0 <= index < count for index in cleanup))
                self.assertLessEqual(text_active, set(cleanup))
                background_only[name] = sorted(set(cleanup) - text_active)
                if 'frame_exposure' in caption:
                    exposures.add(name)
                    values = frame_exposure_values(caption['frame_exposure'], count)
                    self.assertEqual(len(values), count)
                    self.assertTrue(all(caption['frame_alpha'][index] == 0
                                        for index, exposure in enumerate(values) if exposure == 0))
        self.assertEqual(exposures, {'csm02-52', 'csm03-122', 'csm03-185'})
        self.assertIn(269, background_only['csm03-122'])
        self.assertIn(1414, background_only['csm02-61'])


if __name__ == '__main__':
    unittest.main()
