"""Emit a hash-guarded uncompressed UE3 446/25 copy for local runtime experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header
except ImportError:
    from ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header


def decompress_copy(data, expected_hash, decoder, alignment=32768):
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise FormatError("package SHA256 mismatch")
    if type(alignment) is not int or alignment not in (1, 2048, 32768):
        raise FormatError("unsupported output alignment")
    s = parse_summary(data, len(data))
    if s['byte_order'] != 'big' or s['compression_flags'] != 4:
        raise FormatError("requires big-endian LZX-compressed 446/25 input")
    if not s['package_flags'] & 0x02000000:
        raise FormatError("expected compressed package flag")
    chunks = s['compressed_chunks']
    boundary = s['summary_end'] - len(chunks) * 16
    if boundary != chunks[0]['uncompressed_offset']:
        raise FormatError("unsupported prefix layout")
    end = max(c['uncompressed_offset'] + c['uncompressed_size'] for c in chunks)
    original = package_header(data, {**s, 'header_size': end}, decoder)
    before = parse_tables(original, s, len(original))
    out = bytearray(original)
    r = Reader(data); r.read(12); r.string()
    flag_offset = r.pos
    if r.u32() != s['package_flags']:
        raise FormatError("package flag position mismatch")
    struct.pack_into('>I', out, flag_offset, s['package_flags'] & ~0x02000000)
    struct.pack_into('>II', out, boundary - 8, 0, 0)
    out.extend(bytes((-len(out)) % alignment))
    result = bytes(out)
    after = parse_tables(result)
    for key in ('names', 'imports', 'exports'):
        if before[key] != after[key]:
            raise FormatError("decompressed object tables differ")
    if result[boundary:end] != original[boundary:]:
        raise FormatError("logical payload changed")
    return result, dict(schema_version=1, input_sha256=expected_hash,
                        output_sha256=hashlib.sha256(result).hexdigest(),
                        output_size=len(result), alignment=alignment,
                        compression_flags=0, compressed_chunk_count=0,
                        cleared_package_flag='0x02000000', package_flag_offset=flag_offset,
                        logical_payload_preserved=True, game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path); p.add_argument('--sha256', required=True)
    p.add_argument('--lzx-library', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--report', type=Path, required=True)
    p.add_argument('--alignment', type=int, default=32768)
    a = p.parse_args(argv)
    try:
        inputs = [a.package.resolve(), a.lzx_library.resolve()]
        if a.output.resolve() == a.report.resolve() or any(
                x.exists() or x.is_symlink() or x.resolve() in inputs for x in (a.output, a.report)):
            raise FormatError('output/report must be new paths distinct from inputs')
        result, report = decompress_copy(a.package.read_bytes(), a.sha256,
                                         LzxDecoder(a.lzx_library), a.alignment)
        for x in (a.output, a.report):
            x.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('xb') as stream:
            stream.write(result)
        with a.report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2); stream.write('\n')
        if a.output.read_bytes() != result:
            raise FormatError('output reopening mismatch')
        print(json.dumps(report)); return 0
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc)); return 1


if __name__ == '__main__':
    raise SystemExit(main())
