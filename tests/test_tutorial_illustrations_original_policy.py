import json,hashlib,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class OriginalTutorialIllustrationTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((R/'locales/zh-Hans/candidate-decisions/tutorial-illustrations-original-policy.json').read_bytes());self.p=json.loads((R/self.d['active_plan']['path']).read_bytes())
 def test_user_original_only_policy(self):self.assertTrue(self.d['user_required']);self.assertFalse(self.d['apply_illustration_localization']);self.assertEqual((len(self.d['scope']),self.d['withdrawn_groups'],self.d['withdrawn_layers'],self.d['withdrawn_aliases']),(108,36,127,72))
 def test_no_illustration_edit_under_any_identifier(self):
  forbidden={(r['resource'].lower(),r['object'].lower())for r in self.d['scope']}
  for s in self.p['sources']:
   for e in s['textures']:self.assertNotIn((s['path'].lower(),e['object'].lower()),forbidden)
  self.assertFalse(any(l['id'].startswith('tutorial_ui_')for l in self.p['labels']))
 def test_other1212_layers_and654_groups_unchanged(self):
  from tools.texture_overlay import image_id
  self.assertGreaterEqual(len(self.p['labels']),1212);self.assertGreaterEqual(len({image_id(e)for s in self.p['sources']for e in s['textures']}),654);old=json.loads((R/self.d['historical_plan']['path']).read_bytes());self.assertEqual(self.p['labels'][:1212],old['labels'][:1212]);self.assertEqual(hashlib.sha256((R/self.d['active_plan']['path']).read_bytes()).hexdigest(),self.d['active_plan']['sha256'])
 def test_archived_plans_never_feed_active_compositions(self):
  for name in ['tutorial-native-captions','tutorial-menu-native-captions','tutorial-hud-chain-kamond-captions']:
   d=json.loads((R/f'locales/zh-Hans/candidate-decisions/{name}.json').read_bytes());self.assertFalse(d['applied']);self.assertEqual(d['plan'],self.d['historical_plan'])
  for n in [1,2]:
   c=json.loads((R/f'locales/zh-Hans/locale-compositions/disc{n}.json').read_bytes());self.assertEqual(c['texture_plan'],self.d['active_plan'])
 def test_tutorial_titles_and_text_preserved(self):
  titles=[e for s in self.p['sources']if s['path'].split('/')[-1].startswith('Tutorial_')for e in s['textures']];self.assertTrue(titles);self.assertTrue(all('Title' in e['object']for e in titles));self.assertTrue(self.d['preserved_text_and_titles']);self.assertFalse(self.d['game_started'])
 def test_cancelled43_queue_cannot_resume_small_image_work(self):
  a=json.loads((R/'locales/zh-Hans/asset-backlog/ui-tutorial-audit.json').read_bytes());rows={r['id']:r for r in a['rows']}
  for r in self.d['scope']:self.assertFalse(rows[r['id']]['translation_required']);self.assertEqual(rows[r['id']]['status'],'retain_original_user_required')
  q=json.loads((R/'locales/zh-Hans/asset-backlog/batch-queue.json').read_bytes());b=next(b for b in q['batches']if b['id']=='tutorial_screenshots');self.assertFalse(b['translation_required'])
if __name__=='__main__':unittest.main()
