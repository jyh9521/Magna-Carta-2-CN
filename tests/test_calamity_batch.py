"""Source-free contracts for calamity dialogue, extraction and adjacent subtitles."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


class CalamityBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan = load('locales/zh-Hans/batch-010.json')
        self.review = load('locales/zh-Hans/batch-010.review.json')

    def test_scope_and_classification(self):
        counts = Counter()
        for row in self.review['coverage']:
            counts[row['document']] += row['entries']
        self.assertEqual(counts, {'MC2CSMB.int': 73, 'MC2NpcTalk.int': 20, 'MC2Quest.int': 20})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
                         {'dialogue': 109, 'name': 1, 'quest_description': 1,
                          'quest_progress': 1, 'quest_objective': 1})
        self.assertEqual(self.review['status'], 'draft')

    def test_disjoint_ids_and_held_unknown(self):
        paths = [b['plan']['path'] for b in load('locales/zh-Hans/translation-workflow.json')['batches']]
        self.assertEqual(paths[9], 'locales/zh-Hans/batch-010.json')
        old = {e['id'] for p in paths[:9] for e in load(p)['entries']}
        ids = [e['id'] for e in self.plan['entries']]
        self.assertEqual((len(old), len(ids), len(set(ids))), (1776, 113, 113))
        self.assertFalse(old & set(ids))
        self.assertEqual(set(ids), {e['id'] for e in self.review['entries']})
        held = self.review['held_entries']
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]['key'], 'voc_csmb_0320_50')
        self.assertNotIn(held[0]['id'], old | set(ids))
        self.assertRegex(held[0]['source_sha256'], r'^[0-9a-f]{64}$')

    def test_extraction_conditions_and_layout(self):
        ids = self.review['preserved_functional_break_ids']
        self.assertEqual(len(ids), 1)
        description = next(e for e in self.plan['entries'] if e['id'] == ids[0])
        self.assertEqual(description['translation'].count('\\n'), 3)
        self.assertNotIn('line_break_policy', description)
        for word in ('濒死', '一定概率', '洁菲担任队长'):
            self.assertIn(word, description['translation'])
        self.assertIn('Quest: 精华提取成功！', [e['translation'] for e in self.plan['entries']])
        text = '\n'.join(e['translation'] for e in self.plan['entries'])
        for word in ('3年', '150年', '10年', '40年', '第2首都', '不知道是真是假'):
            self.assertIn(word, text)

    def test_candidates_and_full_name_consistency(self):
        terms = {e['source']: e for e in load('locales/zh-Hans/terms.json')['terms']}
        self.assertGreaterEqual(len(terms), 146)
        for source, target in [('마그나카르타', '真名法典'), ('루할트 내전', '鲁哈尔特内战'),
                               ('악몽의 마녀', '梦魇魔女')]:
            self.assertEqual(terms[source]['target'], target)
            self.assertEqual(terms[source]['review_status'], 'candidate')
        self.assertIn('蕾洁菲尔妲公主', '\n'.join(e['translation'] for e in self.plan['entries']))

    def test_public_hashes_and_explicit_breaks(self):
        for row in self.plan['entries']:
            self.assertNotIn('source', row)
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                self.assertGreater(row['line_break_policy']['source_count'], 0)
                self.assertEqual(row['line_break_policy']['target_count'], 0)
        self.assertEqual(sum('line_break_policy' in e for e in self.plan['entries']), 72)

    def test_subtitle_plans_are_locked_and_separate(self):
        profile = load('locales/zh-Hans/subtitle-profile.json')
        self.assertGreaterEqual(len(profile['plans']), 6)
        totals = []
        for spec in profile['plans']:
            raw = (ROOT / spec['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), spec['sha256'])
            totals.append(len(json.loads(raw)['entries']))
        self.assertEqual(sum(totals[:4]), 49)
        self.assertEqual(totals[4:6], [3, 5])
        for spec in profile['plans'][4:6]:
            plan = load(spec['path'])
            self.assertEqual(plan['kind'], 'timed-subtitle-text')
            self.assertTrue(plan['resource'].startswith('MC2Game/Movies/'))
            for row in plan['entries']:
                self.assertNotIn('source', row)
                self.assertLess(row['start'], row['end'])


if __name__ == '__main__':
    unittest.main()
