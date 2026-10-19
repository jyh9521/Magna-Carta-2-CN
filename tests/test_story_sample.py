"""Public source-locked sample contracts; no original game files required."""
import json
from pathlib import Path
import unittest
from tools.font_binding_plan import digest
from tools.validate_catalog import TOKEN
from tools.audit_wrap_layout import sample_paragraph

ROOT = Path(__file__).resolve().parents[1]


class StorySampleTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/'locales/zh-Hans/text-sample-story.json').read_bytes())

    def test_nine_source_hashes_ids_and_original_break_counts(self):
        self.assertEqual(self.plan['source_mode'],'sha256-utf8')
        entries=self.plan['entries'];self.assertEqual(len(entries),9)
        self.assertEqual(len({e['id'] for e in entries}),9)
        self.assertEqual([TOKEN.findall(e['translation']) for e in entries],
                         [[],['\\n'],['\\n'],['\\n'],['\\n'],['\\n'],[],['\\n'],['\\n','\\n']])
        for e in entries:
            self.assertNotIn('source',e)
            self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertNotIn('\n',e['translation'])
        warning=json.loads((ROOT/'locales/zh-Hans/text-probe-layout.json').read_bytes())
        self.assertTrue({e['id'] for e in entries}.isdisjoint(e['id'] for e in warning['entries']))

    def test_real_unbroken_dialogue_is_not_a_synthetic_stress_sentence(self):
        self.assertEqual(self.plan['entries'][0]['translation'],'喂，你想害死我吗？')
        text=self.plan['entries'][6]['translation']
        self.assertTrue(text.endswith('待在这里的。'))
        self.assertNotIn(' ',text);self.assertNotIn('\\n',text)

    def test_layout_selection_preserves_default_and_checks_explicit_id(self):
        self.assertEqual(sample_paragraph(self.plan)[0],self.plan['entries'][0]['id'])
        entry=self.plan['entries'][6]
        self.assertEqual(sample_paragraph(self.plan,entry['id']),(entry['id'],entry['translation']))
        with self.assertRaisesRegex(ValueError,'ID absent'):sample_paragraph(self.plan,'missing')
        with self.assertRaisesRegex(ValueError,'unspaced'):sample_paragraph(dict(entries=[dict(id='test',translation=' ')]))

    def test_route_dependencies_and_explicit_atlas_growth_are_hash_locked(self):
        route=json.loads((ROOT/'locales/zh-Hans/story-sample/route.json').read_bytes())
        self.assertFalse(route['game_rendering_verified']);self.assertTrue(route['raw_packages'])
        self.assertEqual(len(route['font_plans']),2)
        for spec in [route['text_plan'],*route['font_plans']]:
            self.assertEqual(digest((ROOT/spec['path']).read_bytes()),spec['sha256'])
        for spec in route['font_plans']:
            fp=json.loads((ROOT/spec['path']).read_bytes());gp=fp['supplement']
            self.assertEqual(digest((ROOT/gp['path']).read_bytes()),gp['sha256'])
            glyphs=json.loads((ROOT/gp['path']).read_bytes())
            self.assertLessEqual(len(glyphs['glyphs']),128)
            self.assertFalse(glyphs['in_game_verified'])


if __name__ == '__main__':unittest.main()
