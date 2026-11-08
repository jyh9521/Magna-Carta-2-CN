"""A single caption owns all native coloured runs and restores only once."""
import copy
import hashlib
import unittest

import numpy as np

from tools.build_video_captions import render_caption_layer
from tools.texture_overlay import render_parts
from tools.ue3_package import FormatError
from tools.video_title_caption import render_title_parts


class VideoTitlePartsTests(unittest.TestCase):
    def setUp(self):
        from test_texture_render_windows import owned_font
        self.font = owned_font()

    def fixture(self):
        def part(text, x, colour):
            return dict(text=text, rect=[x, 2, 24, 24], font_size=16,
                        appearance=dict(kind='source-style-v1', ink_box=[2, 2, 20, 16],
                                        align='left', gradient=[[0, colour], [1000, colour]],
                                        outline=[0, 0, 0, 0], outline_width=0,
                                        glow=[0, 0, 0, 0], glow_radius=0,
                                        shadow=[0, 0, 0, 0], shadow_offset=[0, 0],
                                        shadow_radius=0, italic=0, tracking=0, weight=0, motion=0))
        return dict(text='AB', parts=[part('A', 1, [255, 0, 0, 255]),
                                     part('B', 26, [255, 220, 0, 255])])

    def test_real_video_dispatch_reuses_existing_bounded_parts_renderer(self):
        caption = self.fixture()
        layer, proof = render_caption_layer(caption, self.font, (52, 30))
        expected = render_parts(self.font, dict(rect=[0, 0, 52, 30], **caption))
        self.assertEqual(layer.tobytes(), expected)
        self.assertEqual(proof['rgba_sha256'], hashlib.sha256(expected).hexdigest())
        self.assertEqual(proof['render_method'], 'owned-text-parts-v1')
        a = np.asarray(layer)
        self.assertTrue(np.any((a[:, :25, 0] == 255) & (a[:, :25, 1] == 0) & (a[:, :25, 3] == 255)))
        self.assertTrue(np.any((a[:, 26:, 0] == 255) & (a[:, 26:, 1] == 220) & (a[:, 26:, 3] == 255)))

    def test_mixed_single_run_schemas_are_rejected(self):
        for key, value in [('appearance', {}), ('font_size', 16), ('style', {})]:
            caption = self.fixture()
            caption[key] = value
            with self.assertRaisesRegex(ValueError, 'replace'):
                render_caption_layer(caption, self.font, (52, 30))

    def test_parts_must_join_exactly_to_declared_wording(self):
        caption = self.fixture()
        caption['text'] = 'BA'
        with self.assertRaises(FormatError):
            render_caption_layer(caption, self.font, (52, 30))

    def test_each_run_is_confined_to_native_canvas(self):
        caption = self.fixture()
        caption['parts'][1]['rect'][0] = 51
        with self.assertRaises(FormatError):
            render_caption_layer(caption, self.font, (52, 30))

    def test_bounded_native_canvas_and_font_are_required(self):
        caption = self.fixture()
        for canvas in ((0, 30), (1921, 30), (52, 1081), (52.0, 30), (52,)):
            with self.subTest(canvas=canvas), self.assertRaises(ValueError):
                render_title_parts(self.font, caption['text'], canvas, caption['parts'])
        with self.assertRaises(ValueError):
            render_title_parts(b'', caption['text'], (52, 30), caption['parts'])

    def test_proof_is_not_a_mutable_alias_of_locale_data(self):
        caption = self.fixture()
        saved = copy.deepcopy(caption)
        _, proof = render_caption_layer(caption, self.font, (52, 30))
        proof['parts'][0]['text'] = 'B'
        self.assertEqual(caption, saved)


if __name__ == '__main__':
    unittest.main()
