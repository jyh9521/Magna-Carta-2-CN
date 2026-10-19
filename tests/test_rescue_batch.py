"""Source-free contracts for sea-cave rescue and Abazet's final NPC block."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class RescueBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-012.json')
        self.review = load('locales/zh-Hans/batch-012.review.json')

    def test_scope_and_categories(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 74, 'MC2NpcTalk.int': 54,
                                 'MC2Quest.int': 12, 'linked-name-fields': 4})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 135, 'name': 5, 'quest_description': 1,
                          'quest_progress': 1, 'quest_objective': 2})
        self.assertEqual(self.review['status'], 'draft')

    def test_increment_and_city_coverage(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[11]['plan']['path'], 'locales/zh-Hans/batch-012.json')
        old = {e['id'] for b in batches[:11] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2102, 144, 144))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        city_count = sum(c['entries'] for b in batches[:12]
                         for c in load(b['review']['path']).get('coverage', [])
                         if c.get('document') == 'MC2NpcTalk.int' and c.get('section') == 'Ch02_Abazet')
        self.assertEqual(city_count, 274)
        held = load('locales/zh-Hans/batch-011.review.json')['held_entries']
        self.assertTrue(all(e['id'] not in old | set(ids) for e in held))

    def test_quest_layout_and_three_placeholders(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        description = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(description['translation'].count('\\n'), 5)
        self.assertNotIn('line_break_policy', description)
        for word in ('3只[强壮拉普斯]', '领取斧子', '炸弹箱', '[破甲]'):
            self.assertIn(word, description['translation'])
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST%s: 消灭强壮拉普斯 (%s / %s)'])
        self.assertEqual(progress[0].count('%s'), 3)

    def test_linked_names_and_candidates(self):
        translations = [e['translation'] for e in self.plan['entries']]
        for name in ('鲁坦', '尼尔提', '杜南平原', '寂静荒野'):
            self.assertIn(name, translations)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 161)
        for source, target in [('루탄', '鲁坦'), ('니르티', '尼尔提'), ('폭탄 상자', '炸弹箱')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')

    def test_source_hashes_and_break_policy(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)

    def test_chapter_two_subtitle_plans_complete(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 10)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:7]), 66)
        totals = []
        for spec in profile['plans'][7:10]:
            raw = (ROOT / spec['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
            plan = json.loads(raw)
            self.assertTrue(plan['resource'].startswith('MC2Game/Movies/csm02-'))
            totals.append(len(plan['entries']))
            self.assertTrue(all('source' not in e and e['start'] < e['end'] for e in plan['entries']))
        self.assertEqual(totals, [13, 9, 5])
        chapter_two = [load(s['path']) for s in profile['plans'][:10]
                       if load(s['path'])['resource'].startswith('MC2Game/Movies/csm02-')]
        self.assertEqual(sum(len(p['entries']) for p in chapter_two), 30)


if __name__ == '__main__':
    unittest.main()
