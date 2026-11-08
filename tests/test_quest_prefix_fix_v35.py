"""The repair changes only the eight confirmed mixed-case notification prefixes."""
import hashlib
import json
from pathlib import Path
import unittest

from tools.build_coalesced import resolve_prefix
from tools.validate_catalog import TOKEN

ROOT = Path(__file__).resolve().parents[1]


class QuestPrefixRepairTests(unittest.TestCase):
    def test_every_confirmed_prefix_has_one_hash_guarded_edit(self):
        old = json.loads((ROOT/'locales/zh-Hans/omission-findings-v34.json').read_bytes())
        findings = {r['field_id']: r for r in old['findings']
                    if r['kind'] == 'untranslated-notification-prefix'}
        plan = json.loads((ROOT/'locales/zh-Hans/quest-prefix-fix-v35.json').read_bytes())
        self.assertEqual(plan['source_mode'], 'sha256-utf8-prefix')
        self.assertEqual(plan['resource'], 'MC2Game/Localization/Coalesced.int')
        self.assertEqual(plan['input_sha256'], 'b7bb76bc8b07dcf217511cdbbebe69be19a99025530ae1ff57223e1ca576eadd')
        self.assertEqual(len(plan['entries']), 8)
        self.assertEqual({e['id'] for e in plan['entries']}, set(findings))
        for edit in plan['entries']:
            source = findings[edit['id']]['effective_value']
            self.assertEqual(edit['source_sha256'], hashlib.sha256(source.encode()).hexdigest())
            self.assertEqual(edit['source_prefix_codepoints'], 5)
            self.assertEqual(edit['replacement'], '任务')
            self.assertIs(edit['preserve_utf16_units'], False)
            target, proof = resolve_prefix(source, edit, edit['selector'])
            self.assertEqual(target, '任务'+source[5:])
            self.assertEqual(TOKEN.findall(source), TOKEN.findall(target))
            self.assertEqual(proof['preserved_suffix_sha256'], hashlib.sha256(source[5:].encode()).hexdigest())

    def test_known_hangul_holds_are_not_silently_reclassified(self):
        before = json.loads((ROOT/'locales/zh-Hans/omission-screen-v34.json').read_bytes())
        after = json.loads((ROOT/'locales/zh-Hans/omission-screen-v35.json').read_bytes())
        for key in ('known_dispositions', 'script_ranges', 'prefix_rules'):
            self.assertEqual(before[key], after[key])
        self.assertNotEqual(before['snapshot']['current_primary_sha256'],
                            after['snapshot']['current_primary_sha256'])


if __name__ == '__main__':
    unittest.main()
