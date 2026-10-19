"""Subtitle candidate must add missing coverage without changing story text."""
import json
from pathlib import Path
import unittest
from tools.font_binding_plan import digest
from tools.audit_text_font_coverage import literal_codepoints

ROOT=Path(__file__).resolve().parents[1]


class SubtitlePlanTests(unittest.TestCase):
    def test_additive_family_and_identical_text_and_existing_family_plans(self):
        old=json.loads((ROOT/'locales/zh-Hans/story-sample/route.json').read_bytes())
        new=json.loads((ROOT/'locales/zh-Hans/story-subtitle/route.json').read_bytes())
        self.assertEqual(new['font_plans'][:2],old['font_plans'])
        self.assertEqual(new['text_plan'],old['text_plan'])
        self.assertEqual(new['expected_text_sha256'],old['expected_text_sha256'])
        self.assertEqual(len(new['font_plans']),3)
        for ref in [new['text_plan'],*new['font_plans']]:
            self.assertEqual(digest((ROOT/ref['path']).read_bytes()),ref['sha256'])

    def test_two_hash_locked_subtitle_aliases_and_no_atlas_growth(self):
        fp=json.loads((ROOT/'locales/zh-Hans/story-subtitle/font.json').read_bytes())
        self.assertEqual(fp['canonical_font_path'],'font.enginemedium_subtitle')
        self.assertEqual(fp['required_source_count'],2)
        self.assertEqual({s['font_object'] for s in fp['sources']},{'EngineMedium_Subtitle','Font.EngineMedium_Subtitle'})
        ref=fp['supplement'];self.assertEqual(digest((ROOT/ref['path']).read_bytes()),ref['sha256'])
        gp=json.loads((ROOT/ref['path']).read_bytes())
        self.assertEqual(len(gp['glyphs']),101)
        self.assertNotIn('atlas_height',gp)
        self.assertEqual(gp['metric_height'],29)
        self.assertTrue(all(g['texture_index']==3 and g['width']==32 and g['height']==32 for g in gp['glyphs']))
        self.assertFalse(gp['in_game_verified'])


if __name__=='__main__':unittest.main()
