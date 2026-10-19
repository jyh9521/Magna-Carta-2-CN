"""Source-free contracts for fourth-prefix Cube mail and conservative layout."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT / path).read_bytes())
class Mail04BatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-023.json')
        self.review = load('locales/zh-Hans/batch-023.review.json')
    def test_scope_and_classification(self):
        counts = Counter()
        for c in self.review['coverage']:
            counts[c['document']] += c['entries']
        self.assertEqual(counts, {'MC2QubeMail.int': 58, 'MC2CharacterName.int': 1})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'mail_subject': 29, 'mail_body': 29, 'name': 1})
        self.assertEqual(self.review['status'], 'draft')
        sections = [c for c in self.review['coverage'] if c['document'] == 'MC2QubeMail.int']
        self.assertEqual([c['section'] for c in sections], [f'E04_{i:03d}' for i in range(1, 30)])
        self.assertTrue(all(c['entries'] == 2 for c in sections))
    def test_disjoint_increment(self):
        batches = load('locales/zh-Hans/translation-workflow.json')['batches']
        self.assertEqual(batches[22]['plan']['path'], 'locales/zh-Hans/batch-023.json')
        old = {e['id'] for b in batches[:22] for e in load(b['plan']['path'])['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (3775, 59, 59))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
    def test_all_mail_hard_breaks_and_empty_paragraphs_preserved(self):
        rows = [e for e in self.plan['entries'] if e['id'] in self.review['preserved_functional_break_ids']]
        expected = [10,9,9,8,6,9,11,12,11,9,10,6,3,11,9,9,8,10,10,9,6,5,9,9,9,10,8,8,5]
        self.assertEqual(len(rows), 29)
        self.assertEqual([e['translation'].count('\\n') for e in rows], expected)
        self.assertTrue(all('line_break_policy' not in e for e in self.plan['entries']))
        self.assertEqual([i for i, line in enumerate(rows[0]['translation'].split('\\n')) if not line], [2,7])
        self.assertEqual([i for i, line in enumerate(rows[7]['translation'].split('\\n')) if not line], [3,8])
        self.assertIn('你了解兰兹海姆历吗？ ', [e['translation'] for e in self.plan['entries']])
    def test_numeric_markers_and_reported_viewpoints(self):
        values = [e['translation'] for e in self.plan['entries']]
        self.assertTrue(any('180度' in t for t in values))
        self.assertTrue(any('1152年' in t and '3000年前' in t for t in values))
        self.assertTrue(any('LV2卡蒙德' in t for t in values))
        self.assertIn('南部军常识 (5)', values)
        self.assertTrue(any('生母' in t and '伊芙琳' in t for t in values))
        self.assertTrue(any('并非所有黑角' in t for t in values))
    def test_candidate_names_and_linked_author(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 200)
        for source, target in [('이그톤','伊格顿'),('휘시스','惠西斯'),('아비스베르크','阿维斯贝尔克'),
                               ('레트러뷰션','惩戒者'),('칼리다','卡利达'),('이블린','伊芙琳')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
            self.assertEqual(terms[source]['relation'], 'unverified')
        self.assertIn('伊格顿', [e['translation'] for e in self.plan['entries']])
    def test_locked_payload_and_movie_nonduplication(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 18)
        self.assertEqual(sum(len(load(s['path'])['entries']) for s in profile['plans'][:18]), 141)
        for spec in profile['plans'][:18]:
            self.assertEqual(hashlib.sha256((ROOT / spec['path']).read_bytes()).hexdigest(), spec['sha256'])
if __name__ == '__main__':
    unittest.main()
