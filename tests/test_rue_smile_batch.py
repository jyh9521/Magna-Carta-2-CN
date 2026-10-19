"""Source-free contracts for Rue's smile quest and Chapter10 travel news."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class RueSmileTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-083.json');self.r=L('locales/zh-Hans/batch-083.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'rue_cerestin':7,'10_dunanfield':7,'10_kotaneco':5,'Default':3,'Navigation':1,'E10_001':2,'E10_002':2});self.assertEqual(len(self.p['entries']),27);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),13);self.assertFalse(self.r['held_entries']);self.assertEqual(len(self.r['preserved_functional_break_ids']),10);self.assertEqual(self.r['status'],'draft');self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':17,'name':5,'quest_description':1,'mail_subject':2,'mail_body':2})
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:82] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8801);self.assertEqual(len(ids),27);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_smile_quest_and_concern(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertIn('试着让塞蕾丝汀逗露开心吧',ts);self.assertIn('石头的微笑',ts);self.assertIn('她是不是讨厌我啊？',ts);self.assertTrue(any('[露]' in t for t in ts));self.assertFalse(any('露确实讨厌你' in t or '魔法石奖励' in t for t in ts))
 def test_rumour_and_cat_voice(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('公主是恶魔的传闻' in t and '是真的吗喵' in t for t in ts));self.assertTrue(any('这件事，我还是很感激的' in t for t in ts));self.assertTrue(any('赶紧滚吧' in t for t in ts));self.assertEqual(sum('喵' in t for t in ts),5);self.assertTrue(any('听说' in t and '休战' in t for t in ts))
 def test_mail_layout_and_rest_house_labels(self):
  es={e['id']:e for e in self.p['entries']};protected=set(self.r['preserved_functional_break_ids']);self.assertTrue(all('line_break_policy' not in es[i] for i in protected));ts=[e['translation'] for e in es.values()]
  for t in ['休息站','休息站老板','休息站管理员','休息站客人','因故暂停前往的地点','新增目的地']:self.assertIn(t,ts)
  bodies=[es[e['id']]['translation'] for e in self.r['entries'] if e['text_kind']=='mail_body'];self.assertEqual(len(bodies),2);self.assertTrue(all('\\n\\n' in t for t in bodies));self.assertTrue(any('[鲁哈尔特盆地]' in t and '杜南平原' in t for t in bodies));self.assertTrue(any('[星光平原]' in t and '[贝尔福特]' in t for t in bodies))
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,83) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
if __name__=='__main__':unittest.main()
