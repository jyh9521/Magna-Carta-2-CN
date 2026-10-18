"""Create a same-size, hash-guarded existing-glyph remap probe (not a release patch)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .ue3_package import FormatError, parse_summary, parse_tables
    from .ue3_fonts import parse_font_payload
except ImportError:
    from ue3_package import FormatError, parse_summary, parse_tables
    from ue3_fonts import parse_font_payload


def probe(data, expected_hash, font_object, codepoint, expected_glyph, target_glyph):
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise FormatError('package SHA256 mismatch')
    for value in (codepoint, expected_glyph, target_glyph):
        if type(value) is not int or not 0 <= value <= 65535:
            raise FormatError('probe fields require uint16 integers')
    if expected_glyph == target_glyph:
        raise FormatError('probe must change the mapping')
    summary = parse_summary(data)
    if summary['byte_order'] != 'big' or summary['compression_flags'] or summary['package_flags'] & 0x02000000:
        raise FormatError('probe requires uncompressed big-endian package')
    tables = parse_tables(data, summary)
    exports = [e for e in tables['exports'] if e['path'] == font_object and e['class_path'] == 'Engine.Font']
    if len(exports) != 1:
        raise FormatError('expected exactly one selected Font export')
    e = exports[0]
    start, size = e['serial_offset'], e['serial_size']
    font = parse_font_payload(data[start:start + size], tables['names'])
    mappings = [r for r in font['remap'] if r['codepoint'] == codepoint]
    if len(mappings) != 1 or mappings[0]['glyph_index'] != expected_glyph:
        raise FormatError('expected original codepoint/glyph mapping mismatch')
    if target_glyph >= len(font['characters']):
        raise FormatError('target glyph outside existing Characters')
    offset = start + mappings[0]['offset'] + 2
    out = bytearray(data)
    struct.pack_into('>H', out, offset, target_glyph)
    result = bytes(out)
    checked = parse_font_payload(result[start:start + size], tables['names'])
    expected = {**mappings[0], 'glyph_index': target_glyph}
    if expected not in checked['remap'] or any(font[k] != checked[k] for k in font if k != 'remap'):
        raise FormatError('unexpected Font payload delta')
    if result[:offset] != data[:offset] or result[offset + 2:] != data[offset + 2:]:
        raise FormatError('bytes outside selected glyph-index field changed')
    return result, dict(schema_version=1, input_sha256=expected_hash,
                        output_sha256=hashlib.sha256(result).hexdigest(),
                        font_object=font_object, codepoint=codepoint,
                        expected_glyph=expected_glyph, target_glyph=target_glyph,
                        field_offset=offset, field_size=2, size=len(result),
                        game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('--sha256', required=True)
    p.add_argument('--font-object', required=True)
    for name in ('codepoint', 'expected-glyph', 'target-glyph'):
        p.add_argument('--' + name, type=lambda x: int(x, 0), required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.output.resolve() == a.report.resolve() or any(
                x.exists() or x.is_symlink() or x.resolve() == a.package.resolve()
                for x in (a.output, a.report)):
            raise FormatError('output/report must be new distinct paths')
        result, report = probe(a.package.read_bytes(), a.sha256, a.font_object,
                               a.codepoint, a.expected_glyph, a.target_glyph)
        for path in (a.output, a.report):
            path.parent.mkdir(parents=True, exist_ok=True)
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
