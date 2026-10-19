"""Source-free contracts for royal proof, introspection, and Dunan tasks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class ProofBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-018.json')
        self.review = load('locales/zh-Hans/batch-018.review.json')
    def test_scope_and_narrative(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 91, 'MC2NpcTalk.int': 31, 'MC2Quest.int': 42,
                                 'MC2CharacterName.int': 2, 'MC2FieldName.int': 1, 'MC2Item.int': 2})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 146, 'narrative': 6, 'name': 7, 'quest_description': 3,
                          'quest_progress': 3, 'quest_objective': 3, 'item_description': 1})
        self.assertEqual(self.review['status'], 'draft')
    def test_disjoint_increment(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[17]['plan']['path'], 'locales/zh-Hans/batch-018.json')
        old = {e['id'] for b in batches[:17] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (2971, 169, 169))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
    def test_functional_paragraph_and_stats(self):
        rows = [e for e in self.plan['entries'] if e['id'] in self.review['preserved_functional_break_ids']]
        self.assertEqual([e['translation'].count('\\n') for e in rows], [5, 1, 2, 1])
        self.assertIn('\\n\\n', rows[0]['translation'])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        self.assertTrue(rows[-1]['translation'].endswith('\\n攻击+70'))
        self.assertIn('[阿尔斯]', rows[1]['translation'])
        self.assertIn('第1哨所', rows[2]['translation'])
        progress = [e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST')]
        self.assertEqual(len(progress), 3)
        self.assertTrue(all(t.startswith('QUEST%s : ') and t.count('%s') == 3 for t in progress))
    def test_proof_claim_and_linked_fields(self):
        values = [e['translation'] for e in self.plan['entries']]
        self.assertIn('而且，4片王之证明中，他已经得到了两片。这才是真正的王者之证。', values)
        for value in ['王室之魂', '黑刃要塞', '阿尔斯', '机密文件']:
            self.assertIn(value, values)
        self.assertIn('嗯。我们约好了，等这场战争结束，就结婚。', values)
        self.assertTrue(any('两处哨所' in t for t in values))
    def test_candidate_terms(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 183)
        for source, target in [('왕의 증명', '王之证明'), ('왕가의 영혼', '王室之魂'),
                               ('검은 칼날 요새', '黑刃要塞'), ('알스', '阿尔斯'), ('기밀문서', '机密文件')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
            self.assertEqual(terms[source]['relation'], 'unverified')
    def test_locked_payload_and_movie_nonduplication(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 18)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:18]), 141)
        for spec in profile['plans'][:18]:
            self.assertEqual(hashlib.sha256((ROOT / spec['path']).read_bytes()).hexdigest(), spec['sha256'])
if __name__ == '__main__':
    unittest.main()
