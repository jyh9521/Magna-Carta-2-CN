"""Source-free contracts for marsh defense, state NPCs and the bell quest."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class DefenseBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-014.json')
        self.review = load('locales/zh-Hans/batch-014.review.json')

    def test_scope_and_classification(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 62, 'MC2NpcTalk.int': 40,
                                 'MC2Quest.int': 19, 'linked-name-fields': 2})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 115, 'name': 3, 'quest_description': 1,
                          'quest_progress': 2, 'quest_objective': 2})
        self.assertEqual(self.review['status'], 'draft')

    def test_increment_and_review_complete(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[13]['plan']['path'], 'locales/zh-Hans/batch-014.json')
        old = {e['id'] for b in batches[:13] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2397, 123, 123))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        self.assertEqual(self.review['held_entries'], [])

    def test_bell_layout_and_progress_prefix_spaces(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        description = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(description['translation'].count('\\n'), 2)
        self.assertNotIn('line_break_policy', description)
        for word in ('[猫猫的铃铛]', '打开', '钥匙'):
            self.assertIn(word, description['translation'])
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(progress, ['QUEST : 获得猫猫的铃铛', 'QUEST : 获得黑猫猫的钥匙'])

    def test_state_section_and_candidate_items(self):
        sections = {r.get('section'): r['entries'] for r in self.review['coverage']}
        self.assertEqual(sections['CSMB03_150'], 33)
        self.assertEqual(sections['Ch03_KotaMare_01'], 40)
        self.assertNotIn('Ch03_KotaMare_02', sections)
        self.assertTrue(any('03_313_00' in n for n in self.review['notes']))
        translations = [e['translation'] for e in self.plan['entries']]
        for name in ('猫猫的铃铛', '黑猫猫的钥匙'):
            self.assertIn(name, translations)
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 168)
        for source, target in [('네코네코의 방울', '猫猫的铃铛'), ('검은 네코네코의 열쇠', '黑猫猫的钥匙')]:
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

    def test_battle_movie_plan_locked(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 14)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:13]), 111)
        spec = profile['plans'][13]
        raw = (ROOT / spec['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
        plan = json.loads(raw)
        self.assertEqual(plan['resource'], 'MC2Game/Movies/csm03-140.txt')
        self.assertEqual(len(plan['entries']), 2)
        self.assertEqual([e['start'] for e in plan['entries']], [1485, 54360])
        self.assertTrue(all('source' not in e and e['start'] < e['end'] for e in plan['entries']))


if __name__ == '__main__':
    unittest.main()
