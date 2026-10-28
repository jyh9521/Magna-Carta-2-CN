import copy
import unittest
from tools.texture_delta import select_delta


class TextureDeltaTests(unittest.TestCase):
    def setUp(self):
        self.old = dict(labels=[dict(id=x, text=x) for x in 'abc'],
            font=dict(path='font', sha256='0'*64),
            sources=[dict(path='one.xxx', discs=[1, 2], textures=[dict(label='a'), dict(label='b')]),
                     dict(path='two.xxx', discs=[1, 2], textures=[dict(label='c')])])
        self.new = copy.deepcopy(self.old)

    def test_changed_layer_keeps_other_layers_of_same_package(self):
        self.new['labels'][0]['text'] = 'changed'
        subset, proof = select_delta(self.old, self.new, 1)
        self.assertEqual([l['id'] for l in subset['labels']], ['a', 'b'])
        self.assertEqual(proof['selected_packages'], ['one.xxx'])
        self.assertEqual(proof['unchanged_packages'], 1)
        self.assertEqual(self.old['labels'][0]['text'], 'a')

    def test_changed_base_composes_other_component_first(self):
        self.new['sources'][0]['base'] = dict(path='new-font.xxx', sha256='1'*64)
        subset, proof = select_delta(self.old, self.new, 2)
        self.assertEqual(proof['selected_packages'], ['one.xxx'])
        self.assertEqual(len(subset['labels']), 2)

    def test_global_font_change_selects_all(self):
        self.new['font']['sha256'] = '1'*64
        subset, proof = select_delta(self.old, self.new, 1)
        self.assertEqual(len(subset['sources']), 2)
        self.assertTrue(proof['globals_changed'])

    def test_no_changes_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no changed'): select_delta(self.old, self.new, 1)

    def test_removed_package_requires_explicit_restore(self):
        self.new['sources'].pop()
        with self.assertRaisesRegex(ValueError, 'removed packages'): select_delta(self.old, self.new, 1)

    def test_missing_layer_and_duplicate_id_rejected(self):
        self.new['labels'].pop()
        with self.assertRaisesRegex(ValueError, 'missing labels'): select_delta(self.old, self.new, 1)
        self.new = copy.deepcopy(self.old); self.new['labels'].append(self.new['labels'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate label'): select_delta(self.old, self.new, 1)


if __name__ == '__main__': unittest.main()
