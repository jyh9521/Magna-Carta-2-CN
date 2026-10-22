"""Source spelling and destination identity are distinct claims."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


class ChapterTermAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.d = load('locales/zh-Hans/candidate-decisions/chapter-term-adoption.json')
        self.p = load(self.d['plan'])

    def test_exact_one_new_draft_and_hash_locks(self):
        self.assertEqual(len(self.p['entries']), 1)
        self.assertEqual(self.d['new_translations'], 1)
        for field in ['plan', 'review']:
            self.assertEqual(hashlib.sha256((ROOT / self.d[field]).read_bytes()).hexdigest(), self.d[field + '_sha256'])
        e = self.p['entries'][0]
        self.assertEqual(e['id'], self.d['entries'][0]['id'])
        self.assertEqual(digest(e['translation']), self.d['entries'][0]['translation_sha256'])
        self.assertIn('[王之灵庙]', e['translation'])

    def test_four_and_functional_tokens_not_imported_from_japanese(self):
        for disc in [1, 2]:
            e = next(e for e in self.d['evidence'] if e['disc'] == disc and e['locale'] == 'int' and e['key'] == 'Chapter12_37')
            self.assertEqual(digest(e['source']), self.p['entries'][0]['source_sha256'])
            target = self.p['entries'][0]['translation']
            for token in ['\\n', '*', '[', ']', '4']:
                self.assertEqual(e['source'].count(token), target.count(token))
            self.assertIn('왕의 영병', e['source'])
        self.assertFalse(self.d['spelling_correction_verified'])

    def test_independent_ui_and_offset_scene_alignment(self):
        for disc in [1, 2]:
            rows = {(e['locale'], e['key']): e['source'] for e in self.d['evidence'] if e['disc'] == disc}
            self.assertEqual(rows['jpn', 'lastrada_sch'], '王の霊廟')
            self.assertEqual(rows['int', 'lastrada_sch'], '라 스트라다 최심부')
            self.assertIn('중심', rows['int', 'voc_csmb_12131_07'])
            self.assertIn('王の霊廟', rows['jpn', 'voc_csmb_12131_08'])
            self.assertIn('증명', rows['int', 'voc_csmb_12131_08'])
            self.assertIn('四つ', rows['jpn', 'voc_csmb_12131_09'])
        for e in self.d['evidence']:
            self.assertEqual(digest(e['source']), e['source_sha256'])

    def test_unresolved_term_is_not_filled_by_dictionary_guess(self):
        held = self.d['retained_originals'][0]
        self.assertEqual(held['term'], '성쇄')
        ids = {e['id'] for batch in load('locales/zh-Hans/translation-workflow.json')['batches'] for e in load(batch['plan']['path'])['entries']}
        self.assertNotIn(held['id'], ids)
        self.assertFalse(self.d['human_finalized'])
        self.assertFalse(self.d['game_rendering_verified'])


if __name__ == '__main__':
    unittest.main()
