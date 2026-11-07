"""Hash-guarded sparse, per-frame RGB replacement; no image reconstruction.

Patches are supplied by the caller. This operation proves their byte scope, not
their visual correctness or provenance. All hashes use SHA-256: source crops use
their native RGB bytes; masks use C-order boolean bytes (0/1); rectangle and
sorted active-frame lists use compact ASCII JSON without a trailing newline.
"""
from __future__ import annotations

import hashlib
import json
import re

import numpy as np
from PIL import Image


MAX_FRAMES = 6144
MAX_RECT_PIXELS = 256 * 1024
MAX_PATCH_BYTES = 128 * 1024 * 1024


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _list_sha(values):
    return _sha(json.dumps(list(values), separators=(',', ':')).encode('ascii'))


class VideoFrameRepairs:
    """Apply one explicit opaque repair on an owned mask per active frame.

    ``records`` contains exactly ``index``, ``source_crop_sha256`` and ``patch``.
    Each patch is a rectangle-sized RGBA image. Its alpha is exactly 255 on the
    common boolean mask and zero elsewhere, including hidden RGB. Input metadata,
    masks and patches are defensively copied into immutable application data.
    """

    def __init__(self, rect, mask, frame_count, active_frames, records, canvas):
        if (not isinstance(canvas, tuple) or len(canvas) != 2
                or any(type(value) is not int for value in canvas)
                or not 1 <= canvas[0] <= 1920 or not 1 <= canvas[1] <= 1080):
            raise ValueError('Frame repair canvas must be a bounded integer tuple')
        if (not isinstance(rect, (tuple, list)) or len(rect) != 4
                or any(type(value) is not int for value in rect)
                or min(rect[:2]) < 0 or min(rect[2:]) < 1
                or rect[2] * rect[3] > MAX_RECT_PIXELS
                or rect[0] + rect[2] > canvas[0]
                or rect[1] + rect[3] > canvas[1]):
            raise ValueError('Frame repair rectangle exceeds its declared scope')
        x, y, width, height = rect
        if (not isinstance(mask, np.ndarray) or mask.dtype != np.dtype('bool')
                or mask.shape != (height, width) or not mask.any() or mask.all()):
            raise ValueError('Frame repair mask must own a nonempty proper rectangle subset')
        if type(frame_count) is not int or not 1 <= frame_count <= MAX_FRAMES:
            raise ValueError('Frame repair frame count is outside the explicit bound')
        if (not isinstance(active_frames, list) or not active_frames
                or len(active_frames) > frame_count
                or any(type(index) is not int or not 0 <= index < frame_count
                       for index in active_frames)
                or len(set(active_frames)) != len(active_frames)):
            raise ValueError('Frame repair active frames must be unique bounded integers')
        active = frozenset(active_frames)
        if not isinstance(records, list) or len(records) != len(active):
            raise ValueError('Frame repair requires exactly one record per active frame')
        # Bound decoded RGBA storage before reading any supplied image pixels.
        total_patch_bytes = len(records) * width * height * 4
        if total_patch_bytes > MAX_PATCH_BYTES:
            raise ValueError('Frame repair RGBA patches exceed the 128 MiB bound')

        metadata = []
        seen = set()
        for record in records:
            if not isinstance(record, dict) or set(record) != {'index', 'source_crop_sha256', 'patch'}:
                raise ValueError('Frame repair record has unknown or missing fields')
            index = record['index']
            if type(index) is not int or index not in active or index in seen:
                raise ValueError('Frame repair record is duplicate, inactive or out of range')
            digest = record['source_crop_sha256']
            if not isinstance(digest, str) or re.fullmatch(r'[0-9a-fA-F]{64}', digest) is None:
                raise ValueError('Frame repair source crop requires a 64-hex SHA-256')
            patch = record['patch']
            if not isinstance(patch, Image.Image) or patch.mode != 'RGBA' or patch.size != (width, height):
                raise ValueError('Frame repair patch must be rectangle-sized RGBA')
            seen.add(index)
            metadata.append((index, digest.lower(), patch))
        if seen != active:
            raise ValueError('Frame repair records do not match the active frame set')

        mask_bytes = np.ascontiguousarray(mask).tobytes()
        owned_mask = np.frombuffer(mask_bytes, dtype=np.bool_).reshape(height, width)
        owned_records = {}
        for index, digest, patch in metadata:
            rgba = np.asarray(patch)
            if (not np.all(rgba[:, :, 3][owned_mask] == 255)
                    or np.any(rgba[:, :, 3][~owned_mask])
                    or np.any(rgba[:, :, :3][~owned_mask])):
                raise ValueError('Frame repair alpha/RGB must cover exactly its owned mask')
            # Only owned native byte triples are retained; no mutable PIL/array
            # references, transparent RGB, feathering or interpolation survives.
            owned_records[index] = (digest, rgba[:, :, :3][owned_mask].tobytes())

        self.rect = tuple(rect)
        self.canvas = tuple(canvas)
        self.frame_count = frame_count
        self.active_frames = tuple(sorted(active))
        self._mask_bytes = mask_bytes
        self._mask = owned_mask
        self._records = owned_records
        self._total_patch_bytes = total_patch_bytes

    @property
    def mask(self):
        """Read-only C-order mask backed by immutable bytes."""
        # A separate view also prevents a caller changing our internal shape.
        return self._mask.view()

    def apply(self, frame, index):
        """Return a fresh RGB image, failing closed on an active crop mismatch."""
        if type(index) is not int or not 0 <= index < self.frame_count:
            raise ValueError('Frame repair index is outside the declared clip')
        if not isinstance(frame, Image.Image) or frame.mode != 'RGB' or frame.size != self.canvas:
            raise ValueError('Frame repair input must exactly match its RGB canvas')
        record = self._records.get(index)
        if record is None:
            return frame.copy()
        x, y, width, height = self.rect
        crop = frame.crop((x, y, x + width, y + height))
        digest, owned_rgb = record
        if _sha(crop.tobytes()) != digest:
            raise ValueError('Frame repair source crop SHA-256 mismatch')
        rgb = np.asarray(crop).copy()
        rgb[self._mask] = np.frombuffer(owned_rgb, dtype=np.uint8).reshape(-1, 3)
        result = frame.copy()
        result.paste(Image.fromarray(rgb), (x, y))
        return result

    def proof(self):
        """Describe deterministic byte-scope guarantees, not artistic acceptance."""
        return {
            'method': 'sparse-frame-rgba-v1',
            'canvas': list(self.canvas),
            'frame_count': self.frame_count,
            'record_count': len(self._records),
            'active_frames': list(self.active_frames),
            'active_frame_set_sha256': _list_sha(self.active_frames),
            'rect': list(self.rect),
            'rect_sha256': _list_sha(self.rect),
            'mask_sha256': _sha(self._mask_bytes),
            'mask_pixels': int(self._mask.sum()),
            'total_patch_bytes': self._total_patch_bytes,
            'outside_mask_retained': True,
            'outside_rect_retained': True,
            'inactive_frames_byte_identical': True,
            'artistic_acceptance': False,
        }
