"""Strict read-only native-field coverage for the verified UE3 446/25 profile.

This is not a text scanner. Counted arrays, numeric fields, references, compiled
shader envelopes and end offsets are consumed structurally, without treating
arbitrary byte patterns as FString values. Unsupported variants fail closed.
GPU instruction decoding and individual shader parameter names are not claimed.

Format research references (no upstream implementation copied):
UEViewer 882794d2624ae1db987da986e03b138b5d177787, UnMesh3.cpp;
LegendaryExplorer b5e746233491ec5a7cbfc077685996af37a3d125,
BinaryConverters/StaticMesh.cs and ShaderCache.cs. Those PC/ME profiles are not
assumed identical: the old node/triangle widths, missing ParameterMapCRC,
Xbox shader headers and the final global map were checked against local bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from .ue3_package import FormatError, LzxDecoder, Reader, parse_summary, parse_tables
from .ue3_fonts import read_properties
from .supplement_font import decode_logical


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise FormatError(message)


class NativeReader:
    def __init__(self, data, names, serial_offset):
        self.data = data
        self.names = names
        self.serial_offset = serial_offset
        self.reader = Reader(data, unicode_endian="<")
        self.fields = []

    @property
    def pos(self):
        return self.reader.pos

    def take(self, name, size, **metadata):
        start = self.pos
        raw = self.reader.read(size)
        self.fields.append(dict(name=name, relative_range=[start, self.pos],
                                sha256=digest(raw), **metadata))
        return raw

    def u32(self, name):
        value = struct.unpack(">I", self.take(name, 4, field_type="uint32"))[0]
        self.fields[-1]["value"] = value
        return value

    def i32(self, name):
        value = struct.unpack(">i", self.take(name, 4, field_type="int32"))[0]
        self.fields[-1]["value"] = value
        return value

    def count(self, name, limit=1_000_000):
        count = self.u32(name)
        require(count <= limit, f"{name}: count exceeds profile limit")
        return count

    def fname(self, name):
        start = self.pos
        index, number = struct.unpack(">II", self.take(name, 8, field_type="FName"))
        require(index < len(self.names) and number == 0,
                f"{name}: unsupported FName index or instance")
        result = dict(index=index, number=number, name=self.names[index],
                      relative_offset=start)
        self.fields[-1]["value"] = result
        return result

    def array(self, name, element_size):
        count = self.count(name + ".count")
        return self.take(name, count * element_size, field_type="numeric-array",
                         element_size=element_size, count=count)

    def prefix(self):
        self.i32("NetIndex")
        start = self.pos
        props = read_properties(self.reader, self.names)
        end = self.pos
        self.fields.append(dict(name="TaggedPropertiesIncludingNone", relative_range=[start, end],
                                sha256=digest(self.data[start:end]), field_type="tagged-properties"))
        strings = []
        for prop in props:
            if prop["type"] == "StrProperty":
                reader = Reader(prop["raw"], unicode_endian="<")
                value = reader.string()
                require(reader.pos == len(prop["raw"]), "trailing StrProperty bytes")
                strings.append(dict(name=prop["name"], array_index=prop["array_index"],
                                    relative_offset=prop["value_offset"], value=value))
        return strings

    def finish(self, **details):
        require(self.pos == len(self.data), "unparsed native trailing bytes")
        at = 0
        for field in self.fields:
            start, end = field["relative_range"]
            require(start == at and end >= start, "non-contiguous field coverage")
            at = end
        require(at == len(self.data), "incomplete field coverage")
        return dict(payload_sha256=digest(self.data), payload_size=len(self.data),
                    fully_consumed=True, fields=self.fields, **details)


def parse_static_mesh_payload(data, names, serial_offset, import_count, export_count):
    """Read the verified old StaticMesh InternalVersion15 numeric layout."""
    r = NativeReader(data, names, serial_offset)
    tagged_strings = r.prefix()
    bounds = struct.unpack(">7f", r.take("Bounds", 28, field_type="7-float32"))
    require(all(math.isfinite(v) for v in bounds), "non-finite mesh bounds")
    body_setup = r.i32("BodySetup")
    require(-import_count <= body_setup <= export_count, "invalid BodySetup reference")
    r.array("KDOP.Nodes", 36)
    r.array("KDOP.Triangles", 16)
    version = r.u32("InternalVersion")
    require(version == 15, "unsupported StaticMesh InternalVersion")
    lod_count = r.count("LODs.count", 16)
    require(lod_count > 0, "empty LOD array is outside verified profile")
    lods = []
    for li in range(lod_count):
        prefix = f"LODs[{li}]"
        flags = r.u32(prefix + ".RawTriangles.flags")
        elements = r.u32(prefix + ".RawTriangles.elements")
        size = r.u32(prefix + ".RawTriangles.size")
        offset = r.u32(prefix + ".RawTriangles.offset")
        require(flags == elements == size == 0 and offset == serial_offset + r.pos,
                "unsupported/non-inline raw triangle bulk")
        sections = []
        for si in range(r.count(prefix + ".Sections.count", 1000)):
            fields = list(struct.unpack(">7i", r.take(f"{prefix}.Sections[{si}]", 28,
                                                    field_type="reference-and-six-int32")))
            require(-import_count <= fields[0] <= export_count, "invalid section material reference")
            sections.append(fields)
        uv_sets = r.u32(prefix + ".UVSets")
        stride = r.u32(prefix + ".VertexStride")
        num_vertices = r.u32(prefix + ".NumVertices")
        require(1 <= uv_sets <= 8 and stride == 32 + 8 * uv_sets, "unsupported vertex/UV stride")
        count = r.count(prefix + ".VertexUV.count")
        require(count == num_vertices, "vertex count mismatch")
        vertices = r.take(prefix + ".VertexUV", stride * count,
                          field_type="position-color-packed-normal-float-UV-array",
                          element_size=stride, count=count)
        for at in range(0, len(vertices), stride):
            require(all(math.isfinite(v) for v in struct.unpack_from(">3f", vertices, at)),
                    "non-finite vertex position")
        require(r.u32(prefix + ".NumVerticesDuplicate") == num_vertices, "duplicate vertex count mismatch")
        for label in ("Indices", "WireframeIndices"):
            raw = r.array(prefix + "." + label, 2)
            require(all(v[0] < num_vertices for v in struct.iter_unpack(">H", raw)),
                    "index outside vertex array")
        r.array(prefix + ".Edges", 16)
        r.array(prefix + ".FaceFlags", 1)
        lods.append(dict(index=li, sections=sections, uv_sets=uv_sets,
                         vertex_stride=stride, num_vertices=num_vertices))
    footer = list(struct.unpack(">5I", r.take("Version15Footer", 20, field_type="five-uint32")))
    require(footer == [1, 0, 0, 0, 0], "unsupported Version15 footer profile")
    return r.finish(profile="UE3-446-25-StaticMesh-InternalVersion15", bounds=bounds,
                    body_setup=body_setup, internal_version=version, lods=lods,
                    footer_words=footer, tagged_strings=tagged_strings, native_string_fields=0,
                    footer_word_semantic_names_known=False, native_semantic_coverage_complete=True)


def parse_shader_cache_payload(data, names, serial_offset):
    """Read the verified Xbox global-cache profile, including all references.

    Non-empty material shader maps are rejected: unlike the present global-only
    profile those can contain native FriendlyName FString fields.
    """
    r = NativeReader(data, names, serial_offset)
    tagged_strings = r.prefix()
    platform = r.take("Platform", 1, field_type="byte")[0]
    require(platform == 2, "unsupported shader platform")
    crc_maps = []
    for label in ("ShaderTypeCRCMap", "VertexFactoryTypeCRCMap"):
        entries = []
        for i in range(r.count(label + ".count", 10000)):
            name = r.fname(f"{label}[{i}].Name")
            crc = r.u32(f"{label}[{i}].CRC")
            entries.append(dict(type=name, crc=crc))
        crc_maps.append(dict(name=label, entries=entries))
    shaders = []
    for i in range(r.count("Shaders.count", 10000)):
        prefix = f"Shaders[{i}]"
        start = r.pos
        name = r.fname(prefix + ".Type")
        guid = r.take(prefix + ".GUID", 16, field_type="GUID").hex()
        end = r.u32(prefix + ".EndOffset") - serial_offset
        shader_platform, frequency = r.take(prefix + ".Target", 2, field_type="two-byte-enums")
        require(shader_platform == platform and frequency in (0, 1), "shader target mismatch")
        size = r.count(prefix + ".BytecodeSize", 16 * 1024 * 1024)
        code_start = r.pos
        code = r.take(prefix + ".Bytecode", size, field_type="compiled-Xbox-GPU-program")
        require(size >= 48, "truncated compiled shader header")
        header = struct.unpack_from(">12I", code)
        require(header[0] == (0x102a1101 if frequency == 0 else 0x102a1100), "shader signature/frequency mismatch")
        require(header[1] + header[2] == size and header[1] >= 48
                and header[1] % 4 == 0 and header[2] % 4 == 0,
                "compiled shader header/body size mismatch")
        require(r.take(prefix + ".GUIDDuplicate", 16, field_type="GUID").hex() == guid,
                "duplicate shader GUID mismatch")
        duplicate = r.fname(prefix + ".TypeDuplicate")
        require(duplicate["index"] == name["index"], "duplicate shader type mismatch")
        instructions = r.u32(prefix + ".InstructionCount")
        require(r.pos <= end <= len(data), "shader end offset outside record")
        require((end - r.pos) % 4 == 0, "shader parameter pair alignment mismatch")
        parameter_start = r.pos
        raw = r.take(prefix + ".ParameterBindings", end - r.pos,
                     field_type="bounded-shader-subclass-data", inferred_element_size=4,
                     semantic_grade="High-confidence deduction",
                     inferred_interpretation="uint16 base-register/count pairs; native serializer not traced")
        pairs = list(struct.iter_unpack(">HH", raw))
        require(all(count <= 32 and (count == 0 or base + count <= 256) for base, count in pairs),
                "shader parameter register pair outside profile")
        shaders.append(dict(index=i, type=name, guid=guid, relative_range=[start, end],
                            frequency=frequency, instructions=instructions,
                            bytecode_range=[code_start, code_start + size],
                            compiled_header_words=list(header), bytecode_sha256=digest(code),
                            parameter_range=[parameter_start, end], inferred_parameter_register_pairs=pairs))
    material_count = r.u32("MaterialShaderMaps.count")
    require(material_count == 0, "non-empty material shader maps need native FString parser")
    global_map = []
    for i in range(r.count("GlobalShaderMap.count", 10000)):
        prefix = f"GlobalShaderMap[{i}]"
        name = r.fname(prefix + ".KeyType")
        guid = r.take(prefix + ".GUID", 16, field_type="GUID").hex()
        duplicate = r.fname(prefix + ".ValueType")
        require(duplicate["index"] == name["index"], "global shader key/value type mismatch")
        matches = [shader for shader in shaders if shader["guid"] == guid
                   and shader["type"]["index"] == name["index"]]
        require(len(matches) == 1, "global shader reference does not resolve uniquely")
        global_map.append(dict(type=name, guid=guid, shader_index=matches[0]["index"]))
    require(len(global_map) == len(shaders)
            and len({entry["shader_index"] for entry in global_map}) == len(shaders),
            "global shader map does not bijectively reference compiled shaders")
    unresolved = [dict(shader_index=shader["index"], type=shader["type"]["name"],
                       relative_range=shader["parameter_range"],
                       byte_count=shader["parameter_range"][1] - shader["parameter_range"][0],
                       semantic_grade="High-confidence deduction")
                  for shader in shaders if shader["parameter_range"][1] > shader["parameter_range"][0]]
    return r.finish(profile="UE3-446-25-Xbox-global-shader-cache", platform=platform,
                    crc_maps=crc_maps, shaders=shaders, global_shader_map=global_map,
                    material_shader_maps_count=material_count, tagged_strings=tagged_strings,
                    known_native_string_fields=0, native_string_fields=None,
                    parameter_slot_names_known=False, native_semantic_coverage_complete=not unresolved,
                    semantic_unresolved_regions=unresolved,
                    semantic_unresolved_bytes=sum(region["byte_count"] for region in unresolved),
                    gpu_instruction_semantics_decoded=False)


def inspect_package(raw, expected_sha256, class_paths, decoder=None):
    require(digest(raw) == expected_sha256, "source package SHA-256 mismatch")
    summary = parse_summary(raw, len(raw))
    require((summary["version"], summary["licensee_version"], summary["byte_order"])
            == (446, 25, "big"), "unsupported package version")
    logical = decode_logical(raw, summary, decoder)
    tables = parse_tables(logical, summary, len(logical))
    supported = {"Engine.StaticMesh", "Engine.ShaderCache"}
    require(set(class_paths) <= supported and class_paths, "unsupported native coverage class")
    objects = []
    for index, export in enumerate(tables["exports"], 1):
        if export["class_path"] not in class_paths:
            continue
        start = export["serial_offset"]
        payload = logical[start:start + export["serial_size"]]
        if export["class_path"] == "Engine.StaticMesh":
            report = parse_static_mesh_payload(payload, tables["names"], start,
                                               len(tables["imports"]), len(tables["exports"]))
        else:
            report = parse_shader_cache_payload(payload, tables["names"], start)
        objects.append(dict(export=index, path=export["path"], class_path=export["class_path"],
                            serial_offset=start, **report))
    require(objects, "no selected native exports")
    return dict(schema_version=1, package_sha256=expected_sha256, objects=objects,
                full_selected_payload_coverage=True, game_resources_written=False,
                complete_game_language_coverage_claimed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--class", dest="classes", action="append", required=True)
    parser.add_argument("--lzx", type=Path)
    parser.add_argument("--lzx-sha256")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists() and not args.output.is_symlink(), "output must be a new file")
    inputs = [args.package] + ([args.lzx] if args.lzx else [])
    require(all(args.output.resolve() != source.resolve() for source in inputs),
            "output must be distinct from every input")
    raw = args.package.read_bytes()
    require(digest(raw) == args.sha256, "source package SHA-256 mismatch")
    summary = parse_summary(raw, len(raw))
    require((summary["version"], summary["licensee_version"], summary["byte_order"])
            == (446, 25, "big"), "unsupported package version")
    if args.lzx:
        require(args.lzx_sha256 and digest(args.lzx.read_bytes()) == args.lzx_sha256,
                "LZX DLL SHA-256 mismatch or missing lock")
    else:
        require(not args.lzx_sha256, "LZX hash supplied without DLL")
    decoder = LzxDecoder(args.lzx) if args.lzx else None
    result = inspect_package(raw, args.sha256, args.classes, decoder)
    output = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(output)
    require(args.output.read_bytes() == output, "report readback mismatch")
    require(args.package.read_bytes() == raw, "source changed during read-only audit")
    print(f"NATIVE_COVERAGE objects={len(result['objects'])} fully_consumed=true source_unchanged=true")


if __name__ == "__main__":
    main()
