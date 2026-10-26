"""Fifth feedback: three label-only fixes; no game or artwork acceptance."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.texture_appearance import validate

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'locales/zh-Hans/texture-overlays/ui-labels-reviewed-v6.json'
OLD = 'locales/zh-Hans/texture-overlays/ui-labels-reviewed-v5.json'
DECISION = 'locales/zh-Hans/candidate-decisions/image-review-feedback-v5-20261027.json'
MAP = 'normal_map_terrain_map_highwind_down_00'
PRIZES = ['ui_batch_1071_prize', 'ui_batch_1082_prize']
def read(name):
    return json.loads((ROOT/name).read_bytes())
def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

class FifthFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, cls.plan, cls.decision = read(OLD), read(PLAN), read(DECISION)
        cls.before = {l['id']: l for l in cls.old['labels']}
        cls.after = {l['id']: l for l in cls.plan['labels']}

    def test_feedback_and_source_identities(self):
        d = self.decision
        self.assertEqual(d['input_csv_sha256'], '88061fc8d1f41ee35da3cddeed2d18bee27afea43056841b886a483a38ccd2b6')
        self.assertEqual((d['review_round'], d['images'], d['feedback_images'], d['revised_images'], d['unchanged_images']), (6, 832, 4, 3, 829))
        self.assertEqual(d['baseline_plan_sha256'], sha(OLD))
        self.assertEqual(d['review_plan_sha256'], sha(PLAN))
        self.assertFalse(d['game_rendering_verified'])

    def test_exact_scope_and_no_resource_changes(self):
        self.assertEqual({k: v for k,v in self.old.items() if k != 'labels'},
                         {k: v for k,v in self.plan.items() if k != 'labels'})
        self.assertEqual(list(self.before), list(self.after))
        changed = {k for k in self.before if self.before[k] != self.after[k]}
        self.assertEqual(changed, {MAP, *PRIZES})
        for k in changed:
            self.assertEqual({a:b for a,b in self.before[k].items() if a != 'appearance'},
                             {a:b for a,b in self.after[k].items() if a != 'appearance'})

    def test_coast_label_only_moves_right(self):
        a, b = self.before[MAP]['appearance'], self.after[MAP]['appearance']
        self.assertEqual(a['align'], 'left')
        self.assertEqual((b['align'], b['ink_box']), ('right', [2,6,140,18]))
        self.assertEqual(a['ink_box'][1::2], b['ink_box'][1::2])
        self.assertEqual({k:v for k,v in a.items() if k not in ('align','ink_box')},
                         {k:v for k,v in b.items() if k not in ('align','ink_box')})

    def test_prizes_enlarge_without_style_or_background_change(self):
        for lid in PRIZES:
            a, b = self.before[lid]['appearance'], self.after[lid]['appearance']
            self.assertEqual((a['ink_box'][3], b['ink_box'][3]), (15,22))
            self.assertEqual(a['ink_box'][:3], b['ink_box'][:3])
            self.assertEqual({k:v for k,v in a.items() if k != 'ink_box'},
                             {k:v for k,v in b.items() if k != 'ink_box'})
        self.assertEqual(self.after[PRIZES[0]]['appearance'], self.after[PRIZES[1]]['appearance'])

    def test_all_layouts_remain_valid(self):
        for lid in [MAP, *PRIZES]:
            l = self.after[lid]
            validate(l['appearance'], *l['rect'][2:])

    def test_non_image_note_does_not_authorize_external_action(self):
        row = self.decision['entries'][0]
        self.assertEqual((row['image_id'], row['previous_feedback'], row['action']), ('Ch02_Navyblue', 'GitHub博客', 'unchanged'))
        self.assertEqual(row['changes'], [])

    def test_records_are_complete_and_self_reference_is_confirmed(self):
        rows = self.decision['entries']
        self.assertEqual([r['number'] for r in rows], list(range(1,833)))
        self.assertEqual(len({r['image_id'] for r in rows}), 832)
        self.assertEqual(sum(bool(r['previous_feedback'].strip()) for r in rows), 4)
        self.assertEqual(sum(r['action']=='revised' for r in rows), 3)
        row = next(r for r in rows if r['image_id']=='ui_batch_1082')
        self.assertIn('explicitly confirmed', row['reference_interpretation'])
        self.assertNotIn('approved', {r['action'] for r in rows})

    def test_compositions_bind_current_plan(self):
        for disc in (1,2):
            p = read(f'locales/zh-Hans/locale-compositions/disc{disc}-reviewed-v6.json')
            self.assertEqual(p['texture_plan'], dict(path=PLAN, sha256=sha(PLAN)))

if __name__ == '__main__':
    unittest.main()
