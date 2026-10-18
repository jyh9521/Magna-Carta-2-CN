"""Read direct UE3 UIStyle font references; static links are not runtime binding."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header, write_report
    from .ue3_fonts import read_properties
except ImportError:
    from ue3_package import FormatError, Reader, LzxDecoder, parse_summary, parse_tables, package_header, write_report
    from ue3_fonts import read_properties


def inspect_links(logical, tables):
    links, unparsed = [], []
    for index, export in enumerate(tables['exports'], 1):
        if export['class_path'] not in ('Engine.UIStyle_Text', 'Engine.UIStyle_Combo'):
            continue
        try:
            start, size = export['serial_offset'], export['serial_size']
            if start < 0 or size < 4 or start + size > len(logical):
                raise FormatError('style payload outside logical package')
            r = Reader(logical[start:start + size]); r.i32()
            props = read_properties(r, tables['names'])
            font_props = [p for p in props if p['name'] == 'StyleFont']
            if len(font_props) > 1:
                raise FormatError('duplicate StyleFont property')
            for prop in font_props:
                if prop['type'] != 'ObjectProperty' or len(prop['raw']) != 4:
                    raise FormatError('StyleFont is not an object reference')
                ref = struct.unpack('>i', prop['raw'])[0]
                if not -len(tables['imports']) <= ref <= len(tables['exports']):
                    raise FormatError('font reference outside object tables')
                target = tables['exports'][ref - 1] if ref > 0 else tables['imports'][-ref - 1] if ref < 0 else None
                if ref > 0 and target['class_path'] != 'Engine.Font':
                    raise FormatError('local StyleFont has non-Font class')
                if ref < 0 and target['class_name']['name'] != 'Font':
                    raise FormatError('imported StyleFont has non-Font class')
                links.append(dict(object_index=index, object=export['path'], serial_offset=start,
                                  property='StyleFont', font_reference=ref,
                                  font_path=target['path'] if target else None,
                                  binding_kind='direct-serialized-reference'))
        except (ValueError, KeyError) as exc:
            unparsed.append(dict(object=export['path'], reason=str(exc)))
    return dict(font_bindings=links, unparsed=unparsed, runtime_binding_verified=False,
                inheritance_resolved=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path); p.add_argument('--sha256', required=True)
    p.add_argument('--lzx-library', type=Path); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        raw = a.package.read_bytes()
        if hashlib.sha256(raw).hexdigest() != a.sha256.lower():
            raise FormatError('package SHA256 mismatch')
        s = parse_summary(raw, len(raw))
        total = max([len(raw)] + [c['uncompressed_offset'] + c['uncompressed_size'] for c in s['compressed_chunks']])
        logical = package_header(raw, dict(s, header_size=total), LzxDecoder(a.lzx_library) if a.lzx_library else None)
        tables = parse_tables(logical, s, total)
        result = dict(schema_version=1, sha256=a.sha256.lower(), **inspect_links(logical, tables))
        write_report(a.output, result)
        print(json.dumps(dict(font_bindings=len(result['font_bindings']), unparsed=len(result['unparsed']), runtime_binding_verified=False), sort_keys=True))
        return int(bool(result['unparsed']))
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
