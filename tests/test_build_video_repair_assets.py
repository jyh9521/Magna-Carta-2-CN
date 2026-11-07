"""Self-authored fine-detail frames and source-locked repair-asset publication."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from tools import build_video_repair_assets as compiler
from tools.video_frame_repairs import VideoFrameRepairs
from tools.bink_audio import inspect
from test_bink_audio import fixture


def digest(data):
    return hashlib.sha256(data).hexdigest()


class RepairAssetTests(unittest.TestCase):
    def frames(self):
        yy, xx = np.indices((6, 8))
        frames = []
        for n in range(2):
            rgb = np.stack(((xx * 37 + n * 19) % 256,
                            (yy * 43 + n * 11) % 256,
                            ((xx + yy) * 29 + n * 7) % 256), axis=2).astype('uint8')
            frames.append(Image.fromarray(rgb))
        return frames

    def case(self):
        truth = self.frames()
        source = [f.copy() for f in truth]
        source[1].paste((250, 225, 200), (3, 2, 5, 4))
        mask = np.zeros((4, 4), bool)
        mask[1:3, 1:3] = True
        kwargs = dict(canvas=(8, 6), frame_count=2, rect=[2, 1, 4, 4],
                      crop=[1, 0, 6, 6], mask=mask,
                      reconstructions={1: truth[1].crop((1, 0, 7, 6))})
        return truth, source, kwargs

    def test_sparse_asset_restores_native_detail_without_touching_other_bytes(self):
        truth, source, kwargs = self.case()
        before = [f.tobytes() for f in source]
        reconstruction = kwargs['reconstructions'][1].tobytes()
        records, proof = compiler.compile_frames(iter(source), **kwargs)
        operation = VideoFrameRepairs(kwargs['rect'], kwargs['mask'], 2, [1], records, (8, 6))
        self.assertEqual(operation.apply(source[0], 0).tobytes(), before[0])
        self.assertEqual(operation.apply(source[1], 1).tobytes(), truth[1].tobytes())
        self.assertEqual([f.tobytes() for f in source], before)
        self.assertEqual(kwargs['reconstructions'][1].tobytes(), reconstruction)
        self.assertFalse(proof['artistic_acceptance'])
        self.assertTrue(proof['outside_mask_retained'])

    def test_exact_source_crop_hash_is_not_the_reconstructed_crop_hash(self):
        _, source, kwargs = self.case()
        records, _ = compiler.compile_frames(iter(source), **kwargs)
        self.assertEqual(records[0]['source_crop_sha256'],
                         digest(source[1].crop((2, 1, 6, 5)).tobytes()))
        rgba = np.asarray(records[0]['patch'])
        self.assertFalse(rgba[~kwargs['mask']].any())
        self.assertTrue((rgba[kwargs['mask'], 3] == 255).all())

    def test_frame_mode_count_and_native_geometry_are_exact(self):
        _, source, kwargs = self.case()
        for sequence in (source[:1], source + source[:1], [source[0].convert('RGBA'), source[1]]):
            with self.subTest(sequence=len(sequence)), self.assertRaises(ValueError):
                compiler.compile_frames(iter(sequence), **kwargs)
        for key, value in [('frame_count', True), ('canvas', (9, 6)),
                           ('rect', [2, 1, True, 4]), ('crop', [3, 0, 4, 6])]:
            bad = dict(kwargs, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                compiler.compile_frames(iter(source), **bad)

    def test_masks_indices_and_reconstruction_formats_fail_before_iteration(self):
        _, source, kwargs = self.case()
        cases = [dict(kwargs, mask=np.ones((4, 4), bool)),
                 dict(kwargs, mask=np.zeros((4, 4), bool)),
                 dict(kwargs, mask=kwargs['mask'].astype('uint8')),
                 dict(kwargs, reconstructions={True: kwargs['reconstructions'][1]}),
                 dict(kwargs, reconstructions={2: kwargs['reconstructions'][1]}),
                 dict(kwargs, reconstructions={1: kwargs['reconstructions'][1].convert('RGBA')}),
                 dict(kwargs, reconstructions={1: Image.new('RGB', (5, 6))})]
        for bad in cases:
            with self.subTest(keys=bad.keys()), self.assertRaises(ValueError):
                compiler.compile_frames(iter(source), **bad)

    def publication(self, root):
        truth, source, kwargs = self.case()
        movie = fixture()
        (root / 'source.bik').write_bytes(movie)
        (root / 'ffmpeg.exe').write_bytes(b'authored-test-tool')
        Image.fromarray(kwargs['mask'].astype('uint8') * 255).save(root / 'mask.png')
        kwargs['reconstructions'][1].save(root / 'reconstruction.png')
        ref = lambda name: dict(path=name, sha256=digest((root / name).read_bytes()))
        spec = dict(schema_version=1, kind='video-repair-assets-input-v1',
                    source=dict(path='source.bik', sha256=digest(movie), size=len(movie),
                                header=inspect(movie)['header']), rect=kwargs['rect'], crop=kwargs['crop'],
                    mask=dict(**ref('mask.png'), pixels_sha256=digest(kwargs['mask'].tobytes())),
                    records=[dict(index=1, **ref('reconstruction.png'))])
        return source, spec

    def test_hash_guarded_publication_reopens_sparse_png_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source, spec = self.publication(root)
            with patch.object(compiler, 'decoded_frames', return_value=iter(f.tobytes() for f in source)):
                report = compiler.build(spec, root, root / 'assets', root / 'ffmpeg.exe',
                                        digest(b'authored-test-tool'))
            manifest = json.loads((root / 'assets/frame-repairs.json').read_bytes())
            record = manifest['records'][0]
            self.assertEqual(record['patch']['sha256'], digest((root / record['patch']['path']).read_bytes()))
            self.assertEqual(report['proof']['record_count'], 1)
            self.assertEqual((root / 'source.bik').read_bytes(), fixture())
            self.assertFalse(report['artistic_acceptance'])

    def test_mismatch_duplicate_traversal_and_changed_inputs_publish_no_assets(self):
        for change in ['hash', 'duplicate', 'traversal', 'mask-pixels', 'changed-reconstruction']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                source, spec = self.publication(root)
                if change == 'hash':
                    spec['source']['sha256'] = '0' * 64
                elif change == 'duplicate':
                    spec['records'] *= 2
                elif change == 'traversal':
                    spec['records'][0]['path'] = '../reconstruction.png'
                elif change == 'mask-pixels':
                    spec['mask']['pixels_sha256'] = '0' * 64
                def stream(*args):
                    if change == 'changed-reconstruction':
                        (root / 'reconstruction.png').write_bytes(b'changed during source decoding')
                    yield from (f.tobytes() for f in source)
                with patch.object(compiler, 'decoded_frames', side_effect=stream), self.assertRaises(ValueError):
                    compiler.build(spec, root, root / 'assets', root / 'ffmpeg.exe', digest(b'authored-test-tool'))
                self.assertFalse((root / 'assets').exists())


if __name__ == '__main__':
    unittest.main()
