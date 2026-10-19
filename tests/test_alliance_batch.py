"""Source-free contracts for alliance, parentage and the six-target quest."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class AllianceBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-015.json')
        self.review = load('locales/zh-Hans/batch-015.review.json')

    def test_scope_and_classification(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 77, 'MC2NpcTalk.int': 26,
                                 'MC2Quest.int': 15, 'linked-name-fields': 4})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 114, 'name': 4, 'item_description': 1,
                          'quest_description': 1, 'quest_progress': 1, 'quest_objective': 1})
        self.assertEqual(self.review['status'], 'draft')

    def test_increment_and_blank_pay_preserved(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[14]['plan']['path'], 'locales/zh-Hans/batch-015.json')
        old = {e['id'] for b in batches[:14] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2520, 122, 122))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        held = self.review['held_entries']
        self.assertEqual(len(held), 1)
        self.assertEqual((held[0]['section'], held[0]['key']), ('Ch02_296_00', 'pay'))
        self.assertNotIn(held[0]['id'], old | set(ids))

    def test_quantities_progress_and_uncertainty(self):
        self.assertEqual(self.review['preserved_functional_break_ids'], [])
        text = '\n'.join(e['translation'] for e in self.plan['entries'])
        for phrase in ('15年前', '6只', '不知道他是死是活', '不确定是不是同一个人'):
            self.assertIn(phrase, text)
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST%s: 消灭黑猫猫 (%s / %s)'])
        self.assertEqual(progress[0].count('%s'), 3)

    def test_aliases_and_candidate_terms(self):
        translations = [e['translation'] for e in self.plan['entries']]
        self.assertEqual(translations.count('拜泽恩'), 2)
        self.assertIn('拜泽恩的遗物', translations)
        self.assertIn('拜泽恩留给塞蕾丝汀的遗物', translations)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 172)
        for source, target in [('바이젠', '拜泽恩'), ('은백의 바이젠', '银白的拜泽恩'), ('향수병', '香水瓶')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')

    def test_public_hashes_and_break_policies(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)

    def test_chapter_one_movie_plans_complete(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 16)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:14]), 113)
        totals = []
        for spec in profile['plans'][14:16]:
            raw = (ROOT / spec['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
            plan = json.loads(raw)
            totals.append(len(plan['entries']))
            self.assertTrue(all('source' not in e and e['start'] < e['end'] for e in plan['entries']))
        self.assertEqual(totals, [8, 6])
        chapter_one = [load(s['path']) for s in profile['plans'][:16]
                       if load(s['path'])['resource'].startswith('MC2Game/Movies/csm01-')]
        self.assertEqual(sum(len(p['entries']) for p in chapter_one), 24)


if __name__ == '__main__':
    unittest.main()
