"""Offline caption contracts using synthetic BIK bytes and self-authored glyphs.

No game assets, installed platform fonts, video decoder, or encoder are used.
Run with unittest discovery, as with the other repository fixture tests.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageFont

from tools.video_caption import (
    bink_header,
    preserve_timing,
    render_layer,
    restore_source_ink,
    wrap_text,
)
from test_texture_render_windows import owned_font


def bink_fixture(*, payloads=(b'ABCD', b'123456'), width=8, height=6,
                 numerator=30000, denominator=1001, keyframes=True):
    """Structurally valid Bink-i container; payloads are deliberately not video."""
    frames = len(payloads)
    first = 44 + 4 * (frames + 1)
    offsets = [first]
    for payload in payloads:
        if not payload or len(payload) % 2:
            raise ValueError('Fixture frames must be nonempty and even-sized')
        offsets.append(offsets[-1] + len(payload))
    size = offsets[-1]
    result = b'BIKi' + struct.pack(
        '<10I', size - 8, frames, max(map(len, payloads)), frames,
        width, height, numerator, denominator, 0, 0,
    )
    table = [value | (int(keyframes) if i < frames else 0)
             for i, value in enumerate(offsets)]
    return result + struct.pack('<' + 'I' * len(table), *table) + b''.join(payloads)


def field(data, offset, value):
    result = bytearray(data)
    struct.pack_into('<I', result, offset, value)
    return bytes(result)


class BinkHeaderTests(unittest.TestCase):
    def test_synthetic_container_and_keyframe_bits_are_read_without_decoding(self):
        expected = dict(width=8, height=6, frames=2, numerator=30000,
                        denominator=1001, magic='BIKi', audio_tracks=0)
        self.assertEqual(bink_header(bink_fixture()), expected)
        self.assertEqual(bink_header(bink_fixture(keyframes=False)), expected)

    def test_bad_magic_and_short_header_are_rejected(self):
        good = bink_fixture()
        for data in (b'', good[:43], good[:47], b'BIKj' + good[4:],
                     b'BIKf' + good[4:], b'BK2i' + good[4:]):
            with self.subTest(prefix=data[:4], size=len(data)), self.assertRaises(ValueError):
                bink_header(data)

    def test_size_frame_count_and_repeated_count_must_agree(self):
        good = bink_fixture()
        for data in (field(good, 4, len(good) - 7),
                     field(good, 4, len(good) - 9), good[:-2],
                     field(good, 8, 0), field(good, 8, 601),
                     field(good, 16, 1)):
            with self.subTest(header=data[:20]), self.assertRaises(ValueError):
                bink_header(data)

    def test_frame_count_upper_bound_accepts_600_and_rejects_601(self):
        self.assertEqual(bink_header(bink_fixture(payloads=(b'xx',) * 600))['frames'], 600)
        with self.assertRaises(ValueError):
            bink_header(bink_fixture(payloads=(b'xx',) * 601))

    def test_invalid_dimensions_rates_audio_tracks_and_flags_are_rejected(self):
        good = bink_fixture()
        cases = [(20, 0), (20, 1921), (24, 0), (24, 1081),
                 (28, 0), (32, 0), (36, 1), (36, 0x10000000),
                 (40, 1), (40, 2)]
        for offset, value in cases:
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                bink_header(field(good, offset, value))

    def test_frame_table_and_largest_frame_are_guarded(self):
        good = bink_fixture()
        # Table starts at 44; actual frame offsets are 56, 60, 66.
        cases = [field(good, 44, 54), field(good, 48, 56),
                 field(good, 48, 54), field(good, 52, 64),
                 field(good, 52, 68), field(good, 12, 4)]
        short_table = field(field(good, 8, 10), 16, 10)
        for data in cases + [short_table]:
            with self.subTest(header=data[:56]), self.assertRaises(ValueError):
                bink_header(data)


class PreserveTimingTests(unittest.TestCase):
    def test_encoder_rounding_restores_exact_rational_and_only_timing_bytes(self):
        source = bink_fixture()
        encoded = bink_fixture(payloads=(b'efgh', b'UVWXYZ'),
                               numerator=2997, denominator=100)
        before_source, before_encoded = source[:], encoded[:]
        restored = preserve_timing(source, encoded)
        self.assertIsInstance(restored, bytes)
        self.assertEqual(struct.unpack_from('<II', restored, 28), (30000, 1001))
        self.assertEqual(restored[:28], encoded[:28])
        self.assertEqual(restored[36:], encoded[36:])
        self.assertEqual(bink_header(restored), bink_header(source))
        self.assertEqual(source, before_source)
        self.assertEqual(encoded, before_encoded)

    def test_equivalent_rate_and_already_exact_rate_are_idempotent(self):
        source = bink_fixture()
        doubled = bink_fixture(numerator=60000, denominator=2002)
        self.assertEqual(preserve_timing(source, doubled), source)
        self.assertEqual(preserve_timing(source, source), source)

    def test_changed_frame_count_or_canvas_is_rejected(self):
        source = bink_fixture()
        for encoded in (bink_fixture(width=9), bink_fixture(height=7),
                        bink_fixture(payloads=(b'ab',)),
                        bink_fixture(payloads=(b'ab', b'cd', b'ef'))):
            with self.subTest(header=bink_header(encoded)), self.assertRaises(ValueError):
                preserve_timing(source, encoded)

    def test_rate_difference_is_bounded_in_both_directions(self):
        source = bink_fixture(numerator=100000, denominator=10000)
        for rate in (99991, 100009):
            restored = preserve_timing(source, bink_fixture(numerator=rate, denominator=10000))
            self.assertEqual(struct.unpack_from('<II', restored, 28), (100000, 10000))
        for rate in (99989, 100011, 50000, 200000):
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                preserve_timing(source, bink_fixture(numerator=rate, denominator=10000))

    def test_invalid_source_and_encoded_headers_are_both_rejected(self):
        good = bink_fixture()
        for bad in (b'bad', field(good, 36, 1), field(good, 40, 1)):
            for source, encoded in ((bad, good), (good, bad)):
                with self.subTest(source=source[:4], encoded=encoded[:4]), self.assertRaises(ValueError):
                    preserve_timing(source, encoded)


class WrapTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Self-authored A/B font has a fixed 750-unit advance for every glyph,
        # including .notdef. These tests concern break placement, not coverage.
        cls.font = ImageFont.truetype(io.BytesIO(owned_font()), 16)
        cls.advance = 12

    def assert_break_contract(self, source, width):
        lines = wrap_text(source, self.font, width)
        self.assertEqual(''.join(lines), source.replace('\n', ''))
        for line in lines:
            self.assertLessEqual(self.font.getlength(line), width)
            if line:
                self.assertNotIn(line[0], '，。！？；：、）】》」』”’…,.!?;:)]}')
                self.assertNotIn(line[-1], '（【《「『“‘([{')
        return lines

    def test_measured_width_wraps_without_losing_characters(self):
        self.assertEqual(wrap_text('ABABAB', self.font, 24), ['AB', 'AB', 'AB'])
        self.assertEqual(wrap_text('AB', self.font, 24), ['AB'])

    def test_explicit_line_break_is_not_joined_or_reflowed_away(self):
        self.assertEqual(wrap_text('AB\nA', self.font, 120), ['AB', 'A'])
        self.assertEqual(wrap_text('ABAB\nBA', self.font, 24), ['AB', 'AB', 'BA'])

    def test_explicit_blank_line_preserves_vertical_spacing(self):
        self.assertEqual(wrap_text('AB\n\nA', self.font, 120), ['AB', '', 'A'])

    def test_single_closing_mark_moves_with_preceding_character(self):
        for mark in '，。！？；：、）】》」』”’…,.!?;:)]}':
            with self.subTest(mark=mark):
                self.assert_break_contract('AB' + mark + 'A', 24)

    def test_consecutive_closing_marks_do_not_begin_a_new_line(self):
        for marks in (',!', '，。', '。”', '！）'):
            with self.subTest(marks=marks):
                self.assert_break_contract('AB' + marks + 'A', 36)

    def test_unbreakable_closing_cluster_is_rejected_not_put_at_line_start(self):
        with self.assertRaises(ValueError):
            wrap_text('A，。', self.font, 24)

    def test_opening_marks_move_with_following_text(self):
        self.assertEqual(self.assert_break_contract('A(B', 24), ['A', '(B'])
        self.assertEqual(self.assert_break_contract('A((B', 36), ['A', '((B'])

    def test_single_character_wider_than_budget_is_rejected(self):
        for width in (0, -1, 11):
            with self.subTest(width=width), self.assertRaises(ValueError):
                wrap_text('A', self.font, width)


class RenderLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.font_bytes = owned_font()

    def style(self, **changes):
        result = dict(
            font_size=20, rect=[12, 10, 96, 48], align='left', line_height=20,
            gradient=[[0, [255, 32, 16, 255]], [1000, [16, 64, 255, 255]]],
            outline=[0, 0, 0, 0], outline_width=0,
            shadow=[0, 0, 0, 0], shadow_offset=[0, 0], shadow_radius=0,
            glow=[0, 0, 0, 0], glow_radius=0,
            inner_edge=[255, 255, 255, 0], inner_edge_width=0, weight=0,
        )
        result.update(changes)
        return result

    def test_real_pixels_and_report_honor_all_three_alignments(self):
        for align, expected_left in (('left', 12), ('center', 45), ('right', 78)):
            with self.subTest(align=align):
                style = self.style(align=align)
                frozen = copy.deepcopy(style)
                image, proof = render_layer('AB', self.font_bytes, (128, 72), style)
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(image.size, (128, 72))
                self.assertEqual(proof['lines'], ['AB'])
                # Authored glyph: 750/1000 em advance, 700/1000 em height.
                self.assertEqual(proof['ink_boxes'], [[expected_left, 10, 30, 14]])
                self.assertIsNotNone(image.getbbox())
                self.assertEqual(proof['alpha_bbox'], image.getbbox())
                core = np.argwhere(np.array(image)[:, :, 3] > 220)
                self.assertGreaterEqual(int(core[:, 1].min()), expected_left)
                self.assertLess(int(core[:, 1].max()), expected_left + 30)
                self.assertEqual(style, frozen)

    def test_gradient_changes_actual_opaque_ink_from_red_to_blue(self):
        image, _ = render_layer('AB', self.font_bytes, (128, 72), self.style())
        pixels = np.array(image)
        top = pixels[10:15, :, :][pixels[10:15, :, 3] > 220]
        bottom = pixels[20:24, :, :][pixels[20:24, :, 3] > 220]
        self.assertTrue(len(top) and len(bottom))
        self.assertGreater(float(top[:, 0].mean()), float(top[:, 2].mean()) + 80)
        self.assertGreater(float(bottom[:, 2].mean()), float(bottom[:, 0].mean()) + 80)

    def test_outline_glow_shadow_and_inner_edge_are_not_ignored(self):
        plain_style = self.style(gradient=[[0, [255] * 4], [1000, [255] * 4]])
        plain, _ = render_layer('AB', self.font_bytes, (128, 72), plain_style)
        effects = [
            ('outline', dict(outline=[0, 255, 0, 255], outline_width=1), (1, 0, 2)),
            ('glow', dict(glow=[255, 0, 0, 180], glow_radius=2), (0, 1, 2)),
            ('shadow', dict(shadow=[0, 0, 255, 255], shadow_offset=[6, 3]), (2, 0, 1)),
            ('inner_edge', dict(inner_edge=[0, 255, 0, 255], inner_edge_width=.5), (1, 0, 2)),
        ]
        for name, changes, (high, low_a, low_b) in effects:
            with self.subTest(effect=name):
                image, _ = render_layer('AB', self.font_bytes, (128, 72),
                                        {**plain_style, **changes})
                self.assertNotEqual(image.tobytes(), plain.tobytes())
                pixels = np.array(image)
                distinctive = ((pixels[:, :, high] > 180)
                               & (pixels[:, :, low_a] < 100)
                               & (pixels[:, :, low_b] < 100)
                               & (pixels[:, :, 3] > 25))
                self.assertTrue(distinctive.any())

    def test_explicit_lines_keep_requested_vertical_advance(self):
        image, proof = render_layer('A\nB', self.font_bytes, (128, 72), self.style())
        self.assertEqual(proof['lines'], ['A', 'B'])
        self.assertEqual([box[1] for box in proof['ink_boxes']], [10, 30])
        self.assertGreater(np.array(image)[30:44, :, 3].max(), 220)

    def test_explicit_blank_line_consumes_space_and_can_overflow(self):
        with self.assertRaises(ValueError):
            render_layer('A\n\nB', self.font_bytes, (128, 72),
                         self.style(rect=[12, 10, 96, 40]))

    def test_invalid_alignment_and_rect_outside_canvas_are_rejected(self):
        cases = [dict(align='justify'), dict(rect=[-1, 10, 96, 48]),
                 dict(rect=[12, -1, 96, 48]), dict(rect=[120, 10, 16, 48]),
                 dict(rect=[12, 65, 96, 10]), dict(rect=[12, 10, 0, 48]),
                 dict(rect=[12, 10, 96, 0]), dict(rect=[12, 10, -1, 48])]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                render_layer('AB', self.font_bytes, (128, 72), self.style(**changes))

    def test_width_and_height_overflow_fail_instead_of_clipping(self):
        for text, rect in [('A', [12, 10, 1, 48]),
                           ('A', [12, 10, 96, 1]),
                           ('A\nB', [12, 10, 96, 20]),
                           ('ABABAB', [12, 10, 30, 20])]:
            with self.subTest(text=text, rect=rect), self.assertRaises(ValueError):
                render_layer(text, self.font_bytes, (128, 72), self.style(rect=rect))

    def test_gradient_requires_both_normalized_endpoints(self):
        for gradient in ([[1, [255] * 4], [1000, [255] * 4]],
                         [[0, [255] * 4], [999, [255] * 4]]):
            with self.subTest(gradient=gradient), self.assertRaises(ValueError):
                render_layer('AB', self.font_bytes, (128, 72), self.style(gradient=gradient))


class RestoreSourceInkTests(unittest.TestCase):
    def fixture(self):
        y, x = np.indices((12, 16))
        pixels = np.stack((20 + x + y, 65 + y * 2, 120 + x * 2), axis=2).astype('uint8')
        pixels[5, 7] = [245, 245, 245]
        # Bright but colored, exactly at the excluded 45-level chroma spread.
        pixels[7, 9] = [255, 210, 210]
        return Image.fromarray(pixels), [4, 3, 8, 6]

    def assert_outside_mask_unchanged(self, original, repaired, rect, mask):
        x, y, w, h = rect
        global_mask = np.zeros((original.height, original.width), bool)
        global_mask[y:y+h, x:x+w] = mask
        before = np.array(original)
        after = np.array(repaired)
        self.assertTrue(np.array_equal(after[~global_mask], before[~global_mask]))
        changed = np.any(after != before, axis=2)
        self.assertFalse((changed & ~global_mask).any())

    def test_repair_changes_only_dilated_ink_and_does_not_mutate_source(self):
        frame, rect = self.fixture()
        before = frame.tobytes()
        repaired, mask = restore_source_ink(frame, rect, 200, 1)
        expected = np.zeros((6, 8), bool)
        expected[1:4, 2:5] = True
        self.assertTrue(np.array_equal(mask, expected))
        self.assertEqual(repaired.mode, 'RGB')
        self.assertEqual(repaired.size, frame.size)
        self.assertEqual(frame.tobytes(), before)
        self.assertNotEqual(repaired.getpixel((7, 5)), (245, 245, 245))
        self.assertEqual(repaired.getpixel((9, 7)), (255, 210, 210))
        self.assert_outside_mask_unchanged(frame, repaired, rect, mask)

    def test_empty_ink_mask_is_a_byte_identical_copy(self):
        frame = Image.new('RGB', (8, 6), (30, 60, 100))
        repaired, mask = restore_source_ink(frame, [1, 1, 6, 4], 200, 1)
        self.assertFalse(mask.any())
        self.assertEqual(repaired.tobytes(), frame.tobytes())
        self.assertIsNot(repaired, frame)

    def test_uniform_exterior_reconstructs_uniform_hole(self):
        frame = Image.new('RGB', (9, 7), (20, 20, 20))
        for y in range(2, 5):
            for x in range(3, 6):
                frame.putpixel((x, y), (240, 240, 240))
        repaired, mask = restore_source_ink(frame, [0, 0, 9, 7], 225, 0)
        self.assertEqual(int(mask.sum()), 9)
        self.assertEqual(repaired.tobytes(), Image.new('RGB', (9, 7), (20, 20, 20)).tobytes())

    def test_threshold_is_inclusive_and_row_thresholds_are_respected(self):
        frame = Image.new('RGB', (8, 6), (20, 20, 20))
        frame.putpixel((3, 1), (220, 220, 220))
        frame.putpixel((3, 4), (220, 220, 220))
        repaired, mask = restore_source_ink(frame, [0, 0, 8, 6], [240, 240, 240, 220, 220, 220], 0)
        self.assertFalse(mask[1, 3])
        self.assertTrue(mask[4, 3])
        self.assertEqual(int(mask.sum()), 1)
        self.assertEqual(repaired.getpixel((3, 1)), (220, 220, 220))
        self.assert_outside_mask_unchanged(frame, repaired, [0, 0, 8, 6], mask)

    def test_threshold_vector_height_mismatch_is_rejected(self):
        frame, rect = self.fixture()
        with self.assertRaises(ValueError):
            restore_source_ink(frame, rect, [200] * 5, 0)

    def test_mask_without_known_exterior_is_rejected(self):
        frame = Image.new('RGB', (8, 6), (240, 240, 240))
        with self.assertRaises(ValueError):
            restore_source_ink(frame, [0, 0, 8, 6], 225, 0)

    def test_out_of_frame_repair_rectangles_are_rejected_not_padded(self):
        frame, _ = self.fixture()
        for rect in ([-1, 1, 8, 6], [1, -1, 8, 6], [12, 1, 8, 6],
                     [1, 9, 8, 6], [0, 0, 17, 12], [0, 0, 16, 13]):
            with self.subTest(rect=rect), self.assertRaises(ValueError):
                restore_source_ink(frame, rect, 225, 0)

    def test_reconstruction_does_not_sample_opposite_crop_edge(self):
        # Each white edge pixel has three real dark neighbors (20). The far
        # edge (200) is not a fourth neighbor: wrapping would incorrectly give
        # (20+20+20+200)/4 = 65 instead of the bounded average 20.
        for seed, opposite in (((0, 3), (8, 3)), ((4, 0), (4, 6))):
            with self.subTest(seed=seed):
                frame = Image.new('RGB', (9, 7), (20, 20, 20))
                frame.putpixel(seed, (240, 240, 240))
                frame.putpixel(opposite, (200, 200, 200))
                repaired, mask = restore_source_ink(frame, [0, 0, 9, 7], 225, 0)
                self.assertEqual(int(mask.sum()), 1)
                self.assertEqual(repaired.getpixel(seed), (20, 20, 20))
                self.assertEqual(repaired.getpixel(opposite), (200, 200, 200))
                self.assert_outside_mask_unchanged(frame, repaired, [0, 0, 9, 7], mask)


class VideoBuildGuardTests(unittest.TestCase):
    def entry(self, identifier='movie_01', filename='movies/clip_01.bik'):
        return dict(id=identifier, source={'file': filename}, captions=[{}])

    def plan(self, entries=None):
        return dict(schema_version=1, kind='bink-caption-plan',
                    entries=[self.entry()] if entries is None else entries)

    def load_fixture(self, root, plan):
        from tools.build_video_captions import load_plan
        raw = plan if isinstance(plan, bytes) else json.dumps(plan).encode('utf-8')
        path = root / 'plan.json'
        path.write_bytes(raw)
        return load_plan(path, hashlib.sha256(raw).hexdigest())

    def test_canonical_member_resolves_under_explicit_root(self):
        from tools.build_video_captions import member
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assertEqual(member(root, 'movies/clip_01.bik'), root/'movies'/'clip_01.bik')

    def test_member_rejects_traversal_absolute_and_noncanonical_paths(self):
        from tools.build_video_captions import member
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            invalid = ['', None, '../clip.bik', 'movies/../clip.bik',
                       'movies\\clip.bik', './clip.bik', 'movies/./clip.bik',
                       'movies//clip.bik', 'movies/', root.as_posix() + '/clip.bik']
            for relative in invalid:
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    member(root, relative)

    def test_member_rejects_windows_drive_stream_and_normalized_aliases(self):
        from tools.build_video_captions import member
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for relative in ('C:movie.bik', 'movie.bik:stream',
                             'movie.bik.', 'movie.bik ', 'movies./clip.bik'):
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    member(root, relative)

    def test_locked_file_accepts_exact_hash_and_inclusive_size_limit(self):
        from tools.build_video_captions import locked_file
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'owned.fixture'
            raw = b'independent synthetic input'
            path.write_bytes(raw)
            self.assertEqual(locked_file(path, hashlib.sha256(raw).hexdigest(), len(raw)), raw)
            self.assertEqual(path.read_bytes(), raw)

    def test_locked_file_rejects_changed_bytes_bad_hash_empty_and_large_input(self):
        from tools.build_video_captions import locked_file
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'owned.fixture'
            original = b'synthetic'
            expected = hashlib.sha256(original).hexdigest()
            path.write_bytes(b'different')
            with self.assertRaises(ValueError):
                locked_file(path, expected)
            path.write_bytes(original)
            for bad_hash in ('0' * 64, expected.upper(), 'short'):
                with self.subTest(hash=bad_hash), self.assertRaises(ValueError):
                    locked_file(path, bad_hash)
            with self.assertRaises(ValueError):
                locked_file(path, expected, len(original) - 1)
            path.write_bytes(b'')
            with self.assertRaises(ValueError):
                locked_file(path, hashlib.sha256(b'').hexdigest())
            with self.assertRaises(ValueError):
                locked_file(Path(directory), expected)

    def test_load_plan_returns_exact_locked_bytes_without_launching_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = self.plan()
            parsed, raw = self.load_fixture(Path(directory), plan)
            self.assertEqual(parsed, plan)
            self.assertEqual(json.loads(raw), plan)

    def test_duplicate_json_keys_movie_ids_and_source_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate_key = json.dumps(self.plan()).replace(
                '"schema_version": 1', '"schema_version": 1, "schema_version": 1', 1).encode()
            cases = [duplicate_key,
                     self.plan([self.entry(), self.entry(filename='movies/clip_02.bik')]),
                     self.plan([self.entry(), self.entry(identifier='movie_02')])]
            for plan in cases:
                with self.subTest(plan=plan), self.assertRaises(ValueError):
                    self.load_fixture(root, plan)

    def test_plan_schema_and_entry_count_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = [{**self.plan(), 'schema_version': 2},
                     {**self.plan(), 'kind': 'unknown'}, self.plan([]),
                     self.plan([self.entry(f'movie_{i}', f'movies/{i}.bik') for i in range(65)])]
            for plan in cases:
                with self.subTest(plan=plan), self.assertRaises(ValueError):
                    self.load_fixture(root, plan)

    def test_movie_identifiers_and_caption_count_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for identifier in ('', 'A', 'a/b', 'a b', 'a' * 65):
                with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                    self.load_fixture(root, self.plan([self.entry(identifier)]))
            for captions in ([], [{}] * 9):
                entry = self.entry()
                entry['captions'] = captions
                with self.subTest(captions=len(captions)), self.assertRaises(ValueError):
                    self.load_fixture(root, self.plan([entry]))

    def test_plan_hash_is_checked_before_json_is_accepted(self):
        from tools.build_video_captions import load_plan
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'plan.json'
            raw = json.dumps(self.plan()).encode()
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                load_plan(path, '0' * 64)

    def test_composite_preserves_pixels_outside_declared_support(self):
        from tools.build_video_captions import composite
        frame = Image.new('RGB', (9, 7), (20, 20, 20))
        frame.putpixel((4, 3), (240, 240, 240))
        before = frame.tobytes()
        mask = np.zeros((3, 3), bool)
        mask[1, 1] = True
        layer = Image.new('RGBA', (9, 7), (0, 0, 0, 0))
        layer.putpixel((6, 2), (200, 50, 30, 255))
        changed = np.zeros((7, 9), bool)
        changed[3, 4] = changed[2, 6] = True
        result = composite(frame, [([3, 2, 3, 3], mask)], layer, changed)
        self.assertEqual(frame.tobytes(), before)
        self.assertEqual(result.getpixel((4, 3)), (20, 20, 20))
        self.assertEqual(result.getpixel((6, 2)), (200, 50, 30))
        self.assertTrue(np.array_equal(np.array(result)[~changed], np.array(frame)[~changed]))

    def test_composite_detects_underdeclared_change_support(self):
        from tools.build_video_captions import composite
        frame = Image.new('RGB', (9, 7), (20, 20, 20))
        layer = Image.new('RGBA', (9, 7), (0, 0, 0, 0))
        layer.putpixel((6, 2), (200, 50, 30, 255))
        with self.assertRaises(ValueError):
            composite(frame, [], layer, np.zeros((7, 9), bool))


if __name__ == '__main__':
    unittest.main()
