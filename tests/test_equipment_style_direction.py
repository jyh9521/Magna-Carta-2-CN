"""Keep every run in the corrected equipment family visibly right-leaning."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class EquipmentStyleDirectionTests(unittest.TestCase):
    def test_all_names_styles_and_weapons_use_right_leaning_source_convention(self):
        path=ROOT/'locales/zh-Hans/texture-overlays/equipment-style-clean-v31.json'
        plan=json.loads(path.read_bytes())
        self.assertEqual(len(plan['labels']),14)
        count=0
        for label in plan['labels']:
            self.assertEqual(len(label['parts']),3)
            for part in label['parts']:
                with self.subTest(image=label['id'],text=part['text']):
                    self.assertGreater(part['appearance']['italic'],0)
                    self.assertLessEqual(part['appearance']['italic'],0.3)
                count+=1
        self.assertEqual(count,42)

if __name__=='__main__':unittest.main()
