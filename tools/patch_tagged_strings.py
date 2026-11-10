"""Hash-guarded, equal-size UE3 wide StrProperty edits; never edit identifiers by search."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct

from .build_font_supplement import context
from .patch_tagged_fields import digest
from .ue3_fonts import read_properties
from .ue3_package import FormatError, Reader, parse_summary
from .ue3_ui_styles import object_flags
from .validate_catalog import TOKEN
from .verify_resource_phase import unique


def locked(path, expected, limit):
    if (not re.fullmatch('[0-9a-f]{64}', expected)
            or not 0 < path.stat().st_size <= limit):
        raise FormatError('invalid input identity/size bound')
    data = path.read_bytes()
    if not 0 < len(data) <= limit or digest(data) != expected:
        raise FormatError('input SHA256/size mismatch')
    return data


def wide_string(text):
    if (not isinstance(text, str) or not 1 <= len(text) <= 4096
            or any(not c.isprintable() for c in text)):
        raise FormatError('bounded printable nonempty string required')
    raw = text.encode('utf-16-le') + b'\0\0'
    return struct.pack('>i', -len(raw) // 2) + raw


def prepare(data, ctx, plan, state='baseline'):
    if not isinstance(data, bytes) or ctx['logical'] != data:
        raise FormatError('physical uncompressed package required')
    if (plan.get('schema_version') != 1 or type(plan['schema_version']) is not int
            or plan.get('profile') != 'ue3-equal-size-wide-tagged-strings-v1'):
        raise FormatError('unsupported tagged string profile')
    if state not in ('baseline', 'modified'):
        raise FormatError('invalid state')
    objects = plan.get('objects')
    if not isinstance(objects, list) or not 1 <= len(objects) <= 1024:
        raise FormatError('invalid object count')
    rows, seen, spans = [], set(), []
    for obj in objects:
        name = obj['object_path']
        if not isinstance(name, str) or name.casefold() in seen:
            raise FormatError('invalid/duplicate object path')
        seen.add(name.casefold())
        found = [(i, e) for i, e in enumerate(ctx['tables']['exports'], 1)
                 if e['path'].casefold() == name.casefold()]
        if len(found) != 1:
            raise FormatError('missing/ambiguous export')
        index, e = found[0]
        lo, hi = object_flags(e)
        if (e['class_path'] != obj['class_path'] or lo & 0x02000000 or hi & 0x200
                or obj.get('tagged_offset') != 4):
            raise FormatError('class/prefix profile mismatch; no stack/CDO supported')
        start, size = e['serial_offset'], e['serial_size']
        if not 0 <= start < start + size <= len(data):
            raise FormatError('export outside package')
        payload = data[start:start + size]
        expected = obj['before_sha256' if state == 'baseline' else 'after_sha256']
        if not re.fullmatch('[0-9a-f]{64}', expected) or digest(payload) != expected:
            raise FormatError('export payload SHA256 mismatch')
        reader = Reader(payload); reader.seek(4)
        props = read_properties(reader, ctx['tables']['names'])
        if reader.pos != len(payload):
            raise FormatError('unsupported export tail')
        fields = obj['fields']
        if not isinstance(fields, list) or not 1 <= len(fields) <= 128:
            raise FormatError('invalid field count')
        for f in fields:
            if type(f['array_index']) is not int or f['array_index'] < 0:
                raise FormatError('invalid field index')
            selected = [p for p in props if p['name'] == f['name']
                        and p['array_index'] == f['array_index']]
            if len(selected) != 1 or selected[0]['type'] != 'StrProperty':
                raise FormatError('missing/ambiguous/non-string field')
            prop = selected[0]
            before, after = wide_string(f['before']), wide_string(f['after'])
            if len(before) != len(after) or before == after:
                raise FormatError('equal-size non-noop string edit required')
            if TOKEN.findall(f['before']) != TOKEN.findall(f['after']):
                raise FormatError('protected tokens changed')
            if prop['raw'] != (before if state == 'baseline' else after):
                raise FormatError('expected wide string mismatch')
            at, end = start + prop['value_offset'], start + prop['value_offset'] + len(before)
            if not start <= at < end <= start + size or any(a < end and at < b for a, b in spans):
                raise FormatError('overlapping/out-of-export edits')
            spans.append((at, end))
            rows.append(dict(object_index=index, object_path=e['path'], field=f['name'],
                             array_index=f['array_index'], offset=at,
                             old_hex=before.hex(), new_hex=after.hex()))
    return rows


def patch(data, ctx, plan, reverse=False):
    rows = prepare(data, ctx, plan, 'modified' if reverse else 'baseline')
    out = bytearray(data)
    for row in rows:
        raw = bytes.fromhex(row['old_hex' if reverse else 'new_hex'])
        out[row['offset']:row['offset'] + len(raw)] = raw
    out = bytes(out)
    prepare(out, dict(ctx, logical=out), plan, 'baseline' if reverse else 'modified')
    inverse = bytearray(out)
    for row in rows:
        raw = bytes.fromhex(row['new_hex' if reverse else 'old_hex'])
        inverse[row['offset']:row['offset'] + len(raw)] = raw
    if bytes(inverse) != data:
        raise FormatError('inverse identity mismatch')
    return out, dict(schema_version=1, profile=plan['profile'], input_sha256=digest(data),
                     output_sha256=digest(out), fields=len(rows), changes=rows,
                     inverse_byte_identical=True, size_unchanged=True,
                     game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['apply', 'rollback'])
    p.add_argument('source', type=Path); p.add_argument('--source-sha256', required=True)
    p.add_argument('--plan', type=Path, required=True); p.add_argument('--plan-sha256', required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--report', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        inputs = [a.source.resolve(), a.plan.resolve()]
        outs = [a.output.resolve(), a.report.resolve()]
        if len(set(outs)) != 2 or set(inputs) & set(outs) or any(x.exists() or x.is_symlink() for x in outs):
            raise FormatError('new distinct outputs required')
        data = locked(a.source, a.source_sha256, 512 * 1024 * 1024)
        plan_raw = locked(a.plan, a.plan_sha256, 4 * 1024 * 1024)
        s = parse_summary(data, len(data))
        if s['byte_order'] != 'big' or s['compression_flags']:
            raise FormatError('uncompressed big-endian package required')
        result, report = patch(data, context(data, None),
                               json.loads(plan_raw, object_pairs_hook=unique), a.mode == 'rollback')
        if a.source.read_bytes() != data or a.plan.read_bytes() != plan_raw:
            raise FormatError('input changed')
        a.output.parent.mkdir(parents=True, exist_ok=True); a.report.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode()
        with a.output.open('xb') as stream: stream.write(result)
        with a.report.open('xb') as stream: stream.write(encoded)
        if a.output.read_bytes() != result or a.report.read_bytes() != encoded:
            raise FormatError('output readback mismatch')
        if a.source.read_bytes() != data or a.plan.read_bytes() != plan_raw:
            raise FormatError('input changed after publication')
        print(f'PASS tagged-strings {a.mode}; fields={report["fields"]}; inverse_byte_identical=true')
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        print('ERROR: ' + str(error)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
