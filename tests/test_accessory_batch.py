"""Source-free contracts for independent accessory display families."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class AccessoryTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-105.json');self.r=load('locales/zh-Hans/batch-105.review.json');self.by={e['id']:e['translation'] for e in self.p['entries']};self.ts=list(self.by.values())
 def test_scope_and_kinds(self):
  self.assertEqual(len(self.ts),212);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['held_entries'],[])
  self.assertEqual(self.r['coverage'],[dict(document='MC2Item.int',section='Accessory',entries=212)])
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':70,'item_description':142});self.assertEqual(set(self.by),{e['id'] for e in self.r['entries']})
 def test_old_ids_and_held_not_overwritten(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:104] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),11636);self.assertFalse(old&self.by.keys())
  held={e['id'] for n in range(1,106) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&self.by.keys())
 def test_functional_layout_and_math(self):
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']));self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('+',76),('%',62),('「',28),('」',28),(chr(92)+'n',146)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_distinct_legacy_values_and_status_names(self):
  expected={'coalesced:bd163ea5450bfadb4723b8519ad6eeacf0d657960ed67dc6ab8fb1ad383da89d': '饰品\\n防御+30%', 'coalesced:3541cd391cf07c1d27b39e300bb98d50114d9fa4de04a71f8dd1662147c09b8b': '饰品\\n防御+10%', 'coalesced:ea841ece1347bf33853059d346c1604e94772a683368560060c8fa9dfc7ed9ec': '饰品\\n攻击+30 速度+10', 'coalesced:b4ddd988f1cb2b055aaf5a4f8ac979af9cc00552062f0d0803a9eb30925218f0': '饰品\\n免疫睡眠异常状态', 'coalesced:459e4e84724a7226bcbdd7327770bdbe1a1bfc878506a556aff74e4133500f45': '饰品\\n攻击+30 速度+10', 'coalesced:7c0fdeefd62377108f7536efb221136826a01a2ef638ca31808005de8c226e89': '饰品\\n对「冻疮」异常状态\\n50%免疫', 'coalesced:ca693c809082fb68b2cece8e2e5631a2713507278aeed44960fcc6ca9d3fc67a': '饰品\\n免疫寒冷异常状态 ', 'coalesced:56aaac44f453738656c97009ba5302e3809a6c91704aa06fb26a275ef43d43d7': '饰品\\n对「冻伤」异常状态50%免疫', 'coalesced:98f4a974857afba25b9375947321629f598142cc2abfcbd5be779d6b2f494c94': '饰品\\n对「眩晕」异常状态50%免疫', 'coalesced:dd4367f5e5271f84a0d003d3695e04d7c21d3c24f2998af60ac0f51761af5f69': '饰品\\n免疫力竭异常状态 ', 'coalesced:8fbb5671c48959cf11465e0745ad09462797e09cbf87499b6a0bf958269f087a': '饰品\\n对「眩晕」异常状态\\n免疫 ', 'coalesced:54d4053e9c6db6e67be256a742a56d71a0fc05fe0da292d40ea5feb139c4c71a': '饰品\\n对「腹痛」异常状态\\n免疫 ', 'coalesced:9f2258777c6807e786dce92a89568e1d3a0b6f8ec245d7c6e8c2b8478c0639ef': '饰品\\n对4大属性以外的属性异常状态50%免疫', 'coalesced:9c0682b1f2180448ecd7ee1def5234afe58a6f2c1c839656398db4f4ca3bbda0': '饰品\\n对其他异常状态50%免疫', 'coalesced:4a27017631fda8678566821cf79638170fd76ef7277c806a05bf84b2a40b112a': '饰品\\n升级时获得的技能点数+50%', 'coalesced:d4e81bf28a718cc591d30e95211ace1e931868bba20bfa48b77fc7e15728fcdc': '饰品\\n技能点数+50%'}
  for i,t in expected.items():self.assertEqual(self.by[i],t)
  self.assertEqual(sum(t.strip()=='救援腰带' for t in self.ts),2);self.assertEqual(sum(t.strip()=='元气戒指' for t in self.ts),2)
 def test_candidate_append_and_reuse(self):
  terms=load('locales/zh-Hans/terms.json')['terms'][787:852];self.assertEqual(len(terms),65);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in terms));self.assertEqual(len({e['source'] for e in terms}),65)
  self.assertNotIn('救援の벨트',{e['source'] for e in terms});self.assertIn('黎明戒指',{e['target'] for e in terms})
 def test_workflow_locks_and_subtitles(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][104].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
