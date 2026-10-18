"""Repository-only probe/document byte contracts; no game assets or Git required."""
import hashlib
import re
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]
PROBES=[('ui-draw-string-native.json','NATIVE_BINDINGS.md'),
        ('ui-draw-string-style-selection.json','NATIVE_STYLE_SELECTION.md'),
        ('ui-draw-string-class-tables.json','NATIVE_CLASS_TABLES.md'),
        ('ui-draw-string-selection-predicate.json','STYLE_SELECTION_PREDICATE.md'),
        ('ui-style-reference-helper.json','STYLE_REFERENCE_HELPER.md'),
        ('ui-object-initialization.json','OBJECT_INITIALIZATION.md')]


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
                text=(ROOT/'docs'/document).read_text(encoding='utf8')
                self.assertEqual(re.findall(r'--plan-sha256\s+([0-9a-f]{64})',text),[expected])


if __name__=='__main__':unittest.main()
