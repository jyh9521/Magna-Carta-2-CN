"""Repository-only probe/document byte contracts; no game assets or Git required."""
import hashlib
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]
PROBES=[('ui-draw-string-native.json','NATIVE_BINDINGS.md'),
        ('ui-draw-string-style-selection.json','NATIVE_STYLE_SELECTION.md'),
        ('ui-draw-string-class-tables.json','NATIVE_CLASS_TABLES.md')]


class NativeProbeContractTests(unittest.TestCase):
    def test_documented_native_probe_sources_use_git_lf_bytes(self):
        for plan,_ in PROBES:
            with self.subTest(plan=plan):
                raw=(ROOT/'references/probes'/plan).read_bytes()
                self.assertNotIn(b'\r',raw);self.assertTrue(raw.endswith(b'\n'))

    def test_documented_native_probe_hashes_match_exact_shipped_plan_bytes(self):
        for plan,document in PROBES:
            with self.subTest(plan=plan):
                raw=(ROOT/'references/probes'/plan).read_bytes();expected=hashlib.sha256(raw).hexdigest()
                self.assertIn(expected,(ROOT/'docs'/document).read_text(encoding='utf8'))


if __name__=='__main__':unittest.main()
