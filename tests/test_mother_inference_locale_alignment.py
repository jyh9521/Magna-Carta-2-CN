from pathlib import Path
import hashlib
import json
import unittest

R = Path(__file__).resolve().parents[1]


class MotherInferenceLocaleAlignmentTests(unittest.TestCase):
    def test_past_inference_retained_without_same_key_locale_overwrite(self):
        def load(path):
            return json.loads((R / path).read_bytes())

        def digest(text):
            return hashlib.sha256(text.encode('utf-8')).hexdigest()

        d = load('locales/zh-Hans/candidate-decisions/mother-inference-locale-alignment.json')
        self.assertEqual((d['context_fields'], d['translation_edits'],
                          d['new_primary_consistency_fields']), (157, 0, 0))
        entries = {}
        for batch in load('locales/zh-Hans/translation-workflow.json')['batches']:
            entries.update({e['id']: e for e in load(batch['plan']['path'])['entries']})
        self.assertEqual(len(d['retained_entries']), 157)
        for e in d['retained_entries']:
            self.assertEqual(entries[e['id']]['source_sha256'], e['source_sha256'])
            self.assertEqual(digest(e['source']), e['source_sha256'])
            self.assertEqual(entries[e['id']]['translation'], e['translation'])
            self.assertEqual(digest(e['translation']), e['translation_sha256'])
        by_key = {e['key']: e for e in d['retained_entries']}
        self.assertIn('反对过', by_key['voc_csmb_1130_46']['translation'])
        self.assertIn('겠지', by_key['voc_csmb_1130_47']['source'])
        self.assertNotIn('杀', by_key['voc_csmb_1130_47']['translation'])
        self.assertEqual(len(d['parallel_locale_sources']), 12)
        for disc in [1, 2]:
            rows = {e['key']: e for e in d['parallel_locale_sources'] if e['disc'] == disc}
            self.assertEqual(len(rows), 6)
            self.assertEqual(rows['voc_csmb_1130_46']['source'], 'ゼフィ・・・？')
            self.assertIn('反対したのだと思う', rows['voc_csmb_1130_47']['source'])
            self.assertIn('殺されて', rows['voc_csmb_1130_48']['source'])
            for e in rows.values():
                self.assertEqual(digest(e['source']), e['source_sha256'])
        self.assertTrue(d['alignment']['offset_is_local_observation_not_general_rule'])
        for flag in ['human_finalized', 'runtime_layout_approved', 'game_rendering_verified']:
            self.assertFalse(d[flag])


if __name__ == '__main__':
    unittest.main()
