"""Source-free contracts for Abazet aftermath and oldfox resistance NPCs."""
from pathlib import Path
import unittest,json,hashlib
R=Path(__file__).resolve().parents[1]
def L(p):return json.loads((R/p).read_bytes())
class AbazetAftermathTests(unittest.TestCase):
 def setUp(self):self.p=L('locales/zh-Hans/batch-085.json');self.r=L('locales/zh-Hans/batch-085.review.json')
 def test_scope_and_layout(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'Ch04_Abazet_2':52,'04_oldfox':15});self.assertEqual(len(self.p['entries']),67);self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),45);self.assertFalse(self.r['held_entries']);self.assertFalse(self.r['preserved_functional_break_ids']);self.assertEqual(self.r['status'],'draft');self.assertTrue(all(e['text_kind']=='dialogue' for e in self.r['entries']))
 def test_ids_and_hashes(self):
  old={e['id'] for b in L('locales/zh-Hans/translation-workflow.json')['batches'][:84] for e in L(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual(len(old),8866);self.assertEqual(len(ids),67);self.assertFalse(ids&old);self.assertEqual(ids,{e['id'] for e in self.r['entries']})
  for e in self.p['entries']:self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_shared_names_and_lake_brackets(self):
  ts=''.join(e['translation'] for e in self.p['entries'])
  for t in ['反哨兵部队','希昂·雷格拉尔','泽格隆','杜南丘陵','鲁哈尔特盆地','王城贝尔福特','[雷恩波尔特]','[拉诺阿拉]湖','斯特拉斯','阿塞莉娜','风息岛']:self.assertIn(t,ts)
  self.assertIn('1000年',ts);self.assertNotIn('1000年前的绝对年份',ts)
 def test_rumours_and_simile_not_revival(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('修恩扎伊特出现在杜南丘陵，是真的吗' in t for t in ts));self.assertTrue(any('要是真的' in t for t in ts));self.assertIn('甚至让人觉得，仿佛希昂·雷格拉尔，活着回来了。',ts);self.assertFalse(any('希昂已经复活' in t or '泽格隆就是希昂' in t for t in ts));self.assertTrue(any('似乎，正在从风息岛撤退' in t for t in ts))
 def test_resistance_and_civilian_states(self):
  ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('援军，就会从杜南丘陵赶来' in t for t in ts));self.assertTrue(any('这里以东' in t for t in ts));self.assertTrue(any('明天吃的面包' in t for t in ts));self.assertIn('伤口一直都好不了。',ts);self.assertIn('呜呜……求你一定要平安回来……',ts);self.assertIn('一切为了兰兹海姆！',ts)
 def test_subtitles_and_held_preserved(self):
  held={e['id'] for n in range(1,85) for e in L(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&{e['id'] for e in self.p['entries']});plans=L('locales/zh-Hans/subtitle-profile.json')['plans'][:44];self.assertEqual(sum(len(L(p['path'])['entries']) for p in plans),315)
  for p in plans:self.assertEqual(hashlib.sha256((R/p['path']).read_bytes()).hexdigest(),p['sha256'])
 def test_missed_capture_is_past_counterfactual_not_future_or_accomplished(self):
  entry=next(e for e in self.p['entries'] if e['id']=='coalesced:8103e09ed5a8cfa98593d018eb94bf5edc3f3494ba681d991d576d5853aa615b')
  self.assertEqual(entry,{'id': 'coalesced:8103e09ed5a8cfa98593d018eb94bf5edc3f3494ba681d991d576d5853aa615b', 'source_sha256': 'ae4fbae87f48ab8cee6a4352771f1b184e2032b5436ced30206c27bc94cff044', 'translation': '要是真的，那可太可惜了。要是当时抓住了那家伙，战争就已经结束了。', 'line_break_policy': {'source_count': 2, 'target_count': 0}})
  self.assertEqual(self.r['status'],'draft')
  self.assertIn('要是真的',entry['translation']);self.assertIn('要是当时抓住了',entry['translation'])
  self.assertIn('战争就已经结束了',entry['translation'])
if __name__=='__main__':unittest.main()
