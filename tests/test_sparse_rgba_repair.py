import copy
import unittest

from tools.sparse_rgba_repair import interpolate_rgba, exemplar_rgba


class SparseRgbaRepairTests(unittest.TestCase):
    def test_constant_surface_and_exact_exterior(self):
        pixels = bytes([20, 40, 60, 180])*25
        damaged = bytearray(pixels)
        damaged[12*4:13*4] = bytes([255, 255, 255, 255])
        mask = bytes([255 if i == 12 else 0 for i in range(25)])
        result = interpolate_rgba(bytes(damaged), 5, 5, mask)
        self.assertEqual(result, pixels)
        self.assertEqual(result, interpolate_rgba(bytes(damaged), 5, 5, mask))

    def test_transparent_hidden_rgb_never_bleeds(self):
        pixels = bytes([255, 0, 255, 0])*9
        mask = bytes([0]*4+[255]+[0]*4)
        result = interpolate_rgba(pixels, 3, 3, mask)
        self.assertEqual(result[16:20], bytes(4))
        self.assertEqual(result[:16], pixels[:16])
        self.assertEqual(result[20:], pixels[20:])

    def test_bounded_masks_reject_ambiguous_or_unsupported_inputs(self):
        for mask in (bytes(9), bytes([255])*9, bytes([1])+bytes(8), bytes(8)):
            with self.subTest(mask=mask), self.assertRaises(ValueError):
                interpolate_rgba(bytes(36), 3, 3, mask)
        for iterations in (-1, True, 257, 0.5):
            with self.subTest(iterations=iterations), self.assertRaises(ValueError):
                interpolate_rgba(bytes(36), 3, 3, bytes([0]*4+[255]+[0]*4), iterations)

    def test_exemplar_retains_exact_exterior_and_translucent_surface(self):
        pixels=bytes([20,40,60,180])*225
        mask=bytes([255 if 6<=i//15<=8 and 6<=i%15<=8 else 0 for i in range(225)])
        damaged=b''.join(bytes([255,255,255,255]) if mask[i] else pixels[i*4:i*4+4] for i in range(225))
        self.assertEqual(exemplar_rgba(damaged,15,15,mask,2,16),pixels)

    def test_exemplar_requires_clean_context_and_bounded_parameters(self):
        mask=bytes([0]*4+[255]+[0]*4)
        with self.assertRaisesRegex(ValueError,'no unmasked source'):
            exemplar_rgba(bytes(36),3,3,mask,2,16)
        for radius,search in ((True,16),(0,16),(6,16),(2,7),(2,97)):
            with self.subTest(radius=radius,search=search),self.assertRaises(ValueError):
                exemplar_rgba(bytes(36),3,3,mask,radius,search)


class TexturePartsTests(unittest.TestCase):
    def setUp(self):
        from test_texture_render_windows import owned_font
        self.font = owned_font()
        self.child = dict(text='A', rect=[0, 0, 32, 32], font_size=14)
        self.label = dict(text='AB', rect=[0, 0, 80, 64], font_size=14,
                          parts=[self.child, dict(self.child, text='B', rect=[40, 32, 32, 32])])

    def test_exact_independent_alpha_composition_and_legacy_identity(self):
        from PIL import Image
        from tools.texture_overlay import render_label
        expected = Image.new('RGBA', (80, 64))
        for part in self.label['parts']:
            im = Image.frombytes('RGBA', (32, 32), render_label(self.font, part))
            expected.alpha_composite(im, tuple(part['rect'][:2]))
        self.assertEqual(render_label(self.font, self.label), expected.tobytes())
        before = render_label(self.font, self.child)
        render_label(self.font, self.label)
        self.assertEqual(before, render_label(self.font, self.child))

    def test_contained_overlapping_effects_use_ordered_alpha_not_clear_rectangles(self):
        from PIL import Image
        from tools.texture_overlay import render_label
        self.label['parts'][1]['rect'] = [0, 0, 32, 32]
        result = render_label(self.font, self.label)
        expected = Image.new('RGBA', (80, 64))
        for part in self.label['parts']:
            expected.alpha_composite(Image.frombytes('RGBA', (32, 32), render_label(self.font, part)), (0, 0))
        self.assertEqual(result, expected.tobytes())

    def test_parts_reject_nested_external_or_outside_geometry(self):
        from tools.texture_overlay import render_label
        from tools.ue3_package import FormatError
        for change in ({'parts': []}, {'font': {}}, {'rect': [70, 0, 32, 32]},
                       {'rect': [False, 0, 32, 32]}, {'text': ''}, {'text': 'C'}):
            label = copy.deepcopy(self.label)
            label['parts'][0].update(change)
            if change.get('text') == 'C':
                label['text'] = 'CB'
            with self.subTest(change=change), self.assertRaises((FormatError, ValueError)):
                render_label(self.font, label)
        for change in ({'text': 'BA'}, {'parts': []}, {'appearance': {}}, {'line_breaks': [1]},
                       {'style': {}}, {'glyph_mask': {}}, {'text': 'A'*129}):
            label = copy.deepcopy(self.label); label.update(change)
            with self.subTest(change=change), self.assertRaises((FormatError, ValueError)):
                render_label(self.font, label)


if __name__ == '__main__':
    unittest.main()
