import copy
import unittest

from tools.texture_region_repair import (alpha_support_mask, merge_delta, object_hash,
                                         source_alpha_preservation, protect_mask_rects)


class TransparentSupportTests(unittest.TestCase):
    def test_all_nonzero_alpha_including_faint_edges(self):
        rgba = bytes([20,20,20,0, 1,2,3,1, 4,5,6,255, 7,8,9,0])
        self.assertEqual(alpha_support_mask(rgba, 4, 1), bytes([0,255,255,0]))

    def test_component_preserves_adjacent_art(self):
        rgba = b''.join(bytes([9,9,9,a]) for a in [255,0,1,0,255, 255,0,255,0,255])
        self.assertEqual(alpha_support_mask(rgba, 5, 2, [2,0]), bytes([0,0,255,0,0,0,0,255,0,0]))

    def test_component_does_not_wrap_across_rows(self):
        rgba = b''.join(bytes([0,0,0,a]) for a in [0,0,255,255,0,0])
        self.assertEqual(alpha_support_mask(rgba, 3, 2, [2,0]), bytes([0,0,255,0,0,0]))

    def test_rejects_invalid_source_or_seed(self):
        for rgba, w, h, seed in [(bytes(4),2,1,None),(bytes(4),1,1,None),
                                 (bytes([0,0,0,1]),1,1,[1,0]),(bytes(8),2,1,[0,0])]:
            with self.assertRaises(ValueError):
                alpha_support_mask(rgba,w,h,seed)

    def test_preservation_detects_foreign_art_damage(self):
        before=bytes([1,2,3,255, 5,6,7,255, 9,9,9,0])
        changed=bytes([0,0,0,0, 5,6,7,255, 0,0,0,0])
        self.assertEqual(source_alpha_preservation(before,changed,3,[0,0,1,1],bytes([255])),
                         dict(visible_source_pixels=1,changed_source_pixels=0))
        damaged=changed[:4]+bytes([0,0,0,0])+changed[8:]
        self.assertEqual(source_alpha_preservation(before,damaged,3,[0,0,1,1],bytes([255]))['changed_source_pixels'],1)

    def test_adjacent_subtitle_protection_excludes_only_its_rectangle(self):
        self.assertEqual(protect_mask_rects(bytes([255])*8,4,2,[[2,1,2,1]]),bytes([255]*6+[0]*2))
        with self.assertRaises(ValueError):
            protect_mask_rects(bytes([255])*8,4,2,[[2,1,3,1]])


class DeltaMergeTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(schema_version=1, kind='texture-text-overlay-plan',
                         labels=[dict(id='old',text='old'),dict(id='other',text='keep')],
                         sources=[dict(path='p',discs=[1,2],original={'sha256':'x'},base={'sha256':'y'},
                                       textures=[dict(object='other',label='other')])])
        header = {k:v for k,v in self.plan['sources'][0].items() if k != 'textures'}
        self.delta = dict(schema_version=1,kind='texture-region-repair-delta',game_rendering_verified=False,
                          labels=[dict(expected_label_sha256=object_hash(self.plan['labels'][0]),
                                       label=dict(id='old',text='fixed')),
                                  dict(expected_label_sha256=None,label=dict(id='new',text='new'))],
                          source_additions=[dict(expected_header_sha256=object_hash(header),source=header,
                                                 textures=[dict(object='portrait',label='new')])])

    def test_bounded_merge_retains_unrelated_data_and_inputs(self):
        original = copy.deepcopy(self.plan); delta = copy.deepcopy(self.delta)
        result = merge_delta(self.plan,self.delta)
        self.assertEqual(self.plan,original); self.assertEqual(self.delta,delta)
        self.assertEqual(result['labels'][0]['text'],'fixed')
        self.assertEqual(result['labels'][1],original['labels'][1])
        self.assertEqual(result['sources'][0]['textures'][0],original['sources'][0]['textures'][0])
        self.assertEqual(len(result['sources'][0]['textures']),2)

    def test_rejects_concurrent_edits(self):
        self.plan['labels'][0]['text'] = 'changed elsewhere'
        with self.assertRaisesRegex(ValueError,'label precondition'):
            merge_delta(self.plan,self.delta)

    def test_rejects_wrong_source_and_duplicate_texture(self):
        bad = copy.deepcopy(self.delta); bad['source_additions'][0]['source']['discs'] = [1]
        with self.assertRaisesRegex(ValueError,'source precondition'):
            merge_delta(self.plan,bad)
        bad = copy.deepcopy(self.delta); bad['source_additions'][0]['textures'][0]['object'] = 'other'
        with self.assertRaisesRegex(ValueError,'duplicate delta texture'):
            merge_delta(self.plan,bad)

    def test_new_source_both_discs_and_replay_rejected(self):
        self.delta['source_additions'].append(dict(expected_header_sha256=None,
            source=dict(path='new',discs=[1,2],original={'sha256':'x'},base={'sha256':'x'}),
            textures=[dict(object='portrait',label='new')]))
        result=merge_delta(self.plan,self.delta)
        self.assertEqual(result['sources'][1]['discs'],[1,2])
        with self.assertRaises(ValueError):
            merge_delta(result,self.delta)


if __name__ == '__main__':
    unittest.main()
