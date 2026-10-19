"""Source-free contracts for Kotamare dialogue, fire KAN and movie cues."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class KotamareBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-011.json')
        self.review = load('locales/zh-Hans/batch-011.review.json')

    def test_scope_and_classification(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 172, 'MC2NpcTalk.int': 18,
                                 'MC2Quest.int': 19, 'linked-name-fields': 4})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 205, 'name': 5, 'quest_description': 1,
                          'quest_progress': 1, 'quest_objective': 1})
        self.assertEqual(self.review['status'], 'draft')

    def test_unique_increment_and_untranslated_markers(self):
        paths = [b['plan']['path'] for b in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(paths[10], 'locales/zh-Hans/batch-011.json')
        old = {e['id'] for p in paths[:10] for e in load(p)['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (1889, 213, 213))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        held = self.review['held_entries']
        self.assertEqual({e['key'] for e in held}, {'02_2263_00', '02_2269_00'})
        self.assertTrue(all(e['id'] not in old | set(ids) for e in held))

    def test_fire_kan_conditions_and_layout(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        description = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(description['translation'].count('\\n'), 2)
        self.assertNotIn('line_break_policy', description)
        for word in ('同一区域', '至少6个', '火属性普通攻击', '[连环力增幅]'):
            self.assertIn(word, description['translation'])
        self.assertIn('QUEST%s: 产生6个火之KAN', [e['translation'] for e in self.plan['entries']])
        text = '\n'.join(e['translation'] for e in self.plan['entries'])
        for word in ('60岁', '200年', '12岁', '10年'):
            self.assertIn(word, text)

    def test_candidate_names_and_linked_fields(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 154)
        for source, target in [('세레스틴', '塞蕾丝汀'), ('케이틴', '凯汀'),
                               ('연환력 증대', '连环力增幅'), ('마비향', '麻痹香')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
        translations = [e['translation'] for e in self.plan['entries']]
        for name in ('塞蕾丝汀', '凯汀', '海底洞窟', '连环力增幅'):
            self.assertIn(name, translations)

    def test_public_hashes_and_explicit_breaks(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)

    def test_adjacent_subtitle_plan_is_locked(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 7)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:6]), 57)
        spec = profile['plans'][6]
        self.assertEqual(spec['path'], 'locales/zh-Hans/subtitles/batch-011-csm03-40.txt.json')
        raw = (ROOT / spec['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
        plan = json.loads(raw)
        self.assertEqual(plan['resource'], 'MC2Game/Movies/csm03-40.txt')
        self.assertEqual(len(plan['entries']), 9)
        self.assertEqual(sum(e['translation'].count('<br>') for e in plan['entries']), 2)
        self.assertTrue(all('source' not in e and e['start'] < e['end'] for e in plan['entries']))


if __name__ == '__main__':
    unittest.main()
