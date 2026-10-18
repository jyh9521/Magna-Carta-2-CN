"""Read tagged *FontName defaults without claiming runtime font selection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header
    from .ue3_fonts import read_properties
except ImportError:
    from ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header
    from ue3_fonts import read_properties


def tagged_font_names(payload, names):
    r = Reader(payload)
    r.i32()  # NetIndex
    props = read_properties(r, names)
    refs, seen = [], set()
    for p in props:
        if not p['name'].endswith('FontName'):
            continue
        if p['name'] in seen or p['array_index'] or p['type'] != 'StrProperty':
            raise FormatError('unsupported duplicate/indexed/non-string FontName')
        seen.add(p['name'])
        value = Reader(p['raw'])
        path = value.string()
        if value.pos != len(p['raw']):
            raise FormatError('FontName trailing bytes')
        refs.append(dict(property=p['name'], value=path, value_offset=p['value_offset']))
    return refs


def inspect(data, expected_hash, object_path='Default__Engine', decoder=None):
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise FormatError('package SHA256 mismatch')
    s = parse_summary(data, len(data))
    if s['byte_order'] != 'big':
        raise FormatError('requires big-endian 446/25 profile')
    end = (max(c['uncompressed_offset'] + c['uncompressed_size'] for c in s['compressed_chunks'])
           if s['compression_flags'] else len(data))
    logical = package_header(data, {**s, 'header_size': end}, decoder)
    t = parse_tables(logical, s, len(logical))
    exports = [e for e in t['exports'] if e['path'] == object_path]
    if len(exports) != 1:
        raise FormatError('expected one selected defaults export')
    e = exports[0]
    refs = tagged_font_names(logical[e['serial_offset']:e['serial_offset'] + e['serial_size']], t['names'])
    for ref in refs:
        ref['logical_package_offset'] = e['serial_offset'] + ref['value_offset']
    return dict(schema_version=1, source_sha256=expected_hash, object_path=object_path,
                references=refs, interpretation='serialized defaults, not effective runtime selection',
                game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('--sha256', required=True)
    p.add_argument('--object', default='Default__Engine')
    p.add_argument('--lzx-library', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in (
                a.package.resolve(), a.lzx_library.resolve() if a.lzx_library else None):
            raise FormatError('output must be new and distinct from inputs')
        decoder = LzxDecoder(a.lzx_library) if a.lzx_library else None
        result = inspect(a.package.read_bytes(), a.sha256, a.object, decoder)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
        if json.loads(a.output.read_text(encoding='utf-8')) != result:
            raise FormatError('output reopening mismatch')
        print(json.dumps(result)); return 0
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc)); return 1


if __name__ == '__main__':
    raise SystemExit(main())
