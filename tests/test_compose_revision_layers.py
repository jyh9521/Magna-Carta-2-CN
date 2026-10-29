import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.compose_revision_layers import compose, build
from tools.reface_font import sha
from tools.replace_texture_regions import selected
from tools import texture_overlay as overlay
from test_texture_layout import profile_fixture
from test_supplement_font import stored_decoder


class RevisionLayerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def ref(self, name, data):
        (self.root/name).write_bytes(data)
        return dict(file=name, sha256=sha(data))

    def plan(self):
        return dict(schema_version=1, kind='offline-resource-revision-layers', resources=[
            dict(path='MC2Game/data.int', discs=[1, 2], before=self.ref('before', b'old'), base=self.ref('after', b'new'))])

    def test_locked_replacement_roundtrip_and_immutable_inputs(self):
        p = self.plan(); out = self.root/'out'
        r = build(p, self.root, out)
        self.assertEqual((out/'candidate/MC2Game/data.int').read_bytes(), b'new')
        self.assertEqual((self.root/'before').read_bytes(), b'old')
        self.assertEqual(r['resources'][0]['before_sha256'], sha(b'old'))
        self.assertTrue((out/'manifest.json').is_file())
        with self.assertRaisesRegex(ValueError, 'new canonical'): build(p, self.root, out)

    def test_all_inputs_locked(self):
        for role in ('base', 'before'):
            p = self.plan(); p['resources'][0][role]['sha256'] = '0'*64
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'SHA256'):
                compose(p, self.root)

    def test_dangling_output_link_is_rejected_before_writing(self):
        p = self.plan(); output = self.root/'redirect'
        with patch.object(type(output), 'is_symlink', return_value=True):
            with self.assertRaisesRegex(ValueError, 'new canonical'):
                build(p, self.root, output)
        self.assertFalse(output.exists())

    def test_path_duplicate_executable_disc_and_noop_guards(self):
        for name in ('../escape', 'default.xex'):
            p = self.plan(); p['resources'][0]['path'] = name
            with self.assertRaises(ValueError): compose(p, self.root)
        p = self.plan(); p['resources'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'): compose(p, self.root)
        for discs in ([0], [True], [2, 1], [], [1, 1]):
            p = self.plan(); p['resources'][0]['discs'] = discs
            with self.assertRaisesRegex(ValueError, 'membership'): compose(p, self.root)
        p = self.plan(); p['resources'][0]['base'] = p['resources'][0]['before']
        with self.assertRaisesRegex(ValueError, 'no changes'): compose(p, self.root)

    def test_native_blocks_use_current_package_not_entire_donor(self):
        before, edit, layers = profile_fixture(compressed=False)
        donor, _ = overlay.patch_package(before, sha(before), [edit], layers, stored_decoder)
        tiles = selected(donor, edit['object'], stored_decoder)[3]['tiles']
        p = self.plan(); r = p['resources'][0]; r['path'] = 'MC2Game/a.xxx'
        r['before'] = self.ref('texture-before', before); r['base'] = r['before']
        r['textures'] = [dict(object=edit['object'], rects=[[8, 4, 8, 8]],
            before_tiles_sha256=sha(selected(before, edit['object'], stored_decoder)[3]['tiles']),
            tiles=self.ref('tiles', tiles))]
        files, report = compose(p, self.root, stored_decoder)
        self.assertEqual(selected(files[r['path']], edit['object'], stored_decoder)[3]['tiles'], tiles)
        self.assertTrue(report['resources'][0]['operations'][0]['proof']['outside_blocks_preserved'])
        bad = copy.deepcopy(p); bad['resources'][0]['textures'][0]['before_tiles_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'native texture input'): compose(bad, self.root, stored_decoder)


if __name__ == '__main__': unittest.main()
