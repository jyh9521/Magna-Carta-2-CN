"""Source-free contracts for the family legacy and chapter-seven mail."""
from collections import Counter
import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class FamilyLegacyTests(unittest.TestCase):
    def setUp(self):self.p=load('locales/zh-Hans/batch-045.json');self.r=load('locales/zh-Hans/batch-045.review.json')
    def test_scope(self):
        c=Counter()
        for e in self.r['coverage']:c[e['document']]+=e['entries']
        self.assertEqual(c,{'MC2Quest.int':33,'MC2QubeMail.int':16,'MC2CharacterName.int':1,'MC2FieldName.int':2,'MC2Item.int':16});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':24,'name':15,'mail_subject':8,'mail_body':8,'item_description':8,'quest_description':4,'system_message':1});self.assertEqual(self.r['status'],'draft')
    def test_disjoint_source_locks(self):
        b=load('locales/zh-Hans/translation-workflow.json')['batches'];old={e['id'] for spec in b[:44] for e in load(spec['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']}
        self.assertEqual((len(old),len(ids)),(6002,68));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(self.r['held_entries'])
        for e in self.p['entries']:
            self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
    def test_functional_mail_and_stats(self):
        rows=[e for e in self.p['entries'] if e['id'] in self.r['preserved_functional_break_ids']];self.assertEqual(len(rows),14);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum(e['translation'].count('\\n') for e in rows),67);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),17)
        kinds={e['id']:e['text_kind'] for e in self.r['entries']};mail=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='mail_body'];self.assertEqual([t.count('\\n') for t in mail],[5,9,12,5,9,10,4,8])
        values=[e['translation'] for e in self.p['entries']];self.assertIn('利登家主的信 ',values)
        self.assertIn('用于解除杜南平原封印石封印的钥匙',values);self.assertIn(' 用于解除杜南盗贼窝点封印石封印的钥匙',values);self.assertIn('克罗塞尔父亲留下的火球\\n精神+61',values);self.assertIn('利登家族世代相传的KAN充能器\\n防御+40 抗性+30',values);self.assertTrue(any('5块封印石' in t for t in values));self.assertTrue(any('5. 拉诺阿拉湖' in t for t in values))
    def test_candidates_not_final(self):
        ts={e['source']:e for e in load('locales/zh-Hans/terms.json')['terms']}
        for s,t in [('리든','利登'),('리든 가','利登家族'),('리든가','利登家族'),('케나로스','凯纳罗斯'),('은둔자의 동굴','隐者洞窟'),('봉인석','封印石'),('고대의 무덤','古代墓穴'),('늙은 여우 볼케이노','老狐沃尔凯诺'),('석회 언덕','石灰丘陵'),('파마의 열쇠','帕玛之钥'),('계마의 열쇠','凯玛之钥'),('율마의 열쇠','尤尔玛之钥'),('윤마의 열쇠','尹玛之钥'),('박마의 열쇠','帕克玛之钥'),('리든 가의 화염구','利登家族火球'),('에메랄드','祖母绿'),('칸 차져','KAN充能器')]:
            self.assertEqual(ts[s]['target'],t);self.assertEqual(ts[s]['review_status'],'candidate');self.assertEqual(ts[s]['relation'],'unverified')
    def test_subtitle_frozen_prefix(self):
        p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),28);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:28]),194)
        for s in p['plans'][:28]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
