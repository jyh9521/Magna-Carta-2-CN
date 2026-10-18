"""Read-only UE3 446/25 package table reader; never deserializes object payloads."""
# Copyright (c) 2026 jyh9521
# MIT; adapted from MagnaCarta2-Recompiled bc0d93ae886a9ebfd998b48b7ec30cf0f92e0c47.
from __future__ import annotations
import argparse
import ctypes
import math
import os
import tempfile
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

TOOL_VERSION = "0.3.0"
class FormatError(ValueError):
    pass

class Reader:
    def __init__(self, data: bytes, endian: str = ">", unicode_endian: str | None = None):
        self.data, self.pos, self.endian = data, 0, endian
        self.unicode_endian = unicode_endian or endian
    def read(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.data):
            raise FormatError(f"range outside buffer at {self.pos}: {n}")
        b = self.data[self.pos:self.pos+n]; self.pos += n
        return b
    def u32(self): return struct.unpack(self.endian + "I", self.read(4))[0]
    def i32(self): return struct.unpack(self.endian + "i", self.read(4))[0]
    def count(self, limit=1_000_000):
        n = self.i32()
        if not 0 <= n <= limit: raise FormatError(f"invalid count: {n}")
        return n
    def string(self):
        n = self.i32()
        if abs(n) > 1_048_576: raise FormatError(f"invalid string length: {n}")
        if not n: return ""
        raw = self.read(abs(n) * (2 if n < 0 else 1))
        term = b"\0\0" if n < 0 else b"\0"
        if not raw.endswith(term): raise FormatError("unterminated FString")
        try: return raw[:-len(term)].decode(("utf-16-be" if self.unicode_endian == ">" else "utf-16-le") if n < 0 else "utf-8")
        except UnicodeError as exc: raise FormatError(f"invalid FString encoding: {exc}") from exc
    def seek(self, offset):
        if not 0 <= offset <= len(self.data): raise FormatError(f"invalid offset: {offset}")
        self.pos = offset

def parse_summary(data: bytes, file_size: int | None = None):
    """Parse the supported profile only; offsets remain logical when compressed."""
    magic = data[:4]
    if magic not in (b"\x9e\x2a\x83\xc1", b"\xc1\x83\x2a\x9e"):
        raise FormatError("not a UE package magic")
    r = Reader(data, ">" if magic[0] == 0x9e else "<"); r.read(4)
    word = r.u32(); version, licensee = word & 0xffff, word >> 16
    if (version, licensee) != (446, 25):
        raise FormatError(f"unsupported serialization profile: {version}/{licensee}")
    out = {"version":version,"licensee_version":licensee,"byte_order":"big" if r.endian==">" else "little"}
    out["header_size"] = r.u32(); out["package_group"] = r.string(); out["package_flags"] = r.u32()
    for label in ("name", "export", "import"):
        out[label+"_count"] = r.count(); out[label+"_offset"] = r.u32()
    out["depends_offset"] = r.u32(); out["guid"] = r.read(16).hex()
    out["generations"] = [{"export_count":r.count(),"name_count":r.count(),"net_object_count":r.count()} for _ in range(r.count(1024))]
    out["engine_version"] = r.u32(); out["cooker_version"] = r.u32(); out["compression_flags"] = r.u32()
    out["compressed_chunks"] = []
    previous_end = 0
    for _ in range(r.count(65536)):
        c = dict(zip(("uncompressed_offset","uncompressed_size","compressed_offset","compressed_size"), [r.u32() for _ in range(4)]))
        if not c["uncompressed_size"] or not c["compressed_size"]: raise FormatError("empty compressed chunk")
        if c["uncompressed_offset"] < previous_end: raise FormatError("overlapping or unordered logical chunks")
        previous_end = c["uncompressed_offset"] + c["uncompressed_size"]
        if file_size is not None and c["compressed_offset"] + c["compressed_size"] > file_size: raise FormatError("compressed chunk outside file")
        out["compressed_chunks"].append(c)
    out["summary_end"] = r.pos
    chunks = out["compressed_chunks"]
    physical_ranges = sorted((c["compressed_offset"], c["compressed_offset"] + c["compressed_size"]) for c in chunks)
    for i, (start, end) in enumerate(physical_ranges):
        if start < r.pos: raise FormatError("compressed chunk overlaps summary")
        if i and start < physical_ranges[i-1][1]: raise FormatError("overlapping physical chunks")
    if bool(chunks) != bool(out["compression_flags"]): raise FormatError("compression flags/chunks mismatch")
    logical_size = max([file_size or len(data)] + [c["uncompressed_offset"]+c["uncompressed_size"] for c in chunks])
    for label in ("name", "export", "import"):
        if out[label+"_count"] and not (r.pos-len(chunks)*16) <= out[label+"_offset"] < logical_size: raise FormatError(f"invalid {label} table offset")
    if not r.pos <= out["header_size"] <= logical_size: raise FormatError("invalid header size")
    return out

