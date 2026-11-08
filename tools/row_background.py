"""Source-pixel restoration for independently verified horizontal UI gradients.

This is not a general image fill. Both separated native donor bands must be
exactly constant across each row and byte-identical to one another. Only an
explicit sparse ownership mask is transported; borders and other pixels remain
unchanged. The hidden gradient continuation is an authoring inference, not a
claim that the original unobscured artwork was recovered.
"""
from __future__ import annotations

import numpy as np


def restore_rows(rgb, rect, mask, donor_bands):
    if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.dtype('uint8')
            or rgb.ndim != 3 or rgb.shape[2] != 3
            or not 1 <= rgb.shape[1] <= 1920 or not 1 <= rgb.shape[0] <= 1080
            or not isinstance(rect, list) or len(rect) != 4
            or any(type(v) is not int for v in rect)):
        raise ValueError('Bounded native RGB and rectangle required')
    x, y, w, h = rect
    if (min(x, y) < 0 or min(w, h) < 1 or x+w > rgb.shape[1] or y+h > rgb.shape[0]
            or not isinstance(mask, np.ndarray) or mask.dtype != np.dtype('bool')
            or mask.shape != (h, w) or not mask.any() or mask.all()):
        raise ValueError('Proper sparse ownership mask required')
    if (not isinstance(donor_bands, list) or len(donor_bands) != 2
            or any(not isinstance(b, list) or len(b) != 2
                   or any(type(v) is not int for v in b)
                   or not 0 <= b[0] < b[1] <= rgb.shape[1] or b[1]-b[0] < 8
                   for b in donor_bands)
            or donor_bands[0][1] > x or donor_bands[1][0] < x+w):
        raise ValueError('Separated left/right native donor bands required')
    samples = [rgb[y:y+h, a:b] for a, b in donor_bands]
    row = samples[0][:, :1]
    if any(not np.array_equal(s, np.broadcast_to(row, s.shape)) for s in samples):
        raise ValueError('Native donor rows are not exactly horizontally invariant')
    output = rgb.copy()
    crop = output[y:y+h, x:x+w]
    crop[mask] = np.broadcast_to(row, crop.shape)[mask]
    return output, dict(method='dual-native-row-transport-v1',
                        donor_bands=[list(b) for b in donor_bands],
                        owned_pixels=int(mask.sum()), donor_maximum_difference=0,
                        unowned_pixels_byte_identical=True,
                        hidden_background_is_inferred=True)
