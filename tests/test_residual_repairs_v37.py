import hashlib
from collections import Counter
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_bytes())


class ResidualRepairPlanTests(unittest.TestCase):
    def test_inscription_uses_confirmed_id_and_preserves_functional_break(self):
        plan = read('locales/zh-Hans/inscription-fix-v37.json')
        prior = read('locales/zh-Hans/omission-screen-v36.json')
        self.assertEqual(plan['input_sha256'], prior['snapshot']['current_primary_sha256'])
        self.assertEqual(plan['source_mode'], 'sha256-utf8')
        self.assertEqual(len(plan['entries']), 1)
        row = plan['entries'][0]
        found = next(x for x in prior['known_dispositions'] if x['id'] == row['id'])
        self.assertEqual(found['status'], 'confirmed-player-gap')
        self.assertEqual(row['source_sha256'], found['value_sha256'])
        self.assertEqual(row['translation'].count('\\n'), 1)
        self.assertEqual(row['translation'], '败者啊，将目光投向黑暗。\\n待兴盛之魂苏醒，南天之星将闪耀光芒……')

    def test_forty_separate_fields_preserve_original_source_locks(self):
        plan = read('locales/zh-Hans/residual-text-fixes-v37.json')
        old = {x['id']: x for x in read('locales/zh-Hans/omission-screen-v36.json')['known_dispositions']}
        self.assertEqual(plan['input_sha256'], 'feaac13b591b00fc46b090cccb15bc8dca6599881a03b581427907544348699a')
        self.assertEqual(len(plan['entries']), 40)
        self.assertEqual(len({x['id'] for x in plan['entries']}), 40)
        for row in plan['entries']:
            self.assertEqual(row['source_sha256'], old[row['id']]['value_sha256'])
            self.assertTrue(row['translation'])
            self.assertFalse(re.search('[\uac00-\ud7a3\x00\r\n]', row['translation']))
        values = [x['translation'] for x in plan['entries']]
        self.assertEqual(values.count('删除'), 24)
        self.assertEqual(values.count('默认值：请输入新标签值'), 3)
        self.assertEqual(values.count('" "'), 2)
        self.assertIn('缺失的台词？', values)  # No invented substitute dialogue.
        self.assertIn('我一直想亲眼看看马雷的资料。（游戏中未使用的台词）', values)

    def test_tagged_plans_only_touch_exact_display_property_not_identifiers(self):
        manifest = read('locales/zh-Hans/tagged-string-fixes-v37/manifest.json')
        prior = read('locales/zh-Hans/omission-package-findings-v36.json')['findings']
        expected = {(x['resource'], x['owner']['path']): x for x in prior if x['field'] == 'StyleName'}
        seen = set()
        self.assertEqual(len(manifest['resources']), 10)
        for resource in manifest['resources']:
            raw = (ROOT/resource['plan']).read_bytes()
            self.assertNotIn(b'\r', raw)  # Hashes must survive Git's LF checkout policy.
            self.assertEqual(hashlib.sha256(raw).hexdigest(), resource['plan_sha256'])
            plan = json.loads(raw)
            for obj in plan['objects']:
                key = resource['resource'], obj['object_path']; self.assertNotIn(key, seen); seen.add(key)
                self.assertEqual(resource['source_sha256'], expected[key]['package_sha256'])
                self.assertEqual(obj['tagged_offset'], 4)
                self.assertEqual(obj['class_path'], 'MC2Game.MC2BattleYupa')
                self.assertEqual(obj['fields'], [dict(name='StyleName', array_index=0, before='대포', after='大炮')])
        self.assertEqual(seen, set(expected))

    def test_every_pending_identity_has_an_explicit_honest_disposition(self):
        prior = read('locales/zh-Hans/omission-screen-v36.json')
        ledger = read('locales/zh-Hans/omission-resolutions-v37.json')
        expected = {x['id'] for x in prior['known_dispositions'] if x['status'] != 'excluded'}
        expected.update(x['id'] for x in read('locales/zh-Hans/omission-package-findings-v36.json')['findings'])
        rows = ledger['findings']
        self.assertEqual(len(rows), 94)
        self.assertEqual(len({x['id'] for x in rows}), 94)
        self.assertEqual({x['id'] for x in rows}, expected)
        self.assertEqual(dict(Counter(x['disposition'] for x in rows)), ledger['summary'])
        self.assertEqual(ledger['summary']['localized'], 52)
        self.assertEqual(ledger['summary']['pending-malformed-source'], 3)
        self.assertEqual(ledger['summary']['pending-test-data-consumer'], 9)
        self.assertFalse(ledger['complete_game_coverage_claimed'])
        for row in rows:
            if row['disposition'].startswith('pending-'):
                self.assertTrue(row['next_check'])

    def test_strict_policy_keeps_malformed_source_pending_and_exclusions_unchanged(self):
        before = read('locales/zh-Hans/omission-screen-v36.json')
        after = read('locales/zh-Hans/omission-screen-v37.json')
        old_excluded = {x['id']: x for x in before['known_dispositions'] if x['status'] == 'excluded'}
        new_excluded = {x['id']: x for x in after['known_dispositions'] if x['status'] == 'excluded'}
        self.assertEqual(new_excluded, old_excluded)
        self.assertEqual(Counter(x['status'] for x in after['known_dispositions']), dict(excluded=23, pending=3))
        adopted = {x['id'] for name in ('inscription-fix-v37', 'residual-text-fixes-v37')
                   for x in read('locales/zh-Hans/' + name + '.json')['entries']}
        self.assertEqual({x['id'] for x in after['known_dispositions']},
                         {x['id'] for x in before['known_dispositions']} - adopted)

    def test_unused_quest_argument_decision_is_locked_to_exact_plain_templates(self):
        ledger = read('locales/zh-Hans/omission-resolutions-v37.json')
        proof = ledger['native_quest_template_proof']
        table = bytes.fromhex(proof['table_hex'])
        self.assertEqual(hashlib.sha256(table).hexdigest(), proof['transition_table_sha256'])
        rows = [x for x in ledger['findings'] if x['disposition'] == 'preserved-current-template-unused-argument']
        self.assertEqual(len(rows), 27)
        for row in rows:
            template = row['template']; text = template['resolved_value']
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), template['resolved_sha256'])
            self.assertNotIn('%', text)
            state = 0
            for char in text:
                n = ord(char); category = table[n - 0x20] & 15 if 0x20 <= n <= 0x78 else 0
                value = table[category * 8 + state]
                state = (value - 256 if value >= 128 else value) >> 4
                self.assertEqual(state, 0)


if __name__ == '__main__': unittest.main()