def parse_tables(data: bytes, summary=None, logical_size=None):
    s = summary or parse_summary(data, len(data))

    r = Reader(data, ">" if s["byte_order"] == "big" else "<", "<")
    r.seek(s["name_offset"]); names=[]
    for _ in range(s["name_count"]): names.append(r.string()); r.read(8)
    name_end = r.pos
    def fname():
        i, n = r.u32(), r.u32()
        if i >= len(names): raise FormatError(f"invalid FName index: {i}")
        return {"index":i,"number":n,"name":names[i] if not n else f"{names[i]}_{n-1}"}
    def ref():
        v = r.i32()
        if not -s["import_count"] <= v <= s["export_count"]: raise FormatError(f"invalid object reference: {v}")
        return v
    r.seek(s["import_offset"]); imports=[]
    for _ in range(s["import_count"]):
        imports.append({"class_package":fname(),"class_name":fname(),"outer":ref(),"object_name":fname()})
    import_end = r.pos
    r.seek(s["export_offset"]); exports=[]
    for _ in range(s["export_count"]):
        start=r.pos
        e={"class":ref(),"super":ref(),"outer":ref(),"object_name":fname(),"archetype":ref(),"object_flags":r.read(8).hex(),"serial_size":r.u32(),"serial_offset":r.u32()}
        if e["serial_size"] and (e["serial_offset"] < s["header_size"] or e["serial_offset"]+e["serial_size"]>(logical_size or len(data))): raise FormatError("export serial range outside package")
        e["components"]=[{"name":fname(),"object":ref()} for _ in range(r.count())]
        e["export_flags"]=r.u32(); e["net_object_counts"]=[r.count() for _ in range(r.count(65536))]; e["guid"]=r.read(16).hex()
        e["table_offset"]=start; exports.append(e)
    export_end = r.pos
    ranges=sorted((a,b,label) for a,b,label in ((s["name_offset"],name_end,"name"),(s["import_offset"],import_end,"import"),(s["export_offset"],export_end,"export")) if b>a)
    for i,(a,b,label) in enumerate(ranges):
        if b>s["header_size"]: raise FormatError(f"{label} table exceeds header")
        if i and a<ranges[i-1][1]: raise FormatError("overlapping tables")
    def path(index):
        seen=set(); parts=[]
        while index:
            if index in seen: raise FormatError("cyclic object outer")
            seen.add(index); obj=imports[-index-1] if index<0 else exports[index-1]
            parts.append(obj["object_name"]["name"]); index=obj["outer"]
        return ".".join(reversed(parts))
    for i,obj in enumerate(imports): obj["path"]=path(-i-1)
    for i,obj in enumerate(exports):
        obj["path"]=path(i+1); obj["class_path"]=path(obj["class"]) if obj["class"] else "Class"
    edges=[]
    for i,obj in enumerate(exports):
        for field in ("class","super","outer","archetype"):
            if obj[field]: edges.append({"source":i+1,"field":field,"target":obj[field]})
        for component in obj["components"]:
            if component["object"]: edges.append({"source":i+1,"field":"component","target":component["object"]})
    dependencies=sorted({i["path"].split(".")[0] for i in imports if i["class_name"]["name"]=="Package"})
    return {"names":names,"imports":imports,"exports":exports,"table_edges":edges,"package_dependencies":dependencies,"table_ends":{"name":name_end,"import":import_end,"export":export_end}}

def strip_lzx_frames(data: bytes) -> bytes:
    """Remove Xbox LZX framing (2-byte size or FF/u16 output/u16 input)."""
    r=Reader(data); out=bytearray()
    while r.pos<len(data):
        first=r.read(1)[0]
        if first==255:
            expected=int.from_bytes(r.read(2),"big"); size=int.from_bytes(r.read(2),"big")
            if not 1<=expected<=32768: raise FormatError("invalid LZX frame output size")
        else:
            size=(first<<8)|r.read(1)[0]
        if not size:
            if any(data[r.pos:]): raise FormatError("nonzero bytes after LZX terminator")
            break
        out.extend(r.read(size))
    return bytes(out)

