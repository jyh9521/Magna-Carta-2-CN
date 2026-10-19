"""Source-free contracts for departure, escort objectives and styled choices."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class DepartureTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-064.json');self.r=load('locales/zh-Hans/batch-064.review.json')
 def test_scope_and_voice(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB12_005':14,'CSMB12_007':30,'CSMB12_008':12,'CSMB12_009':2,'CSMB12_010':5,'CSMB12_020':3,'Chapter12':10});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':63,'narrative':12,'menu_option':1});self.assertEqual(self.r['status'],'draft');ids={e['id'] for e in self.r['entries'] if e['text_kind']=='narrative'};self.assertEqual(sum(e['id'] in ids for e in self.p['entries'][14:44]),6)
 def test_unique_source_locks_and_old_held(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:63] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7696,76));self.assertFalse(old&ids);self.assertFalse(self.r['held_entries']);self.assertEqual(ids,{e['id'] for e in self.r['entries']});self.assertFalse(ids&{e['id'] for e in load('locales/zh-Hans/batch-063.review.json')['held_entries']})
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_functional_layout(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual([e['translation'].count('\\n') for e in rows],[1,1,1,0,0,1,1]);self.assertTrue(all('line_break_policy' not in e for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),38);self.assertTrue(rows[0]['translation'].endswith(' '))
 def test_styled_menu_and_buttons(self):
  ids={e['id'] for e in self.r['entries'] if e['text_kind']=='menu_option'};rows=[e for e in self.p['entries'] if e['id'] in ids];self.assertEqual(len(rows),1);t=rows[0]['translation'];self.assertEqual(t,r'<Styles:MC2_StyleFont_0>X<Styles:/> 出发\n<Styles:MC2_StyleFont_0>Y<Styles:/> 还需要准备');self.assertEqual(re.findall(r'<[^>]*>',t),['<Styles:MC2_StyleFont_0>','<Styles:/>']*2)
 def test_candidate_and_relationship_not_invented(self):
  t=next(t for t in load('locales/zh-Hans/terms.json')['terms'] if t['source']=='쾌속이동장치');self.assertEqual(t['target'],'高速移动装置');self.assertEqual((t['review_status'],t['relation']),('candidate','unverified'));self.assertIn(t['source_string_id'],{e['id'] for e in self.p['entries']});ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('像父亲一样' in t for t in ts));self.assertFalse(any('生父' in t for t in ts));self.assertTrue(any('究竟是谁' in t for t in ts))
 def test_subtitle_frozen_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),37);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:37]),270)
  for s in p['plans'][:37]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
