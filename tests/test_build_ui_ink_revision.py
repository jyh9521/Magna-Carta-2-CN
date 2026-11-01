import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_ui_ink_revision import build
from tools.patch_tagged_fields import digest


class InkBuildTests(unittest.TestCase):
    def test_committed_profiles_lock_exact_lf_dependency_bytes(self):
        root = Path(__file__).resolve().parents[1]
        for disc in (1, 2):
            path = root/f'locales/zh-Hans/ui-ink-revision-v13-disc{disc}.json'
            self.assertNotIn(b'\r\n', path.read_bytes())
            plan = json.loads(path.read_bytes())
            refs = [plan['overlay'], *plan['text_plans'],
                    *(row['plan'] for row in plan['field_plans'])]
            for ref in refs:
                raw = (root/ref['path']).read_bytes()
                self.assertNotIn(b'\r\n', raw)
                self.assertEqual(digest(raw), ref['sha256'])

    def fixture(self, root):
        source = root/'source'; source.mkdir()
        (source/'sample.int').write_bytes(b'before')
        def write(name, value):
            p = root/name; p.write_text(json.dumps(value), encoding='utf8')
            return dict(path=name, sha256=digest(p.read_bytes()))
        overlay = write('overlay.json', {})
        text = write('text.json', dict(resource='sample.int'))
        profile = dict(schema_version=1, kind='ui-ink-revision', disc=1,
            toc_path='toc.txt', sources=[dict(resource='sample.int', sha256=digest(b'before'))],
            overlay=overlay, transfers=[], alpha_filters=[], font_metrics=[], field_plans=[],
            text_plans=[text], enrollments=['sample.int'])
        write('profile.json', profile)
        return source, root/'profile.json', profile

    def call(self, root, source, profile, expected=None, output=None, donor=None):
        with patch('tools.build_ui_ink_revision.prepare', side_effect=donor,
                   return_value=({}, {'plan_canonical_sha256': '0'*64}, [])), \
             patch('tools.build_ui_ink_revision.resolve_changes', return_value={}), \
             patch('tools.build_ui_ink_revision.rebuild', return_value=b'after'):
            return build(profile, expected or digest(profile.read_bytes()), root, source,
                         output or root/'output', None)

    def test_new_sparse_copy_original_enrollment_and_readback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source, p, _ = self.fixture(root)
            result = self.call(root, source, p)
            self.assertEqual((source/'sample.int').read_bytes(), b'before')
            self.assertEqual((root/'output/baseline/sample.int').read_bytes(), b'before')
            self.assertEqual((root/'output/candidate/sample.int').read_bytes(), b'after')
            manifest = json.loads((root/'output/replacements.json').read_bytes())
            self.assertEqual(manifest['resources'][0]['original']['sha256'], digest(b'before'))
            self.assertFalse(result['game_started'])

    def test_stale_profile_and_source_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source, p, _ = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'profile SHA256'):
                self.call(root, source, p, expected='0'*64)
            (source/'sample.int').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'source resource SHA256'):
                self.call(root, source, p)
            self.assertFalse((root/'output').exists())

    def test_mid_build_input_change_aborts_before_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source, p, _ = self.fixture(root)
            def changed(*args):
                (source/'sample.int').write_bytes(b'changed')
                return {}, {'plan_canonical_sha256': '0'*64}, []
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.call(root, source, p, donor=changed)
            self.assertFalse((root/'output').exists())

    def test_existing_nested_duplicate_and_undeclared_targets_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source, p, plan = self.fixture(root)
            for output in [source, source/'nested']:
                with self.assertRaisesRegex(ValueError, 'disjoint'):
                    self.call(root, source, p, output=output)
            plan['sources'].append(dict(resource='SAMPLE.int', sha256=digest(b'before')))
            p.write_text(json.dumps(plan), encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                self.call(root, source, p)
            plan['sources'].pop(); plan['transfers'] = [dict(resource='unknown.xxx')]
            p.write_text(json.dumps(plan), encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'undeclared'):
                self.call(root, source, p)


if __name__ == '__main__':
    unittest.main()
