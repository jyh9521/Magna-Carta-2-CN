"""Source-free contracts for Claire's dispute and the royal gate."""
from collections import Counter
import hashlib,json,re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_bytes())
class RoyalGateTests(unittest.TestCase):
 def setUp(self):self.p=load('locales/zh-Hans/batch-068.json');self.r=load('locales/zh-Hans/batch-068.review.json')
 def test_scope_and_status(self):
  self.assertEqual({e['section']:e['entries'] for e in self.r['coverage']},{'CSMB12_120':15,'CSMB12_130':32,'CSMB12_131':16,'CSMB12_132':6,'Chapter12':5});self.assertEqual(Counter(e['text_kind'] for e in self.r['entries']),{'dialogue':67,'narrative':2,'quest_status':4,'system_message':1});self.assertEqual(self.r['status'],'draft')
 def test_no_overlap_and_two_held_ids(self):
  old={e['id'] for b in load('locales/zh-Hans/translation-workflow.json')['batches'][:67] for e in load(b['plan']['path'])['entries']};ids={e['id'] for e in self.p['entries']};self.assertEqual((len(old),len(ids)),(7957,74));self.assertFalse(old&ids);self.assertEqual(ids,{e['id'] for e in self.r['entries']});held={e['id']:e for e in self.r['held_entries']};self.assertEqual(set(held),{'coalesced:0c288b44c8343b88a64c9b62493601cb058044da2bc0b97fa5cd9012250fb7e8','coalesced:a160f429712928d18b47c08c8f8290d97dcf87f61582afb923d1bd7cc3b65c5d'});self.assertFalse(ids&held.keys());self.assertEqual(held['coalesced:0c288b44c8343b88a64c9b62493601cb058044da2bc0b97fa5cd9012250fb7e8']['source_sha256'],hashlib.sha256(b'').hexdigest())
  for e in self.p['entries']:self.assertNotIn('source',e);self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$');self.assertTrue(e['translation']);self.assertFalse(any(c in e['translation'] for c in '\r\n\0'))
 def test_progress_labels_and_layout(self):
  fs=set(self.r['preserved_functional_break_ids']);rows=[e for e in self.p['entries'] if e['id'] in fs];self.assertEqual([e['translation'] for e in rows],[f'王之证明 ({n}/4)' for n in range(1,5)]+['已经通过试炼……']);self.assertTrue(all('line_break_policy' not in e and e['translation'].count('\\n')==0 for e in rows));self.assertEqual(sum('line_break_policy' in e for e in self.p['entries']),38)
 def test_narration_and_unresolved_positions(self):
  kinds={e['id']:e['text_kind'] for e in self.r['entries']};ns=[e['translation'] for e in self.p['entries'] if kinds[e['id']]=='narrative'];self.assertEqual(len(ns),2);self.assertIn('乐园便会消失',ns[0]);self.assertIn('艰辛的未来',ns[1]);ts=[e['translation'] for e in self.p['entries']];self.assertTrue(any('150年后' in t for t in ts));self.assertTrue(any('这也可能是真实的世界' in t for t in ts));self.assertTrue(any('我希望' in t and '平安回到地面' in t for t in ts));self.assertTrue(any('洁菲已经获得证明，应该能直接通过' in t for t in ts))
 def test_gate_candidate_distinct_from_proof_trial(self):
  terms=load('locales/zh-Hans/terms.json')['terms'];self.assertGreaterEqual(len(terms),364);e=terms[363];self.assertEqual((e['source'],e['target'],e['review_status'],e['relation']),('왕의 관문','王之关卡','candidate','unverified'));ts={e['source']:e['target'] for e in terms};self.assertEqual(ts['왕의 증명'],'王之证明');self.assertEqual(ts['왕의 시련'],'王之试炼');self.assertIn('Compose37未知名称',e['basis'])
 def test_previous_subtitle_prefix(self):
  p=load('locales/zh-Hans/subtitle-profile.json');self.assertGreaterEqual(len(p['plans']),38);self.assertEqual(sum(len(load(s['path'])['entries']) for s in p['plans'][:38]),271)
  for s in p['plans'][:38]:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
