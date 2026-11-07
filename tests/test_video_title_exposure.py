"""Synthetic RGBA fixtures separate foreground exposure from title opacity."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from tools import build_video_captions as builder
from tools.video_caption import restore_masked
from tools.video_frame_repairs import VideoFrameRepairs
from tools.video_title_caption import VideoTitleCaption
from test_bink_audio import fixture as bink_fixture


def digest(data):
    return hashlib.sha256(data).hexdigest()


class VideoTitleExposureTests(unittest.TestCase):
    def fixture(self, alpha=None):
        mask = np.zeros((4, 4), dtype=bool)
        mask[1:3, 1:3] = True
        layer = Image.new('RGBA', (8, 6))
        # Fill, outline, shadow and antialiased fringe are distinct RGBA pixels.
        for position, rgba in [((3, 2), (200, 120, 60, 255)),
                               ((2, 2), (27, 13, 7, 230)),
                               ((4, 3), (17, 9, 3, 96)),
                               ((5, 3), (100, 150, 200, 37))]:
            layer.putpixel(position, rgba)
        layer.putpixel((0, 0), (77, 88, 99, 0))
        frame = Image.new('RGB', layer.size, (31, 83, 149))
        args = dict(rect=[2, 1, 4, 4], mask=mask, layer=layer,
                    frame_alpha=[0, 128, 255, 255] if alpha is None else alpha,
                    expected_frames=4)
        return args, frame

    def expected(self, args, frame, index, exposure=255):
        alpha = args['frame_alpha'][index]
        if not alpha:
            return frame.copy()
        repaired, _ = restore_masked(frame, args['rect'], args['mask'])
        rgba = np.asarray(args['layer']).copy()
        for channel in range(3):
            rgba[:, :, channel] = np.array([
                round(int(value) * exposure / 255) for value in rgba[:, :, channel].flat
            ], dtype=np.uint8).reshape(rgba.shape[:2])
        rgba[:, :, 3] = np.array([
            round(int(value) * alpha / 255) for value in rgba[:, :, 3].flat
        ], dtype=np.uint8).reshape(rgba.shape[:2])
        return Image.alpha_composite(repaired.convert('RGBA'), Image.fromarray(rgba)).convert('RGB')

    def test_rgb_exposure_is_not_an_alpha_fade_over_a_coloured_background(self):
        args, frame = self.fixture([255] * 4)
        dark = VideoTitleCaption(**args, frame_exposure=[128] * 4).apply(frame, 0)
        faded_args = dict(args, frame_alpha=[128] * 4)
        faded = VideoTitleCaption(**faded_args).apply(frame, 0)
        self.assertEqual(dark.getpixel((3, 2)), (100, 60, 30))
        self.assertNotEqual(dark.getpixel((3, 2)), faded.getpixel((3, 2)))
        self.assertEqual(dark.getpixel((7, 5)), frame.getpixel((7, 5)))

    def test_zero_exposure_keeps_opaque_black_ink_instead_of_revealing_background(self):
        args, frame = self.fixture([255] * 4)
        operation = VideoTitleCaption(**args, frame_exposure=[0] * 4)
        result = operation.apply(frame, 2)
        self.assertEqual(result.getpixel((3, 2)), (0, 0, 0))
        self.assertNotEqual(result.getpixel((3, 2)), frame.getpixel((3, 2)))
        self.assertEqual(operation.proof()['active_frames'], 4)

    def test_fill_outline_shadow_and_fringe_rgb_scale_but_alpha_scales_independently(self):
        args, frame = self.fixture()
        exposures = [0, 73, 128, 255]
        operation = VideoTitleCaption(**args, frame_exposure=exposures)
        for index, exposure in enumerate(exposures):
            with self.subTest(index=index):
                self.assertEqual(operation.apply(frame, index).tobytes(),
                                 self.expected(args, frame, index, exposure).tobytes())
        base = np.asarray(operation.paint_layer)
        for (alpha, exposure), scaled in operation._scaled.items():
            values = np.asarray(scaled)
            self.assertTrue(np.array_equal(values[:, :, 3], np.array([
                round(int(value) * alpha / 255) for value in base[:, :, 3].flat
            ], dtype=np.uint8).reshape(base.shape[:2])))
            for channel in range(3):
                self.assertTrue(np.array_equal(values[:, :, channel], np.array([
                    round(int(value) * exposure / 255) for value in base[:, :, channel].flat
                ], dtype=np.uint8).reshape(base.shape[:2])))

    def test_default_none_and_full_exposure_preserve_legacy_pixels(self):
        args, frame = self.fixture()
        implicit = VideoTitleCaption(**args)
        explicit_none = VideoTitleCaption(**args, frame_exposure=None)
        full = VideoTitleCaption(**args, frame_exposure=[255] * 4)
        for index in range(4):
            expected = self.expected(args, frame, index)
            for operation in (implicit, explicit_none, full):
                self.assertEqual(operation.apply(frame, index).tobytes(), expected.tobytes())
        self.assertEqual(implicit.proof(), explicit_none.proof())
        self.assertNotIn('frame_exposure_sha256', implicit.proof())
        self.assertEqual(full.proof()['frame_exposure_sha256'], digest(bytes([255] * 4)))

    def test_cache_uses_alpha_and_exposure_and_reuses_the_same_pair(self):
        args, frame = self.fixture([128] * 4)
        operation = VideoTitleCaption(**args, frame_exposure=[255, 64, 255, 0])
        first = operation.apply(frame, 0)
        cached = operation._scaled[(128, 255)]
        operation.apply(frame, 1)
        self.assertEqual(operation.apply(frame, 2).tobytes(), first.tobytes())
        self.assertIs(operation._scaled[(128, 255)], cached)
        operation.apply(frame, 3)
        self.assertEqual(set(operation._scaled), {(128, 255), (128, 64), (128, 0)})
        other = Image.new('RGB', frame.size, (77, 66, 55))
        self.assertEqual(operation.apply(other, 0).tobytes(), self.expected(args, other, 0).tobytes())

    def test_exposure_curve_and_source_images_are_not_mutated_or_retained_by_reference(self):
        args, frame = self.fixture()
        exposure = [0, 32, 128, 255]
        before_layer, before_frame = args['layer'].tobytes(), frame.tobytes()
        before_mask = args['mask'].tobytes()
        operation = VideoTitleCaption(**args, frame_exposure=exposure)
        expected = operation.apply(frame, 2).tobytes()
        proof = operation.proof()
        exposure[:] = [255] * 4
        self.assertEqual(operation.apply(frame, 2).tobytes(), expected)
        self.assertEqual(operation.proof(), proof)
        self.assertEqual(operation.frame_exposure, (0, 32, 128, 255))
        self.assertEqual(args['layer'].tobytes(), before_layer)
        self.assertEqual(frame.tobytes(), before_frame)
        self.assertEqual(args['mask'].tobytes(), before_mask)
        self.assertEqual(proof['frame_exposure_sha256'], digest(bytes([0, 32, 128, 255])))

    def test_exposure_values_are_complete_strict_integer_bytes(self):
        args, _ = self.fixture()
        invalid = [[], [255], [255] * 5, (255,) * 4, '255', 255, {},
                   [0, True, 128, 255], [0, False, 128, 255], [0, 1.0, 128, 255],
                   [0, -1, 128, 255], [0, 256, 128, 255], [0, None, 128, 255],
                   [0, float('nan'), 128, 255], [0, float('inf'), 128, 255],
                   [0, np.int64(1), 128, 255], np.array([0, 1, 128, 255])]
        for exposure in invalid:
            with self.subTest(exposure=repr(exposure)), self.assertRaises(ValueError):
                VideoTitleCaption(**args, frame_exposure=exposure)
        for count in (0, 6145, True, 4.0):
            with self.subTest(expected_frames=count), self.assertRaises(ValueError):
                VideoTitleCaption(**dict(args, expected_frames=count), frame_exposure=[255] * 4)

    def test_inactive_frame_and_outside_owned_support_remain_identical(self):
        args, frame = self.fixture()
        operation = VideoTitleCaption(**args, frame_exposure=[255, 0, 32, 64])
        before = np.asarray(frame)
        allowed = np.asarray(args['layer'].getchannel('A')) > 0
        allowed[1:5, 2:6] |= args['mask']
        for index in range(4):
            result = operation.apply(frame, index)
            self.assertTrue(np.array_equal(np.asarray(result)[~allowed], before[~allowed]))
            if index == 0:
                self.assertEqual(result.tobytes(), frame.tobytes())
                self.assertIsNot(result, frame)
        self.assertNotIn((0, 255), operation._scaled)
        for index in (-1, 4, True, 1.0):
            with self.subTest(index=index), self.assertRaises(ValueError):
                operation.apply(frame, index)

    def test_source_locked_repairs_stay_separate_from_foreground_exposure(self):
        args, frame = self.fixture()
        records = []
        repaired_rgb = (90, 70, 50)
        for index in (1, 2, 3):
            rgba = np.zeros((4, 4, 4), np.uint8)
            rgba[args['mask']] = (*repaired_rgb, 255)
            records.append(dict(index=index,
                source_crop_sha256=digest(frame.crop((2, 1, 6, 5)).tobytes()), patch=Image.fromarray(rgba)))
        repairs = VideoFrameRepairs(args['rect'], args['mask'], 4, [1, 2, 3], records, frame.size)
        operation = VideoTitleCaption(**args, repairs=repairs, frame_exposure=[0, 0, 0, 0])
        result = operation.apply(frame, 2)
        self.assertEqual(result.getpixel((3, 2)), (0, 0, 0))
        self.assertEqual(result.getpixel((4, 2)), repaired_rgb)
        self.assertEqual(result.getpixel((7, 5)), frame.getpixel((7, 5)))
        altered = frame.copy()
        altered.putpixel((2, 1), (1, 2, 3))
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            operation.apply(altered, 2)

    def test_background_only_repairs_outlive_visible_text_and_exposure(self):
        args, frame = self.fixture([0, 255, 0, 0])
        records = []
        for index in (1, 2, 3):
            rgba = np.zeros((4, 4, 4), np.uint8)
            rgba[args['mask']] = (90, 70, 50, 255)
            records.append(dict(index=index,
                source_crop_sha256=digest(frame.crop((2, 1, 6, 5)).tobytes()), patch=Image.fromarray(rgba)))
        repairs = VideoFrameRepairs(args['rect'], args['mask'], 4, [1, 2, 3], records, frame.size)
        operation = VideoTitleCaption(**args, repairs=repairs, frame_exposure=[0, 128, 0, 0])
        for index in (2, 3):
            result = operation.apply(frame, index)
            self.assertEqual(result.getpixel((3, 2)), (90, 70, 50))
            self.assertEqual(result.getpixel((2, 2)), frame.getpixel((2, 2)))
        self.assertEqual(operation.apply(frame, 0).tobytes(), frame.tobytes())
        proof = operation.proof()
        self.assertEqual((proof['active_frames'], proof['last_active_frame_exclusive']), (3, 4))
        self.assertEqual((proof['text_active_frames'], proof['last_text_active_frame_exclusive']), (1, 2))
        self.assertEqual(proof['background_only_frames'], 2)
        self.assertFalse(operation._scaled)


class BuilderExposurePreflightTests(unittest.TestCase):
    def test_invalid_exposure_and_untimed_scope_reject_before_asset_inspection(self):
        cases = [dict(frame_alpha=[255, 255], frame_exposure=[255]),
                 dict(frame_alpha=[255, 255], frame_exposure=[True, 255]),
                 dict(frame_alpha=[0, 0], frame_exposure=[255, 255]),
                 dict(frame_exposure=[255, 255]), dict(frame_exposure=None),
                 dict(frame_alpha=[255, 255], frame_exposure=[255, 255], native=True)]
        for value in cases:
            caption = {key: field for key, field in value.items() if key != 'native'}
            caption['erase'] = {'native_screen': {}} if value.get('native') else {}
            with (self.subTest(caption=caption),
                  patch.object(builder, 'locked_file', side_effect=AssertionError('asset read')),
                  patch('PIL.Image.open', side_effect=AssertionError('image read')),
                  self.assertRaises(ValueError)):
                builder.frame_repair_metadata(caption, 2, (8, 6), Path.cwd())

    def test_prepare_layers_checks_exposure_before_fonts_repairs_or_frame_decode(self):
        source = bink_fixture(tracks=0)
        entry = dict(source=dict(file='source.bik', sha256=digest(source), size=len(source)),
                     captions=[dict(frame_alpha=[255, 255], frame_exposure=[255], erase={})])
        plan = dict(fonts={'owned': dict(path='font.bin', sha256='0' * 64)})
        def source_only(path, *args, **kwargs):
            if Path(path).name != 'source.bik':
                raise AssertionError('font or repair asset read before curve validation')
            return source
        with (patch.object(builder, 'locked_file', side_effect=source_only),
              patch.object(builder, 'first_frame', side_effect=AssertionError('decoder called')),
              patch('PIL.Image.open', side_effect=AssertionError('PNG opened')),
              self.assertRaisesRegex(ValueError, 'exposure')):
            builder.prepare_layers(plan, entry, Path.cwd(), Path.cwd(), 'UNUSED')

    def test_builder_passes_exposure_to_timed_caption_without_needing_a_font_fixture(self):
        args, frame = VideoTitleExposureTests().fixture([255] * 4)
        source = bink_fixture(tracks=0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.bik').write_bytes(source)
            (root / 'font.bin').write_bytes(b'authored-font-placeholder')
            caption = dict(text='A', font='owned', frame_alpha=[255, 255], frame_exposure=[64, 192],
                           erase=dict(rect=args['rect'], threshold=200, radius=0))
            entry = dict(source=dict(file='source.bik', sha256=digest(source), size=len(source),
                                     first_rgb_sha256=digest(frame.tobytes())), captions=[caption])
            plan = dict(fonts={'owned': dict(path='font.bin', sha256=digest(b'authored-font-placeholder'))})
            with (patch.object(builder, 'first_frame', return_value=frame),
                  patch.object(builder, 'source_ink_mask', return_value=args['mask']),
                  patch.object(builder, 'render_caption_layer', return_value=(args['layer'], {})),
                  patch('fontTools.ttLib.TTFont') as font):
                font.return_value.__enter__.return_value.getBestCmap.return_value = {ord('A'): 'A'}
                operation = builder.prepare_layers(plan, entry, root, root, 'UNUSED')[3][0]
            self.assertEqual(operation.frame_exposure, (64, 192))
            self.assertEqual(operation.proof()['frame_exposure_sha256'], digest(bytes([64, 192])))
            self.assertEqual(operation.apply(frame, 0).getpixel((3, 2)), (50, 30, 15))


if __name__ == '__main__':
    unittest.main()
