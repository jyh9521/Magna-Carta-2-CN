"""Read-only tagged/native UE3 446/25 Font inspection; no texture decoding or edits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .ue3_package import Reader, FormatError, parse_summary, parse_tables
except ImportError:
    from ue3_package import Reader, FormatError, parse_summary, parse_tables


def fname(reader, names):
    index, number = reader.u32(), reader.u32()
    if index >= len(names) or number:
        raise FormatError("unsupported property FName index or instance")
    return names[index]


def read_properties(reader, names):
    """446 tagged properties; offsets refer to reader's complete byte buffer."""
    properties = []
    for _ in range(4096):
        offset = reader.pos
        name = fname(reader, names)
        if name == "None":
            return properties
        kind = fname(reader, names)
        size, array_index = reader.u32(), reader.u32()
        prop = {"name": name, "type": kind, "size": size,
                "array_index": array_index, "offset": offset}
        if kind == "StructProperty":
            prop["struct"] = fname(reader, names)
        if kind == "BoolProperty":
            prop["bool"] = reader.u32()
            if prop["bool"] not in (0, 1) or size != 0:
                raise FormatError("invalid BoolProperty")
        prop["value_offset"] = reader.pos
        prop["raw"] = reader.read(size)
        properties.append(prop)
    raise FormatError("property count exceeds limit")


def unique_properties(properties):
    result = {}
    for prop in properties:
        if prop["array_index"] or prop["name"] in result:
            raise FormatError("duplicate or indexed property unsupported")
        result[prop["name"]] = prop
    return result


def int_property(prop):
    if prop["type"] != "IntProperty" or len(prop["raw"]) != 4:
        raise FormatError("expected IntProperty")
    return struct.unpack(">i", prop["raw"])[0]


def object_array(prop):
    if prop["type"] != "ArrayProperty":
        raise FormatError("expected object ArrayProperty")
    r = Reader(prop["raw"])
    out = [r.i32() for _ in range(r.count(65536))]
    if r.pos != len(r.data):
        raise FormatError("object array trailing bytes")
    return out


def tagged_characters(prop, names):
    if prop["type"] != "ArrayProperty":
        raise FormatError("expected Characters ArrayProperty")
    r = Reader(prop["raw"])
    characters = []
    for _ in range(r.count(65536)):
        start = r.pos
        fields = unique_properties(read_properties(r, names))
        if set(fields) != {"StartU", "StartV", "USize", "VSize", "TextureIndex"}:
            raise FormatError("unsupported FontCharacter fields")
        glyph = {key: int_property(fields[key]) for key in ("StartU", "StartV", "USize", "VSize")}
        texture = fields["TextureIndex"]
        if texture["type"] != "ByteProperty" or len(texture["raw"]) != 1:
            raise FormatError("expected byte TextureIndex")
        glyph["TextureIndex"] = texture["raw"][0]
        glyph["tagged_offset"] = prop["value_offset"] + start
        if any(glyph[key] < 0 for key in ("StartU", "StartV", "USize", "VSize")):
            raise FormatError("negative atlas coordinate")
        characters.append(glyph)
    if r.pos != len(r.data):
        raise FormatError("Characters trailing bytes")
    return characters


