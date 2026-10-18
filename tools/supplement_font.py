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
    if type(plan.get("font_size")) is not int or not 1 <= plan["font_size"] <= 128:
        raise FormatError("plan font_size outside 1..128")
    if "metric_height" in plan and (type(plan["metric_height"]) is not int or not 1 <= plan["metric_height"] <= 128):
        raise FormatError("invalid metric_height")
    glyphs = plan.get("glyphs")
    if not isinstance(glyphs, list) or not 1 <= len(glyphs) <= 16:
        raise FormatError("prototype plan requires 1..16 glyphs")
    seen = set()
    for glyph in glyphs:
        if not isinstance(glyph, dict) or set(glyph) != {"character", "texture_index", "x", "y", "width", "height"}:
            raise FormatError("unsupported glyph plan fields")
        char = glyph["character"]
        if not isinstance(char, str) or len(char) != 1 or not 0 < ord(char) <= 65535 or unicodedata.category(char).startswith("C") or char.isspace():
            raise FormatError("glyph must be one printable BMP non-control character")
        if char in seen:
            raise FormatError("duplicate planned codepoint")
        seen.add(char)
        if any(type(glyph[k]) is not int for k in ("texture_index", "x", "y", "width", "height")):
            raise FormatError("glyph placement must use integer fields")
        if not 0 <= glyph["texture_index"] <= 255 or min(glyph["x"], glyph["y"]) < 0 or any(glyph[k] % 4 for k in ("x", "y", "width", "height")) or not 4 <= glyph["width"] <= 128 or not 4 <= glyph["height"] <= 128:
            raise FormatError("glyph requires bounded block-aligned cell")
    if any(plan.get("metric_height", g["height"]) > g["height"] for g in glyphs):
        raise FormatError("metric_height exceeds cell height")
    if len({g["texture_index"] for g in glyphs}) != 1:
        raise FormatError("prototype supplements only one existing atlas at a time")
    return glyphs


def rasterize_plan(font_file, expected_hash, plan):
    """Font cmap check plus shared-baseline raster; imports optional dependencies lazily."""
    glyphs = validate_plan(plan)
    font_data = font_file.read_bytes()
    verify_hash(font_data, expected_hash, "font source")
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    import io
    with TTFont(io.BytesIO(font_data)) as source:
        cmap = source.getBestCmap()
        if not cmap or any(cmap.get(ord(g["character"])) in (None, ".notdef") for g in glyphs):
            raise FormatError("font cmap lacks requested glyph (tofu rejected)")
        glyph_names = {g["character"]: cmap[ord(g["character"])] for g in glyphs}
    font = ImageFont.truetype(io.BytesIO(font_data), plan["font_size"])
    boxes = {g["character"]: font.getbbox(g["character"], anchor="ls") for g in glyphs}
    max_descent = max(max(0, box[3]) for box in boxes.values())
    baseline = min(g["height"] for g in glyphs) - 1 - max_descent
    alphas, report = {}, []
    for g in glyphs:
        char = g["character"]
        box = boxes[char]
        x = (g["width"] - (box[2] - box[0])) // 2 - box[0]
        if x + box[0] < 0 or x + box[2] > g["width"] or baseline + box[1] < 0 or baseline + box[3] > g["height"]:
            raise FormatError("glyph would clip at shared baseline")
        image = Image.new("L", (g["width"], g["height"]))
        ImageDraw.Draw(image).text((x, baseline), char, font=font, anchor="ls", fill=255)
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


def append_font_payload(data, names, additions):
    """Append tagged/native/remap records; retain every original stored record byte."""
    old = parse_font_payload(data, names)
    if not old["is_remapped"]:
        raise FormatError("supplement requires existing explicit remap")
    count, remap_count = len(old["characters"]), len(old["remap"])
    if count + len(additions) > 65536:
        raise FormatError("glyph index exceeds u16 remap range")
    if any(a["codepoint"] in {r["codepoint"] for r in old["remap"]} for a in additions):
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
    out += data[old_native_end:old["remap_offset"]] + word(remap_count + len(additions))
    pairs_end = old["remap_offset"] + 4 + remap_count * 4
    out += data[old["remap_offset"] + 4:pairs_end]
    out += b"".join(struct.pack(">HH", a["codepoint"], count + i) for i, a in enumerate(additions)) + data[pairs_end:]
    new = parse_font_payload(out, names)
    if [[g[k] for k in METRIC_KEYS] for g in new["characters"][:count]] != [[g[k] for k in METRIC_KEYS] for g in old["characters"]]:
        raise FormatError("original glyph metric preservation failed")
    if [(r["codepoint"], r["glyph_index"]) for r in new["remap"][:remap_count]] != [(r["codepoint"], r["glyph_index"]) for r in old["remap"]]:
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


