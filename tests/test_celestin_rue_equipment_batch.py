"""Source-free contracts for Celestin and Rue equipment and preserved source shapes."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class CelestinRueEquipmentTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-109.json');self.r=load('locales/zh-Hans/batch-109.review.json');self.by={e['id']:e['translation'] for e in self.p['entries']};self.ts=list(self.by.values())
 def test_scope_and_classification(self):
  self.assertEqual(len(self.ts),155);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['coverage'],[{'document': 'MC2Item.int', 'section': 'Weapon_bow_celestin', 'entries': 30}, {'document': 'MC2Item.int', 'section': 'Weapon_aroma_celestin', 'entries': 30}, {'document': 'MC2Item.int', 'section': 'Weapon_shuriken_rue', 'entries': 27}, {'document': 'MC2Item.int', 'section': 'Weapon_katana_rue', 'entries': 23}, {'document': 'MC2Item.int', 'section': 'armor_backpack_rue', 'entries': 20}, {'document': 'MC2Item.int', 'section': 'armor_brooch_celestin', 'entries': 25}])
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':54,'equipment_description':101});self.assertEqual(set(self.by),{e['id'] for e in self.r['entries']})
 def test_missing_values_and_unchanged_source_held(self):
  self.assertEqual({e['id']:e['source_sha256'] for e in self.r['held_entries']},{'coalesced:a55d2259338fbaba37a91ffc8b765dde90c7f262689c21fd346b84cf2c3b1486': '8dc9ea4cffe1d8d9b00b1a0ec6e5c00f0e042f8eb1cb52aa1edbdb44c38049bc', 'coalesced:eeed08543c5b7642ded59a82485dc108ca7095d74c46fc12f5237c418f339268': 'ce958b4c2bf72c9562bc1f98f60312f6ca6afe1199e981d20de890478a6127dd', 'coalesced:4a4ce071324eec9f82afaa47fbae51b81eb65bec77151e86dd5eb3aa6a452236': '831794cac54ff48dd282b7926492b8525baca398182903e59f61be9c2dd6bd7b', 'coalesced:2fefb5c30e8d06cd343458de739b96ed072a71a2d9648dc2ce321537acdfbb8f': '674934f23fd7b714c191a1565a6ad2ae7e30e946090b283b7706478038674007', 'coalesced:2e170407cef919c03cdd1c952f047de9d1941c037e7bd794c4360c10109fb7e9': '831794cac54ff48dd282b7926492b8525baca398182903e59f61be9c2dd6bd7b', 'coalesced:a3f573d75cf287324dbf6f59f3bb7ffd8d92b1e06603bf95419c9ff87c19b275': '5fcf449e1af011701c1868d303970bec2e75fbc8859922587b65a0041990e73a', 'coalesced:d42679fc3a33ee59a9300dead30ec2f2a2439aade30199b63059cf1b8bf51eb0': '8663907c67747e41bcc690c2e45ac226a59e8753427af5a346812cd3531a703e'})
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:108] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),12459);self.assertFalse(old&self.by.keys())
  held={e['id'] for n in range(1,110) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&self.by.keys())
 def test_math_and_functional_layout(self):
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']));self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('+', 138), ('\\n', 101)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_source_categories_stat_differences_and_whitespace(self):
  for i,t in {'coalesced:48bc2dda2eb6126a931754bb1b3b04ad15267c68b2d1426a639cfaa33e4065e4': ' 弓\\n精神+260', 'coalesced:ead2b6bc891d57861f81ec798a6d16542fa81c52fc1e66fa7b9a879c112f20ca': '传说中的神射手曾使用过的弓\\n', 'coalesced:4faa14400df2dfae30f7bc6eb15d9143290a98dceab3e9b7316f1b5fdc19b092': '弓\\n', 'coalesced:a246fa80b6086ed6dc4b39e4e63d0fe68db4d5d7764f602ac689ebc43f83c210': '被誉为花中之花的依兰依兰香器\\n', 'coalesced:7f9386d90737b0a675e111a6c919710c41894079747cd9e670e0fc61d6f2b330': '香器\\n ', 'coalesced:ecde12e7d5059b97f56b9a85ca2c31eda06991ec53f3c0a802502a153309397d': '手里剑\\n', 'coalesced:930ba59879213600a46cb0a42aa18a8caace851b615f1be9d07244b56aee83c8': '据说能以准确瞄准要害的攻击掀起血之风的手里剑\\n', 'coalesced:c2478e66e963f0b9be9a6201e2bc5737f617190957d74626c4c5e52b0f692b8c': '能贯穿一切的最强手里剑\\n精神+210 ', 'coalesced:dfb1a77a9df2d974fcdfcde4aa6d3304cb43da64ddc02c912b68c2a01e14ff35': '短刀\\n攻击+60', 'coalesced:5ec758535d467c5ab3052230ccb81f6b61062ca5731bd13eab58aa33286a12b9': '刀\\n攻击+130', 'coalesced:ace562bc53733bcc6437f9ee883deb1c33590aa715cd5d697f452b3732a13b61': '能施展如风般迅速锐利攻击的短刀\\n攻击+180', 'coalesced:79dbda3cb84726ca9bfea71de58377d86e1c912ee9252db1f93ea5a36be64415': '蕴含地狱罗刹气息的短刀\\n攻击+140', 'coalesced:f1a53e8ed60e071beab1b2b32ed4874d5271c9a50b85cafb72f8a78fd8460735': '据说飞溅的鲜血会绘成红莲的刀\\n', 'coalesced:6f3410957ce316540cf2a5eb1db59bda372d51dc8160c7b1ed38d09172863118': '电击背包', 'coalesced:193673ac5a7db8ff83e7657f17d18f70134834f736d343a0359c874ea4b3e3b3': '电击背包', 'coalesced:b1c0df65022fb2f56631dfabe4b45cce1a19578c5155c1992754c69afb5938cc': '锁扣背包', 'coalesced:62c9855924b5d8622f3bcbb2376ac69bd2c752e0cace3ba1156c625fb59f86a5': '希望胸针'}.items():self.assertEqual(self.by[i],t)
  self.assertEqual(sum(t.strip()=='电击背包' for t in self.ts),2);self.assertNotIn('太刀',''.join(self.ts));self.assertIn('香器'+chr(92)+'n精神+18 耐力恢复+3',self.ts)
 def test_candidate_append_and_reuse(self):
  new=load('locales/zh-Hans/terms.json')['terms'][1018:1071];self.assertEqual(len(new),53);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new));self.assertNotIn('수리검',{e['source'] for e in new})
  self.assertEqual({e['source']:e['target'] for e in new}['우사'],'雨师')
 def test_workflow_and_subtitles(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][108].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
