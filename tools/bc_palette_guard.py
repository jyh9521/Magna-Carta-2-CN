"""Opt-in opaque BC3 pixel guards for shared edit/numeric blocks.

Untouched pixels retain original palette selectors. Guarded pixels are never
re-rendered, and unrepresentable new colors fail instead of silently disappearing.
"""
import hashlib
import re
import struct
from .ue3_package import FormatError

MAX_RGB_ERROR = 32


def apply_pixel_guards(texture, before, patched, resolved, rows):
    from .texture_layout import decode_texture, rect_units
    from .texture_overlay import rgba_crop
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
        raise FormatError('pixel guard region bound')
    width, height = texture['width'], texture['height']
    if texture['format'] != 7 or len(before) != width * height * 4:
        raise FormatError('pixel guard requires BC3 RGBA')
    checked, seen, area = [], set(), 0
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'id', 'rect', 'rgba_sha256'}
                or not isinstance(row['id'], str) or not 1 <= len(row['id']) <= 128
                or row['id'] in seen or not isinstance(row['rgba_sha256'], str)
                or not re.fullmatch('[0-9a-f]{64}', row['rgba_sha256'])):
            raise FormatError('invalid pixel guard')
        rect = row['rect']
        if (not isinstance(rect, list) or len(rect) != 4
                or any(type(v) is not int for v in rect)):
            raise FormatError('pixel guard integer rectangle required')
        x, y, w, h = rect
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
            raise FormatError('pixel guard outside image')
        for other in checked:
            a, b, c, d = other['rect']
            if x < a + c and a < x + w and y < b + d and b < y + h:
                raise FormatError('overlapping pixel guards')
        area += w * h
        if area > 1024 * 1024:
            raise FormatError('pixel guard total bound')
        source = rgba_crop(before, width, rect)
        if hashlib.sha256(source).hexdigest() != row['rgba_sha256']:
            raise FormatError('pixel guard source hash mismatch')
        checked.append(row)
        seen.add(row['id'])
    desired = bytearray(before)
    allowed = set()
    for label, rgba in resolved:
        x, y, w, h = label['rect']
        allowed.update(rect_units(texture['layout'], label['rect']))
        for dy in range(h):
            start = ((y + dy) * width + x) * 4
            desired[start:start + w * 4] = rgba[dy * w * 4:(dy + 1) * w * 4]
    for row in checked:
        if rgba_crop(desired, width, row['rect']) != rgba_crop(before, width, row['rect']):
            raise FormatError('intended edit overlaps protected pixels')
    blocks = {}
    region_blocks = []
    for row in checked:
        x, y, w, h = row['rect']
        offsets = set()
        for by in range(y // 4 * 4, y + h, 4):
            for bx in range(x // 4 * 4, x + w, 4):
                offset = rect_units(texture['layout'], [bx, by, 4, 4])[0]
                if offset in allowed:
                    offsets.add(offset)
                    blocks[offset] = bx, by
        region_blocks.append(offsets)
    original = texture['tiles']
    output = bytearray(patched)
    for offset, (bx, by) in blocks.items():
        native = original[offset:offset + 16]
        linear = b''.join(native[i:i + 2][::-1] for i in range(0, 16, 2))
        c0, c1, indices = struct.unpack('<HHI', linear[8:])
        def unpack(value):
            r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
            return r * 8 + r // 4, g * 4 + g // 16, b * 8 + b // 4
        palette = [unpack(c0), unpack(c1)]
        palette += [tuple((2 * a + b) // 3 for a, b in zip(*palette)),
                    tuple((a + 2 * b) // 3 for a, b in zip(*palette))]
        for dy in range(4):
            for dx in range(4):
                at = ((by + dy) * width + bx + dx) * 4
                source, target = before[at:at + 4], desired[at:at + 4]
                if source[3] != 255 or target[3] != 255:
                    raise FormatError('shared pixel guard blocks must be opaque')
                if source == target:
                    continue
                choice = min(range(4), key=lambda i: sum(
                    (target[k] - palette[i][k]) ** 2 for k in range(3)))
                if max(abs(target[k] - palette[choice][k]) for k in range(3)) > MAX_RGB_ERROR:
                    raise FormatError('source palette cannot represent guarded edit color')
                shift = 2 * (dy * 4 + dx)
                indices = (indices & ~(3 << shift)) | (choice << shift)
        block = linear[:12] + struct.pack('<I', indices)
        output[offset:offset + 16] = b''.join(block[i:i + 2][::-1] for i in range(0, 16, 2))
    output = bytes(output)
    after = decode_texture(texture, output)
    reports = []
    for row, offsets in zip(checked, region_blocks):
        source, result = rgba_crop(before, width, row['rect']), rgba_crop(after, width, row['rect'])
        if source != result:
            raise FormatError('protected pixel output hash mismatch')
        reports.append(dict(id=row['id'], rect=row['rect'],
                            before_rgba_sha256=hashlib.sha256(source).hexdigest(),
                            after_rgba_sha256=hashlib.sha256(result).hexdigest(),
                            pixels_preserved=True, source_palette_blocks=len(offsets)))
    return output, reports
