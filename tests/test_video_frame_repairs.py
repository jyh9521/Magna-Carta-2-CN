"""Owned synthetic pixel fixtures for strict per-frame repair transport."""
import hashlib
import json
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from tools.video_frame_repairs import VideoFrameRepairs


def sha(data):
    return hashlib.sha256(data).hexdigest()


class VideoFrameRepairsTests(unittest.TestCase):
    def fixture(self):
        rect = [5, 4, 12, 10]
        mask = np.zeros((10, 12), dtype=bool)
        mask[2:8, 3:5] = True
        mask[4:6, 3:9] = True
        frames = [Image.new('RGB', (24, 18), (20 + index, 40, 60)) for index in range(4)]
        records = []
        for index in (1, 2):
            rgba = np.zeros((10, 12, 4), dtype=np.uint8)
            rgba[mask] = (91 + index, 123, 211, 255)
            records.append(dict(index=index, source_crop_sha256=sha(frames[index].crop((5, 4, 17, 14)).tobytes()),
                                patch=Image.fromarray(rgba)))
        args = dict(rect=rect, mask=mask, frame_count=4, active_frames=[1, 2],
                    records=records, canvas=(24, 18))
        return args, frames

    def reject(self, field, values):
        for value in values:
            args, _ = self.fixture()
            args[field] = value
            with self.subTest(field=field, value=repr(value)[:120]), self.assertRaises(ValueError):
                VideoFrameRepairs(**args)

    def test_exact_owned_rgb_only_and_no_input_mutation(self):
        args, frames = self.fixture()
        operation = VideoFrameRepairs(**args)
        for index in args['active_frames']:
            source = frames[index]
            before = source.tobytes()
            result = operation.apply(source, index)
            expected = np.asarray(source).copy()
            expected[4:14, 5:17][args['mask']] = np.asarray(args['records'][index - 1]['patch'])[:, :, :3][args['mask']]
            self.assertEqual(result.tobytes(), expected.tobytes())
            self.assertEqual(source.tobytes(), before)
            self.assertIsNot(result, source)
            self.assertEqual(result.mode, 'RGB')

    def test_inactive_frames_are_identical_independent_copies(self):
        args, frames = self.fixture()
        operation = VideoFrameRepairs(**args)
        for index in (0, 3):
            before = frames[index].tobytes()
            result = operation.apply(frames[index], index)
            self.assertEqual(result.tobytes(), before)
            result.putpixel((0, 0), (255, 0, 0))
            self.assertEqual(frames[index].tobytes(), before)

    def test_moving_fine_grid_is_retained_where_harmonic_erasure_loses_it(self):
        from tools.video_caption import restore_masked
        rect = (8, 8, 48, 32)
        mask = np.zeros((32, 48), dtype=bool)
        mask[4:28, 8:13] = True
        mask[4:28, 30:35] = True
        mask[13:18, 8:35] = True
        yy, xx = np.indices((48, 64))
        clean, source, records = [], [], []
        for index in range(4):
            grid = ((xx + index) // 2 + yy // 2) % 2
            native = np.stack((20 + grid * 200, 50 + grid * 150, 230 - grid * 180), axis=2).astype('uint8')
            clean.append(Image.fromarray(native))
            burned = native.copy()
            if index in (1, 2):
                burned[8:40, 8:56][mask] = (245, 230, 210)
                rgba = np.zeros((32, 48, 4), dtype=np.uint8)
                rgba[:, :, :3][mask] = native[8:40, 8:56][mask]
                rgba[:, :, 3][mask] = 255
                records.append(dict(index=index, source_crop_sha256=sha(burned[8:40, 8:56].tobytes()),
                                    patch=Image.fromarray(rgba)))
            source.append(Image.fromarray(burned))
        operation = VideoFrameRepairs(rect, mask, 4, [1, 2], records, (64, 48))
        for index in range(4):
            self.assertEqual(operation.apply(source[index], index).tobytes(), clean[index].tobytes())
        self.assertNotEqual(clean[1].tobytes(), clean[2].tobytes())
        old_result, _ = restore_masked(source[1], rect, mask)
        native_crop = np.asarray(clean[1])[8:40, 8:56].astype(float)
        old_crop = np.asarray(old_result)[8:40, 8:56].astype(float)
        self.assertGreater(np.abs(native_crop[mask] - old_crop[mask]).mean(), 50)
        adjacent_owned = mask[:, 1:] & mask[:, :-1]
        native_detail = np.abs(np.diff(native_crop, axis=1))[adjacent_owned].mean()
        old_detail = np.abs(np.diff(old_crop, axis=1))[adjacent_owned].mean()
        self.assertGreater(native_detail, old_detail * 4)

    def test_source_crop_hash_covers_unowned_pixels_inside_rect(self):
        args, frames = self.fixture()
        operation = VideoFrameRepairs(**args)
        for position in ((8, 6), (5, 4)):
            frame = frames[1].copy()
            frame.putpixel(position, (1, 2, 3))
            before = frame.tobytes()
            with self.subTest(position=position), self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                operation.apply(frame, 1)
            self.assertEqual(frame.tobytes(), before)

    def test_source_changes_outside_rect_are_retained_not_falsely_hashed(self):
        args, frames = self.fixture()
        frame = frames[1].copy()
        frame.putpixel((0, 0), (7, 8, 9))
        result = VideoFrameRepairs(**args).apply(frame, 1)
        self.assertEqual(result.getpixel((0, 0)), (7, 8, 9))

    def test_wrong_valid_hash_fails_closed_without_fallback(self):
        args, frames = self.fixture()
        args['records'][0]['source_crop_sha256'] = '0' * 64
        operation = VideoFrameRepairs(**args)
        before = frames[1].tobytes()
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            operation.apply(frames[1], 1)
        self.assertEqual(frames[1].tobytes(), before)

    def test_uppercase_hex_is_normalized_without_changing_guard(self):
        args, frames = self.fixture()
        args['records'][0]['source_crop_sha256'] = args['records'][0]['source_crop_sha256'].upper()
        self.assertNotEqual(VideoFrameRepairs(**args).apply(frames[1], 1).tobytes(), frames[1].tobytes())

    def test_constructor_defensively_copies_all_mutable_inputs(self):
        args, frames = self.fixture()
        operation = VideoFrameRepairs(**args)
        expected = operation.apply(frames[1], 1).tobytes()
        proof = operation.proof()
        args['mask'][:] = False
        args['rect'][:] = [0, 0, 1, 1]
        args['active_frames'].clear()
        for record in args['records']:
            record['patch'].paste((0, 0, 0, 0), (0, 0, 12, 10))
            record['source_crop_sha256'] = 'f' * 64
        args['records'].clear()
        self.assertEqual(operation.apply(frames[1], 1).tobytes(), expected)
        self.assertEqual(operation.proof(), proof)
        with self.assertRaises(ValueError):
            operation.mask[0, 0] = True
        with self.assertRaises(ValueError):
            operation.mask.flags.writeable = True
        self.assertIsNot(operation.mask, operation.mask)
        self.assertEqual(operation.mask.shape, (10, 12))
        self.assertEqual(operation.apply(frames[1], 1).tobytes(), expected)
        proof['active_frames'].clear()
        proof['rect'].clear()
        self.assertEqual(operation.proof()['active_frames'], [1, 2])
        self.assertEqual(operation.proof()['rect'], [5, 4, 12, 10])

    def test_proof_hashes_are_canonical_and_do_not_claim_artistic_acceptance(self):
        args, _ = self.fixture()
        first = VideoFrameRepairs(**args).proof()
        args['active_frames'].reverse()
        args['records'].reverse()
        second = VideoFrameRepairs(**args).proof()
        self.assertEqual(first, second)
        self.assertEqual(first['method'], 'sparse-frame-rgba-v1')
        self.assertEqual(first['record_count'], 2)
        self.assertEqual(first['active_frame_set_sha256'], sha(b'[1,2]'))
        self.assertEqual(first['rect_sha256'], sha(b'[5,4,12,10]'))
        self.assertEqual(first['mask_sha256'], sha(args['mask'].tobytes()))
        for key in ('outside_mask_retained', 'outside_rect_retained', 'inactive_frames_byte_identical'):
            self.assertIs(first[key], True)
        self.assertIs(first['artistic_acceptance'], False)
        json.dumps(first, allow_nan=False)

    def test_canvas_and_rectangle_types_bounds_and_finite_values(self):
        self.reject('canvas', ([24, 18], (), (24,), (1921, 18), (24, 1081), (0, 18),
                               (True, 18), (24.0, 18), (float('nan'), 18), (24, float('inf'))))
        self.reject('rect', (None, [], [0, 0, 1], [0, 0, 1, 1, 0], [-1, 0, 1, 1],
                             [0, 0, 0, 1], [0, 0, 1, -1], [20, 0, 12, 10], [0, 15, 12, 10],
                             [True, 0, 12, 10], [0, 0, 12.0, 10], [float('nan'), 0, 12, 10],
                             [0, 0, float('inf'), 10]))
        args, _ = self.fixture()
        args.update(rect=[0, 0, 513, 512], canvas=(1920, 1080), mask=np.zeros((512, 513), bool))
        with self.assertRaisesRegex(ValueError, 'rectangle'):
            VideoFrameRepairs(**args)

    def test_mask_requires_boolean_geometry_and_nonempty_proper_subset(self):
        self.reject('mask', (None, [[False]], np.zeros((10, 12), 'uint8'),
                             np.zeros((9, 12), bool), np.zeros((10, 12), bool),
                             np.ones((10, 12), bool), np.zeros((10, 12, 1), bool)))

    def test_noncontiguous_boolean_mask_has_canonical_copy(self):
        args, _ = self.fixture()
        padded = np.zeros((10, 24), bool)
        padded[:, ::2] = args['mask']
        args['mask'] = padded[:, ::2]
        self.assertFalse(args['mask'].flags.c_contiguous)
        proof = VideoFrameRepairs(**args).proof()
        self.assertEqual(proof['mask_sha256'], sha(args['mask'].tobytes(order='C')))

    def test_frame_count_and_active_set_are_strictly_bounded(self):
        self.reject('frame_count', (0, -1, 6145, True, 4.0, float('nan'), float('inf'), None))
        self.reject('active_frames', ([], (), [1, 1], [1, 2, 3, 0, 1], [-1, 2], [1, 4],
                                      [True, 2], [1.0, 2], [1, float('nan')], None))
        args, frames = self.fixture()
        args['frame_count'] = 6144
        operation = VideoFrameRepairs(**args)
        self.assertEqual(operation.apply(frames[0], 6143).tobytes(), frames[0].tobytes())

    def test_records_must_cover_active_set_exactly(self):
        args, _ = self.fixture()
        one, two = args['records']
        for records in (None, (), [], [one], [one, two, two], [one, one],
                        [dict(one, index=0), two], [dict(one, index=4), two],
                        [dict(one, index=True), two], [dict(one, index=1.0), two]):
            args, _ = self.fixture()
            args['records'] = records
            with self.subTest(records=repr(records)[:120]), self.assertRaises(ValueError):
                VideoFrameRepairs(**args)

    def test_record_missing_unknown_fields_and_non_dicts_reject(self):
        for replacement in (None, [], {}, {'index': 1}, {'index': 1, 'source_crop_sha256': '0' * 64}):
            args, _ = self.fixture()
            args['records'][0] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                VideoFrameRepairs(**args)
        args, _ = self.fixture()
        args['records'][0]['unknown'] = True
        with self.assertRaises(ValueError):
            VideoFrameRepairs(**args)

    def test_crop_hash_metadata_must_be_exact_64_hex_characters(self):
        for digest in (None, 1, b'0' * 64, '', '0' * 63, '0' * 65, 'g' * 64, '0' * 63 + '\n'):
            args, _ = self.fixture()
            args['records'][0]['source_crop_sha256'] = digest
            with self.subTest(digest=repr(digest)), self.assertRaises(ValueError):
                VideoFrameRepairs(**args)

    def test_patch_mode_and_geometry_must_be_exact(self):
        for image in (None, np.zeros((10, 12, 4), 'uint8'), Image.new('RGB', (12, 10)),
                      Image.new('P', (12, 10)), Image.new('RGBA', (11, 10))):
            args, _ = self.fixture()
            args['records'][0]['patch'] = image
            with self.subTest(image=repr(image)[:80]), self.assertRaises(ValueError):
                VideoFrameRepairs(**args)

    def test_alpha_and_hidden_rgb_cannot_expand_or_feather_scope(self):
        for position, channel, value in (((3, 2), 3, 0), ((3, 2), 3, 254),
                                         ((0, 0), 3, 1), ((0, 0), 3, 255),
                                         ((0, 0), 0, 1), ((0, 0), 2, 255)):
            args, _ = self.fixture()
            rgba = np.asarray(args['records'][0]['patch']).copy()
            x, y = position
            rgba[y, x, channel] = value
            args['records'][0]['patch'] = Image.fromarray(rgba)
            with self.subTest(position=position, channel=channel, value=value), self.assertRaises(ValueError):
                VideoFrameRepairs(**args)

    def test_total_rgba_byte_limit_rejects_before_reading_pixels(self):
        mask = np.zeros((512, 512), bool)
        mask[0, 0] = True
        image = Image.new('RGBA', (512, 512))
        image.putpixel((0, 0), (1, 2, 3, 255))
        records = [dict(index=index, source_crop_sha256='0' * 64, patch=image) for index in range(129)]
        with patch('tools.video_frame_repairs.np.asarray', side_effect=AssertionError('pixels read before size guard')):
            with self.assertRaisesRegex(ValueError, '128 MiB'):
                VideoFrameRepairs([0, 0, 512, 512], mask, 129, list(range(129)), records, (512, 512))
        operation = VideoFrameRepairs([0, 0, 512, 512], mask, 128, list(range(128)), records[:128], (512, 512))
        self.assertEqual(operation.proof()['total_patch_bytes'], 128 * 1024 * 1024)

    def test_apply_checks_canvas_mode_and_index_even_when_inactive(self):
        args, frames = self.fixture()
        operation = VideoFrameRepairs(**args)
        for index in (-1, 4, True, 0.0, None, float('nan'), float('inf')):
            with self.subTest(index=index), self.assertRaises(ValueError):
                operation.apply(frames[0], index)
        for image in (None, np.asarray(frames[0]), frames[0].convert('RGBA'), frames[0].convert('L'),
                      Image.new('RGB', (25, 18)), Image.new('RGB', (24, 17))):
            for index in (0, 1):
                with self.subTest(image=repr(image)[:60], index=index), self.assertRaises(ValueError):
                    operation.apply(image, index)


if __name__ == '__main__':
    unittest.main()
