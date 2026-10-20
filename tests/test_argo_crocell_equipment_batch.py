"""Source-free contracts for Argo and Crocell equipment and held source values."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class ArgoCrocellEquipmentTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-108.json');self.r=load('locales/zh-Hans/batch-108.review.json');self.by={e['id']:e['translation'] for e in self.p['entries']};self.ts=list(self.by.values())
 def test_scope_and_classification(self):
  self.assertEqual(len(self.ts),184);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['coverage'],[{'document': 'MC2Item.int', 'section': 'Weapon_Ax_argo', 'entries': 31}, {'document': 'MC2Item.int', 'section': 'Weapon_hammer_argo', 'entries': 33}, {'document': 'MC2Item.int', 'section': 'Weapon_fireball_crocell', 'entries': 27}, {'document': 'MC2Item.int', 'section': 'Weapon_knuckle_crocell', 'entries': 31}, {'document': 'MC2Item.int', 'section': 'armor_kan_charger_crocell', 'entries': 31}, {'document': 'MC2Item.int', 'section': 'armor_guantlet_argo', 'entries': 31}])
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':63,'equipment_description':121});self.assertEqual(set(self.by),{e['id'] for e in self.r['entries']})
 def test_missing_stats_empty_and_unchanged_source_held(self):
  self.assertEqual({e['id']:e['source_sha256'] for e in self.r['held_entries']},{'coalesced:6bc43ca87553cea6cadd3f21584a89f5de7e68a15ddda0fc92aafeeb276e16b8': '42a4fb6815387b97679dd53796348da8260346675fe915f37e6d8cb0b3c73065', 'coalesced:50be14d45b57f11e72df4e309976908c4e5b0c02c259678ed397b9eed03782e7': '1541cb095ca6664e84762f6adc7755a58ac98767043024b3a07c8d5209af7f60', 'coalesced:2eecde698409517c348d06a6c18e6035a1243f3a6a40fa9ea77454722411c4c6': 'c189e33b8b32c7533dc4f653dcf66fd8d4542d978b95f367462c2e97aa130b41', 'coalesced:8973c66e337b849c3b31d390d5852f786e5df3b38bf94b6f0b4102c3b33a4a55': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'coalesced:3fa3c42dd25dc248a5c296348b89d2e980580e5b88d6d89f6de182c63fc80121': '4edfe627e7996e48967a80e8e0445164f9a4823a17daff4a8e1c204c0a2ef3cf', 'coalesced:45b6832869646ba35fe07b2ddf9b881577fb74800031bd8ba0956a64850a10d0': '43848c65d4377e6d2dec7c90f17bfd316f381a332ca94e976ca89c86c6fbd4ce', 'coalesced:353750a6cd4fd2b8e2798a7e2becaa2f6b19b19a3411a8c52dd3acd9edc37533': '3c09ca0b83c60fae00de71120e13a5d3e424ef1ee6dfbd472a279d34696e08aa', 'coalesced:a9c6a80fff879613ea3fea1785ccbb6e16fd1fc45275baac3f53fb45b85c58fc': '80dd0b7c0b2e8797bb3ea559898381f9b5cbd3315778d7e92758309e58b08f7c', 'coalesced:33628fb00022f73f22eefba60fd10022df94f42ca553e5d3b4b8f7fd7322656f': '5c5b697d4757277281a8d8ab9e3ee818a253d5f660bb372ef2c9e302bb00055a', 'coalesced:fb92f81f0fca945f69dbf8031f641862dd8847cc19328d464888af2aab889711': '00267a072af9152824b5db23a29b3008900a3a97fc29f55e06927c914db7ffe8'})
  self.assertEqual(sum(e['source_sha256']==hashlib.sha256(b'').hexdigest() for e in self.r['held_entries']),1)
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:107] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),12275);self.assertFalse(old&self.by.keys())
  held={e['id'] for n in range(1,109) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&self.by.keys())
 def test_math_and_functional_layout(self):
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']));self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('+', 181), ('\\n', 120)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_actual_source_names_and_stat_whitespace(self):
  for i,t in {'coalesced:1f69b3acc95319c7b300af8c0f95c68de79f1b578aad5921e8a06c85a0e424ea': '以仿佛连天空也能劈开的气势斩杀敌人的最强斧\\n攻击+ 240', 'coalesced:157ba1f25e94b99fe8757ba76658253ab5aef436d5e0397f086504870a23e9b9': '斧\\n攻击+240', 'coalesced:22b41d3217f387a318e10a94d57ea70dcc221063969cc7aec0dc44fb5b384aec': '1000吨锤', 'coalesced:ab5d6b29ab5115f27a91f7d0af8a939c9cbd657f2ea27a120f274ce8e765c3be': '幻象', 'coalesced:61d58360e499287590648453470c938546027a3e9047a745fb26df8fb7251bc6': '赤炎球', 'coalesced:1297a95c542398791b88afdc521ae40a74fe006a6bbaeb40d915efc8db59c521': '火舞', 'coalesced:b7525732e4363ed8ba352f771c6f54b9b551698aca2d628f5f431010b12c28aa': '能使敌人陷入致命中毒状态的火球', 'coalesced:9398a2314353a1b5772f0cd1a3b40d9e7da1f061635b788993c577654055659c': '火球\\n精神+61', 'coalesced:122ed580644bce873e2f32c460b142557d4181058c306d7bca71a23cf1d31d4f': 'KAN充能器\\n防御+40 抗性+30', 'coalesced:7bb91da6ee08544a271ab007145f1b66617b3c2bcfcd56dc2b37de35202c1f4b': '龙人护手', 'coalesced:235f2736a13a00cf9b821dc4c11101555ce976a1a0c8b7de73d0ce39be515b45': '致命击 ', 'coalesced:43afd34925a960810fa43ec0b43fe8fd9da93efc02fac8985a1e242ecd7dd152': '赤红鬼才 ', 'coalesced:374f0e69db8f1e39ce1dfad6d50acdf10c0d18d0541c4e62d3e53fcc4f459107': '阿维斯拳套'}.items():self.assertEqual(self.by[i],t)
  self.assertNotIn('毒炎球',self.ts);self.assertIn('1000吨锤',self.ts)
 def test_candidate_append(self):
  new=load('locales/zh-Hans/terms.json')['terms'][955:1018];self.assertEqual(len(new),63);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));self.assertEqual(len({e['source'] for e in new}),63)
  by={e['source']:e['target'] for e in new};self.assertEqual(by['일류전'],'幻象');self.assertEqual(by['竜人の건틀렛'],'龙人护手')
 def test_workflow_and_subtitles(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][107].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
