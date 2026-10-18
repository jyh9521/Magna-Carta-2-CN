"""Inspect FontName defaults or embedded Font classes without inferring runtime use."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

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


def _tables(data, expected_hash, decoder):
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise FormatError('package SHA256 mismatch')
    s = parse_summary(data, len(data))
    if s['byte_order'] != 'big':
        raise FormatError('requires big-endian 446/25 profile')
    end = (max(c['uncompressed_offset'] + c['uncompressed_size'] for c in s['compressed_chunks'])
           if s['compression_flags'] else len(data))
    logical = package_header(data, {**s, 'header_size': end}, decoder)
    return logical, parse_tables(logical, s, len(logical))


def inventory(data, expected_hash, decoder=None):
    """List Font-class exports wherever embedded; do not infer payload or use."""
    _, tables = _tables(data, expected_hash, decoder)
    candidates = []
    for index, e in enumerate(tables['exports'], 1):
        if e['class_path'].rsplit('.', 1)[-1] not in ('Font', 'MultiFont'):
            continue
        candidates.append({k: e[k] for k in ('path', 'class_path', 'serial_offset', 'serial_size',
                                            'export_flags', 'object_flags', 'outer')})
        candidates[-1]['object_index'] = index
        parents, ref = [], e['outer']
        while ref:
            parent = tables['exports'][ref - 1] if ref > 0 else tables['imports'][-ref - 1]
            record = dict(object_index=ref, path=parent['path'])
            if ref > 0:
                record.update({k: parent[k] for k in ('class_path', 'export_flags', 'object_flags')})
            else:
                record['class_name'] = parent['class_name']['name']
            parents.append(record)
            ref = parent['outer']
        candidates[-1]['outer_chain'] = parents
        candidates[-1]['class_default'] = e['path'].rsplit('.', 1)[-1].startswith('Default__')
    return dict(schema_version=1, source_sha256=expected_hash, font_class_exports=candidates,
                offset_convention='logical package offsets, not compressed file positions',
                interpretation='serialized class candidates, not validated Font payloads or runtime selection',
                game_rendering_verified=False)


def inspect(data, expected_hash, object_path='Default__Engine', decoder=None):
    logical, t = _tables(data, expected_hash, decoder)
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


def tagged_font_consumers(logical, tables):
    """Scan bounded top-level tags, never guess types inside arrays/native data."""
    links, unparsed, skipped = [], [], []
    parsed = 0
    excluded = {'Class', 'Function', 'State', 'ScriptStruct', 'Enum', 'Const',
                'Font', 'MultiFont', 'Texture2D'}

    def resolve(ref):
        if not ref:
            return None
        if not -len(tables['imports']) <= ref <= len(tables['exports']):
            raise FormatError('ObjectProperty reference outside object tables')
        obj = tables['exports'][ref - 1] if ref > 0 else tables['imports'][-ref - 1]
        kind = obj['class_path'].rsplit('.', 1)[-1] if ref > 0 else obj['class_name']['name']
        return dict(object_index=ref, path=obj['path'], class_name=kind,
                    reference_kind='export' if ref > 0 else 'import')

    for index, e in enumerate(tables['exports'], 1):
        leaf = e['class_path'].rsplit('.', 1)[-1]
        identity = dict(object_index=index, object_path=e['path'], class_path=e['class_path'])
        if leaf in excluded or leaf.endswith('Property') or not e['serial_size']:
            skipped.append(dict(**identity, reason='excluded native/metadata/asset class or empty payload'))
            continue
        try:
            start, size = e['serial_offset'], e['serial_size']
            if start < 0 or size < 4 or start + size > len(logical):
                raise FormatError('consumer payload outside logical package')
            r = Reader(logical[start:start + size]); r.i32()
            props = read_properties(r, tables['names'])
            pending = []
            for prop in props:
                if prop['type'] != 'ObjectProperty':
                    continue
                if len(prop['raw']) != 4:
                    raise FormatError('ObjectProperty must contain one int32 reference')
                ref, = struct.unpack('>i', prop['raw'])
                target = resolve(ref)
                if target and target['class_name'] in ('Font', 'MultiFont'):
                    pending.append(dict(**identity, property=prop['name'], array_index=prop['array_index'],
                                        logical_package_offset=start + prop['value_offset'], target=target,
                                        archetype_reference=e.get('archetype', 0),
                                        binding_kind='direct-top-level-serialized-font-reference'))
            # An invalid later property invalidates all links from this object.
            links.extend(pending)
            parsed += 1
        except (ValueError, KeyError) as exc:
            unparsed.append(dict(**identity, reason=str(exc)))
    return dict(font_consumers=links, coverage=dict(total_exports=len(tables['exports']),
                parsed_tagged_exports=parsed, skipped_exports=len(skipped), unparsed_exports=len(unparsed)),
                skipped=skipped, unparsed=unparsed,
                interpretation='direct top-level serialized links only; no inheritance, arrays, structs, native data or dynamic selection',
                inheritance_resolved=False, game_rendering_verified=False)


def consumers(data, expected_hash, decoder=None):
    logical, tables = _tables(data, expected_hash, decoder)
    return dict(schema_version=1, source_sha256=expected_hash,
                offset_convention='logical package offsets, not compressed file positions',
                **tagged_font_consumers(logical, tables))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('--sha256', required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--object', default=None)
    mode.add_argument('--inventory', action='store_true', help='List embedded Font/MultiFont class candidates, including defaults')
    mode.add_argument('--consumers', action='store_true', help='Scan direct top-level Font references across tagged objects')
    p.add_argument('--lzx-library', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in (
                a.package.resolve(), a.lzx_library.resolve() if a.lzx_library else None):
            raise FormatError('output must be new and distinct from inputs')
        decoder = LzxDecoder(a.lzx_library) if a.lzx_library else None
        data = a.package.read_bytes()
        result = (consumers(data, a.sha256, decoder) if a.consumers else
                  inventory(data, a.sha256, decoder) if a.inventory else
                  inspect(data, a.sha256, a.object or 'Default__Engine', decoder))
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
        if json.loads(a.output.read_text(encoding='utf-8')) != result:
            raise FormatError('output reopening mismatch')
        print(json.dumps(dict(source_sha256=a.sha256, **result['coverage'],
                              font_consumers=len(result['font_consumers']), game_rendering_verified=False)
                         if a.consumers else result)); return 0
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc)); return 1


if __name__ == '__main__':
    raise SystemExit(main())
