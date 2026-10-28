import json
from pathlib import Path
import tempfile
import unittest

from tools.probe_texture_region_repairs import evaluate_pixels, rollback
from tools.texture_region_repair import digest


class NativeArtProbeTests(unittest.TestCase):
    def test_faint_glow_and_missing_binding_go_red(self):
        source=bytes([0,0,0,0])*16
        glow=source[:3]+bytes([1])+source[4:]
        case=dict(required_label='caption',required_text='new',empty_alpha_rects=[[0,0,4,4]])
        checks=evaluate_pixels(case,glow,source,4,{})
        self.assertFalse(checks['required_translation_binding'])
        self.assertFalse(checks['empty_alpha_0'])
        self.assertTrue(all(evaluate_pixels(case,source,source,4,{'caption':{'text':'new'}}).values()))

    def test_protected_native_text_damage_goes_red(self):
        source=bytes([20,30,40,255])*16
        modified=bytes(4)+source[4:]
        case=dict(required_label='c',required_text='x',protected_rects=[[0,0,4,4]])
        self.assertFalse(evaluate_pixels(case,modified,source,4,{'c':{'text':'x'}})['protected_pixels_0'])

    def test_guarded_rollback_isolated_copy_preserves_modified(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); before=b'AAAABBBB'; after=b'AAAACCCC'
            (root/'x-BASELINE.native').write_bytes(before)
            (root/'x-MODIFIED.native').write_bytes(after)
            manifest=dict(cases=[dict(id='x',baseline_file='x-BASELINE.native',modified_file='x-MODIFIED.native',
                baseline_sha256=digest(before),modified_sha256=digest(after),
                units=[dict(offset=4,before=b'BBBB'.hex(),after=b'CCCC'.hex())])])
            (root/'DIFF_FILE.json').write_text(json.dumps(manifest))
            self.assertEqual(rollback(root),0)
            self.assertEqual((root/'x-ROLLBACK.native').read_bytes(),before)
            self.assertEqual((root/'x-MODIFIED.native').read_bytes(),after)
            (root/'x-MODIFIED.native').write_bytes(b'not-valid')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                rollback(root)


if __name__ == '__main__':
    unittest.main()