def parse_font_payload(data, names):
    """Parse one bounded export. Verify both stored representations agree."""
    r = Reader(data)
    net_index = r.i32()
    props = unique_properties(read_properties(r, names))
    if not {"Characters", "Textures"} <= props.keys() or set(props) - {"Characters", "Textures", "IsRemapped"}:
        raise FormatError("unsupported Font properties")
    characters = tagged_characters(props["Characters"], names)
    textures = object_array(props["Textures"])
    tagged_remapped = int_property(props["IsRemapped"]) if "IsRemapped" in props else 0
    native_offset = r.pos
    if r.count(65536) != len(characters):
        raise FormatError("native/tagged character count mismatch")
    keys = ("StartU", "StartV", "USize", "VSize", "TextureIndex")
    for glyph in characters:
        glyph["native_offset"] = r.pos
        values = [r.i32() for _ in range(4)] + [r.read(1)[0]]
        if values != [glyph[k] for k in keys]:
            raise FormatError("native/tagged character mismatch")
        if glyph["TextureIndex"] >= len(textures):
            raise FormatError("glyph texture index outside Textures")
    if [r.i32() for _ in range(r.count(65536))] != textures:
        raise FormatError("native/tagged texture references mismatch")
    unknown_offset = r.pos
    unknown = r.i32()
    if unknown != 0:
        raise FormatError("unsupported nonzero native field before remap")
    remap_offset = r.pos
    remap = []
    seen = set()
    for _ in range(r.count(65536)):
        offset = r.pos
        codepoint, glyph_index = struct.unpack(">HH", r.read(4))
        if codepoint in seen or glyph_index >= len(characters):
            raise FormatError("duplicate remap codepoint or invalid glyph index")
        seen.add(codepoint)
        remap.append({"codepoint": codepoint, "glyph_index": glyph_index, "offset": offset})
    remapped = r.i32()
    if remapped not in (0, 1) or remapped != tagged_remapped:
        raise FormatError("native/tagged IsRemapped mismatch")
    if bool(remap) != bool(remapped):
        raise FormatError("remap state/count mismatch")
    if r.pos != len(data):
        raise FormatError("Font export trailing bytes")
    return {"net_index": net_index, "characters": characters, "textures": textures,
            "is_remapped": bool(remapped), "remap": remap, "native_offset": native_offset,
            "unknown_zero_offset": unknown_offset, "remap_offset": remap_offset,
            "properties": [{k: v for k, v in p.items() if k != "raw"} for p in props.values()]}


def inspect_package(data):
    summary = parse_summary(data, len(data))
    if summary["compression_flags"] or summary["byte_order"] != "big":
        raise FormatError("Font payload reader requires uncompressed big-endian 446/25 package")
    tables = parse_tables(data, summary)
    fonts = []
    for export in tables["exports"]:
        if export["class_path"] != "Engine.Font":
            continue
        offset, size = export["serial_offset"], export["serial_size"]
        font = parse_font_payload(data[offset:offset + size], tables["names"])
        font.update({"path": export["path"], "serial_offset": offset, "serial_size": size})
        atlas = []
        for ref in font["textures"]:
            if not 1 <= ref <= len(tables["exports"]):
                raise FormatError("font texture does not reference local export")
            texture = tables["exports"][ref - 1]
            if texture["class_path"] != "Engine.Texture2D":
                raise FormatError("font texture reference has wrong class")
            r = Reader(data[texture["serial_offset"]:texture["serial_offset"] + texture["serial_size"]])
            r.i32()
            props = unique_properties(read_properties(r, tables["names"]))
            width, height = int_property(props["SizeX"]), int_property(props["SizeY"])
            if width <= 0 or height <= 0:
                raise FormatError("invalid texture dimensions")
            atlas.append({"reference": ref, "path": texture["path"], "width": width, "height": height,
                          "serial_offset": texture["serial_offset"], "serial_size": texture["serial_size"]})
        anomalies = []
        for glyph_index, glyph in enumerate(font["characters"]):
            texture = atlas[glyph["TextureIndex"]]
            if glyph["StartU"] + glyph["USize"] > texture["width"] or glyph["StartV"] + glyph["VSize"] > texture["height"]:
                anomalies.append({"glyph_index": glyph_index, "issue": "rectangle exceeds tagged atlas dimensions"})
        font["atlas_bounds_anomalies"] = anomalies
        font["atlases"] = atlas
        font["character_count"] = len(font["characters"])
        font["remap_count"] = len(font["remap"])
        font["all_tagged_native_fields_equal"] = True
        fonts.append(font)
    return {"schema_version": 1, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "profile": "446/25-big-uncompressed", "font_count": len(fonts), "fonts": fonts,
            "offset_convention": "Font field offsets relative to serial_offset; atlas serial offsets package-absolute",
            "runtime_coverage_verified": False, "texture_pixels_decoded": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.package.resolve() == args.output.resolve() or args.output.exists():
            raise FormatError("output must be a new file different from input")
        result = inspect_package(args.package.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
        print(json.dumps({"font_count": result["font_count"], "sha256": result["sha256"],
                          "glyph_counts": {f["path"]: f["character_count"] for f in result["fonts"]}}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

