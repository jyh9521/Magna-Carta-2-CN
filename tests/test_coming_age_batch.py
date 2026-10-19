"""Source-free contracts for chapter-six quests excluding two held formats."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class ComingAgeTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-039.json');self.r=load('locales/zh-Hans/batch-039.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Quest.int':89,'MC2CharacterName.int':3,'MC2Item.int':4,'MC2UI.int':1})
        self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':70,'name':11,'quest_objective':6,'quest_description':5,'quest_progress':3,'item_description':2})
        self.assertEqual(self.r['status'],'draft');self.assertFalse(self.r['held_entries'])
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:38] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(5400,97));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
        held=[e for n in (36,38) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json')['held_entries']];self.assertEqual(len(held),2);self.assertFalse({e['id'] for e in held}&(old|ids))
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_layout_and_placeholders(self):
        functional=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in functional]
        self.assertEqual(len(rows),5);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual([e['translation'].count('\\n') for e in rows],[4,1,1,1,2])
        self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),58)
        self.assertEqual([i for i,t in enumerate(rows[0]['translation'].split('\\n')) if not t],[1])
        values=[e['translation'] for e in self.p['entries']];self.assertIn('QUEST%s: 获得香气之源 (%s / %s)',values);self.assertIn('尤尼昂之角 ',values);self.assertTrue(any('一共有4处' in t for t in values));self.assertTrue(any('共3项仪式' in t for t in values));self.assertTrue(any('明天定为庆典之日' in t for t in values))
    def test_candidates_and_legacy_flower(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('네스틴','内斯汀'),('스위틴','斯维汀'),('그라미','格拉米'),('유니온','尤尼昂'),('유니온의 뿔','尤尼昂之角'),('향의 원천','香气之源'),('자연의 의식','自然仪式'),('힘의 의식','力量仪式'),('향의 의식','香气仪式'),('아셀리나의 눈물','阿塞莉娜之泪')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
        values=[e['translation'] for e in self.p['entries']];self.assertEqual(values.count('香气之源'),2)
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),27);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:27]),187)
        for s in p['plans'][:27]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
