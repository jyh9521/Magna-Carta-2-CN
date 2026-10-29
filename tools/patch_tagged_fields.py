"""Guarded, same-size UE3 tagged scalar edits; compose by export payload identity."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

try:
    from .build_font_supplement import context
    from .ue3_fonts import read_properties
    from .ue3_package import FormatError, Reader, parse_summary
except ImportError:
    from build_font_supplement import context
    from ue3_fonts import read_properties
    from ue3_package import FormatError, Reader, parse_summary


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scalar_bytes(kind, value):
    if kind == 'FloatProperty':
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise FormatError('finite float required')
        return struct.pack('>f', value)
    if kind in ('ByteProperty', 'IntProperty', 'BoolProperty'):
        if not isinstance(value, int) or isinstance(value, bool):
            raise FormatError('integer scalar required')
        if kind == 'BoolProperty':
            if value not in (0, 1):
                raise FormatError('boolean scalar requires 0/1')
            return struct.pack('>I', value)
        return struct.pack('>B' if kind == 'ByteProperty' else '>i', value)
    raise FormatError('unsupported scalar type')


def select_field(payload, names, tagged_offset, path):
    """Resolve an exact indexed tag path, never search a byte pattern or guess a prefix."""
    if not isinstance(tagged_offset, int) or not 4 <= tagged_offset <= 32:
        raise FormatError('bounded verified tagged prefix required')
    if not isinstance(path, list) or not 1 <= len(path) <= 8:
        raise FormatError('bounded property path required')
    reader = Reader(payload); reader.seek(tagged_offset)
    properties = read_properties(reader, names)
    base = 0
    for depth, part in enumerate(path):
        if set(part) != {'name', 'array_index'} or not isinstance(part['name'], str) or not isinstance(part['array_index'], int):
            raise FormatError('invalid indexed property path')
        matches = [p for p in properties if p['name'] == part['name'] and p['array_index'] == part['array_index']]
        if len(matches) != 1:
            raise FormatError('missing/ambiguous indexed tag: ' + part['name'])
        prop = matches[0]
        if depth == len(path) - 1:
            offset = base + prop.get('bool_value_offset', prop['value_offset'])
            raw = struct.pack('>I', prop['bool']) if prop['type'] == 'BoolProperty' else prop['raw']
            return prop['type'], offset, raw
        if prop['type'] != 'StructProperty':
            raise FormatError('path traverses a non-struct tag')
        base += prop['value_offset']
        reader = Reader(prop['raw']); properties = read_properties(reader, names)
        if reader.pos != len(reader.data):
            raise FormatError('nested tagged struct has unconsumed bytes')
    raise FormatError('empty property path')


def prepare(data, ctx, plan, state='baseline'):
    if ctx['logical'] != data:
        raise FormatError('same-size edits require the physical uncompressed package')
    if plan.get('schema_version') != 1 or plan.get('profile') != 'ue3-tagged-scalar-fields-v1':
        raise FormatError('unsupported tagged-field profile')
    objects = plan.get('objects')
    if not isinstance(objects, list) or not 1 <= len(objects) <= 1024:
        raise FormatError('invalid selected export count')
    if state not in ('baseline', 'modified'):
        raise FormatError('invalid selected field state')
    rows = []; used = set(); occupied = set()
    for obj in objects:
        path = obj['object_path']
        if path.casefold() in used:
            raise FormatError('duplicate selected export')
        used.add(path.casefold())
        es = [(i, e) for i, e in enumerate(ctx['tables']['exports'], 1) if e['path'].casefold() == path.casefold()]
        if len(es) != 1:
            raise FormatError('missing/ambiguous export: ' + path)
        index, export = es[0]
        if export['class_path'] != obj['class_path']:
            raise FormatError('selected export class mismatch')
        start, size = export['serial_offset'], export['serial_size']
        if not 0 <= start < start + size <= len(data):
            raise FormatError('export outside package')
        payload = data[start:start + size]
        expected = obj['before_sha256' if state == 'baseline' else 'after_sha256']
        if not re.fullmatch('[0-9a-f]{64}', expected) or digest(payload) != expected:
            raise FormatError('selected export payload SHA256 mismatch: ' + path)
        fields = obj.get('fields')
        if not isinstance(fields, list) or not 1 <= len(fields) <= 128:
            raise FormatError('invalid scalar field count')
        for field in fields:
            kind, relative, old = select_field(payload, ctx['tables']['names'], obj['tagged_offset'], field['property_path'])
            if kind != field['type']:
                raise FormatError('selected field type mismatch')
            before = scalar_bytes(kind, field['before'])
            after = scalar_bytes(kind, field['after'])
            if before == after:
                raise FormatError('scalar edit is a no-op')
            if old != (before if state == 'baseline' else after):
                raise FormatError('selected scalar value mismatch')
            offset = start + relative
            span = set(range(offset, offset + len(old)))
            if occupied.intersection(span) or not start <= offset < offset + len(old) <= start + size:
                raise FormatError('overlapping/out-of-export scalar edit')
            occupied.update(span)
            rows.append(dict(object_index=index, object_path=path, class_path=export['class_path'],
                             property_path=field['property_path'], type=kind, offset=offset,
                             relative_offset=relative, old_hex=before.hex(), new_hex=after.hex(),
                             before=field['before'], after=field['after']))
    return rows


def patch(data, ctx, plan, reverse=False):
    rows = prepare(data, ctx, plan, 'modified' if reverse else 'baseline')
    result = bytearray(data)
    for row in rows:
        raw = bytes.fromhex(row['old_hex' if reverse else 'new_hex'])
        result[row['offset']:row['offset'] + len(raw)] = raw
    result = bytes(result)
    check_ctx = dict(ctx, logical=result)
    prepare(result, check_ctx, plan, 'baseline' if reverse else 'modified')
    restored = bytearray(result)
    for row in rows:
        raw = bytes.fromhex(row['new_hex' if reverse else 'old_hex'])
        restored[row['offset']:row['offset'] + len(raw)] = raw
    if bytes(restored) != data:
        raise FormatError('inverse edits changed unrelated bytes')
    return result, dict(schema_version=1, profile=plan['profile'], source_sha256=digest(data),
                        output_sha256=digest(result), size=len(data), selected_objects=len(plan['objects']),
                        fields=len(rows), changes=rows, inverse_byte_identical=True,
                        direction='rollback' if reverse else 'apply', game_rendering_verified=False,
                        deployment_performed=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['apply', 'rollback', 'verify'])
    p.add_argument('source', type=Path); p.add_argument('--source-sha256', required=True)
    p.add_argument('--profile', type=Path, required=True); p.add_argument('--profile-sha256', required=True)
    p.add_argument('--state', choices=['baseline', 'modified'], default='modified')
    p.add_argument('--output', type=Path); p.add_argument('--report', type=Path)
    a = p.parse_args(argv)
    try:
        data = a.source.read_bytes(); raw_plan = a.profile.read_bytes(); plan = json.loads(raw_plan)
        if digest(data) != a.source_sha256 or digest(raw_plan) != a.profile_sha256:
            raise FormatError('source/profile SHA256 mismatch')
        summary = parse_summary(data, len(data))
        if summary['compression_flags'] or summary['byte_order'] != 'big':
            raise FormatError('verified uncompressed big-endian package required')
        ctx = context(data, None)
        if a.mode == 'verify':
            rows = prepare(data, ctx, plan, a.state)
            if a.source.read_bytes() != data or a.profile.read_bytes() != raw_plan:
                raise FormatError('input changed during verification')
            print(f'PASS tagged-fields state={a.state}; objects={len(plan["objects"])}; fields={len(rows)}; source unchanged')
            return 0
        if not a.output or not a.report:
            raise FormatError('output and report required')
        outs = [a.output.resolve(), a.report.resolve()]
        if len(set(outs)) != 2 or set(outs).intersection([a.source.resolve(), a.profile.resolve()]) or any(x.exists() or x.is_symlink() for x in outs):
            raise FormatError('new distinct output/report paths required')
        result, report = patch(data, ctx, plan, reverse=a.mode == 'rollback')
        report['profile_sha256'] = digest(raw_plan)
        if a.source.read_bytes() != data or a.profile.read_bytes() != raw_plan:
            raise FormatError('input changed during patching')
        a.output.parent.mkdir(parents=True, exist_ok=True); a.report.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_bytes(result)
        encoded = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf8')
        a.report.write_bytes(encoded)
        if a.output.read_bytes() != result or a.report.read_bytes() != encoded:
            raise FormatError('output/report readback mismatch')
        print(f'PASS tagged-fields {a.mode}; objects={report["selected_objects"]}; fields={report["fields"]}; inverse_byte_identical=true')
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        print('ERROR ' + str(exc)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
