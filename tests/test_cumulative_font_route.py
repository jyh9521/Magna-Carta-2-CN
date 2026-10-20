"""Source-only contracts for cumulative fonts, not cumulative text deployment."""
from pathlib import Path
import hashlib
import json
import unittest
from tools.supplement_font import validate_plan

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'locales/zh-Hans/cumulative-font-route'


def load(path):
    return json.loads(Path(path).read_bytes())


def locked(ref):
    p = ROOT/ref['path']
    if hashlib.sha256(p.read_bytes()).hexdigest() != ref['sha256']:
        raise AssertionError('plan reference hash drift')
    return load(p)


class CumulativeFontRouteTests(unittest.TestCase):
    def test_all_family_and_glyph_references_locked(self):
        route = load(BASE/'route.json')
        self.assertEqual(len(route['font_plans']), 3)
        for ref,count in zip(route['font_plans'], [2390,2389,2390]):
            self.assertEqual(len(validate_plan(locked(locked(ref)['supplement']))), count)

    def test_drawable_and_blank_records_reused_exactly(self):
        for i in range(3):
            p = load(BASE/f'glyphs-{i}.json')
            old = load(ROOT/f'locales/zh-Hans/drawable-demand-probes/glyphs-{i}.json')
            blank = load(ROOT/f'locales/zh-Hans/layout-advance-probes/glyphs-{i}.json')
            self.assertEqual(p['glyphs'], old['glyphs']+blank['glyphs'])
            for k in set(old)-{'glyphs','purpose'}:
                self.assertEqual(p[k], old[k])

    def test_all_seven_original_bindings_retained(self):
        n = 0
        for i in range(3):
            p = load(BASE/f'font-{i}.json')
            old = load(ROOT/f'locales/zh-Hans/readability-fonts/font-{i}.json')
            for k in set(old)-{'supplement','expected_supplement_semantic_sha256'}:
                self.assertEqual(p[k], old[k])
            n += len(p['sources'])
        self.assertEqual(n, 7)

    def test_text_scope_does_not_silently_expand(self):
        old = load(ROOT/'locales/zh-Hans/readability-fonts/route.json')
        p = load(BASE/'route.json')
        for k in set(old)-{'font_plans'}:
            self.assertEqual(p[k], old[k])
        self.assertEqual(len(locked(p['text_plan'])['entries']), 262)
        self.assertEqual(len(p['additional_text_plans']), 4)
        for ref in p['additional_text_plans']:locked(ref)

    def test_control_is_not_replaced_or_added(self):
        for i,width in enumerate([27,20,32]):
            p = load(BASE/f'glyphs-{i}.json')
            cps = [ord(g['character']) for g in p['glyphs']]
            self.assertNotIn(9, cps)
            self.assertEqual(cps[-1], 12288)
            self.assertEqual(p['glyphs'][-1]['layout'], 'blank-advance')
            self.assertEqual(p['glyphs'][-1]['metric_width'], width)
            self.assertNotIn(12288, p.get('replace_blank_codepoints', []))

    def test_candidate_semantics_are_explicit_not_original_or_old_probe(self):
        for i in range(3):
            p = load(BASE/f'font-{i}.json')
            old = load(ROOT/f'locales/zh-Hans/readability-fonts/font-{i}.json')
            v = p['expected_supplement_semantic_sha256']
            self.assertRegex(v, r'^[0-9a-f]{64}$')
            self.assertNotIn(v, [p['expected_semantic_sha256'],old['expected_supplement_semantic_sha256']])

    def test_scope_is_source_locked_and_not_runtime_approval(self):
        p = load(BASE/'scope.json')
        self.assertEqual(p['workflow_sha256'], hashlib.sha256((ROOT/'locales/zh-Hans/translation-workflow.json').read_bytes()).hexdigest())
        self.assertEqual(p['layout_manifest_sha256'], hashlib.sha256((ROOT/'locales/zh-Hans/layout-advance-probes/manifest.json').read_bytes()).hexdigest())
        self.assertFalse(p['cumulative_text_deployed'])
        self.assertFalse(p['resource_refresh_performed'])
        self.assertFalse(p['game_rendering_verified'])
        self.assertEqual(p['control_literal_unchanged'], [9])
