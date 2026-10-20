"""Current text revisions do not rewrite historical font/style experiments."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_line_context import atoms
from tools.audit_text_font_coverage import literal_codepoints
from tools.validate_catalog import TOKEN

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'locales/zh-Hans/readability-fix.json'
CURRENT = 'locales/zh-Hans/readability-revised.json'
TERM = 'coalesced:72eff463a7ab0592d9c4f9af4a5916dc27732b3815a5eafdfb56a048464c4d96'
NUMBER = 'coalesced:97cee44222d2dbfa70581cccc02656f6da6cb366b411c31a751e671ee7cb7642'


def load(name):
    return json.loads((ROOT/name).read_bytes())


class ReadabilityRevisionTests(unittest.TestCase):
    def test_only_two_exact_scalars_in_single_existing_workflow_slot(self):
        old = load(BASELINE)
        current = load(CURRENT)
        expected = copy.deepcopy(old)
        for entry in expected['entries']:
            if entry['id'] == TERM:
                self.assertIn('尖刺蠕虫', entry['translation'])
                entry['translation'] = entry['translation'].replace('尖刺蠕虫', '穿刺蠕虫')
            elif entry['id'] == NUMBER:
                self.assertIn('第三年', entry['translation'])
                entry['translation'] = entry['translation'].replace('第三年', '第3年')
        self.assertEqual(current, expected)
        self.assertEqual(len(current['entries']), 262)
        refs = [batch['plan'] for batch in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(sum(ref['path'] == CURRENT for ref in refs), 1)
        self.assertFalse(any(ref['path'] == BASELINE for ref in refs))
        ref = next(ref for ref in refs if ref['path'] == CURRENT)
        self.assertEqual(hashlib.sha256((ROOT/CURRENT).read_bytes()).hexdigest(), ref['sha256'])

    def test_strict_atoms_controls_and_full_demand_subset(self):
        old = {entry['id']: entry for entry in load(BASELINE)['entries']}
        current = {entry['id']: entry for entry in load(CURRENT)['entries']}
        self.assertNotEqual(atoms(old[NUMBER]['translation']), atoms('3'))
        self.assertEqual(atoms(current[NUMBER]['translation']), atoms('3'))
        for identity in [TERM, NUMBER]:
            self.assertEqual(TOKEN.findall(old[identity]['translation']), TOKEN.findall(current[identity]['translation']))
        before = set()
        after = set()
        seen = set()
        for batch in load('locales/zh-Hans/translation-workflow.json')['batches']:
            path = batch['plan']['path']
            entries = load(path)['entries']
            for entry in entries:
                self.assertNotIn(entry['id'], seen)
                seen.add(entry['id'])
                before_entry = old[entry['id']] if path == CURRENT else entry
                before.update(literal_codepoints(before_entry['translation']))
                after.update(literal_codepoints(entry['translation']))
        self.assertEqual(len(seen), 14082)
        self.assertEqual(len(before), 2446)
        self.assertEqual(len(after), 2445)
        self.assertEqual(before-after, {ord('尖')})
        self.assertFalse(after-before)


if __name__ == '__main__':
    unittest.main()
