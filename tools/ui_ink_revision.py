"""Bounded native ink operations; all labels, regions and thresholds are data.

Alpha cleanup preserves BC3 RGB bytes. Optical metric fitting never removes
coloured pixels; callers explicitly bound the faint black shadow it may trim.
Neither operation claims to reproduce a game's final compositing shader.
"""
import struct

from .audit_font_optical_size import Sampler, ink_box
from .patch_tagged_fields import digest
from .replace_texture_regions import selected, replace_tiles
from .texture_layout import decode_texture, rect_units
from .texture_overlay import encode_alpha_range
from .ue3_fonts import read_properties, parse_font_payload
from .ue3_package import Reader
from .build_font_supplement import context


def alpha_palette(endpoints):
    a, b = endpoints
    if a > b:
        return [a, b] + [((7-i)*a+i*b)//7 for i in range(1, 7)]
    return [a, b] + [((5-i)*a+i*b)//5 for i in range(1, 5)] + [0, 255]


def clear_block_alpha(block, mask):
    if (not isinstance(block, bytes) or len(block) != 16 or len(mask) != 16
            or any(type(v) is not bool for v in mask)):
        raise ValueError('one BC3 block and sixteen Boolean mask samples required')
    if not any(mask):
        return block, 0
    if all(mask):
        return bytes(8) + block[8:], 0
    palette = alpha_palette(block[:2])
    bits = int.from_bytes(block[2:8], 'little')
    indexes = [(bits >> (3*i)) & 7 for i in range(16)]
    old = [palette[i] for i in indexes]
    if 0 in palette:
        zero = palette.index(0)
        bits = sum((zero if mask[i] else indexes[i]) << (3*i) for i in range(16))
        return block[:2] + bits.to_bytes(6, 'little') + block[8:], 0
    alpha = encode_alpha_range([0 if mask[i] else old[i] for i in range(16)])
    new_palette = alpha_palette(alpha[:2])
    bits = int.from_bytes(alpha[2:8], 'little')
    delta = max(abs(new_palette[(bits >> (3*i)) & 7]-old[i])
                for i in range(16) if not mask[i])
    return alpha + block[8:], delta


def clean_alpha(data, obj, rectangles, rgb_ceiling, max_retained_delta=0):
    if type(rgb_ceiling) is not int or not 0 <= rgb_ceiling <= 127:
        raise ValueError('explicit bounded dark-background threshold required')
    if (type(max_retained_delta) is not int or not 0 <= max_retained_delta <= 32
            or not isinstance(rectangles, list) or not 1 <= len(rectangles) <= 32):
        raise ValueError('bounded alpha error and nonempty regions required')
    _, _, _, texture = selected(data, obj, None)
    pixels = decode_texture(texture)
    w = texture['width']
    tiles = bytearray(texture['tiles'])
    units = set()
    removed = changed = delta = 0
    for rectangle in rectangles:
        new_units = set(rect_units(texture['layout'], rectangle))
        if units & new_units:
            raise ValueError('overlapping alpha regions')
        units.update(new_units)
        x, y, rw, rh = rectangle
        for by in range(y//4, (y+rh)//4):
            for bx in range(x//4, (x+rw)//4):
                mask = []
                for yy in range(by*4, by*4+4):
                    for xx in range(bx*4, bx*4+4):
                        p = pixels[(yy*w+xx)*4:(yy*w+xx)*4+4]
                        mask.append(bool(p[3] and max(p[:3]) <= rgb_ceiling))
                removed += sum(mask)
                at = texture['layout']['offsets'][by*(w//4)+bx]
                native = bytes(tiles[at:at+16])
                block = b''.join(native[i:i+2][::-1] for i in range(0, 16, 2))
                result, error = clear_block_alpha(block, mask)
                delta = max(delta, error)
                if delta > max_retained_delta:
                    raise ValueError('retained alpha quantization exceeds contract')
                encoded = b''.join(result[i:i+2][::-1] for i in range(0, 16, 2))
                changed += encoded != native
                tiles[at:at+16] = encoded
    if changed:
        result, proof = replace_tiles(data, digest(data), obj, bytes(tiles), rectangles, None)
    else:
        result, proof = data, dict(changed_blocks=0, outside_blocks_preserved=True)
    # The RGB half of every block, including unselected padding, stays exact.
    if any(tiles[i+8:i+16] != texture['tiles'][i+8:i+16]
           for i in range(0, len(tiles), 16)):
        raise ValueError('native RGB block changed')
    return result, dict(**proof, removed_shadow_pixels=removed,
                        retained_alpha_max_delta=delta, native_rgb_byte_identical=True)


def right_ink_width(cell, right_padding, max_black_shadow_alpha):
    if (type(right_padding) is not int or not 0 <= right_padding <= 8
            or type(max_black_shadow_alpha) is not int
            or not 0 <= max_black_shadow_alpha <= 32):
        raise ValueError('bounded optical margin and shadow threshold required')
    box = ink_box(cell)
    if box is None:
        raise ValueError('empty native foreground')
    width = box[2] + right_padding
    if width > cell.width:
        raise ValueError('metric extension would sample unowned atlas pixels')
    for r, g, b, a in cell.crop((width, 0, cell.width, cell.height)).get_flattened_data():
        if a and (max(r, g, b) != 0 or a > max_black_shadow_alpha):
            raise ValueError('optical trim would remove foreground or unapproved shadow')
    return width


def fit_right_ink(data, obj, reference, reference_obj, codepoints, right_padding, shadow_alpha):
    """Measure an embedded atlas; a declared external-bulk alias uses its metrics.

    Both serialized metric copies change. Atlas bytes and the visible glyph core
    remain unchanged; any trimmed low-alpha black fringe is counted explicitly.
    """
    if (not isinstance(codepoints, list) or not 1 <= len(codepoints) <= 128
            or len(set(codepoints)) != len(codepoints)
            or any(type(cp) is not int or not 0 <= cp <= 65535 for cp in codepoints)):
        raise ValueError('explicit unique bounded codepoints required')
    sample = Sampler(reference, reference_obj)
    c = context(data, None)
    es = [e for e in c['tables']['exports'] if e['path'] == obj and e['class_path'] in ('Font', 'Engine.Font')]
    if len(es) != 1 or c['logical'] != data:
        raise ValueError('unique raw native font required')
    e = es[0]
    start, size = e['serial_offset'], e['serial_size']
    payload = data[start:start+size]
    font = parse_font_payload(payload, c['tables']['names'])
    mapping = ({r['codepoint']: r['glyph_index'] for r in font['remap']} if font['is_remapped']
               else {i: i for i in range(len(font['characters']))})
    out = bytearray(data)
    rows = []
    for cp in codepoints:
        g = font['characters'][mapping[cp]]
        rg = sample.font['characters'][sample.mapping[cp]]
        if any(g[k] != rg[k] for k in ('StartU', 'StartV', 'USize', 'VSize', 'TextureIndex')):
            raise ValueError('reference/alias native metrics mismatch')
        cell = sample.glyph(cp)
        width = right_ink_width(cell, right_padding, shadow_alpha)
        reader = Reader(payload)
        reader.seek(g['tagged_offset'])
        prop = next(p for p in read_properties(reader, c['tables']['names']) if p['name'] == 'USize')
        for offset in (prop['value_offset'], g['native_offset']+8):
            struct.pack_into('>i', out, start+offset, width)
        fringe = cell.crop((width, 0, cell.width, cell.height))
        rows.append(dict(codepoint=cp, before=g['USize'], after=width,
                         trimmed_black_shadow_pixels=sum(p[3] != 0 for p in fringe.get_flattened_data())))
    result = bytes(out)
    checked = parse_font_payload(result[start:start+size], c['tables']['names'])
    for cp, row in zip(codepoints, rows, strict=True):
        if checked['characters'][mapping[cp]]['USize'] != row['after']:
            raise ValueError('tagged/native optical metric roundtrip failed')
    if result[:start] != data[:start] or result[start+size:] != data[start+size:]:
        raise ValueError('non-font export changed')
    return result, dict(object=obj, glyphs=rows, atlases_byte_identical=True,
                        foreground_pixels_preserved=True, reference_sha256=digest(reference))
