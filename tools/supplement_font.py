"""Hash-guarded append-only UE3 font supplement prototype; local assets only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import unicodedata

try:
    from .ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header
    from .ue3_fonts import parse_font_payload, read_properties, unique_properties, int_property
    from .ue3_textures import parse_texture_payload, bulk_header, compressed_chunk, supplement_white_dxt5_cell, xbox_tiled_block_offset, untile_dxt5, decode_dxt5
    from .lzx_stored import wrap_ue3_chunk
except ImportError:
    from ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header
    from ue3_fonts import parse_font_payload, read_properties, unique_properties, int_property
    from ue3_textures import parse_texture_payload, bulk_header, compressed_chunk, supplement_white_dxt5_cell, xbox_tiled_block_offset, untile_dxt5, decode_dxt5
    from lzx_stored import wrap_ue3_chunk

METRIC_KEYS = ("StartU", "StartV", "USize", "VSize", "TextureIndex")
# Explicit per-plan opt-in only; atlas placement, remap and ink checks still
# decide whether a particular source can accept the requested additions.
MAX_ADDITIONAL_GLYPHS = 4096


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify_hash(data, expected, label):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected) or sha256(data) != expected.lower():
        raise FormatError(f"{label} SHA-256 mismatch")


def word(value):
    return struct.pack(">I", value)


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("schema_version") != 1 or plan.get("in_game_verified") is not False:
        raise FormatError("plan requires schema_version1 and in_game_verified=false")
    padding=plan.get('ink_padding')
    if padding is not None and (not isinstance(padding,dict) or set(padding)!={'left','right'}
            or any(type(v) is not int or not 0<=v<=16 for v in padding.values())):
        raise FormatError('ink_padding requires bounded integer left/right margins')
    if type(plan.get("font_size")) is not int or not 1 <= plan["font_size"] <= 128:
        raise FormatError("plan font_size outside 1..128")
    if 'remap_conversion' in plan and plan['remap_conversion'] != 'identity-256':
        raise FormatError('unsupported explicit remap_conversion')
    if "metric_height" in plan and (type(plan["metric_height"]) is not int or not 1 <= plan["metric_height"] <= 128):
        raise FormatError("invalid metric_height")
    if 'atlas_height' in plan and (type(plan['atlas_height']) is not int or
            not 128 <= plan['atlas_height'] <= 2048 or plan['atlas_height'] & (plan['atlas_height']-1)):
        raise FormatError('atlas_height must be a power of two within 128..2048')
    if 'atlas_width' in plan and (type(plan['atlas_width']) is not int or
            not 128 <= plan['atlas_width'] <= 2048 or plan['atlas_width'] & (plan['atlas_width']-1)):
        raise FormatError('atlas_width must be a power of two within 128..2048')
    glyphs = plan.get("glyphs")
    replacements=plan.get('replace_blank_codepoints',[])
    if (not isinstance(replacements,list) or len(set(replacements))!=len(replacements)
            or any(type(cp) is not int or not 1<=cp<=65535 for cp in replacements)):
        raise FormatError('invalid blank glyph replacement list')
    limit = plan.get('glyph_limit', 128)
    if type(limit) is not int or not 1 <= limit <= MAX_ADDITIONAL_GLYPHS:
        raise FormatError(f'glyph_limit must be within 1..{MAX_ADDITIONAL_GLYPHS}')
    if not isinstance(glyphs, list) or not 1 <= len(glyphs) <= limit:
        raise FormatError(f"prototype plan requires 1..{limit} glyphs")
    growth = plan.get('metric_height_growth')
    if growth is not None:
        if (not isinstance(growth, dict) or set(growth) != {'original', 'candidate'}
                or any(type(growth[k]) is not int for k in growth)
                or not 1 <= growth['original'] < growth['candidate'] <= 128
                or plan.get('metric_height') != growth['candidate']):
            raise FormatError('invalid explicit metric height growth')
    seen = set()
    for glyph in glyphs:
        if not isinstance(glyph, dict) or set(glyph)-{'metric_width', 'layout'} != {"character", "texture_index", "x", "y", "width", "height"}:
            raise FormatError("unsupported glyph plan fields")
        char = glyph["character"]
        blank = glyph.get('layout') == 'blank-advance'
        if 'layout' in glyph and not blank:
            raise FormatError('unsupported explicit glyph layout')
        if not isinstance(char, str) or len(char) != 1 or not 0 < ord(char) <= 65535 or unicodedata.category(char).startswith("C") or (char.isspace() and not blank):
            raise FormatError("glyph must be one printable BMP non-control character")
        if blank and (unicodedata.category(char) != 'Zs' or 'metric_width' not in glyph):
            raise FormatError('blank-advance requires a Zs separator and explicit metric_width')
        if blank and ord(char) in replacements:
            raise FormatError('blank-advance cannot replace an existing mapping')
        if char in seen:
            raise FormatError("duplicate planned codepoint")
        seen.add(char)
        if any(type(glyph[k]) is not int for k in ("texture_index", "x", "y", "width", "height")):
            raise FormatError("glyph placement must use integer fields")
        if 'metric_width' in glyph and (type(glyph['metric_width']) is not int or not 1<=glyph['metric_width']<=glyph['width']):
            raise FormatError('invalid explicit glyph metric width')
        if not 0 <= glyph["texture_index"] <= 255 or min(glyph["x"], glyph["y"]) < 0 or any(glyph[k] % 4 for k in ("x", "y", "width", "height")) or not 4 <= glyph["width"] <= 128 or not 4 <= glyph["height"] <= 128:
            raise FormatError("glyph requires bounded block-aligned cell")
    if any(plan.get("metric_height", g["height"]) > g["height"] for g in glyphs):
        raise FormatError("metric_height exceeds cell height")
    if len({g["texture_index"] for g in glyphs}) != 1:
        raise FormatError("prototype supplements only one existing atlas at a time")
    if set(replacements)-{ord(g['character']) for g in glyphs}:raise FormatError('replacement absent from planned glyphs')
    return glyphs


def rasterize_plan(font_file, expected_hash, plan):
    """Font cmap check plus shared-baseline raster; imports optional dependencies lazily."""
    glyphs = validate_plan(plan)
    drawable = [g for g in glyphs if g.get('layout') != 'blank-advance']
    font_data = font_file.read_bytes()
    verify_hash(font_data, expected_hash, "font source")
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    import io
    with TTFont(io.BytesIO(font_data)) as source:
        cmap = source.getBestCmap()
        if not cmap or any(cmap.get(ord(g["character"])) in (None, ".notdef") for g in drawable):
            raise FormatError("font cmap lacks requested glyph (tofu rejected)")
        glyph_names = {g["character"]: cmap[ord(g["character"])] for g in drawable}
    font = ImageFont.truetype(io.BytesIO(font_data), plan["font_size"])
    boxes = {g["character"]: font.getbbox(g["character"], anchor="ls") for g in drawable}
    max_descent = max((max(0, box[3]) for box in boxes.values()), default=0)
    baseline = min(g["height"] for g in glyphs) - 1 - max_descent
    # Retain the historical baseline when it fits. A larger sample can need
    # the optional bottom margin for an ascender; never shrink or clip glyphs.
    baseline = max(baseline, -min((box[1] for box in boxes.values()), default=0))
    metric_limit = min(plan.get('metric_height',g['height']) for g in glyphs)
    if baseline + max_descent > metric_limit:
        # BC3 cells are block-aligned; their padding is not visible metric space.
        # Move the whole baseline only when the complete union still fits.
        baseline = metric_limit - max_descent
        if baseline + min((box[1] for box in boxes.values()), default=0) < 0:
            raise FormatError('glyph union exceeds metric height at shared baseline')
    alphas, report = {}, []
    for g in glyphs:
        char = g["character"]
        if g.get('layout') == 'blank-advance':
            alpha = bytes(g['width'] * g['height'])
            alphas[ord(char)] = alpha
            report.append(dict(codepoint=ord(char), raster_kind='explicit-blank-advance',
                               source_glyph=None, source_bbox=None, cell_baseline=None,
                               raster_bbox=None, alpha_sha256=sha256(alpha)))
            continue
        box = boxes[char]
        x = (g["width"] - (box[2] - box[0])) // 2 - box[0]
        if x + box[0] < 0 or x + box[2] > g["width"] or baseline + box[1] < 0 or baseline + box[3] > g["height"]:
            raise FormatError("glyph would clip at shared baseline")
        image = Image.new("L", (g["width"], g["height"]))
        ImageDraw.Draw(image).text((x, baseline), char, font=font, anchor="ls", fill=255)
        if 'metric_width' in g:
            ink=image.getbbox()
            if ink is None or ink[2]-ink[0]>g['metric_width']:raise FormatError('ink exceeds explicit metric width')
            padding=plan.get('ink_padding')
            if padding is not None:
                if ink[2]-ink[0]+padding['left']+padding['right']>g['metric_width']:
                    raise FormatError('explicit ink padding does not fit metric width')
                extra=g['metric_width']-(ink[2]-ink[0]+padding['left']+padding['right'])
                left=padding['left']+extra//2
            else:left=min(1,g['metric_width']-(ink[2]-ink[0]))
            fitted=Image.new('L',image.size)
            fitted.paste(image.crop((ink[0],0,ink[2],g['height'])),(left,0))
            image=fitted
        alpha = image.tobytes()
        if not any(alpha):
            raise FormatError("glyph raster is empty")
        alphas[ord(char)] = alpha
        report.append({"codepoint": ord(char), "source_glyph": glyph_names[char], "source_bbox": box,
                       "cell_baseline": baseline, "raster_bbox": image.getbbox(), "alpha_sha256": sha256(alpha)})
    return alphas, report


def tagged_glyph(names, metric):
    def fname(name):
        try:
            return struct.pack(">II", names.index(name), 0)
        except ValueError as exc:
            raise FormatError(f"required property name absent: {name}") from exc
    out = bytearray()
    for key in METRIC_KEYS:
        raw = bytes([metric[key]]) if key == "TextureIndex" else word(metric[key])
        out.extend(fname(key) + fname("ByteProperty" if key == "TextureIndex" else "IntProperty") + word(len(raw)) + word(0) + raw)
    return bytes(out) + fname("None")


def identity_remap_payload(data, names):
    """Opt-in candidate: retain 256 glyphs and introduce explicit u8 identity keys.

    Disk transformation only. Neither caller/draw-path equivalence nor runtime
    activation is inferred from the selected native measurement branch.
    """
    old=parse_font_payload(data,names)
    if old['is_remapped'] or old['remap'] or len(old['characters'])!=256:
        raise FormatError('identity-256 requires exactly 256 non-remapped glyphs')
    for name in ('None','IsRemapped','IntProperty'):
        if names.count(name)!=1:raise FormatError('identity remap requires unique existing property names')
    prefix=bytearray(data[:old['native_offset']])
    tag=next((p for p in old['properties'] if p['name']=='IsRemapped'),None)
    if tag is not None:
        prefix[tag['value_offset']:tag['value_offset']+4]=word(1)
    else:
        fname=lambda name:word(names.index(name))+word(0)
        prefix=prefix[:-8]+fname('IsRemapped')+fname('IntProperty')+word(4)+word(0)+word(1)+prefix[-8:]
    out=bytes(prefix)+data[old['native_offset']:old['remap_offset']]+word(256)
    out+=b''.join(struct.pack('>HH',i,i) for i in range(256))+word(1)
    new=parse_font_payload(out,names)
    if new['characters'] and ([[g[k] for k in METRIC_KEYS] for g in new['characters']]!=[[g[k] for k in METRIC_KEYS] for g in old['characters']]
        or new['textures']!=old['textures']):raise FormatError('identity remap changed original metrics/textures')
    return out


def append_font_payload(data, names, additions, remap_conversion=None, replace_blank_codepoints=()):
    """Append tagged/native/remap records; retain every original stored record byte."""
    old = parse_font_payload(data, names)
    if remap_conversion is not None:
        if remap_conversion!='identity-256':raise FormatError('unsupported explicit remap_conversion')
        data=identity_remap_payload(data,names);old=parse_font_payload(data,names)
    if not old["is_remapped"]:
        raise FormatError("supplement requires existing explicit remap")
    count, remap_count = len(old["characters"]), len(old["remap"])
    if count + len(additions) > 65536:
        raise FormatError("glyph index exceeds u16 remap range")
    replacements=set(replace_blank_codepoints);old_cps={r['codepoint'] for r in old['remap']}
    if replacements-old_cps:raise FormatError('replacement codepoint has no original mapping')
    if any(a["codepoint"] in old_cps-replacements for a in additions):
        raise FormatError("supplement codepoint already mapped")
    if len({a["codepoint"] for a in additions}) != len(additions):
        raise FormatError("duplicate supplement codepoint")
    chars = next(p for p in old["properties"] if p["name"] == "Characters")
    tagged = b"".join(tagged_glyph(names, a) for a in additions)
    prefix = bytearray(data[:chars["value_offset"]])
    struct.pack_into(">I", prefix, chars["offset"] + 16, chars["size"] + len(tagged))
    chars_end = chars["value_offset"] + chars["size"]
    out = bytes(prefix) + word(count + len(additions)) + data[chars["value_offset"] + 4:chars_end] + tagged
    out += data[chars_end:old["native_offset"]] + word(count + len(additions))
    old_native_end = old["native_offset"] + 4 + count * 17
    out += data[old["native_offset"] + 4:old_native_end]
    out += b"".join(struct.pack(">iiiiB", *(a[k] for k in METRIC_KEYS)) for a in additions)
    out += data[old_native_end:old["remap_offset"]] + word(remap_count + len(additions)-len(replacements))
    pairs_end = old["remap_offset"] + 4 + remap_count * 4
    new_indices={a['codepoint']:count+i for i,a in enumerate(additions)}
    out += b''.join(struct.pack('>HH',r['codepoint'],new_indices[r['codepoint']] if r['codepoint'] in replacements else r['glyph_index']) for r in old['remap'])
    out += b"".join(struct.pack(">HH", a["codepoint"], count + i) for i, a in enumerate(additions) if a['codepoint'] not in replacements) + data[pairs_end:]
    new = parse_font_payload(out, names)
    if [[g[k] for k in METRIC_KEYS] for g in new["characters"][:count]] != [[g[k] for k in METRIC_KEYS] for g in old["characters"]]:
        raise FormatError("original glyph metric preservation failed")
    if [(r["codepoint"], r["glyph_index"]) for r in new["remap"][:remap_count] if r['codepoint'] not in replacements] != [(r["codepoint"], r["glyph_index"]) for r in old["remap"] if r['codepoint'] not in replacements]:
        raise FormatError("original remap preservation failed")
    return out


def overlaps(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def block_rect(rect):
    x, y, w, h = rect
    return x // 4, y // 4, (x + w + 3) // 4 - x // 4, (y + h + 3) // 4 - y // 4


def validate_placements(font, texture, glyphs):
    index = glyphs[0]["texture_index"]
    existing = [(g["StartU"], g["StartV"], g["USize"], g["VSize"]) for g in font["characters"] if g["TextureIndex"] == index and g["USize"] and g["VSize"]]
    accepted = []
    for g in glyphs:
        rect = (g["x"], g["y"], g["width"], g["height"])
        if rect[0] + rect[2] > texture["width"] or rect[1] + rect[3] > texture["height"]:
            raise FormatError("supplement cell outside atlas dimensions")
        if any(overlaps(block_rect(rect), block_rect(old)) for old in existing + accepted):
            raise FormatError("supplement cell overlaps original/planned glyph BC3 blocks")
        accepted.append(rect)


def decode_logical(data, summary, decoder):
    if summary["byte_order"] != "big":
        raise FormatError("only big-endian 446/25 packages supported")
    if not summary["compression_flags"]:
        return data
    end = max(c["uncompressed_offset"] + c["uncompressed_size"] for c in summary["compressed_chunks"])
    return package_header(data, {**summary, "header_size": end}, decoder)


def repack_append_only(original, summary, logical, new_logical):
    """Preserve original compressed payloads except first header chunk; add last chunk."""
    if not summary["compression_flags"]:
        return new_logical, {"kind": "uncompressed", "preserved_compressed_chunks": 0}
    if summary["compression_flags"] != 4:
        raise FormatError("only LZX package compression supported")
    chunks = summary["compressed_chunks"]
    arrays_offset = summary["summary_end"] - 16 * len(chunks)
    if arrays_offset != chunks[0]["uncompressed_offset"] or arrays_offset < 8:
        raise FormatError("unsupported logical prefix/chunk table layout")
    first_end = chunks[0]["uncompressed_offset"] + chunks[0]["uncompressed_size"]
    if new_logical[first_end:len(logical)] != logical[first_end:]:
        raise FormatError("changes outside first original compressed chunk")
    prefix = bytearray(original[:arrays_offset])
    struct.pack_into(">I", prefix, arrays_offset - 4, len(chunks) + 1)
    packed = bytearray()
    entries = []
    physical_base = arrays_offset + 16 * (len(chunks) + 1)
    previous_end = summary["summary_end"]
    for i, c in enumerate(chunks):
        if c["compressed_offset"] < previous_end:
            raise FormatError("physical chunks out of order")
        packed.extend(original[previous_end:c["compressed_offset"]])
        payload = (wrap_ue3_chunk(new_logical[c["uncompressed_offset"]:first_end]) if i == 0 else
                   original[c["compressed_offset"]:c["compressed_offset"] + c["compressed_size"]])
        entries.append((c["uncompressed_offset"], c["uncompressed_size"], physical_base + len(packed), len(payload)))
        packed.extend(payload)
        previous_end = c["compressed_offset"] + c["compressed_size"]
    appended = wrap_ue3_chunk(new_logical[len(logical):])
    entries.append((len(logical), len(new_logical) - len(logical), physical_base + len(packed), len(appended)))
    packed.extend(appended)
    packed.extend(original[previous_end:])
    output = bytes(prefix) + b"".join(struct.pack(">IIII", *e) for e in entries) + bytes(packed)
    return output, {"kind": "LZX-first-chunk-plus-final-append", "preserved_compressed_chunks": len(chunks) - 1,
                    "new_chunk_count": len(entries), "original_trailing_bytes_preserved": len(original) - previous_end}



def parse_atlas_payload(data, names, serial_offset):
    """Original startup resident textures use raw bulk flag0, standalone uses0x40."""
    r = Reader(data)
    r.i32()
    props = unique_properties(read_properties(r, names))
    source = bulk_header(r, serial_offset)
    if any(source[k] for k in ("flags", "element_count", "size_on_disk")) or r.count(16) != 1:
        raise FormatError("prototype atlas requires empty SourceArt and one mip")
    bulk = bulk_header(r, serial_offset)
    if bulk["flags"] == 0x40:
        return parse_texture_payload(data, names, serial_offset)[0]
    if bulk["flags"] != 0 or not bulk["element_count"] or bulk["size_on_disk"] != bulk["element_count"]:
        raise FormatError("unsupported resident atlas bulk flags or sizes")
    width, height = int_property(props["SizeX"]), int_property(props["SizeY"])
    if props["Format"]["type"] != "ByteProperty" or props["Format"]["raw"] != b"\7":
        raise FormatError("resident atlas requires verified Format7")
    if min(width, height) < 32 or max(width, height) > 8192 or width % 4 or height % 4:
        raise FormatError("unsupported resident atlas dimensions")
    aligned_width, aligned_height = (width + 127) & ~127, (height + 127) & ~127
    if bulk["element_count"] != aligned_width * aligned_height:
        raise FormatError("resident raw tiled byte size mismatch")
    r.read(bulk["size_on_disk"])
    dimensions_offset = r.pos
    if (r.u32(), r.u32()) != (width, height) or r.pos != len(data):
        raise FormatError("resident atlas dimensions or export termination mismatch")
    return {"width": width, "height": height, "source_art": source,
            "mips": [{"index": 0, "width": width, "height": height,
                      "aligned_width": aligned_width, "aligned_height": aligned_height,
                      "bulk": bulk, "dimensions_offset": dimensions_offset}]}


def atlas_tiles(atlas, texture, decoder):
    bulk = texture["mips"][0]["bulk"]
    payload = atlas[bulk["payload_offset"]:bulk["payload_offset"] + bulk["size_on_disk"]]
    if bulk["flags"] == 0:
        return payload
    return compressed_chunk(payload, bulk["element_count"], decoder)[1]


def grow_atlas(atlas, names, serial_offset, texture, new_height, decoder):
    """Explicit vertical-only growth; tile addresses depend on unchanged width.

    Preserve every original tiled byte, prove original decoded rows identical,
    and update tagged/native height and inline bulk count/size consistently.
    Always emits raw inline bulk; callers must explicitly opt into raw atlases.
    """
    if (new_height <= texture['height'] or new_height > 2048 or new_height < 128
            or new_height & (new_height-1) or len(texture['mips']) != 1):
        raise FormatError('atlas growth requires increasing power-of-two one-mip height')
    old_tiles = atlas_tiles(atlas, texture, decoder)
    new_size = texture['mips'][0]['aligned_width'] * ((new_height+127)&~127)
    if new_size < len(old_tiles):
        raise FormatError('atlas growth would shrink storage')
    tiles = old_tiles + bytes(new_size-len(old_tiles))
    old_rgba = decode_dxt5(untile_dxt5(old_tiles, texture['width'], texture['height']), texture['width'], texture['height'])
    grown_rgba = decode_dxt5(untile_dxt5(tiles, texture['width'], new_height), texture['width'], new_height)
    if old_rgba != grown_rgba[:len(old_rgba)]:
        raise FormatError('atlas growth changed original decoded rows')
    r = Reader(atlas); r.i32(); props = unique_properties(read_properties(r, names))
    bulk = texture['mips'][0]['bulk']
    out = bytearray(atlas[:bulk['payload_offset']] + tiles + word(texture['width']) + word(new_height))
    struct.pack_into('>I',out,props['SizeY']['value_offset'],new_height)
    struct.pack_into('>III',out,bulk['header_offset'],0,new_size,new_size)
    parsed = parse_atlas_payload(bytes(out),names,serial_offset)
    if atlas_tiles(bytes(out),parsed,decoder) != tiles:
        raise FormatError('grown atlas reparse mismatch')
    return bytes(out), parsed


def grow_atlas_axes(atlas, names, serial_offset, texture, new_width, new_height, decoder):
    """Explicit bounded growth; relocate BC3 blocks without recompressing them.

    Width changes alter Xenos addresses. Preserve original block values including
    alignment padding at their new addresses, then prove the original decoded
    rectangle identical. The vertical-only implementation remains unchanged.
    """
    old_width, old_height = texture['width'], texture['height']
    if (any(type(v) is not int or not (32 if v == old else 128) <= v <= 2048 or v & (v - 1)
            for v, old in ((new_width, old_width), (new_height, old_height))) or new_width < old_width
            or new_height < old_height or (new_width, new_height) == (old_width, old_height)
            or len(texture['mips']) != 1):
        raise FormatError('atlas axes require nonshrinking power-of-two growth within 128..2048')
    if new_width == old_width:
        return grow_atlas(atlas, names, serial_offset, texture, new_height, decoder)
    old_tiles = atlas_tiles(atlas, texture, decoder)
    old_aw, old_ah = (old_width + 127) & ~127, (old_height + 127) & ~127
    new_aw, new_ah = (new_width + 127) & ~127, (new_height + 127) & ~127
    if len(old_tiles) != old_aw * old_ah:
        raise FormatError('original atlas tiled size mismatch')
    tiles = bytearray(new_aw * new_ah)
    used = set()
    for y in range(old_ah // 4):
        for x in range(old_aw // 4):
            source = xbox_tiled_block_offset(x, y, old_aw // 4) * 16
            target = xbox_tiled_block_offset(x, y, new_aw // 4) * 16
            if source + 16 > len(old_tiles) or target + 16 > len(tiles) or target in used:
                raise FormatError('atlas retile address outside buffer or duplicate')
            used.add(target)
            tiles[target:target + 16] = old_tiles[source:source + 16]
    tiles = bytes(tiles)
    old_rgba = decode_dxt5(untile_dxt5(old_tiles, old_width, old_height), old_width, old_height)
    new_rgba = decode_dxt5(untile_dxt5(tiles, new_width, new_height), new_width, new_height)
    crop = b''.join(new_rgba[y * new_width * 4:(y * new_width + old_width) * 4]
                    for y in range(old_height))
    if crop != old_rgba:
        raise FormatError('atlas retile changed original decoded rectangle')
    r = Reader(atlas); r.i32(); props = unique_properties(read_properties(r, names))
    bulk = texture['mips'][0]['bulk']
    out = bytearray(atlas[:bulk['payload_offset']] + tiles + word(new_width) + word(new_height))
    for key, value in [('SizeX', new_width), ('SizeY', new_height)]:
        struct.pack_into('>I', out, props[key]['value_offset'], value)
    struct.pack_into('>III', out, bulk['header_offset'], 0, len(tiles), len(tiles))
    parsed = parse_atlas_payload(bytes(out), names, serial_offset)
    if (parsed['width'], parsed['height']) != (new_width, new_height) or atlas_tiles(bytes(out), parsed, decoder) != tiles:
        raise FormatError('retiled atlas reparse mismatch')
    return bytes(out), parsed


def supplement_package(data, expected_hash, font_object, plan, alphas, decoder, raw_atlas=False):
    verify_hash(data, expected_hash, "package")
    glyphs = validate_plan(plan)
    summary = parse_summary(data, len(data))
    logical = decode_logical(data, summary, decoder)
    tables = parse_tables(logical, summary, len(logical))
    try:
        from .audit_text_font_coverage import supported_font_class
    except ImportError:
        from audit_text_font_coverage import supported_font_class
    candidates = [e for e in tables["exports"] if e["path"] == font_object and supported_font_class(tables,e)]
    if len(candidates) != 1:
        raise FormatError("font object must resolve to exactly one Engine.Font export")
    export = candidates[0]
    old_font = logical[export["serial_offset"]:export["serial_offset"] + export["serial_size"]]
    font = parse_font_payload(old_font, tables["names"])
    replacements=plan.get('replace_blank_codepoints',[])
    if replacements:
        from tools.font_ink import ink_records
        records=ink_records(dict(logical=logical,tables=tables),font,replacements,decoder)
        if any(r['status']!='transparent' for r in records):raise FormatError('replacement requires verified transparent original glyph')
    atlas_index = glyphs[0]["texture_index"]
    if atlas_index >= len(font["textures"]):
        raise FormatError("planned atlas index outside font Textures")
    ref = font["textures"][atlas_index]
    if not 1 <= ref <= len(tables["exports"]):
        raise FormatError("atlas reference is not a local export")
    atlas_export = tables["exports"][ref - 1]
    local_class=atlas_export['class']
    local_texture=(atlas_export['class_path']=='Texture2D' and type(local_class) is int and 0<local_class<=len(tables['exports'])
        and tables['exports'][local_class-1]['path']=='Texture2D' and tables['exports'][local_class-1]['class_path']=='Class')
    if atlas_export["class_path"] != "Engine.Texture2D" and not local_texture:
        raise FormatError("atlas reference is not Texture2D")
    atlas_offset, atlas_size = atlas_export["serial_offset"], atlas_export["serial_size"]
    atlas = logical[atlas_offset:atlas_offset + atlas_size]
    texture = parse_atlas_payload(atlas, tables["names"], atlas_offset)
    if len(texture["mips"]) != 1:
        raise FormatError("prototype supports one-mip atlas only")
    original_width, original_height = texture['width'], texture['height']
    original_bulk_flags = texture['mips'][0]['bulk']['flags']
    if 'atlas_height' in plan or 'atlas_width' in plan:
        if not raw_atlas:
            raise FormatError('atlas growth requires explicit raw_atlas')
        if 'atlas_width' in plan:
            atlas, texture = grow_atlas_axes(atlas, tables['names'], atlas_offset, texture,
                plan['atlas_width'], plan.get('atlas_height', original_height), decoder)
        else:
            atlas, texture = grow_atlas(atlas, tables['names'], atlas_offset, texture, plan['atlas_height'], decoder)
    validate_placements(font, texture, glyphs)
    mip = texture["mips"][0]
    bulk = mip["bulk"]
    tiled = atlas_tiles(atlas, texture, decoder)
    old_tiled = tiled
    old_max_height = max(g["VSize"] for g in font["characters"])
    allowed_blocks = set()
    additions = []
    for g in glyphs:
        cp = ord(g["character"])
        if cp not in alphas:
            raise FormatError("missing glyph coverage raster")
        if g.get('layout') == 'blank-advance' and any(alphas[cp]):
            raise FormatError('blank-advance requires all-zero alpha')
        metric_height = plan.get("metric_height", g["height"])
        growth = plan.get('metric_height_growth')
        if growth is not None and growth['original'] != old_max_height:
            raise FormatError('metric height growth original maximum mismatch')
        if metric_height > old_max_height and growth is None:
            raise FormatError("supplement metric increases original maximum font height")
        if any(alphas[cp][metric_height * g["width"]:]):
            raise FormatError("glyph alpha outside metric_height would clip")
        tiled = supplement_white_dxt5_cell(tiled, texture["width"], texture["height"], g["x"], g["y"], g["width"], g["height"], alphas[cp])
        for by in range(g["y"] // 4, (g["y"] + g["height"]) // 4):
            for bx in range(g["x"] // 4, (g["x"] + g["width"]) // 4):
                allowed_blocks.add(xbox_tiled_block_offset(bx, by, mip["aligned_width"] // 4) * 16)
        metric_width=g.get('metric_width',g['width'])
        if any(any(alphas[cp][y*g['width']+metric_width:(y+1)*g['width']]) for y in range(g['height'])):raise FormatError('glyph alpha outside metric_width would clip')
        additions.append({"codepoint": cp, "StartU": g["x"], "StartV": g["y"], "USize": metric_width, "VSize": metric_height, "TextureIndex": atlas_index})
    changed_blocks = {i for i in range(0, len(tiled), 16) if tiled[i:i + 16] != old_tiled[i:i + 16]}
    if not changed_blocks <= allowed_blocks:
        raise FormatError("texture blocks changed outside selected cells")
    # Compare actual decoded surface, not just metadata or texture hashes.
    old_rgba = decode_dxt5(untile_dxt5(old_tiled, texture["width"], texture["height"]), texture["width"], texture["height"])
    new_rgba = decode_dxt5(untile_dxt5(tiled, texture["width"], texture["height"]), texture["width"], texture["height"])
    max_alpha_error = 0
    selected_pixels = set()
    for g in glyphs:
        for y in range(g["height"]):
            for x in range(g["width"]):
                pixel = (g["y"] + y) * texture["width"] + g["x"] + x
                selected_pixels.add(pixel)
                max_alpha_error = max(max_alpha_error, abs(new_rgba[pixel * 4 + 3] - alphas[ord(g["character"])][y * g["width"] + x]))
    if max_alpha_error > 18:
        raise FormatError("new glyph alpha quantization exceeds bound")
    for g in glyphs:
        if g.get('layout') == 'blank-advance' and any(
                new_rgba[((g['y'] + y) * texture['width'] + g['x'] + x) * 4 + 3]
                for y in range(g['height']) for x in range(g['width'])):
            raise FormatError('blank-advance decoded cell must remain transparent')
    if any(old_rgba[i * 4:i * 4 + 4] != new_rgba[i * 4:i * 4 + 4] for i in range(texture["width"] * texture["height"]) if i not in selected_pixels):
        raise FormatError("original atlas surface outside cells changed")
    new_font = append_font_payload(old_font, tables["names"], additions,plan.get('remap_conversion'),replacements)
    new_font_parsed = parse_font_payload(new_font, tables["names"])
    tagged_size = next(p["size"] for p in font["properties"] if p["name"] == "Characters") - 4
    def original_record_hashes(payload, parsed):
        tagged_start = next(p["value_offset"] for p in parsed["properties"] if p["name"] == "Characters") + 4
        native_start, remap_start = parsed["native_offset"] + 4, parsed["remap_offset"] + 4
        return {"tagged": sha256(payload[tagged_start:tagged_start + tagged_size]),
                "native": sha256(payload[native_start:native_start + len(font["characters"]) * 17]),
                "remap": sha256(b''.join(payload[remap_start+i*4:remap_start+(i+1)*4] for i,r in enumerate(font['remap']) if r['codepoint'] not in replacements))}
    original_hashes = original_record_hashes(old_font, font)
    if original_hashes != original_record_hashes(new_font, new_font_parsed):
        raise FormatError("old tagged/native/remap record hash preservation failed")
    font_offset = (len(logical) + 3) & ~3
    new_atlas_offset = (font_offset + len(new_font) + 3) & ~3
    compressed = wrap_ue3_chunk(tiled) if bulk["flags"] == 0x40 and not raw_atlas else tiled
    new_atlas = bytearray(atlas[:bulk["payload_offset"]] + compressed + atlas[bulk["payload_offset"] + bulk["size_on_disk"]:])
    struct.pack_into(">I", new_atlas, bulk["size_on_disk_field_offset"], len(compressed))
    if raw_atlas:
        struct.pack_into(">I", new_atlas, bulk["header_offset"], 0)
    for header in (texture["source_art"], bulk):
        struct.pack_into(">I", new_atlas, header["data_offset_field_offset"], new_atlas_offset + header["payload_offset"])
    # Validate rebuilt native bulk framing and byte-for-byte tile content.
    parsed_atlas = parse_atlas_payload(bytes(new_atlas), tables["names"], new_atlas_offset)
    new_bulk = parsed_atlas["mips"][0]["bulk"]
    verified_tiles = atlas_tiles(bytes(new_atlas), parsed_atlas, decoder)
    if verified_tiles != tiled:
        raise FormatError("stored LZX texture roundtrip failed")
    new_logical = bytearray(logical)
    new_logical.extend(bytes(font_offset - len(new_logical)) + new_font)
    new_logical.extend(bytes(new_atlas_offset - len(new_logical)) + new_atlas)
    for e, offset, payload in ((export, font_offset, new_font), (atlas_export, new_atlas_offset, new_atlas)):
        struct.pack_into(">II", new_logical, e["table_offset"] + 32, len(payload), offset)
    # Reparse tables; every unaffected export must have identical location and bytes.
    new_tables = parse_tables(bytes(new_logical), summary, len(new_logical))
    preserved = 0
    for old, new in zip(tables["exports"], new_tables["exports"]):
        if old["table_offset"] in (export["table_offset"], atlas_export["table_offset"]):
            continue
        if old != new or logical[old["serial_offset"]:old["serial_offset"] + old["serial_size"]] != new_logical[new["serial_offset"]:new["serial_offset"] + new["serial_size"]]:
            raise FormatError("unaffected export preservation failed")
        preserved += 1
    allowed_bytes = {e["table_offset"] + i for e in (export, atlas_export) for i in range(32, 40)}
    if any(a != b and i not in allowed_bytes for i, (a, b) in enumerate(zip(logical, new_logical))):
        raise FormatError("original logical bytes changed outside export serial fields")
    output, compression_report = repack_append_only(data, summary, logical, bytes(new_logical))
    output_summary = parse_summary(output, len(output))
    verified_logical = decode_logical(output, output_summary, decoder)
    expected_logical = bytearray(new_logical)
    if summary["compression_flags"]:
        count_field = summary["summary_end"] - 16 * len(summary["compressed_chunks"]) - 4
        struct.pack_into(">I", expected_logical, count_field, len(output_summary["compressed_chunks"]))
    if verified_logical != expected_logical:
        raise FormatError("complete rebuilt package logical roundtrip failed")
    parse_tables(verified_logical, output_summary, len(verified_logical))
    report={"schema_version": 1, "status": "static-prototype-verified", "input_sha256": sha256(data), "output_sha256": sha256(output),
                    "input_size": len(data), "output_size": len(output), "font_object": font_object,
                    "atlas_object": atlas_export["path"], "original_texture_bulk_flags": original_bulk_flags, "original_glyph_count": len(font["characters"]),
                    "supplemented_glyph_count": len(font["characters"]) + len(additions),
                    "added_codepoints": [a["codepoint"] for a in additions], "original_glyphs_and_remap_preserved": not bool(replacements),
                    "original_glyphs_and_unselected_remap_preserved": True, "replaced_blank_codepoints": replacements,
                    "original_record_sha256": original_hashes,
                    "original_max_glyph_height": old_max_height,
                    "supplemented_max_glyph_height": max(g["VSize"] for g in new_font_parsed["characters"]),
                    "unaffected_exports_byte_identical": preserved, "original_payload_ranges_retained": True,
                    "changed_tile_blocks": len(changed_blocks), "allowed_tile_blocks": len(allowed_blocks),
                    "all_other_tile_blocks_and_padding_identical": True,
                    "original_glyph_rect_pixels_identical": True, "all_pixels_outside_selected_cells_identical": True,
                    "maximum_new_glyph_alpha_error": max_alpha_error,
                    "original_tiled_sha256": sha256(old_tiled), "supplemented_tiled_sha256": sha256(tiled),
                    "new_font_offset": font_offset, "new_atlas_offset": new_atlas_offset,
                    "package_compression": compression_report, "runtime_rendering_verified": False,
                    "rasterization_quality_verified": False}
    layout_glyphs = [dict(codepoint=ord(g['character']), metric_width=g['metric_width'],
                         kind='blank-advance', decoded_alpha_zero=True)
                     for g in glyphs if g.get('layout') == 'blank-advance']
    if layout_glyphs:
        report['explicit_layout_glyphs'] = layout_glyphs
    if 'remap_conversion' in plan:
        report['remap_conversion']=dict(profile='identity-256',original_mode=False,candidate_mode=True,identity_entries=256,
            old_glyph_metrics_preserved=True,runtime_equivalence_verified=False)
    if 'atlas_width' in plan:
        report['atlas_growth'] = dict(original_width=original_width, original_height=original_height,
            candidate_width=texture['width'], candidate_height=texture['height'],
            original_tiled_bytes_retained=texture['width'] == original_width,
            original_block_values_relocated=texture['width'] != original_width,
            original_decoded_rectangle_identical=True)
    elif 'atlas_height' in plan:
        report['atlas_growth'] = dict(original_height=original_height, candidate_height=texture['height'],
            width=texture['width'], original_tiled_bytes_retained=True, original_decoded_rows_identical=True)
    return output,report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--package-sha256", required=True)
    parser.add_argument("--font-file", type=Path, required=True)
    parser.add_argument("--font-sha256", required=True)
    parser.add_argument("--font-object", required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--lzx-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--raw-atlas", action="store_true", help="Explicit raw-inline atlas experiment")
    args = parser.parse_args(argv)
    try:
        inputs = [args.package, args.font_file, args.plan, args.lzx_library]
        if args.output.exists() or args.report.exists() or args.output.resolve() == args.report.resolve() or any(p.resolve() in (args.output.resolve(), args.report.resolve()) for p in inputs):
            raise FormatError("output/report must be new files distinct from every input")
        data = args.package.read_bytes()
        verify_hash(data, args.package_sha256, "package")
        plan_data = args.plan.read_bytes()
        plan = json.loads(plan_data.decode("utf-8-sig"))
        alphas, raster_report = rasterize_plan(args.font_file, args.font_sha256, plan)
        output, report = supplement_package(data, args.package_sha256, args.font_object, plan, alphas,
                                             LzxDecoder(args.lzx_library), args.raw_atlas)
        report["raw_atlas_requested"] = args.raw_atlas
        report.update({"font_source_sha256": args.font_sha256.lower(), "plan_sha256": sha256(plan_data), "rasters": raster_report})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as handle:
            handle.write(output)
        with args.report.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
        if args.output.read_bytes() != output or json.loads(args.report.read_text(encoding="utf-8")) != json.loads(json.dumps(report)):
            raise FormatError("written artifacts failed reopening verification")
        print(json.dumps(report, ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
