"""Source-free contracts for Juto and Zephie equipment and incomplete source stats."""
from pathlib import Path
import unittest,json,hashlib,collections
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_bytes())
class JutoZephieEquipmentTests(unittest.TestCase):
 def setUp(self):
  self.p=load('locales/zh-Hans/batch-107.json');self.r=load('locales/zh-Hans/batch-107.review.json');self.by={e['id']:e['translation'] for e in self.p['entries']};self.ts=list(self.by.values())
 def test_scope_and_classification(self):
  self.assertEqual(len(self.ts),202);self.assertEqual(self.r['status'],'draft');self.assertEqual(self.r['coverage'],[{'document': 'MC2Item.int', 'section': 'Weapon_onehanded sword_juto', 'entries': 42}, {'document': 'MC2Item.int', 'section': 'Weapon_twohanded sword_juto', 'entries': 32}, {'document': 'MC2Item.int', 'section': 'Weapon_fan_zephie', 'entries': 33}, {'document': 'MC2Item.int', 'section': 'Weapon_rod_zephie', 'entries': 33}, {'document': 'MC2Item.int', 'section': 'armor_bracelet_zephie', 'entries': 30}, {'document': 'MC2Item.int', 'section': 'armor_pauldron_juto', 'entries': 32}])
  self.assertEqual(collections.Counter(e['text_kind'] for e in self.r['entries']),{'item_name':69,'equipment_description':133});self.assertEqual(set(self.by),{e['id'] for e in self.r['entries']})
 def test_incomplete_stats_held_and_old_ids_preserved(self):
  self.assertEqual({e['id']:e['source_sha256'] for e in self.r['held_entries']},{'coalesced:0b2fed137ee42a23db64a2b1436bc55f5954941d3f24b2144611bfcade44ead0': 'f94b92002325ce2bb3728ecefac58e53e0ed2c45f20dc63955b5bd55289b4565', 'coalesced:c3e87c38d0e08b359639f6eb3c3dc3231d04aba62d3d7f1d2b5e404eb95cf19e': 'f231f0e77789c6c7d80934b9d1d39b976637a865d7738a7716239edc5985a648', 'coalesced:1a27de65f91a9ba1858c84a4122639c508bdbb0f42fcb92d4567bac01fb688a7': 'f7421b52a340fd2375fcfa5ca0ca4fd58737cad5306b8553ac9aacc331c87287', 'coalesced:5fed2bcefe11b408d60af066be447e6158f9554c0feb4dbc89f9471957b849cc': 'f231f0e77789c6c7d80934b9d1d39b976637a865d7738a7716239edc5985a648'})
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:106] for e in load(b['plan']['path'])['entries']};self.assertEqual(len(old),12073);self.assertFalse(old&self.by.keys())
  held={e['id'] for n in range(1,108) for e in load(f'locales/zh-Hans/batch-{n:03d}.review.json').get('held_entries',[])};self.assertFalse(held&self.by.keys())
 def test_math_and_functional_empty_lines(self):
  self.assertEqual(set(self.by),set(self.r['preserved_functional_break_ids']));self.assertFalse(any('line_break_policy' in e for e in self.p['entries']))
  for symbol,count in [('+', 195), ('\\n', 137), ('\t', 1)]:self.assertEqual(sum(t.count(symbol) for t in self.ts),count)
  for e in self.p['entries']:
   self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertNotIn('source',e);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_actual_source_names_conditions_and_whitespace(self):
  for i,t in {'coalesced:54a276342eb6df7079be5989bcdcb2dfceeb205e6faf574b8f5458b45ab9158a': "原名为'曙光'，蕴含着初升太阳热量的单手剑。\\n攻击+24 防御+5", 'coalesced:9dda2da691b4ec14c4a84fb0e6e81e24f36a2db070a74c1d8628b26774631eec': "传说中的剑士'卡林兹'曾使用过的究极单手剑。\\n完成南部军首个任务后可装备\\n攻击+250 防御+55", 'coalesced:cbbb3e9e10a594ac732577dd2812bb2fa52841f33788fdbb9ea731f22d76be6f': '单手剑\\n完成南部军首个任务后，可装备\\n攻击+250 防御+55', 'coalesced:9e8d44ac266c02a0ff58fae610b05ab0729f55a49b5e97d24d861bb3afc03d45': '能将对手确实置于死地的恶魔单手剑\\n', 'coalesced:2c78b2993c7a6f620beaf6546966df8e6b661b1a79c803146f7f2f9d4a8ad1c9': '单手剑\\n ', 'coalesced:fafbeb924720ac2f7ec8010a36656c960bcb76ae14b99108184c17b40e9cbc41': '单手剑\\n', 'coalesced:4d1373d455b6c07c683a50c3d0ed0c952e67ec41176422d89af9584b4df63b2c': '单手剑\\n ', 'coalesced:0015d54659288a1cb5daad87ec77e6251c11c6de68f3fc0ad8db958d7ef17efc': '暂魂剑 ', 'coalesced:6d9797019a15adb3e6488148e67a5d6458e1273fbcf2e1ae834fa348f2630430': '据说连灵魂也能斩裂的双手剑\\n', 'coalesced:214f1170b1cf4758482ef6aaaa1e48be3e3be4b9972388493f87bf279a8833f0': '如其名般闪耀洁白光芒的究极双手剑\\n完成南部军首个任务后可装备\\n攻击+270', 'coalesced:22541ae16dc1f4e6e7f440f38827a57b2cb226c8ee6a239280e337a9e5bdd300': '双手剑\\n完成南部军首个任务后，可装备\\n攻击+270', 'coalesced:6a653e4549a25801ad202a63b1a3bdf3d8b77c66013ea23f385cb89dfef26b68': '能呼应战意而发挥守护之力的扇\\n', 'coalesced:0ac6ee31632bf71988f302a7fc15396e57943d6ff615bb12d1c9a84f47e57dce': '扇\\n', 'coalesced:02d43811f6402fa1464e19e06423310ea8a7883095d35c667f54b428d7aadb24': '法杖\\n ', 'coalesced:12c94e60d509886a88506869a215154f53ee99cfe270c5fbebdce7802f5ea67c': '深渊肩甲', 'coalesced:7f648d3bd277ef37112f1cd02cc58ce4341cf05feee41019158da77acffc95e5': '钻石肩甲', 'coalesced:af54d3a958ff2556a4ac7415c7066dcbf958b59e367c6257518c9c8b819d6a0a': '青铜护手', 'coalesced:a4789166a94d96221cb0b318d2fde1fad306da702f63484c24b0cc4ed071dde4': '副装备\\n防御+1\t'}.items():self.assertEqual(self.by[i],t)
  self.assertEqual(sum('完成南部军首个任务后' in t for t in self.ts),4);self.assertNotIn('斩魂剑',self.ts)
 def test_candidates_and_pinned_series_reference(self):
  ts=load('locales/zh-Hans/terms.json')['terms'];new=ts[885:955];self.assertEqual(len(new),70);self.assertTrue(all(e['review_status']=='candidate' and e['relation']=='unverified' for e in new))
  person=next(e for e in new if e['source']=='칼린츠');self.assertEqual(person['target'],'卡林兹');self.assertEqual(len(person['series_references']),2);self.assertTrue(all(e['target']=='卡林兹' for e in person['series_references']))
 def test_workflow_and_subtitles_unchanged(self):
  for e in load('locales/zh-Hans/translation-workflow.json')['batches'][106].values():self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
  plans=load('locales/zh-Hans/subtitle-profile.json')['plans'];self.assertEqual(len(plans),44);self.assertEqual(sum(len(load(e['path'])['entries']) for e in plans),315)
  for e in plans:self.assertEqual(hashlib.sha256((R/e['path']).read_bytes()).hexdigest(),e['sha256'])
if __name__=='__main__':unittest.main()
