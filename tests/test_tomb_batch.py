"""Source-free contracts for trust, tomb dialogue and four Kotamare NPC states."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class TombBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-016.json')
        self.review = load('locales/zh-Hans/batch-016.review.json')

    def test_scope_and_classification(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 134, 'MC2NpcTalk.int': 25,
                                 'MC2Quest.int': 18, 'linked-name-fields': 2})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 168, 'narrative': 5, 'name': 3,
                          'quest_description': 1, 'quest_progress': 1, 'quest_objective': 1})
        self.assertEqual(self.review['status'], 'draft')

    def test_increment_and_bounded_chapter_coverage(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[15]['plan']['path'], 'locales/zh-Hans/batch-016.json')
        old = {e['id'] for b in batches[:15] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2642, 179, 179))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        coverage = [c for b in batches[:16] for c in load(b['review']['path']).get('coverage', [])]
        self.assertEqual(sum(c['entries'] for c in coverage if c.get('document') == 'MC2CSMB.int'
                             and c.get('section', '').startswith('CSMB03_')), 687)
        held = load('locales/zh-Hans/batch-010.review.json')['held_entries'][0]
        self.assertNotIn(held['id'], old | set(ids))
        states = {'Ch03_KotaMare', 'Ch03_KotaMare_01', 'Ch03_KotaMare_02', 'Ch03_KotaMare_03'}
        self.assertEqual(sum(c['entries'] for c in coverage if c.get('document') == 'MC2NpcTalk.int'
                             and c.get('section') in states), 118)

    def test_quest_layout_and_five_targets(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        description = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(description['translation'].count('\\n'), 1)
        self.assertNotIn('line_break_policy', description)
        self.assertIn('5只[乌鸦兽]', description['translation'])
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST%s: 狩猎乌鸦兽 (%s / %s)'])
        self.assertEqual(progress[0].count('%s'), 3)

    def test_linked_names_and_candidates(self):
        translations = [e['translation'] for e in self.plan['entries']]
        self.assertIn('斯特拉斯之墓', translations)
        self.assertIn('阿塞莉娜之泪', translations)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 176)
        for source, target in [('아셀리나', '阿塞莉娜'), ('카르타대전', '卡尔塔大战'), ('스트라스의 묘', '斯特拉斯之墓')]:
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

    def test_next_chapter_movies_source_locked(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 18)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:16]), 127)
        totals = []
        breaks = 0
        for spec in profile['plans'][16:18]:
            raw = (ROOT / spec['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
            plan = json.loads(raw)
            totals.append(len(plan['entries']))
            breaks += sum(e['translation'].count('<br>') for e in plan['entries'])
            self.assertTrue(all('source' not in e and e['start'] < e['end'] for e in plan['entries']))
        self.assertEqual(totals, [1, 13])
        self.assertEqual(breaks, 6)


if __name__ == '__main__':
    unittest.main()
