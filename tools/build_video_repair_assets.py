"""Freeze reviewed temporal reconstructions as small, source-guarded RGBA patches.

Inference is deliberately separate. A clean checkout rebuilds captions from the
versioned sparse patches, without a neural runtime or complete original frames.
This compiler verifies provenance and byte scope, not artistic acceptance.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .build_video_captions import locked_file, member, encoded
from .verify_resource_phase import hash_value, unique
from .video_caption import decoded_frames, sha
from .video_frame_repairs import VideoFrameRepairs, MAX_PATCH_BYTES

MAX_RECONSTRUCTION_BYTES = 256 * 1024 * 1024


def geometry(canvas, rect, crop):
    for name, value in [('repair', rect), ('reconstruction', crop)]:
        if (not isinstance(value, list) or len(value) != 4
                or any(type(v) is not int for v in value)
                or min(value[:2]) < 0 or min(value[2:]) < 1
                or value[0] + value[2] > canvas[0]
                or value[1] + value[3] > canvas[1]):
            raise ValueError(name + ' rectangle outside native canvas')
    x, y, w, h = rect
    cx, cy, cw, ch = crop
    if x < cx or y < cy or x + w > cx + cw or y + h > cy + ch or w * h > 256 * 1024:
        raise ValueError('Reconstruction must contain the bounded repair rectangle')


def compile_frames(frames, *, canvas, frame_count, rect, crop, mask,
                   reconstructions):
    """Compile exact owned pixels; all input images remain unchanged.

    ``frames`` yields original RGB PIL images in source order. Reconstruction
    images cover ``crop``; their mapping keys are absolute source frame indices.
    No colour correction, spatial filling, motion estimation or text occurs here.
    """
    if (not isinstance(canvas, tuple) or len(canvas) != 2
            or any(type(v) is not int for v in canvas)
            or not 1 <= canvas[0] <= 1920 or not 1 <= canvas[1] <= 1080
            or type(frame_count) is not int or not 1 <= frame_count <= 6144):
        raise ValueError('Bounded native canvas/frame count required')
    geometry(canvas, rect, crop)
    x, y, w, h = rect
    cx, cy, cw, ch = crop
    if (x < cx or y < cy or x + w > cx + cw or y + h > cy + ch
            or w * h > 256 * 1024
            or not isinstance(mask, np.ndarray) or mask.dtype != np.dtype('bool')
            or mask.shape != (h, w) or not mask.any() or mask.all()):
        raise ValueError('Reconstruction must contain a proper sparse repair mask')
    if (not isinstance(reconstructions, dict) or not reconstructions
            or len(reconstructions) * w * h * 4 > MAX_PATCH_BYTES
            or len(reconstructions) * cw * ch * 3 > MAX_RECONSTRUCTION_BYTES
            or any(type(n) is not int or not 0 <= n < frame_count
                   for n in reconstructions)):
        raise ValueError('Bounded unique absolute reconstruction indices required')
    for image in reconstructions.values():
        if (not isinstance(image, Image.Image) or image.mode != 'RGB' or image.size != (cw, ch)
                or getattr(image, 'n_frames', 1) != 1):
            raise ValueError('Reconstruction must be exact native RGB crop geometry')
    records = []
    count = 0
    for index, image in enumerate(frames):
        count += 1
        if (count > frame_count or not isinstance(image, Image.Image)
                or image.mode != 'RGB' or image.size != canvas):
            raise ValueError('Original frame count/mode/canvas mismatch')
        if index not in reconstructions:
            continue
        original = image.crop((x, y, x + w, y + h))
        background = reconstructions[index].crop((x - cx, y - cy, x - cx + w, y - cy + h))
        patch = np.zeros((h, w, 4), np.uint8)
        patch[mask, :3] = np.asarray(background)[mask]
        patch[mask, 3] = 255
        records.append(dict(index=index, source_crop_sha256=sha(original.tobytes()),
                            patch=Image.fromarray(patch)))
    if count != frame_count:
        raise ValueError('Original clip ended before its declared frame count')
    operation = VideoFrameRepairs(rect, mask, frame_count,
                                 sorted(reconstructions), records, canvas)
    return records, operation.proof()


def build(spec, project, output, ffmpeg, ffmpeg_sha256):
    project, output = Path(project).resolve(), Path(output).resolve()
    if (output.exists() or not output.is_relative_to(project) or output == project
            or set(spec) != {'schema_version', 'kind', 'source', 'crop', 'rect', 'mask', 'records'}
            or spec['schema_version'] != 1 or spec['kind'] != 'video-repair-assets-input-v1'):
        raise ValueError('New in-project output and explicit repair input required')
    source = spec['source']
    if set(source) != {'path', 'sha256', 'size', 'header'}:
        raise ValueError('Explicit original movie identity required')
    path = member(project, source['path'])
    if output.is_relative_to(path.parent) and path.parent == output:
        raise ValueError('Repair output overlaps original movie')
    data = locked_file(path, source['sha256'])
    if len(data) != source['size']:
        raise ValueError('Original movie size mismatch')
    from .bink_audio import inspect
    header = inspect(data)['header']
    if header != source['header']:
        raise ValueError('Original movie header mismatch')
    geometry((header['width'], header['height']), spec['rect'], spec['crop'])
    locked_file(ffmpeg, ffmpeg_sha256, 256 * 1024 * 1024)
    mask_ref = spec['mask']
    if set(mask_ref) != {'path', 'sha256', 'pixels_sha256'}:
        raise ValueError('Explicit binary repair-mask identity required')
    mask_data = locked_file(member(project, mask_ref['path']), mask_ref['sha256'], 1024 * 1024)
    with Image.open(io.BytesIO(mask_data)) as image:
        if (image.format != 'PNG' or image.mode != 'L' or image.size != tuple(spec['rect'][2:])
                or getattr(image, 'n_frames', 1) != 1):
            raise ValueError('Repair mask PNG geometry/mode mismatch')
        values = np.asarray(image)
        if not np.isin(values, [0, 255]).all():
            raise ValueError('Repair mask PNG must be binary')
        mask = values > 0
    if sha(mask.tobytes()) != hash_value(mask_ref['pixels_sha256']):
        raise ValueError('Repair mask pixels mismatch')
    rows = spec['records']
    if (not isinstance(rows, list) or not rows or len(rows) > header['frames']
            or len(rows) * spec['rect'][2] * spec['rect'][3] * 4 > MAX_PATCH_BYTES
            or len(rows) * spec['crop'][2] * spec['crop'][3] * 3 > MAX_RECONSTRUCTION_BYTES):
        raise ValueError('Repair reconstruction storage bound')
    reconstructions, inputs = {}, []
    for row in rows:
        if set(row) != {'index', 'path', 'sha256'}:
            raise ValueError('Unknown reconstruction record fields')
        index = row['index']
        if type(index) is not int or not 0 <= index < header['frames'] or index in reconstructions:
            raise ValueError('Duplicate or invalid source frame index')
        input_path = member(project, row['path'])
        if input_path.is_relative_to(output):
            raise ValueError('Reconstruction input overlaps output')
        raw = locked_file(input_path, row['sha256'], 16 * 1024 * 1024)
        with Image.open(io.BytesIO(raw)) as image:
            if (image.format != 'PNG' or image.mode != 'RGB' or image.size != tuple(spec['crop'][2:])
                    or getattr(image, 'n_frames', 1) != 1):
                raise ValueError('Reconstruction PNG geometry/mode mismatch')
            reconstructions[index] = image.copy()
        inputs.append((input_path, row['sha256']))
    frames = (Image.frombytes('RGB', (header['width'], header['height']), raw)
              for raw in decoded_frames(ffmpeg, path, header))
    records, proof = compile_frames(frames, canvas=(header['width'], header['height']),
        frame_count=header['frames'], rect=spec['rect'], crop=spec['crop'],
        mask=mask, reconstructions=reconstructions)
    # Recheck all inputs before publishing even the first sparse asset.
    if path.read_bytes() != data:
        raise ValueError('Original movie changed during repair compilation')
    locked_file(member(project, mask_ref['path']), mask_ref['sha256'], 1024 * 1024)
    for input_path, digest in inputs:
        locked_file(input_path, digest, 16 * 1024 * 1024)
    locked_file(ffmpeg, ffmpeg_sha256, 256 * 1024 * 1024)
    output.mkdir(parents=True)
    published = []
    for row in records:
        target = output / (str(row['index']).zfill(4) + '.png')
        buffer = io.BytesIO()
        row['patch'].save(buffer, format='PNG')
        raw = buffer.getvalue()
        with target.open('xb') as stream:
            stream.write(raw)
        if target.read_bytes() != raw:
            raise ValueError('Sparse repair asset reopening mismatch')
        published.append(dict(index=row['index'], source_crop_sha256=row['source_crop_sha256'],
            patch=dict(path=target.relative_to(project).as_posix(), sha256=sha(raw))))
    for row in published:
        locked_file(member(project, row['patch']['path']), row['patch']['sha256'],
                    spec['rect'][2] * spec['rect'][3] * 4 + 64 * 1024)
    if path.read_bytes() != data:
        raise ValueError('Original movie changed before asset publication')
    locked_file(member(project, mask_ref['path']), mask_ref['sha256'], 1024 * 1024)
    for input_path, digest in inputs:
        locked_file(input_path, digest, 16 * 1024 * 1024)
    locked_file(ffmpeg, ffmpeg_sha256, 256 * 1024 * 1024)
    manifest = dict(method='sparse-frame-rgba-v1', records=published)
    report = dict(source=source, crop=spec['crop'], rect=spec['rect'],
                  mask=mask_ref, proof=proof, artistic_acceptance=False)
    for name, value in [('frame-repairs.json', manifest), ('COMPILATION.json', report)]:
        raw = encoded(value)
        with (output / name).open('xb') as stream:
            stream.write(raw)
        if (output / name).read_bytes() != raw:
            raise ValueError('Repair compilation report reopening mismatch')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--input-sha256', required=True)
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--ffmpeg', required=True, type=Path)
    parser.add_argument('--ffmpeg-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        spec = json.loads(locked_file(args.input, args.input_sha256, 8 * 1024 * 1024), object_pairs_hook=unique)
        result = build(spec, args.project_root, args.output_dir, args.ffmpeg, args.ffmpeg_sha256)
        print('SPARSE_FRAME_PATCHES=' + str(result['proof']['record_count']) + ' RESULT=PASS')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('ERROR: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
