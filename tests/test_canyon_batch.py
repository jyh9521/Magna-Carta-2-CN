"""Source-free contracts for enhancement, canyon scenes and hostage rescue."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class CanyonBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-009.json')
        self.review = load('locales/zh-Hans/batch-009.review.json')

    def test_scope_and_suffix_branch(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 72, 'MC2NpcTalk.int': 20,
                                 'MC2Quest.int': 43, 'linked-name-fields': 9})
        self.assertIn({'document': 'MC2CSMB.int', 'section': 'CSMB02_60_1', 'entries': 5},
                      self.review['coverage'])
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 125, 'narrative': 5, 'name': 10, 'menu': 1,
                          'quest_description': 1, 'quest_progress': 1, 'quest_objective': 1})

    def test_ids_are_new_and_review_complete(self):
        paths = [b['plan']['path'] for b in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(paths[8], 'locales/zh-Hans/batch-009.json')
        old = {e['id'] for p in paths[:8] for e in load(p)['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (1632, 144, 144))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        self.assertEqual(self.review['status'], 'draft')

    def test_functional_choice_and_quest_layout(self):
        ids = self.review['preserved_functional_break_ids']
        rows = [e for e in self.plan['entries'] if e['id'] in ids]
        self.assertEqual(len(rows), 2)
        self.assertEqual(sorted(e['translation'].count('\\n') for e in rows), [1, 6])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        choice = next(e['translation'] for e in rows if '<Styles:' in e['translation'])
        self.assertLess(choice.index('>X<Styles:/>'), choice.index('>Y<Styles:/>'))
        description = next(e['translation'] for e in rows if '[反击]' in e['translation'])
        self.assertIn('\\n\\n', description)
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST%s: 营救人质！'])
        self.assertEqual(progress[0].count('%s'), 1)

    def test_linked_names_and_terms(self):
        translations = [e['translation'] for e in self.plan['entries']]
        self.assertEqual(translations.count('公会联盟成员'), 2)
        for name in ('精华提取', '强化', '水色湿地', '杜南丘陵', '克蕾尔', '修亚伦'):
            self.assertIn(name, translations)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 143)
        for source, target in [('카몬드 보드', '卡蒙德盘'), ('정수추출', '精华提取'), ('홀', '插孔')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')

    def test_hashes_and_explicit_break_policies(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)


if __name__ == '__main__':
    unittest.main()
