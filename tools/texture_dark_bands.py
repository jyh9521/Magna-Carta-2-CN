"""Repair explicit gradient notches without redrawing a native texture.

Only the rendered RGB delta is applied to existing pixels. Coverage, layout,
background restoration and all native BC3 alpha bytes remain untouched.
No automatic global smoothing or default encoder change is performed.
"""
import copy
import struct
import statistics

from .bc3_rgb_fit import encode_fitted_rgba_block
from .repair_texture_labels import revise
from .texture_layout import decode_texture, rect_units
from .texture_overlay import render_label, rgba_crop
from .ue3_textures import decode_dxt5


def core_mask(font, label):
    """Reuse the exact glyph geometry, including the outline's reserved margin."""
    flat = copy.deepcopy(label)
    a = flat['appearance']
    a['gradient'] = [[0, [255, 255, 255, 255]], [1000, [255, 255, 255, 255]]]
    for key in ('outline', 'shadow', 'glow'):
        a[key][3] = 0
    return render_label(font, flat)[3::4]


def row_means(pixels, mask, width):
    if len(pixels) != len(mask)*4 or len(mask) % width:
        raise ValueError('row measurement dimensions')
    result = []
    for y in range(len(mask)//width):
        values = [pixels[i*4] for i in range(y*width, (y+1)*width)
                  if mask[i] >= 250 and pixels[i*4+3] >= 240]
        result.append(sum(values)/len(values) if values else None)
    return result


def dark_rows(pixels, mask, width, threshold=20):
    rows = row_means(pixels, mask, width)
    return [y for y in range(1, len(rows)-1)
            if all(rows[k] is not None for k in (y-1, y, y+1))
            and min(rows[y-1], rows[y+1])-rows[y] >= threshold]


def narrow_gradient_positions(label, max_span_pixels=3.25):
    stops = label['appearance']['gradient']; height = label['appearance']['ink_box'][3]
    positions = []; i = 1
    while i < len(stops)-1:
        end = i
        # A two-sample dark plateau has no strictly lower single sample.
        # Keep the same colour/span thresholds; include the complete run.
        while end+1 < len(stops)-1 and stops[end+1][1][0] == stops[i][1][0]:
            end += 1
        if (min(stops[i-1][1][0], stops[end+1][1][0])-stops[i][1][0] >= 20
                and (stops[end+1][0]-stops[i-1][0])*(height-1)/1000 <= max_span_pixels):
            positions.extend(p for p, _ in stops[i:end+1])
        i = end+1
    return positions


def repair_dark_outline(texture, label, font):
    """Opt-in repair of bright BC3 RGB leakage on an existing dark outline.

    No stroke dilation, alpha fitting, font/geometry change or foreground
    recolouring request is involved. Only explicit bad-edge blocks are fit.
    """
    layout = texture['layout']
    if layout['format'] != 7 or layout['unit_bytes'] != 16:
        raise ValueError('outline RGB repair requires BC3')
    if max(label['appearance']['outline'][:3]) > 32:
        raise ValueError('dark outline required')
    draw = render_label(font, label); mask = core_mask(font, label)
    original = decode_texture(texture); rect = label['rect']; w,h = rect[2:]
    pixels = rgba_crop(original, texture['width'], rect); target = bytearray(pixels)
    units = rect_units(layout, rect)
    def leaking(data):
        return [i for i in range(w*h) if mask[i] <= 16 and draw[i*4+3] >= 128
                and data[i*4+3] >= 96 and max(draw[i*4:i*4+3]) <= 32
                and max(data[i*4:i*4+3])-max(draw[i*4:i*4+3]) > 24]
    bad = leaking(pixels)
    for i in bad:
        target[i*4:i*4+3] = draw[i*4:i*4+3]
    affected = {(i%w//4,i//w//4) for i in bad}; native = bytearray(texture['tiles'])
    changes = 0
    for bx,by in sorted(affected):
        desired = b''.join(target[((by*4+y)*w+bx*4)*4:((by*4+y)*w+bx*4+4)*4] for y in range(4))
        weighted = bytearray(desired)
        for y in range(4):
            for x in range(4):
                if (by*4+y)*w+bx*4+x in bad:
                    weighted[(y*4+x)*4+3] = 255
        at = units[by*(w//4)+bx]; previous = texture['tiles'][at:at+16]
        linear = b''.join(previous[k:k+2][::-1] for k in range(0,16,2))
        encoded = linear[:8]+encode_fitted_rgba_block(bytes(weighted))[8:]
        def error(data):
            return sum(weighted[i+3]**2*sum((desired[i+k]-data[i+k])**2 for k in range(3)) for i in range(0,64,4))
        if error(decode_dxt5(encoded,4,4)) >= error(decode_dxt5(linear,4,4)):
            continue
        native[at:at+16] = b''.join(encoded[k:k+2][::-1] for k in range(0,16,2)); changes += 1
    native = bytes(native); result = decode_texture(texture,native)
    if original[3::4] != result[3::4] or any(native[i:i+8] != texture['tiles'][i:i+8] for i in range(0,len(native),16)):
        raise ValueError('outline RGB repair changed alpha')
    remaining = leaking(rgba_crop(result,texture['width'],rect))
    return native, dict(changed_blocks=changes, affected_blocks=len(affected),
                        bright_outline_pixels_before=len(bad), bright_outline_pixels_after=len(remaining),
                        native_alpha_identical=True, outline_geometry_unchanged=True)


def quantization_rows(pixels, expected, mask, width):
    """Screen only: require three solid samples and a localized median deficit."""
    if len(pixels) != len(expected) or len(pixels) != len(mask)*4 or len(mask) % width:
        raise ValueError('quantization measurement dimensions')
    deficits = []
    for y in range(len(mask)//width):
        values = [expected[i*4]-pixels[i*4] for i in range(y*width, (y+1)*width)
                  if mask[i] >= 250 and pixels[i*4+3] >= 240]
        deficits.append(statistics.median(values) if len(values) >= 3 else None)
    return [y for y in range(1, len(deficits)-1)
            if all(deficits[z] is not None for z in (y-1,y,y+1))
            and deficits[y] >= 20 and deficits[y]-max(deficits[y-1],deficits[y+1]) >= 15]


def repair(texture, label, font, positions, refit_rows=()):
    """Return new native tiles and a bounded proof; never write a source file."""
    layout = texture['layout']
    if layout['format'] != 7 or layout['unit_bytes'] != 16:
        raise ValueError('RGB-only repair requires BC3')
    if not positions and not refit_rows:
        raise ValueError('explicit nonempty RGB correction required')
    if any(color[3] != 255 for _, color in label['appearance']['gradient']):
        raise ValueError('RGB band repair requires opaque foreground gradient samples')
    after = revise(label, positions)
    old_draw, new_draw = render_label(font, label), render_label(font, after)
    if old_draw[3::4] != new_draw[3::4]:
        raise ValueError('gradient correction changed coverage')
    original = decode_texture(texture)
    rect = label['rect']; w, h = rect[2:]
    if (not isinstance(refit_rows, (list, tuple)) or len(refit_rows) > h
            or any(type(y) is not int or not 0 <= y < h for y in refit_rows)
            or len(set(refit_rows)) != len(refit_rows)):
        raise ValueError('invalid explicit native refit rows')
    pixels = rgba_crop(original, texture['width'], rect)
    mask = core_mask(font, label)
    target = bytearray(pixels); affected = set(); changed_pixels = 0; band_rows = set(refit_rows)
    for i in range(w*h):
        at = i*4
        if not pixels[at+3] or not old_draw[at+3]:
            continue
        # Straight-alpha delta of the same foreground over the existing backdrop.
        # Do not paste a transparent redraw over opaque tutorial/map pixels.
        factor = min(1, old_draw[at+3]/pixels[at+3])
        for k in range(3):
            delta = round((new_draw[at+k]-old_draw[at+k])*factor)
            target[at+k] = (new_draw[at+k] if mask[i] >= 240 and
                            old_draw[at:at+3] != new_draw[at:at+3]
                            else max(0, min(255, pixels[at+k]+delta)))
        if target[at:at+3] != pixels[at:at+3]:
            affected.add((i%w//4, i//w//4)); changed_pixels += 1
            band_rows.add(i//w)
    guard_rows = {y+d for y in band_rows for d in (-1, 0, 1) if 0 <= y+d < h}
    for i, coverage in enumerate(mask):
        if coverage >= 240 and i//w in guard_rows:
            affected.add((i%w//4, i//w//4))
    # A BC3 palette is shared by four rows. Fit the existing solid foreground
    # in those same blocks to the corrected gradient too; otherwise lifting a
    # bad row can quantize its good neighbour into a new artificial dark row.
    for bx, by in affected:
        for yy in range(by*4, by*4+4):
            for xx in range(bx*4, bx*4+4):
                i = yy*w+xx
                if (old_draw[i*4+3] >= 16 and
                        abs(old_draw[i*4+3]-pixels[i*4+3]) <= 8):
                    target[i*4:i*4+3] = new_draw[i*4:i*4+3]
                elif mask[i] >= 240 and pixels[i*4+3] >= 240:
                    target[i*4:i*4+3] = new_draw[i*4:i*4+3]
    native = bytearray(texture['tiles']); units = rect_units(layout, rect)
    changed = []; old_error = 0; new_error = 0
    for bx, by in sorted(affected):
        desired = b''.join(target[((by*4+y)*w+bx*4)*4:((by*4+y)*w+bx*4+4)*4]
                           for y in range(4))
        previous = b''.join(pixels[((by*4+y)*w+bx*4)*4:((by*4+y)*w+bx*4+4)*4]
                            for y in range(4))
        at = units[by*(w//4)+bx]
        old_native = texture['tiles'][at:at+16]
        old_linear = b''.join(old_native[k:k+2][::-1] for k in range(0, 16, 2))
        fit_input = bytearray(desired)
        for y in range(4):
            for x in range(4):
                i = y*4+x
                if mask[(by*4+y)*w+bx*4+x] < 240:
                    fit_input[i*4+3] //= 4
                elif by*4+y not in band_rows:
                    fit_input[i*4+3] //= 2
        encoded = old_linear[:8] + encode_fitted_rgba_block(bytes(fit_input))[8:]
        # RGB565 may prefer a darker interpolant for a warm, nearly opaque
        # stroke beside a white highlight. Keep the fitted endpoints, but do
        # not select that artificial dark level for the declared band core.
        c0, c1, indices = struct.unpack('<HHI', encoded[8:])
        palette = [tuple(decode_dxt5(encoded[:12]+struct.pack('<I', j), 4, 4)[:3])
                   for j in range(4)]
        for y in range(4):
            for x in range(4):
                i = y*4+x; pos = (by*4+y)*w+bx*4+x
                if mask[pos] < 250 or by*4+y not in guard_rows:
                    continue
                want = desired[i*4:i*4+3]; choice = (indices >> (2*i)) & 3
                floor = max(want)-16
                eligible = [j for j, color in enumerate(palette) if max(color) >= floor]
                if max(palette[choice]) < floor and eligible:
                    choice = min(eligible, key=lambda j: sum((want[k]-palette[j][k])**2 for k in range(3)))
                    indices = (indices & ~(3 << (2*i))) | (choice << (2*i))
        encoded = encoded[:8]+struct.pack('<HHI', c0, c1, indices)
        decoded = decode_dxt5(encoded, 4, 4)
        def error(data):
            return sum(fit_input[i+3]**2 * sum((desired[i+k]-data[i+k])**2 for k in range(3))
                       for i in range(0, 64, 4))
        previous_error, candidate_error = error(previous), error(decoded)
        if candidate_error >= previous_error:
            continue
        old_error += previous_error; new_error += candidate_error
        encoded = b''.join(encoded[k:k+2][::-1] for k in range(0, 16, 2))
        native[at:at+16] = encoded
        changed.append(at)
    result = bytes(native)
    decoded = decode_texture(texture, result)
    if original[3::4] != decoded[3::4]:
        raise ValueError('native alpha changed')
    if any(result[i:i+8] != texture['tiles'][i:i+8] for i in range(0, len(result), 16)):
        raise ValueError('native alpha block changed')
    allowed = set(units)
    if not set(changed) <= allowed:
        raise ValueError('RGB correction escaped label')
    return result, dict(changed_blocks=len(changed), affected_blocks=len(affected),
                        changed_pixels=changed_pixels, native_alpha_identical=True,
                        band_rows=sorted(band_rows), guard_rows=sorted(guard_rows),
                        removed_gradient_positions=positions,
                        before_weighted_rgb_error=old_error, after_weighted_rgb_error=new_error,
                        unaffected_blocks_identical=True)
