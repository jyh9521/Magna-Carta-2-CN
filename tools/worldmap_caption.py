"""Measure fixed, bright caption cores over moving source-locked backgrounds."""
from __future__ import annotations

from .video_caption import sha


def temporal_static_mask(frames, rect, specification, expected_frames):
    import numpy as np
    from PIL import Image, ImageFilter
    keys = {'minimum_brightness', 'maximum_range', 'dilation', 'mask_sha256', 'pixels'}
    optional = {'minimum_red_blue_difference', 'minimum_red_green_difference'}
    if (not keys <= set(specification) or set(specification)-keys-optional
            or type(expected_frames) is not int or not 1 <= expected_frames <= 6144
            or not isinstance(rect, list) or len(rect) != 4 or any(type(x) is not int for x in rect)
            or min(rect[:2]) < 0 or min(rect[2:]) <= 0 or rect[2]*rect[3] > 256*1024):
        raise ValueError('Bounded temporal caption mask required')
    minimum, spread, dilation = (specification[k] for k in ('minimum_brightness', 'maximum_range', 'dilation'))
    if (any(type(x) is not int for x in (minimum, spread, dilation)) or not 0 <= minimum <= 255
            or not 0 <= spread <= 128 or not 0 <= dilation <= 8):
        raise ValueError('Temporal caption mask threshold bound')
    for key in optional & set(specification):
        if type(specification[key]) is not int or not -255 <= specification[key] <= 255:
            raise ValueError('Temporal caption chromatic support bound')
    x, y, w, h = rect
    low = high = minimum_rb = minimum_rg = None
    count = 0
    for frame in frames:
        count += 1
        if count > expected_frames or x+w > frame.width or y+h > frame.height:
            raise ValueError('Temporal caption mask frame count/geometry mismatch')
        values = np.asarray(frame.convert('RGB').crop((x, y, x+w, y+h)))
        low = values.copy() if low is None else np.minimum(low, values)
        high = values.copy() if high is None else np.maximum(high, values)
        signed=values.astype('int16')
        rb=signed[:,:,0]-signed[:,:,2];rg=signed[:,:,0]-signed[:,:,1]
        minimum_rb=rb.copy() if minimum_rb is None else np.minimum(minimum_rb,rb)
        minimum_rg=rg.copy() if minimum_rg is None else np.minimum(minimum_rg,rg)
    if count != expected_frames:
        raise ValueError('Temporal caption mask frame count mismatch')
    seed = (low.mean(2) >= minimum) & ((high.astype('int16')-low).max(2) <= spread)
    if 'minimum_red_blue_difference' in specification:
        seed &= minimum_rb >= specification['minimum_red_blue_difference']
    if 'minimum_red_green_difference' in specification:
        seed &= minimum_rg >= specification['minimum_red_green_difference']
    mask = np.asarray(Image.fromarray(seed.astype('uint8')*255).filter(ImageFilter.MaxFilter(2*dilation+1))) > 0
    if not mask.any() or sha(mask.tobytes()) != specification['mask_sha256'] or int(mask.sum()) != specification['pixels']:
        raise ValueError('Temporal caption mask identity mismatch')
    return mask
