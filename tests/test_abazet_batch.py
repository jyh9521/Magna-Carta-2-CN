"""Public contracts for city arrival, NPCs, choices and the first city quest."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_bytes())


class AbazetBatchTests(unittest.TestCase):
    def setUp(self):
        self.plan=load('locales/zh-Hans/batch-005.json')
        self.review=load('locales/zh-Hans/batch-005.review.json')

    def test_scope_and_classifications(self):
        self.assertEqual(len(self.plan['entries']),276)
        count=Counter()
        for row in self.review['coverage']:count[row['document']]+=row['entries']
        self.assertEqual(count,{'MC2CSMB.int':160,'MC2NpcTalk.int':84,'MC2Quest.int':21,'linked-name-fields':11})
        self.assertEqual(Counter(e['text_kind'] for e in self.review['entries']),
            {'dialogue':250,'narrative':11,'name':12,'quest_description':1,'quest_progress':1,'quest_objective':1})
        self.assertEqual(self.review['status'],'draft')
        self.assertEqual({e['id'] for e in self.plan['entries']},{e['id'] for e in self.review['entries']})

    def test_functional_choices_and_quest_paragraph_breaks_are_preserved(self):
        ids=self.review['preserved_functional_break_ids']
        self.assertEqual(len(set(ids)),3)
        rows=[e for e in self.plan['entries'] if e['id'] in ids]
        self.assertEqual(sorted(e['translation'].count('\\n') for e in rows),[1,1,3])
        self.assertTrue(all('line_break_policy' not in e for e in rows))
        choices=[e['translation'] for e in rows if '<Styles:' in e['translation']]
        self.assertEqual(len(choices),2)
        for text in choices:
            self.assertIn('>X<Styles:/>',text)
            self.assertIn('>Y<Styles:/>',text)
            self.assertEqual(text.count('<Styles:MC2_StyleFont_0>'),2)
        desc=next(e['translation'] for e in rows if '<Styles:' not in e['translation'])
        self.assertIn('\\n\\n',desc)
        self.assertIn('3只',desc)

    def test_quest_progress_prefix_and_placeholders_remain_machine_readable(self):
        progress=[e['translation'] for e in self.plan['entries'] if e['translation'].startswith('QUEST%s:')]
        self.assertEqual(len(progress),1)
        self.assertEqual(progress[0].count('%s'),3)
        self.assertTrue(progress[0].endswith('(%s / %s)'))

    def test_hash_only_plan_and_explicit_dialogue_break_policies(self):
        for row in self.plan['entries']:
            self.assertNotIn('source',row)
            self.assertRegex(row['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertTrue(row['translation'].strip())
            self.assertFalse(any(c in row['translation'] for c in '\r\n\0'))
            if 'line_break_policy' in row:
                p=row['line_break_policy']
                self.assertGreater(p['source_count'],0)
                self.assertEqual(p['target_count'],0)
                self.assertNotIn('\\n',row['translation'])

    def test_linked_names_and_title_forms(self):
        terms=load('locales/zh-Hans/terms.json')['terms'];by_source={e['source']:e for e in terms}
        self.assertGreaterEqual(len(terms),102)
        edits={e['id']:e['translation'] for e in self.plan['entries']}
        for source in ('루','슈나이더','이엘','이엠','이엔','해독제'):
            t=by_source[source]
            self.assertEqual(t['review_status'],'candidate')
            self.assertEqual(edits[t['source_string_id']],t['target'])
        self.assertEqual(by_source['알렉스']['form'],'short-name')
        self.assertEqual(by_source['알렉스 백작']['form'],'title')
        self.assertNotEqual(by_source['알렉스']['id'],by_source['알렉스 백작']['id'])
        self.assertEqual(sum(e['translation']=='阿维斯族' for e in self.plan['entries']),2)

    def test_prior_batches_and_ids_are_preserved(self):
        names=('readability-fix','batch-002','batch-003','batch-004','batch-005')
        workflow=load('locales/zh-Hans/translation-workflow.json')
        self.assertEqual([b['plan']['path'] for b in workflow['batches'][:5]],
            ['locales/zh-Hans/'+name+'.json' for name in names])
        prior={e['id'] for name in names[:-1] for e in load('locales/zh-Hans/'+name+'.json')['entries']}
        current={e['id'] for e in self.plan['entries']}
        self.assertEqual(len(prior),841)
        self.assertFalse(prior & current)
        self.assertEqual(len(prior|current),1117)


if __name__=='__main__':unittest.main()
