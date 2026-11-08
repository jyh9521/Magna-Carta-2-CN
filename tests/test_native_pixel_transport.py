"""Exact native-pixel donors must never become an unbounded image fill."""
import unittest

from tools.native_pixel_transport import transport_rgba


class NativePixelTransportTests(unittest.TestCase):
    def setUp(self):
        self.source = bytes([10, 20, 30, 201, 40, 50, 60, 202,
                             70, 80, 90, 203, 100, 110, 120, 204])
        self.mask = bytes([255, 255, 0, 0])
        self.donors = {'a': dict(rgba=self.source, width=4, height=1,
                                 clean_rectangles=[[2, 0, 2, 1]])}
        self.runs = [dict(destination=[0, 0, 2], donor='a', source=[3, 0], step_x=-1)]

    def call(self, **kw):
        args = dict(source=self.source, width=4, height=1, mask=self.mask,
                    donors=self.donors, runs=self.runs)
        args.update(kw)
        return transport_rgba(**args)

    def test_mirror_is_exact_source_rgb_with_original_alpha(self):
        result, proof = self.call()
        self.assertEqual(result, bytes([100, 110, 120, 201, 70, 80, 90, 202]) + self.source[8:])
        self.assertTrue(proof['unowned_rgba_byte_identical'])
        self.assertTrue(proof['all_alpha_byte_identical'])
        self.assertEqual(proof['owned_pixels'], 2)

    def test_repeated_column_is_not_average_or_interpolation(self):
        runs = [dict(destination=[0, 0, 2], donor='a', source=[3, 0], step_x=0)]
        result, _ = self.call(runs=runs)
        self.assertEqual(result[:8], bytes([100, 110, 120, 201, 100, 110, 120, 202]))

    def test_independent_donor_does_not_mutate_either_input(self):
        other = bytes([1, 2, 3, 255] * 4)
        donors = {'a': dict(rgba=other, width=4, height=1, clean_rectangles=[[0, 0, 4, 1]])}
        result, _ = self.call(donors=donors)
        self.assertEqual(result[:8], bytes([1, 2, 3, 201, 1, 2, 3, 202]))
        self.assertEqual(donors['a']['rgba'], other)
        self.assertEqual(self.source[0], 10)

    def test_selected_source_donor_is_rejected_even_if_claimed_clean(self):
        donors = {'a': dict(rgba=self.source, width=4, height=1, clean_rectangles=[[0, 0, 4, 1]])}
        runs = [dict(destination=[0, 0, 2], donor='a', source=[0, 0], step_x=1)]
        with self.assertRaisesRegex(ValueError, 'owned source'):
            self.call(donors=donors, runs=runs)

    def test_outside_declared_clean_donor_is_rejected(self):
        donors = {'a': dict(rgba=bytes([0] * 16), width=4, height=1, clean_rectangles=[[3, 0, 1, 1]])}
        with self.assertRaisesRegex(ValueError, 'clean donor'):
            self.call(donors=donors)

    def test_missing_selected_pixel_is_rejected(self):
        runs = [dict(destination=[0, 0, 1], donor='a', source=[3, 0], step_x=0)]
        with self.assertRaisesRegex(ValueError, 'cover'):
            self.call(runs=runs)

    def test_overlap_is_rejected_even_when_values_agree(self):
        with self.assertRaisesRegex(ValueError, 'overlap'):
            self.call(runs=self.runs + self.runs)

    def test_unowned_destination_is_rejected(self):
        runs = [dict(destination=[0, 0, 3], donor='a', source=[3, 0], step_x=0)]
        with self.assertRaisesRegex(ValueError, 'unowned'):
            self.call(runs=runs)

    def test_outside_source_is_rejected_without_wraparound(self):
        runs = [dict(destination=[0, 0, 2], donor='a', source=[3, 0], step_x=1)]
        with self.assertRaisesRegex(ValueError, 'source bounds'):
            self.call(runs=runs)

    def test_outside_destination_is_rejected(self):
        runs = [dict(destination=[3, 0, 2], donor='a', source=[3, 0], step_x=0)]
        with self.assertRaisesRegex(ValueError, 'destination'):
            self.call(runs=runs)

    def test_binary_proper_sparse_mask_required(self):
        for mask in (bytes(4), bytes([255] * 4), bytes([1, 255, 0, 0]), b''):
            with self.subTest(mask=mask), self.assertRaises(ValueError):
                self.call(mask=mask)

    def test_geometry_and_integer_steps_are_strict(self):
        for value in (True, 2, .5, -2):
            runs = [dict(destination=[0, 0, 2], donor='a', source=[3, 0], step_x=value)]
            with self.subTest(step=value), self.assertRaises(ValueError):
                self.call(runs=runs)

    def test_clean_rectangles_are_bounded(self):
        for rect in ([0, 0, 5, 1], [-1, 0, 2, 1], [0, 0, 0, 1], [True, 0, 2, 1]):
            donors = {'a': dict(rgba=self.source, width=4, height=1, clean_rectangles=[rect])}
            with self.subTest(rect=rect), self.assertRaises(ValueError):
                self.call(donors=donors)

    def test_unknown_donor_and_unexpected_fields_fail_closed(self):
        runs = [dict(destination=[0, 0, 2], donor='missing', source=[3, 0], step_x=-1)]
        with self.assertRaises(ValueError):
            self.call(runs=runs)
        with self.assertRaises(ValueError):
            self.call(runs=[dict(self.runs[0], averaging=True)])


