"""Source-free contracts for rescue aftermath, Hwan's letter and early movies."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class ReturnBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-013.json')
        self.review = load('locales/zh-Hans/batch-013.review.json')

    def test_scope_and_classification(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 95, 'MC2NpcTalk.int': 41,
                                 'MC2Quest.int': 13, 'linked-name-fields': 2})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 147, 'name': 3, 'quest_description': 1})
        self.assertEqual(self.review['status'], 'draft')

    def test_increment_and_review_ids(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[12]['plan']['path'], 'locales/zh-Hans/batch-013.json')
        old = {e['id'] for b in batches[:12] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2246, 151, 151))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        self.assertEqual(self.review['held_entries'], [])

    def test_letter_layout_and_dialogue_quantities(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        row = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(row['translation'].count('\\n'), 1)
        self.assertNotIn('line_break_policy', row)
        self.assertIn('[胡安的信]', row['translation'])
        translations = [e['translation'] for e in self.plan['entries']]
        self.assertIn('胡安的信', translations)
        self.assertIn('胡安的请求', translations)
        text = '\n'.join(translations)
        for phrase in ('100份', '200份', '尼尔提是我的儿子'):
            self.assertIn(phrase, text)

    def test_separate_npc_states_and_candidates(self):
        sections = {r.get('section'): r['entries'] for r in self.review['coverage']}
        self.assertEqual(sections['02_oldfox'], 14)
        self.assertEqual(sections['Ch03_KotaMare'], 27)
        self.assertNotIn('Ch03_KotaMare_01', sections)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 165)
        for source, target in [('후안의 편지', '胡安的信'), ('치유연환술', '治愈连环术'),
                               ('바리케이드', '路障'), ('사랑의 묘약', '爱情魔药')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')

    def test_public_hashes_and_break_policy(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)

    def test_early_subtitles_are_source_locked(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 13)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:10]), 93)
        totals = []
        for spec in profile['plans'][10:13]:
            raw = (ROOT / spec['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
            plan = json.loads(raw)
            totals.append(len(plan['entries']))
            self.assertTrue(all('source' not in e and e['start'] < e['end'] for e in plan['entries']))
        self.assertEqual(totals, [8, 9, 1])


if __name__ == '__main__':
    unittest.main()
