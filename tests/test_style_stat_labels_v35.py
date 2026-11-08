"""Locale evidence and physical-alias coverage for the normal stat capsules."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'locales/zh-Hans/texture-overlays'


class StyleStatLabelPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((BASE/'style-stat-labels-v35.json').read_bytes())
        self.repairs = json.loads((BASE/'style-stat-repairs-v35.json').read_bytes())
        self.aliases = json.loads((BASE/'style-stat-aliases-v35.json').read_bytes())

    def test_adopted_stat_terms_and_independent_upgrade_run_are_preserved(self):
        terms = {'def': '防御', 'dex': '速度', 'esp': '精神', 'esr': '抗性',
                 'hp': '生命值提升', 'srv': '耐力恢复', 'sta': '耐力',
                 'str': '攻击', 'strcopy': '攻击'}
        labels = {x['id'].removeprefix('style_stat_'): x for x in self.plan['labels']}
        self.assertEqual(set(labels), set(terms))
        for key, term in terms.items():
            self.assertEqual(labels[key]['text'], term)
        self.assertEqual([p['text'] for p in labels['hp']['parts']], ['生命值', '提升'])
        self.assertLess(labels['hp']['parts'][1]['appearance']['ink_box'][3],
                        labels['hp']['parts'][0]['appearance']['ink_box'][3])

    def test_normal_and_japanese_copy_have_separate_source_identity(self):
        cases = {c['id']: c for c in self.repairs['cases']}
        a, b = cases['style_stat_str'], cases['style_stat_strcopy']
        self.assertNotEqual(a['rgba_sha256'], b['rgba_sha256'])
        self.assertEqual(b['object'], 'Style_Skill_Status_STR_normalcopy')
        labels = {x['id']: x for x in self.plan['labels']}
        self.assertEqual(labels['style_stat_str']['source_text_sha256'],
                         hashlib.sha256('공격'.encode()).hexdigest())
        self.assertEqual(labels['style_stat_strcopy']['source_text_sha256'],
                         hashlib.sha256('攻撃'.encode()).hexdigest())

    def test_all_small_patches_are_hash_bound_and_sparse_at_native_size(self):
        from PIL import Image
        for label in self.plan['labels']:
            restoration = label['restoration']
            images = {}
            for key, mode in (('mask', 'L'), ('patch', 'RGBA')):
                ref = restoration[key]; path = ROOT/ref['path']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ref['sha256'])
                with Image.open(path) as im:
                    self.assertEqual(im.mode, mode); self.assertEqual(im.size, (128, 32))
                    images[key] = im.tobytes()
            mask, pixels = images['mask'], images['patch']
            self.assertFalse(set(mask)-{0, 255})
            self.assertGreater(mask.count(255), 0); self.assertLess(mask.count(255), 2048)
            for i, value in enumerate(mask):
                self.assertEqual(pixels[i*4+3] if value else pixels[i*4:i*4+4],
                                 255 if value else bytes(4))

    def test_native_transport_recipe_and_source_descriptor_are_reproducible(self):
        self.assertEqual(self.repairs['method'], 'nearest-source-pixel-rgb-preserve-alpha-v1')
        self.assertEqual(self.repairs['hidden_background'], 'native-motif-continuation-not-original-recovery')
        descriptor = json.loads((BASE/'style-stat-sources-v35.json').read_bytes())
        source = descriptor['resources'][0]
        self.assertEqual(source['discs'], [1, 2])
        self.assertEqual(source['expected_sha256'],
                         '6f9562d8f2a52dabc2c36e598f23bd9ac8d383e8c2cab95284d65a2feae2e5bc')
        for case in self.repairs['cases']:
            self.assertEqual(case['source'], dict(path=source['destination'], sha256=source['expected_sha256']))
            self.assertEqual(case['dimensions'], [128, 32])
            self.assertTrue(case['runs'])
            self.assertTrue(all(d['clean_rectangles'] for d in case['donors']))

    def test_all_34_physical_labels_and_no_blank_or_selector_are_selected(self):
        resources = self.aliases['resources']
        self.assertEqual(len(resources), 2)
        self.assertEqual(sum(len(r['textures'])*len(r['discs']) for r in resources), 34)
        self.assertEqual(sorted(len(r['textures']) for r in resources), [8, 9])
        copies = 0
        for resource in resources:
            self.assertEqual(resource['discs'], [1, 2])
            self.assertNotIn(resource['path'], ('', '.'))
            for texture in resource['textures']:
                self.assertNotIn('Alll_Disable', texture['object'])
                self.assertNotIn('Select', texture['object'])
                copies += 2 if texture['object'].endswith('normalcopy') else 0
                cells = set()
                for x, y, w, h in texture['rectangles']:
                    self.assertTrue(all(v % 4 == 0 for v in (x, y, w, h)))
                    self.assertTrue(0 <= x < x+w <= 128 and 0 <= y < y+h <= 32)
                    new = {(a, b) for a in range(x, x+w, 4) for b in range(y, y+h, 4)}
                    self.assertFalse(cells & new); cells |= new
        self.assertEqual(copies, 2)

    def test_source_alpha_and_unchanged_block_preservation_are_explicit(self):
        for source in self.plan['sources']:
            self.assertEqual(source['discs'], [1, 2])
            for texture in source['textures']:
                self.assertEqual(texture['alpha_encoding'], 'preserve-source')
                self.assertTrue(texture['preserve_unchanged_blocks'])
                self.assertEqual(texture['profile'], dict(kind='xbox-inline-bc-v1', format=7))

    def test_raw_plan_hash_and_lf_publication_match_alias_guard(self):
        ref = self.aliases['overlay_plan']; raw = (ROOT/ref['path']).read_bytes()
        self.assertNotIn(b'\r', raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])


if __name__ == '__main__':
    unittest.main()
