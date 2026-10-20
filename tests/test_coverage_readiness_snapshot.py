"""Source-free snapshot contracts; missing coverage must not masquerade as release."""
from pathlib import Path
import json
import unittest


class CoverageReadinessSnapshotTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.p = json.loads((root / 'locales/zh-Hans/coverage-readiness.json').read_bytes())

    def test_packet_and_cumulative_scope_are_distinct(self):
        self.assertEqual(self.p['packet']['existing_int_entries'], 262)
        self.assertEqual(self.p['demand']['int_entries'], 14082)
        self.assertEqual(self.p['packet']['verified_hash_references'], 64)
        self.assertEqual(self.p['packet']['resource_count'], 10)

    def test_int_and_subtitle_demand_are_separate(self):
        d = self.p['demand']
        self.assertEqual((d['int_literal_codepoints'], d['combined_literal_codepoints']), (2446, 2451))
        self.assertEqual(d['subtitle_entries'], 315)
        self.assertEqual(d['subtitle_only_codepoints'], [21009, 28382, 31713, 34615, 39278])

    def test_all_seven_aliases_have_confirmed_gaps(self):
        fonts = self.p['fonts']; self.assertEqual(len(fonts), 7)
        self.assertEqual(len({f['label'] for f in fonts}), 7)
        for i, f in enumerate(fonts):
            self.assertEqual(f['status_counts']['missing-remap'], 1616 if i < 5 else 1615)
            self.assertEqual(f['status_counts']['mapped'], 834 if i < 5 else 835)
            self.assertEqual(sum(f['status_counts'].values()), 2451)
            self.assertRegex(f['package_sha256'], r'^[0-9a-f]{64}$')

    def test_control_literal_is_not_silently_removed_or_drawn(self):
        self.assertEqual(self.p['demand']['unverified_control_codepoints'], [9])
        self.assertTrue(all(f['status_counts']['control-or-format-literal-unverified'] == 1
                            for f in self.p['fonts']))

    def test_readiness_does_not_claim_rendering_or_refresh(self):
        for k in ['full_glyph_coverage_ready', 'game_rendering_verified', 'resource_refresh_performed']:
            self.assertIs(self.p[k], False)
        self.assertEqual(self.p['status'], 'offline-gap-confirmed-not-deployed')
        for k in ['source_sha256', 'workflow_sha256']:
            self.assertRegex(self.p[k], r'^[0-9a-f]{64}$')


if __name__ == '__main__':
    unittest.main()