class NativePixelRepairReplayTests(unittest.TestCase):
    def fixture(self, root):
        import io
        from PIL import Image
        from tools.build_font_supplement import context
        from tools.patch_tagged_fields import digest
        from tools.texture_layout import read_texture, decode_texture
        from tools.texture_overlay import select_texture_export
        from test_texture_layout import profile_fixture
        from test_supplement_font import stored_decoder
        data, edit, _ = profile_fixture(7)
        (root/'source.xxx').write_bytes(data)
        c = context(data, stored_decoder)
        e = select_texture_export(c['tables'], edit['object'])
        payload = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        t = read_texture(payload, c['tables']['names'], e['serial_offset'], edit['profile'], stored_decoder)
        w, h = t['width'], t['height']
        rgba = decode_texture(t)
        mask = Image.new('L', (w, h)); mask.putpixel((8, 8), 255)
        mask.save(root/'mask.png')
        ref = lambda name: dict(path=name, sha256=digest((root/name).read_bytes()))
        identity = dict(source=ref('source.xxx'), object=edit['object'], profile=edit['profile'],
                        dimensions=[w, h], rgba_sha256=digest(rgba))
        runs = [dict(destination=[8, 8, 1], donor='native', source=[16, 8], step_x=0)]
        donors = {'native': dict(rgba=rgba, width=w, height=h, clean_rectangles=[[16, 0, 1, h]])}
        rebuilt, _ = transport_rgba(rgba, w, h, mask.tobytes(), donors, runs)
        patch = bytes(w*h*4)
        i = (8*w+8)*4
        patch = patch[:i] + rebuilt[i:i+4] + patch[i+4:]
        stream = io.BytesIO(); Image.frombytes('RGBA', (w, h), patch).save(stream, format='PNG')
        case = dict(id='owned', **identity, mask=ref('mask.png'),
                    donors=[dict(id='native', **identity, clean_rectangles=[[16, 0, 1, h]])],
                    runs=runs, patch=dict(path='owned.png', sha256=digest(stream.getvalue())),
                    result_rgba_sha256=digest(rebuilt))
        return dict(schema_version=1, kind='native-pixel-transport-texture-repair-v1',
                    method='nearest-source-pixel-rgb-preserve-alpha-v1',
                    hidden_background='native-motif-continuation-not-original-recovery',
                    cases=[case]), stored_decoder

    def test_real_decode_replay_and_all_outputs_reopen(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.build_native_pixel_repairs import build
        from tools.patch_tagged_fields import digest
        with TemporaryDirectory() as temp:
            root = Path(temp); recipe, decoder = self.fixture(root)
            result = build(recipe, root, root/'replay', decoder)
            self.assertEqual(len(result['cases']), 1)
            self.assertEqual(digest((root/'replay/owned.png').read_bytes()), recipe['cases'][0]['patch']['sha256'])
            self.assertEqual(json.loads((root/'replay/manifest.json').read_bytes()), result)
            self.assertTrue(result['cases'][0]['unowned_rgba_byte_identical'])

    def test_source_mask_result_and_patch_guards_fail_before_publication(self):
        import copy
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.build_native_pixel_repairs import build
        with TemporaryDirectory() as temp:
            root = Path(temp); recipe, decoder = self.fixture(root)
            for field in ('source', 'mask', 'patch', 'rgba_sha256', 'result_rgba_sha256', 'dimensions'):
                bad = copy.deepcopy(recipe); case = bad['cases'][0]
                if field in ('source', 'mask', 'patch'):
                    case[field]['sha256'] = '0'*64
                else:
                    case[field] = [1, 1] if field == 'dimensions' else '0'*64
                with self.subTest(field=field), self.assertRaises(ValueError):
                    build(bad, root, root/field, decoder)
                self.assertFalse((root/field).exists())

    def test_portable_path_conflicts_reject_before_any_output(self):
        import copy
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.build_native_pixel_repairs import build
        with TemporaryDirectory() as temp:
            root = Path(temp); recipe, decoder = self.fixture(root)
            for names in (['manifest.json'], ['Manifest.json'], ['../x.png'],
                          ['a.png', 'A.PNG'], ['a.png', 'a.png+z.png', 'a.png/b.png']):
                bad = copy.deepcopy(recipe); base = bad['cases'][0]; bad['cases'] = []
                for i, name in enumerate(names):
                    case = copy.deepcopy(base); case['id'] = str(i); case['patch']['path'] = name
                    bad['cases'].append(case)
                with self.subTest(names=names), self.assertRaises(ValueError):
                    build(bad, root, root/'rejected', decoder)
                self.assertFalse((root/'rejected').exists())


if __name__ == '__main__':
    unittest.main()
