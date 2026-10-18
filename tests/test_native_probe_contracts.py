"""Repository-only probe/document byte contracts; no game assets or Git required."""
import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]
PROBES=[('ui-draw-string-native.json','NATIVE_BINDINGS.md'),
        ('ui-draw-string-style-selection.json','NATIVE_STYLE_SELECTION.md'),
        ('ui-draw-string-class-tables.json','NATIVE_CLASS_TABLES.md'),
        ('ui-draw-string-selection-predicate.json','STYLE_SELECTION_PREDICATE.md'),
        ('ui-style-reference-helper.json','STYLE_REFERENCE_HELPER.md'),
        ('font-metrics-initialized-tables.json','INITIALIZED_NATIVE_TABLES.md'),
        ('ui-object-initialization.json','OBJECT_INITIALIZATION.md')]


class NativeProbeContractTests(unittest.TestCase):
    def test_initialized_plan_metadata_hashes_are_documented_and_scoped(self):
        plan=json.loads((ROOT/'references/probes/font-metrics-initialized-tables.json').read_bytes())
        text=(ROOT/'docs/INITIALIZED_NATIVE_TABLES.md').read_text(encoding='utf-8')
        self.assertEqual([(t['engine_class'],t['table_count']) for t in plan['tables']],[('Font',2),('MultiFont',1),('Canvas',10)])
        for table in plan['tables']:
            self.assertIn(table['metadata_sha256'],text)
            self.assertEqual(table['symbol_prefix'],'intU'+table['engine_class']+'exec')
        self.assertIn('--native-only',text)

    def test_initialized_plan_does_not_relabel_cold_descriptor_profile(self):
        new=json.loads((ROOT/'references/probes/font-metrics-initialized-tables.json').read_bytes())
        old=json.loads((ROOT/'references/probes/ui-draw-string-native.json').read_bytes())
        self.assertEqual(new['profile'],'ppc-initialized-native-row8-v1')
        self.assertEqual(old['profile'],'ppc-native-row12-cold-init-v1')
        self.assertNotIn('initializer_start',new);self.assertIn('initializer_start',old)

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
