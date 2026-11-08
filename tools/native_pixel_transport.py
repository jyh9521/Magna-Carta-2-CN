"""Sparse, explicit native-pixel transport; no interpolation or image synthesis.

Every repaired RGB sample names one clean donor pixel. The target alpha and all
unowned target bytes are retained. Reusing a native motif is an authored hidden
background continuation, not proof of the original obscured pixels.
"""
from __future__ import annotations


def _geometry(width, height, pixels):
    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= 2048 or not 1 <= height <= 2048
            or not isinstance(pixels, bytes) or len(pixels) != width*height*4):
        raise ValueError('Bounded native RGBA geometry required')


def _rect(rect, width, height):
    if (not isinstance(rect, list) or len(rect) != 4
            or any(type(v) is not int for v in rect)
            or min(rect[:2]) < 0 or min(rect[2:]) < 1
            or rect[0]+rect[2] > width or rect[1]+rect[3] > height):
        raise ValueError('Bounded clean donor rectangle required')
    return rect


def transport_rgba(source, width, height, mask, donors, runs):
    """Copy specified horizontal donor runs into a proper sparse binary mask.

    ``step_x`` is -1, 0 or 1 (mirror, repeated column or direct copy). All
    coordinates are native integers. Runs must cover exactly the owned mask;
    donor reads must lie in explicit clean rectangles. A donor that equals the
    source may not read any owned source pixel, even if marked clean by mistake.
    """
    _geometry(width, height, source)
    if (not isinstance(mask, bytes) or len(mask) != width*height
            or set(mask)-{0, 255} or not any(mask) or all(mask)):
        raise ValueError('Proper sparse binary ownership mask required')
    if (not isinstance(donors, dict) or not 1 <= len(donors) <= 16
            or not isinstance(runs, list) or not 1 <= len(runs) <= width*height):
        raise ValueError('Bounded donor/run inventory required')
    for name, donor in donors.items():
        if (not isinstance(name, str) or not name or len(name) > 128
                or not isinstance(donor, dict)
                or set(donor) != {'rgba', 'width', 'height', 'clean_rectangles'}):
            raise ValueError('Explicit donor identity/fields required')
        _geometry(donor['width'], donor['height'], donor['rgba'])
        rects = donor['clean_rectangles']
        if not isinstance(rects, list) or not 1 <= len(rects) <= 32:
            raise ValueError('Bounded clean donor rectangles required')
        for rect in rects:
            _rect(rect, donor['width'], donor['height'])
    result, covered = bytearray(source), set()
    for run in runs:
        if (not isinstance(run, dict)
                or set(run) != {'destination', 'donor', 'source', 'step_x'}
                or run['donor'] not in donors
                or type(run['step_x']) is not int or run['step_x'] not in (-1, 0, 1)):
            raise ValueError('Explicit integer native donor run required')
        dest, start = run['destination'], run['source']
        if (not isinstance(dest, list) or len(dest) != 3
                or any(type(v) is not int for v in dest)
                or min(dest[:2]) < 0 or dest[2] < 1
                or dest[0]+dest[2] > width or dest[1] >= height):
            raise ValueError('Native destination bounds')
        if (not isinstance(start, list) or len(start) != 2
                or any(type(v) is not int for v in start)):
            raise ValueError('Native source bounds')
        donor = donors[run['donor']]
        dw, dh, pixels = donor['width'], donor['height'], donor['rgba']
        for n in range(dest[2]):
            sx, sy = start[0]+n*run['step_x'], start[1]
            if not 0 <= sx < dw or not 0 <= sy < dh:
                raise ValueError('Native source bounds')
            if not any(x <= sx < x+w and y <= sy < y+h
                       for x, y, w, h in donor['clean_rectangles']):
                raise ValueError('Read outside declared clean donor')
            si, di = sy*dw+sx, dest[1]*width+dest[0]+n
            if not mask[di]:
                raise ValueError('Native run writes an unowned destination')
            if di in covered:
                raise ValueError('Native destination overlap')
            if (dw, dh, pixels) == (width, height, source) and mask[si]:
                raise ValueError('Native run reads an owned source pixel')
            result[di*4:di*4+3] = pixels[si*4:si*4+3]
            covered.add(di)
    if len(covered) != mask.count(255):
        raise ValueError('Native runs do not exactly cover ownership mask')
    result = bytes(result)
    if (result[3::4] != source[3::4]
            or any(result[i*4:i*4+4] != source[i*4:i*4+4]
                   for i, value in enumerate(mask) if not value)):
        raise ValueError('Native pixel-transport preservation failure')
    return result, dict(method='nearest-source-pixel-rgb-preserve-alpha-v1',
                        owned_pixels=len(covered), donor_reads=len(covered),
                        all_donor_reads_in_declared_clean_regions=True,
                        unowned_rgba_byte_identical=True,
                        all_alpha_byte_identical=True,
                        averaging_or_interpolation_used=False,
                        hidden_background_is_inferred=True)
