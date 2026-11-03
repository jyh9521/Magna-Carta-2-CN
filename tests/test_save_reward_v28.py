import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'locales/zh-Hans'


class SaveRewardContractTests(unittest.TestCase):
    def test_all_three_save_load_scene_copies_and_slots_are_covered(self):
        plan = json.loads((ROOT/'save-reward-image-bounds-v28.json').read_bytes())
        images = [i for i in plan['images'] if i['object'].endswith('.SavePoint_Title')]
        self.assertEqual(len(images), 9)
        self.assertEqual(sum(i['package'] == 'save' for i in images), 6)
        self.assertEqual(sum(i['package'] == 'title' for i in images), 3)
        for key, count in [('save', 12), ('title', 6)]:
            profile = json.loads((ROOT/f'save-reward-{key}-fields-v28.json').read_bytes())
            self.assertEqual(len(profile['objects']), count)
            for obj in profile['objects']:
                self.assertIn('SavePoint_Title', obj['object_path'])
                self.assertEqual(len(obj['fields']), 1)
                self.assertEqual((obj['fields'][0]['before'], obj['fields'][0]['after']), (16, 20))

    def test_quest_title_moves_without_changing_frame_rewards_or_textures(self):
        profile = json.loads((ROOT/'save-reward-game-fields-v28.json').read_bytes())
        self.assertEqual(len(profile['objects']), 1)
        obj = profile['objects'][0]
        self.assertTrue(obj['object_path'].endswith('.Quest_Check_Title_img'))
        self.assertEqual([(f['property_path'][-1]['array_index'], f['before'], f['after'])
                          for f in obj['fields']], [(0, 271, 301), (1, -11, -8.5)])

    def test_title_center_is_bound_to_its_native_frame_and_inherited_height(self):
        plan = json.loads((ROOT/'save-reward-image-bounds-v28.json').read_bytes())
        frame = next(i for i in plan['images'] if i['id'] == 'quest-frame')
        self.assertEqual(frame['height_default'], dict(package='engine', object='Default__UIImage', value=50))
        self.assertEqual(frame['region'], [0, 14, 216, 50])
        self.assertEqual(plan['centers'], [dict(name='quest-complete-own-frame', label='quest-label',
                                               frame='quest-frame', tolerance=.01)])


if __name__ == '__main__':
    unittest.main()
