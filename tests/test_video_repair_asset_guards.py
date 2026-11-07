"""Adversarial authoring-asset guards using tiny, self-authored fixtures."""
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from tools import build_video_repair_assets as compiler
from tools.bink_audio import inspect
from test_bink_audio import fixture as bink_fixture


def digest(data):
    return hashlib.sha256(data).hexdigest()


class VideoRepairAssetGuardTests(unittest.TestCase):
    def fixture(self, root):
        yy, xx = np.indices((6, 8))
        frames = []
        for index in range(2):
            rgb = np.stack(((xx * 31 + index * 17) % 256,
                            (yy * 43 + index * 23) % 256,
                            ((xx + yy) * 29 + index * 11) % 256), axis=2).astype('uint8')
            frames.append(Image.fromarray(rgb))
            Image.fromarray(rgb).save(root / f'reconstruction-{index}.png')
        mask = np.zeros((4, 4), dtype=bool)
        mask[1:3, 1:3] = True
        Image.fromarray(mask.astype('uint8') * 255).save(root / 'mask.png')
        movie = bink_fixture()
        (root / 'source.bik').write_bytes(movie)
        (root / 'ffmpeg.exe').write_bytes(b'authored-test-tool')
        reference = lambda name: dict(path=name, sha256=digest((root / name).read_bytes()))
        spec = dict(schema_version=1, kind='video-repair-assets-input-v1',
                    source=dict(path='source.bik', sha256=digest(movie), size=len(movie),
                                header=inspect(movie)['header']),
                    rect=[2, 1, 4, 4], crop=[0, 0, 8, 6],
                    mask=dict(**reference('mask.png'), pixels_sha256=digest(mask.tobytes())),
                    records=[dict(index=n, **reference(f'reconstruction-{n}.png')) for n in range(2)])
        return frames, mask, spec

    def build(self, root, frames, spec):
        with patch.object(compiler, 'decoded_frames',
                          return_value=iter(image.tobytes() for image in frames)):
            return compiler.build(spec, root, root / 'assets', root / 'ffmpeg.exe',
                                  digest(b'authored-test-tool'))

    def assert_no_manifest(self, root):
        self.assertFalse((root / 'assets/frame-repairs.json').exists())
        self.assertFalse((root / 'assets/COMPILATION.json').exists())

    def test_animated_mask_rejects_before_original_decode_or_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames, _, spec = self.fixture(root)
            path = root / 'mask.png'
            with Image.open(path) as image:
                first = image.copy()
            second = Image.fromarray(255 - np.asarray(first))
            first.save(path, format='PNG', save_all=True, append_images=[second], duration=100, loop=0)
            spec['mask']['sha256'] = digest(path.read_bytes())
            with Image.open(path) as image:
                self.assertEqual(image.n_frames, 2)
            with (patch.object(compiler, 'decoded_frames', side_effect=AssertionError('decoder called')),
                  self.assertRaisesRegex(ValueError, 'mask PNG')):
                compiler.build(spec, root, root / 'assets', root / 'ffmpeg.exe', digest(b'authored-test-tool'))
            self.assertFalse((root / 'assets').exists())

    def test_animated_reconstruction_rejects_before_original_decode_or_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, spec = self.fixture(root)
            path = root / 'reconstruction-0.png'
            with Image.open(path) as image:
                first = image.copy()
            first.save(path, format='PNG', save_all=True,
                       append_images=[Image.new('RGB', first.size, (250, 1, 2))], duration=100, loop=0)
            spec['records'][0]['sha256'] = digest(path.read_bytes())
            with Image.open(path) as image:
                self.assertEqual(image.mode, 'RGB')
                self.assertEqual(image.n_frames, 2)
            with (patch.object(compiler, 'decoded_frames', side_effect=AssertionError('decoder called')),
                  self.assertRaisesRegex(ValueError, 'Reconstruction PNG')):
                compiler.build(spec, root, root / 'assets', root / 'ffmpeg.exe', digest(b'authored-test-tool'))
            self.assertFalse((root / 'assets').exists())

    def test_direct_compiler_rejects_animated_reconstruction_before_iteration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, mask, spec = self.fixture(root)
            path = root / 'animated.png'
            Image.new('RGB', (8, 6)).save(path, save_all=True,
                append_images=[Image.new('RGB', (8, 6), (255, 0, 0))], duration=100, loop=0)
            def forbidden_frames():
                raise AssertionError('source iterator consumed')
                yield
            with Image.open(path) as image, self.assertRaisesRegex(ValueError, 'Reconstruction'):
                compiler.compile_frames(forbidden_frames(), canvas=(8, 6), frame_count=2,
                    rect=spec['rect'], crop=spec['crop'], mask=mask, reconstructions={0: image})

    def test_late_earlier_asset_mutation_rejects_before_manifest_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames, _, spec = self.fixture(root)
            original_save = Image.Image.save
            saves = []
            def mutate_earlier(image, target, *args, **kwargs):
                result = original_save(image, target, *args, **kwargs)
                if image.mode == 'RGBA':
                    saves.append(1)
                    if len(saves) == 2:
                        (root / 'assets/0000.png').write_bytes(b'changed after its immediate reopening')
                return result
            with (patch.object(Image.Image, 'save', mutate_earlier),
                  self.assertRaisesRegex(ValueError, 'SHA256 mismatch')):
                self.build(root, frames, spec)
            self.assertEqual(len(saves), 2)
            self.assert_no_manifest(root)
            self.assertEqual(digest((root / 'source.bik').read_bytes()), spec['source']['sha256'])

    def check_late_link(self, kind):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames, _, spec = self.fixture(root)
            sentinel = root / 'authored-sentinel.bin'
            before = b'authored sentinel must not be truncated by output publication'
            sentinel.write_bytes(before)
            if kind == 'symlink':
                probe = root / 'capability-probe'
                try:
                    probe.symlink_to(sentinel)
                except OSError:
                    self.skipTest('Host does not permit an authored test symlink')
                probe.unlink()
            original_save = Image.Image.save
            injected = []
            def insert_link(image, target, *args, **kwargs):
                result = original_save(image, target, *args, **kwargs)
                if image.mode == 'RGBA' and not injected:
                    path = root / 'assets/0000.png'
                    if kind == 'symlink':
                        path.symlink_to(sentinel)
                    else:
                        os.link(sentinel, path)
                    injected.append(path)
                return result
            with patch.object(Image.Image, 'save', insert_link), self.assertRaises(FileExistsError):
                self.build(root, frames, spec)
            self.assertEqual(len(injected), 1)
            self.assertEqual(sentinel.read_bytes(), before)
            self.assertEqual(injected[0].read_bytes(), before)
            self.assert_no_manifest(root)

    def test_late_hardlink_target_is_not_overwritten(self):
        self.check_late_link('hardlink')

    def test_late_symlink_target_is_not_overwritten(self):
        self.check_late_link('symlink')

    def test_late_json_hardlink_targets_are_not_overwritten(self):
        for name in ('frame-repairs.json', 'COMPILATION.json'):
            with self.subTest(target=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                frames, _, spec = self.fixture(root)
                sentinel = root / 'authored-json-sentinel.bin'
                before = b'authored sentinel for an exclusive JSON publication test'
                sentinel.write_bytes(before)
                original_save = Image.Image.save
                injected = []
                def insert_link(image, target, *args, **kwargs):
                    result = original_save(image, target, *args, **kwargs)
                    if image.mode == 'RGBA' and not injected:
                        path = root / 'assets' / name
                        os.link(sentinel, path)
                        injected.append(path)
                    return result
                with patch.object(Image.Image, 'save', insert_link), self.assertRaises(FileExistsError):
                    self.build(root, frames, spec)
                self.assertEqual(len(injected), 1)
                self.assertEqual(sentinel.read_bytes(), before)
                self.assertEqual(injected[0].read_bytes(), before)

    def test_all_inputs_are_rechecked_after_sparse_png_publication(self):
        for name in ('source.bik', 'mask.png', 'reconstruction-0.png', 'ffmpeg.exe'):
            with self.subTest(input=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                frames, _, spec = self.fixture(root)
                original_save = Image.Image.save
                changed = []
                def mutate_input(image, target, *args, **kwargs):
                    result = original_save(image, target, *args, **kwargs)
                    if image.mode == 'RGBA' and not changed:
                        path = root / name
                        path.write_bytes(path.read_bytes() + b'changed after prepublication recheck')
                        changed.append(path)
                    return result
                with patch.object(Image.Image, 'save', mutate_input), self.assertRaises(ValueError):
                    self.build(root, frames, spec)
                self.assertEqual(len(changed), 1)
                self.assert_no_manifest(root)

    def test_full_crop_memory_bound_precedes_reconstruction_reads_and_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, spec = self.fixture(root)
            count = compiler.MAX_RECONSTRUCTION_BYTES // (1920 * 1080 * 3) + 1
            self.assertLessEqual(count, 6144)
            movie = bytearray(bink_fixture(videos=(b'xx',) * count, tracks=0))
            struct.pack_into('<II', movie, 20, 1920, 1080)
            (root / 'source.bik').write_bytes(movie)
            spec['source'].update(size=len(movie), sha256=digest(movie), header=inspect(movie)['header'])
            spec['crop'] = [0, 0, 1920, 1080]
            spec['records'] = [dict(spec['records'][0], index=n) for n in range(count)]
            original_locked_file = compiler.locked_file
            def forbid_reconstruction(path, *args, **kwargs):
                if Path(path).name.startswith('reconstruction-'):
                    raise AssertionError('reconstruction read before decoded-memory bound')
                return original_locked_file(path, *args, **kwargs)
            with (patch.object(compiler, 'locked_file', forbid_reconstruction),
                  patch.object(compiler, 'decoded_frames', side_effect=AssertionError('decoder called')),
                  self.assertRaisesRegex(ValueError, 'storage bound')):
                compiler.build(spec, root, root / 'assets', root / 'ffmpeg.exe', digest(b'authored-test-tool'))
            self.assertFalse((root / 'assets').exists())

    def test_direct_full_crop_memory_bound_precedes_original_iteration(self):
        count = compiler.MAX_RECONSTRUCTION_BYTES // (1920 * 1080 * 3) + 1
        image = Image.new('RGB', (1920, 1080))
        mask = np.array([[True, False]])
        def forbidden_frames():
            raise AssertionError('source iterator consumed')
            yield
        with self.assertRaisesRegex(ValueError, 'Bounded unique'):
            compiler.compile_frames(forbidden_frames(), canvas=image.size, frame_count=count,
                rect=[0, 0, 2, 1], crop=[0, 0, 1920, 1080], mask=mask,
                reconstructions=dict.fromkeys(range(count), image))


if __name__ == '__main__':
    unittest.main()
