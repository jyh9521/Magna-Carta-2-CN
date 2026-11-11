"""Source-only contracts for the exact 12 inherited pending identities."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_bytes())


class PendingClosureTests(unittest.TestCase):
    def test_exact_twelve_closed_without_changing_other_findings(self):
        before = read('locales/zh-Hans/omission-resolutions-v37.json')
        after = read('locales/zh-Hans/omission-resolutions-v38.json')
        old = {x['id']: x for x in before['findings']}
        new = {x['id']: x for x in after['findings']}
        self.assertEqual(len(new), 94)
        self.assertEqual(old.keys(), new.keys())
        pending = {k for k, v in old.items() if v['disposition'].startswith('pending-')}
        self.assertEqual(len(pending), 12)
        self.assertEqual({k for k in old if old[k] != new[k]}, pending)
        self.assertEqual(Counter(x['disposition'] for x in new.values()), after['summary'])
        self.assertEqual(after['summary'], {'localized': 61,
            'preserved-native-unregistered-document': 3,
            'preserved-current-template-unused-argument': 27,
            'preserved-identity-bearing-field': 3})
        self.assertFalse(after['complete_game_coverage_claimed'])
        raw = (ROOT / after['prior_ledger']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), after['prior_ledger_sha256'])
        self.assertTrue(any('opaque' in x for x in after['remaining_coverage']))

    def test_nine_translations_bind_original_fields_and_only_display_tags(self):
        path = ROOT / 'locales/zh-Hans/legacy-display-fixes-v38.json'
        raw = path.read_bytes(); plan = json.loads(raw)
        self.assertNotIn(b'\r', raw)
        self.assertEqual(plan['profile'], 'ue3-relocated-wide-tagged-strings-v1')
        self.assertEqual(plan['source_size'], 28442624)
        self.assertEqual(plan['output_alignment'], 32768)
        self.assertEqual(len(plan['objects']), 5)
        old = {(x['owner']['path'], x['field']): x for x in
               read('locales/zh-Hans/omission-resolutions-v37.json')['findings']
               if x['disposition'] == 'pending-test-data-consumer'}
        new = {x['id']: x for x in read('locales/zh-Hans/omission-resolutions-v38.json')['findings']}
        fields = {(o['object_path'], f['name']): f for o in plan['objects'] for f in o['fields']}
        self.assertEqual(fields.keys(), old.keys())
        self.assertEqual(len(fields), 9)
        for key, field in fields.items():
            entry = old[key]; adopted = new[entry['id']]
            self.assertEqual(plan['source_sha256'], entry['package_sha256'])
            self.assertEqual(field['array_index'], 0)
            self.assertEqual(hashlib.sha256(field['before'].encode()).hexdigest(), entry['value_sha256'])
            self.assertEqual(field['after'], adopted['translation'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), adopted['plan_sha256'])
            self.assertFalse(adopted['runtime_translation_verified'])
            self.assertFalse(re.search('[\uac00-\ud7a3\x00\r\n]', field['after']))
            self.assertFalse(field['after'].endswith('。'))
        self.assertEqual(fields['data_item.etc.CureSeed', 'Description']['after'], '单体恢复30%')
        self.assertEqual(fields['data_item.etc.HealLeaf', 'Description']['after'], '全体恢复30%')
        self.assertEqual(fields['data_item.Test.Ice_Hat', 'Description']['after'], '炎热概率降低10%')
        percentages = [f['literal_percentages'] for f in fields.values() if 'literal_percentages' in f]
        self.assertCountEqual(percentages, [['30%'], ['30%'], ['10%']])

    def test_only_three_source_bound_native_exclusions_added(self):
        before = read('locales/zh-Hans/omission-screen-v37.json')
        after = read('locales/zh-Hans/omission-screen-v38.json')
        old = {x['id']: x for x in before['known_dispositions']}
        new = {x['id']: x for x in after['known_dispositions']}
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual(len(new), 26)
        self.assertEqual(before['snapshot']['current_primary_sha256'], after['snapshot']['current_primary_sha256'])
        profile_raw = (ROOT / 'references/ini-registration-profile.json').read_bytes()
        profile = json.loads(profile_raw)
        changed = []
        for key, value in old.items():
            if value['status'] == 'excluded':
                self.assertEqual(value, new[key])
            else:
                changed.append(key); updated = new[key]
                self.assertEqual(updated['value_sha256'], value['value_sha256'])
                self.assertEqual(updated['status'], 'excluded')
                proof = updated['native_evidence']
                self.assertEqual(proof['profile_sha256'], hashlib.sha256(profile_raw).hexdigest())
                self.assertEqual(proof['native_image_sha256'], profile['image_sha256'])
                self.assertEqual(proof['document_sha256'], 'e75793352fadefd4b3be757c7546e2d61a357e1fa51aac01e34769672e06e1b7')
                self.assertEqual(proof['current_section_register'], 'r27=0')
                self.assertEqual(proof['terminal_exit'], '0x82478738')
                self.assertEqual((proof['source_code_units'], proof['terminal_cursor']), (195, 196))
        self.assertEqual(len(changed), 3)


if __name__ == '__main__':
    unittest.main()