class LzxDecoder:
    def __init__(self, library: Path):
        self.library=ctypes.CDLL(str(library.resolve()))
        self.function=self.library.ue3_lzx
        self.function.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
        self.function.restype=ctypes.c_int
    def __call__(self, data, size):
        if not 0<size<=128*1024*1024: raise FormatError("LZX output size exceeds limit")
        raw=strip_lzx_frames(data); output=ctypes.create_string_buffer(size)
        result=self.function(raw,len(raw),output,size)
        if result: raise FormatError(f"libmspack LZX failed: {result}")
        return output.raw

def package_header(data, summary, decoder):
    """Recover only logical header chunks; object payloads are not returned."""
    if not summary["compression_flags"]: return data
    if summary["compression_flags"]!=4: raise FormatError("unsupported compression flags")
    if decoder is None: raise FormatError("LZX decoder not configured")
    size=summary["header_size"]
    if size>128*1024*1024: raise FormatError("header exceeds limit")
    out=bytearray(size); covered=0
    for c in summary["compressed_chunks"]:
        off=c["uncompressed_offset"]
        if off>=size: break
        if not covered:
            if off > len(data): raise FormatError("header prefix outside package")
            out[:off]=data[:off]; covered=off
        if off!=covered: raise FormatError("gap in compressed header chunks")
        r=Reader(data); r.seek(c["compressed_offset"])
        if r.u32()!=0x9e2a83c1: raise FormatError("invalid chunk magic")
        block_size,total_comp,total_uncomp=r.u32(),r.u32(),r.u32()
        if not 0<block_size<=16*1024*1024 or total_uncomp!=c["uncompressed_size"]: raise FormatError("invalid chunk sizes")
        blocks=[(r.u32(),r.u32()) for _ in range(math.ceil(total_uncomp/block_size))]
        if sum(v[0] for v in blocks)!=total_comp or sum(v[1] for v in blocks)!=total_uncomp: raise FormatError("compressed block totals mismatch")
        if r.pos+total_comp!=c["compressed_offset"]+c["compressed_size"]: raise FormatError("chunk physical size mismatch")
        for comp,uncomp in blocks:
            if not 0<uncomp<=block_size: raise FormatError("invalid block output size")
            if off<size:
                decoded=decoder(r.read(comp),uncomp)
                if len(decoded) != uncomp: raise FormatError("invalid decoder output length")
                end=min(off+uncomp,size); out[off:end]=decoded[:end-off]
            else: r.read(comp)
            off+=uncomp
        covered=off
        if covered>=size: break
    if covered<size: raise FormatError("compressed header incomplete")
    return bytes(out)

def analyze_package(data: bytes, expected_sha256: str, decoder=None):
    """Hash-guard a standalone original package and report metadata, never payloads."""
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected_sha256):
        raise FormatError("expected SHA-256 must contain 64 hexadecimal characters")
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256.lower():
        raise FormatError("package SHA-256 mismatch")
    summary = parse_summary(data, len(data))
    result = {"schema_version": 1, "tool_version": TOOL_VERSION,
              "size": len(data), "sha256": digest, "summary": summary}
    if summary["compression_flags"] and decoder is None:
        result.update(status="summary-only", reason=f"compression flags={summary['compression_flags']}; decoder not configured; tables not validated")
    else:
        header = package_header(data, summary, decoder)
        logical_size = max([len(data)] + [c["uncompressed_offset"] + c["uncompressed_size"]
                                         for c in summary["compressed_chunks"]])
        tables = parse_tables(header, summary, logical_size)
        result.update(tables)
        result["class_histogram"] = dict(Counter(x["class_path"] for x in tables["exports"]))
        result["status"] = "tables-validated"
    return result


def write_report(output: Path, report):
    """Publish complete JSON exclusively; never truncate an existing destination."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=output.name + ".", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Same-directory hard-link publishes atomically and fails if output exists.
        os.link(tmp, output)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--lzx-library", type=Path,
                        help="optional trusted native adapter exporting ue3_lzx; not bundled")
    args = parser.parse_args(argv)
    try:
        inputs = [args.package] + ([args.lzx_library] if args.lzx_library else [])
        if any(args.output.resolve() == path.resolve() for path in inputs):
            raise FormatError("output must differ from inputs")
        if args.output.exists() or args.output.is_symlink():
            raise FormatError("output already exists")
        data = args.package.read_bytes()
        # Verify before loading any optional native adapter.
        result = analyze_package(data, args.sha256)
        if args.lzx_library:
            result = analyze_package(data, args.sha256, LzxDecoder(args.lzx_library))
        write_report(args.output, result)
        print(json.dumps({"status": result["status"], "sha256": result["sha256"],
                          "names": result["summary"]["name_count"],
                          "imports": result["summary"]["import_count"],
                          "exports": result["summary"]["export_count"]}, sort_keys=True))
        return 0
    except (OSError, FormatError, ValueError, AttributeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