def supplement_package(data, expected_hash, font_object, plan, alphas, decoder, raw_atlas=False):
    verify_hash(data, expected_hash, "package")
    glyphs = validate_plan(plan)
    summary = parse_summary(data, len(data))
    logical = decode_logical(data, summary, decoder)
    tables = parse_tables(logical, summary, len(logical))
    candidates = [e for e in tables["exports"] if e["path"] == font_object and e["class_path"] == "Engine.Font"]
    if len(candidates) != 1:
        raise FormatError("font object must resolve to exactly one Engine.Font export")
    export = candidates[0]
    old_font = logical[export["serial_offset"]:export["serial_offset"] + export["serial_size"]]
    font = parse_font_payload(old_font, tables["names"])
    atlas_index = glyphs[0]["texture_index"]
    if atlas_index >= len(font["textures"]):
        raise FormatError("planned atlas index outside font Textures")
    ref = font["textures"][atlas_index]
    if not 1 <= ref <= len(tables["exports"]):
        raise FormatError("atlas reference is not a local export")
    atlas_export = tables["exports"][ref - 1]
    if atlas_export["class_path"] != "Engine.Texture2D":
        raise FormatError("atlas reference is not Texture2D")
    atlas_offset, atlas_size = atlas_export["serial_offset"], atlas_export["serial_size"]
    atlas = logical[atlas_offset:atlas_offset + atlas_size]
    texture = parse_atlas_payload(atlas, tables["names"], atlas_offset)
    if len(texture["mips"]) != 1:
        raise FormatError("prototype supports one-mip atlas only")
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
        metric_height = plan.get("metric_height", g["height"])
        if metric_height > old_max_height:
            raise FormatError("supplement metric increases original maximum font height")
        if any(alphas[cp][metric_height * g["width"]:]):
            raise FormatError("glyph alpha outside metric_height would clip")
        tiled = supplement_white_dxt5_cell(tiled, texture["width"], texture["height"], g["x"], g["y"], g["width"], g["height"], alphas[cp])
        for by in range(g["y"] // 4, (g["y"] + g["height"]) // 4):
            for bx in range(g["x"] // 4, (g["x"] + g["width"]) // 4):
                allowed_blocks.add(xbox_tiled_block_offset(bx, by, mip["aligned_width"] // 4) * 16)
        additions.append({"codepoint": cp, "StartU": g["x"], "StartV": g["y"], "USize": g["width"], "VSize": metric_height, "TextureIndex": atlas_index})
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
    if any(old_rgba[i * 4:i * 4 + 4] != new_rgba[i * 4:i * 4 + 4] for i in range(texture["width"] * texture["height"]) if i not in selected_pixels):
        raise FormatError("original atlas surface outside cells changed")
    new_font = append_font_payload(old_font, tables["names"], additions)
    new_font_parsed = parse_font_payload(new_font, tables["names"])
    tagged_size = next(p["size"] for p in font["properties"] if p["name"] == "Characters") - 4
    def original_record_hashes(payload, parsed):
        tagged_start = next(p["value_offset"] for p in parsed["properties"] if p["name"] == "Characters") + 4
        native_start, remap_start = parsed["native_offset"] + 4, parsed["remap_offset"] + 4
        return {"tagged": sha256(payload[tagged_start:tagged_start + tagged_size]),
                "native": sha256(payload[native_start:native_start + len(font["characters"]) * 17]),
                "remap": sha256(payload[remap_start:remap_start + len(font["remap"]) * 4])}
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
    return output, {"schema_version": 1, "status": "static-prototype-verified", "input_sha256": sha256(data), "output_sha256": sha256(output),
                    "input_size": len(data), "output_size": len(output), "font_object": font_object,
                    "atlas_object": atlas_export["path"], "original_texture_bulk_flags": bulk["flags"], "original_glyph_count": len(font["characters"]),
                    "supplemented_glyph_count": len(font["characters"]) + len(additions),
                    "added_codepoints": [a["codepoint"] for a in additions], "original_glyphs_and_remap_preserved": True,
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
