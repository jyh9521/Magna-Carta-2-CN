from pathlib import Path
import hashlib
import json
import unittest

R = Path(__file__).resolve().parents[1]


class RemainingWeaponsRetentionTests(unittest.TestCase):
    def test_source_locked_retention_without_locale_overwrite(self):
        def load(path):
            return json.loads((R / path).read_bytes())

        def digest(text):
            return hashlib.sha256(text.encode('utf-8')).hexdigest()

        d = load('locales/zh-Hans/candidate-decisions/remaining-weapons-retention.json')
        self.assertEqual((d['context_fields'], d['source_physical'],
                          d['translation_edits'], d['new_primary_consistency_fields']),
                         (173, 180, 0, 0))
        entries = {}
        for batch in load('locales/zh-Hans/translation-workflow.json')['batches']:
            entries.update({e['id']: e for e in load(batch['plan']['path'])['entries']})
        self.assertEqual(len(d['retained_entries']), 173)
        for e in d['retained_entries']:
            current = entries[e['id']]
            self.assertEqual(current['source_sha256'], e['source_sha256'])
            self.assertEqual(digest(current['translation']), e['translation_sha256'])
        by_key = {e['key']: entries[e['id']] for e in d['retained_entries']}
        for decision in d['decisions']:
            self.assertEqual(decision['target'], by_key[decision['key']]['translation'])
        self.assertEqual(len(d['retained_originals']), 7)
        for e in d['retained_originals']:
            adopted = {a['id']: a for a in load('locales/zh-Hans/candidate-decisions/preserved-partials-adoption.json')['entries']}
            if e['id'] in entries:
                self.assertIn(e['id'], adopted)
                self.assertEqual(entries[e['id']]['source_sha256'], e['source_sha256'])
                self.assertEqual(digest(entries[e['id']]['translation']), adopted[e['id']]['translation_sha256'])
            else:
                self.assertNotIn(e['id'], adopted)
        self.assertEqual(len(d['parallel_locale_sources']), 6)
        for disc in [1, 2]:
            rows = [e for e in d['parallel_locale_sources'] if e['disc'] == disc]
            self.assertEqual(len(rows), 3)
            self.assertEqual(next(e['source'] for e in rows if e['key'] == '409_knuckle'), '幻想拳')
            for e in rows:
                self.assertEqual(digest(e['source']), e['source_sha256'])
        for flag in ['human_finalized', 'runtime_layout_approved', 'game_rendering_verified']:
            self.assertFalse(d[flag])


if __name__ == '__main__':
    unittest.main()
