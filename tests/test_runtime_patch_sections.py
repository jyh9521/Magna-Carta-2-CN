"""Separately switchable runtime patches partition, never duplicate, guarded writes."""
import tempfile
from pathlib import Path
import tomllib
import unittest

from tools.runtime_patch import build,patch_toml
from test_runtime_patch import fixture_plan,image_fixture


def plan():
    p=fixture_plan(image_fixture())
    p['patch_sections']=[dict(name='First',description='First probe',is_enabled=False,write_addresses=[0x1020]),
                         dict(name='Second',description='Second probe',is_enabled=False,write_addresses=[0x1080])]
    return p


class RuntimeSectionTests(unittest.TestCase):
    def test_sections_partition_all_words_and_preserve_disabled_state(self):
        t=tomllib.loads(patch_toml(plan()).decode())
        self.assertEqual([x['name'] for x in t['patch']],['First','Second'])
        self.assertEqual([len(x['be32']) for x in t['patch']],[1,3])
        self.assertTrue(all(x['is_enabled'] is False for x in t['patch']))
        self.assertEqual(t['patch'][0]['be32'][0]['address'],0x1020)

    def test_build_multiple_sections_uses_existing_source_guards(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);game=root/'game';game.write_bytes(b'game');exe=root/'exe';exe.write_bytes(b'exe')
            m=build(image_fixture(),plan(),game,exe,root/'out')
            self.assertFalse(m['game_started'])
            t=tomllib.loads(next((root/'out').glob('*.toml')).read_text())
            self.assertEqual(len(t['patch']),2)

    def test_missing_duplicate_unknown_and_bool_addresses_fail(self):
        for addresses in [[],[0x1020],[0x1080,0x1080],[0x1020,0x1080],[0x9999],[True]]:
            p=plan();p['patch_sections'][1]['write_addresses']=addresses
            with self.subTest(addresses=addresses),self.assertRaises(ValueError):patch_toml(p)

    def test_section_count_and_unknown_override_fields_fail(self):
        for value in [[],{},'bad',[{}]*9]:
            p=plan();p['patch_sections']=value
            with self.subTest(value=value),self.assertRaises((ValueError,KeyError)):patch_toml(p)
        for key in ['writes','image_sha256','title_id']:
            p=plan();p['patch_sections'][0][key]='override'
            with self.subTest(key=key),self.assertRaises(ValueError):patch_toml(p)

    def test_metadata_types_are_checked_for_each_section(self):
        for key,value in [('is_enabled','false'),('description',False),('name',''),('author',42)]:
            p=plan();p['patch_sections'][1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):patch_toml(p)


if __name__=='__main__':unittest.main()
