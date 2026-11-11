"""Relocate fully tagged, self-contained UE3 string objects with exact rollback.

Only the selected export records change in the original byte prefix. Original
payloads stay outside active export ranges in that prefix; new payloads are appended. This reuses
the append/export-record mechanism of set_ui_font_overrides and runtime_package
without shifting unknown native offsets or rewriting unrelated exports.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import struct

from .patch_tagged_strings import digest, locked, wide_string
from .ue3_fonts import read_properties
from .ue3_package import FormatError, Reader, parse_summary, parse_tables
from .ue3_ui_styles import object_flags
from .validate_catalog import TOKEN
from .verify_resource_phase import unique

PROFILE = 'ue3-relocated-wide-tagged-strings-v1'
MAX_PACKAGE = 512 * 1024 * 1024
MAX_PLAN = 4 * 1024 * 1024


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise FormatError('lowercase SHA256 required')
    return value


def _semantic_sha(plan):
    return digest(json.dumps(plan, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def _fstring(raw):
    if len(raw) < 4:
        raise FormatError('truncated FString')
    count = struct.unpack_from('>i', raw)[0]
    if count == 0:
        if len(raw) != 4: raise FormatError('empty FString has trailing data')
        return ''
    if not 1 <= abs(count) <= 16384:
        raise FormatError('bounded FString required')
    unit = 2 if count < 0 else 1; terminator = bytes(unit)
    if len(raw) != 4 + abs(count) * unit or not raw.endswith(terminator):
        raise FormatError('FString length/termination mismatch')
    value = raw[4:-unit].decode('utf-16-le' if unit == 2 else 'utf-8')
    if '\0' in value: raise FormatError('interior FString NUL')
    return value


def _self_contained_properties(raw, tables, start=0, depth=0):
    """Fail closed on arrays, opaque/native tails, and unsupported native structs.

    Scalar leaves are serialization values or object/name table indexes, never
    physical file pointers. Vector is the one supported native struct; every
    other struct must itself be a complete tagged stream with supported leaves.
    """
    if depth > 8: raise FormatError('tagged struct nesting limit')
    reader = Reader(raw); reader.seek(start)
    props = read_properties(reader, tables['names'])
    if reader.pos != len(raw): raise FormatError('unsupported native object/struct tail')
    seen = set()
    for p in props:
        key = (p['name'], p['array_index'])
        if key in seen: raise FormatError('duplicate indexed property')
        seen.add(key); kind, value = p['type'], p['raw']
        if kind == 'StrProperty': _fstring(value)
        elif kind in ('IntProperty', 'FloatProperty', 'ObjectProperty'):
            if len(value) != 4: raise FormatError('invalid scalar property size')
            if kind == 'ObjectProperty':
                reference = struct.unpack('>i', value)[0]
                if not -len(tables['imports']) <= reference <= len(tables['exports']):
                    raise FormatError('object reference outside tables')
        elif kind == 'BoolProperty':
            if value or p['size'] or p['bool'] not in (0, 1): raise FormatError('invalid boolean property')
        elif kind == 'ByteProperty':
            if len(value) != 1: raise FormatError('only byte-valued ByteProperty supported')
        elif kind == 'NameProperty':
            if len(value) != 8: raise FormatError('invalid name property size')
            index, _ = struct.unpack('>II', value)
            if index >= len(tables['names']): raise FormatError('name reference outside table')
        elif kind == 'StructProperty':
            if p['struct'] == 'Vector':
                if len(value) != 12 or not all(math.isfinite(v) for v in struct.unpack('>fff', value)):
                    raise FormatError('invalid native Vector')
            else:
                _self_contained_properties(value, tables, 0, depth + 1)
        else:
            raise FormatError('unsupported self-contained property type: ' + kind)
    return props


def _protected(before, after, field):
    literals = field.get('literal_percentages', [])
    if (not isinstance(literals, list) or len(literals) > 16
            or any(not isinstance(value, str) for value in literals)
            or len(set(literals)) != len(literals)):
        raise FormatError('invalid literal percentage declarations')
    for value in literals:
        if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?%', value):
            raise FormatError('numeric literal percentage required')
        pattern = re.compile(r'(?<![0-9.])' + re.escape(value))
        a, b = len(pattern.findall(before)), len(pattern.findall(after))
        if not 1 <= a <= 32 or a != b:
            raise FormatError('literal percentage value/count changed')
        before, after = pattern.sub('', before), pattern.sub('', after)
    if TOKEN.findall(before) != TOKEN.findall(after):
        raise FormatError('protected tokens changed')


def rewrite_payload(payload, tables, fields):
    """Build an object in memory for plan preparation; caller then locks its SHA."""
    if not isinstance(payload, bytes) or not 4 < len(payload) <= 4 * 1024 * 1024:
        raise FormatError('bounded immutable payload required')
    props = _self_contained_properties(payload, tables, 4)
    if not isinstance(fields, list) or not 1 <= len(fields) <= 128:
        raise FormatError('bounded field selection required')
    edits, seen = [], set()
    for f in fields:
        if (not isinstance(f, dict) or set(f) - {'name', 'array_index', 'before', 'after', 'literal_percentages'}
                or not {'name', 'array_index', 'before', 'after'} <= f.keys()
                or not isinstance(f['name'], str) or type(f['array_index']) is not int or f['array_index'] < 0):
            raise FormatError('exact indexed string field required')
        key = (f['name'], f['array_index'])
        if key in seen: raise FormatError('duplicate field selection')
        seen.add(key)
        selected = [p for p in props if (p['name'], p['array_index']) == key]
        if len(selected) != 1 or selected[0]['type'] != 'StrProperty':
            raise FormatError('missing/ambiguous/non-string field')
        p = selected[0]; before, after = wide_string(f['before']), wide_string(f['after'])
        if before == after: raise FormatError('non-noop string edit required')
        _protected(f['before'], f['after'], f)
        if p['raw'] != before: raise FormatError('expected wide string mismatch')
        edits.append(dict(field=f['name'], array_index=f['array_index'], tag_offset=p['offset'],
                          value_offset=p['value_offset'], before_size=len(before), after_size=len(after),
                          before_sha256=digest(before), after_sha256=digest(after),
                          before=before, after=after))
    out = bytearray(payload)
    for e in sorted(edits, key=lambda e: e['value_offset'], reverse=True):
        at = e['value_offset']; out[at:at + e['before_size']] = e['after']
        struct.pack_into('>I', out, e['tag_offset'] + 16, e['after_size'])
    result = bytes(out); new = _self_contained_properties(result, tables, 4)
    if len(new) != len(props): raise FormatError('property cardinality changed')
    chosen = {(e['field'], e['array_index']): e for e in edits}
    for a, b in zip(props, new, strict=True):
        if (a['name'], a['array_index'], a['type'], a.get('struct')) != (b['name'], b['array_index'], b['type'], b.get('struct')):
            raise FormatError('property identity changed')
        e = chosen.get((a['name'], a['array_index']))
        if e:
            if b['raw'] != e['after'] or b['size'] != e['after_size']: raise FormatError('string readback mismatch')
        elif a['raw'] != b['raw'] or a['size'] != b['size'] or a.get('bool') != b.get('bool'):
            raise FormatError('unselected property changed')
    return result, [{k: v for k, v in e.items() if k not in ('before', 'after')} for e in edits]


def _plan(plan):
    required = {'schema_version', 'profile', 'source_sha256', 'source_size', 'output_alignment', 'objects'}
    if (not isinstance(plan, dict) or set(plan) != required or type(plan.get('schema_version')) is not int
            or plan['schema_version'] != 1 or plan['profile'] != PROFILE):
        raise FormatError('unsupported relocated string profile')
    _hash(plan['source_sha256'])
    if type(plan['output_alignment']) is not int or plan['output_alignment'] != 32768:
        raise FormatError('explicit 32768-byte runtime output alignment required')
    if type(plan['source_size']) is not int or not 1 <= plan['source_size'] <= MAX_PACKAGE:
        raise FormatError('invalid source size')
    if not isinstance(plan['objects'], list) or not 1 <= len(plan['objects']) <= 1024:
        raise FormatError('bounded object selection required')
    seen = set()
    for obj in plan['objects']:
        if (not isinstance(obj, dict) or set(obj) != {'object_path', 'class_path', 'tagged_offset', 'before_sha256', 'after_sha256', 'fields'}
                or not isinstance(obj['object_path'], str) or not obj['object_path']
                or not isinstance(obj['class_path'], str) or not obj['class_path']
                or type(obj['tagged_offset']) is not int or obj['tagged_offset'] != 4):
            raise FormatError('invalid object profile')
        if obj['object_path'].casefold() in seen: raise FormatError('duplicate object selection')
        seen.add(obj['object_path'].casefold()); _hash(obj['before_sha256']); _hash(obj['after_sha256'])


def _package(data):
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_PACKAGE:
        raise FormatError('bounded immutable package required')
    summary = parse_summary(data, len(data))
    if summary['byte_order'] != 'big' or summary['compression_flags'] or summary['package_flags'] & 0x02000000:
        raise FormatError('uncompressed big-endian package required')
    return summary, parse_tables(data, summary, len(data))


def apply(data, plan):
    _plan(plan)
    if not isinstance(data, bytes) or len(data) != plan['source_size'] or digest(data) != plan['source_sha256']:
        raise FormatError('source identity mismatch')
    summary, tables = _package(data); selected = []
    for obj in plan['objects']:
        matches = [(i, e) for i, e in enumerate(tables['exports'], 1) if e['path'] == obj['object_path']]
        if len(matches) != 1: raise FormatError('missing/ambiguous export')
        index, e = matches[0]; lo, hi = object_flags(e)
        if e['class_path'] != obj['class_path'] or lo & 0x02000000 or hi & 0x200:
            raise FormatError('class/profile mismatch; stack/CDO unsupported')
        start, size = e['serial_offset'], e['serial_size']; payload = data[start:start + size]
        if digest(payload) != obj['before_sha256']: raise FormatError('original payload SHA256 mismatch')
        new, fields = rewrite_payload(payload, tables, obj['fields'])
        if digest(new) != obj['after_sha256']: raise FormatError('rebuilt payload SHA256 mismatch')
        selected.append((index, e, payload, new, fields))
    # An old payload is inactive only if no other export also owns its bytes.
    # Preserve unrelated aliases but reject any overlap involving a selected object.
    selected_indexes = {row[0] for row in selected}; max_end = max_selected_end = 0
    spans = sorted((e['serial_offset'], e['serial_offset'] + e['serial_size'], i)
                   for i, e in enumerate(tables['exports'], 1) if e['serial_size'])
    for start, end, index in spans:
        if (index in selected_indexes and start < max_end) or start < max_selected_end:
            raise FormatError('overlapping source export involving selected object')
        max_end = max(max_end, end)
        if index in selected_indexes: max_selected_end = max(max_selected_end, end)
    output = bytearray(data); changes = []
    for index, e, old, new, fields in sorted(selected):
        target = (len(output) + 3) & ~3
        if target + len(new) + plan['output_alignment'] - 1 > MAX_PACKAGE: raise FormatError('rebuilt package exceeds bound')
        output.extend(bytes(target - len(output)) + new)
        field = e['table_offset'] + 32; old_metadata = data[field:field + 8]
        if old_metadata != struct.pack('>II', len(old), e['serial_offset']): raise FormatError('export record mismatch')
        new_metadata = struct.pack('>II', len(new), target)
        output[field:field + 8] = new_metadata
        changes.append(dict(object_index=index, object_path=e['path'], class_path=e['class_path'], table_offset=e['table_offset'],
                            old_metadata_hex=old_metadata.hex(), new_metadata_hex=new_metadata.hex(),
                            before_offset=e['serial_offset'], before_size=len(old), before_payload_sha256=digest(old),
                            after_offset=target, after_size=len(new), after_payload_sha256=digest(new), fields=fields,
                            retained_inactive_range=[e['serial_offset'], e['serial_offset'] + len(old)],
                            appended_range=[target, target + len(new)]))
    payload_end = len(output)
    output.extend(bytes((-len(output)) % plan['output_alignment'])); result = bytes(output)
    after_summary, after = _package(result)
    if after_summary != summary: raise FormatError('package summary changed')
    if {k: v for k, v in after.items() if k != 'exports'} != {k: v for k, v in tables.items() if k != 'exports'}:
        raise FormatError('name/import/dependency table changed')
    indexes = selected_indexes
    for index, (a, b) in enumerate(zip(tables['exports'], after['exports'], strict=True), 1):
        if index not in indexes:
            if a != b or data[a['serial_offset']:a['serial_offset'] + a['serial_size']] != result[b['serial_offset']:b['serial_offset'] + b['serial_size']]:
                raise FormatError('unselected export changed')
        elif {k: v for k, v in a.items() if k not in ('serial_offset', 'serial_size')} != {k: v for k, v in b.items() if k not in ('serial_offset', 'serial_size')}:
            raise FormatError('selected export identity changed')
    restored = bytearray(result[:len(data)])
    for row in changes:
        field = row['table_offset'] + 32; restored[field:field + 8] = bytes.fromhex(row['old_metadata_hex'])
    if bytes(restored) != data: raise FormatError('original prefix changed outside selected export metadata')
    report = dict(schema_version=1, profile=PROFILE, source_sha256=digest(data), source_size=len(data),
                  output_sha256=digest(result), output_size=len(result), plan_semantic_sha256=_semantic_sha(plan),
                  fields=sum(len(x['fields']) for x in changes), changes=changes,
                  appended_range=[len(data), len(result)], original_payloads_retained_inactive=True,
                  output_alignment=plan['output_alignment'], final_padding_range=[payload_end, len(result)],
                  unselected_exports_preserved=True, name_import_dependency_tables_preserved=True,
                  source_summary_preserved=True, inverse_byte_identical=True, game_rendering_verified=False)
    return result, report


def rollback(data, plan, journal):
    _plan(plan)
    if (not isinstance(data, bytes) or not isinstance(journal, dict) or type(journal.get('schema_version')) is not int or journal['schema_version'] != 1
            or journal.get('profile') != PROFILE or journal.get('plan_semantic_sha256') != _semantic_sha(plan)
            or journal.get('source_sha256') != plan['source_sha256'] or journal.get('source_size') != plan['source_size']
            or journal.get('output_size') != len(data) or journal.get('output_sha256') != digest(data)):
        raise FormatError('rollback journal/input identity mismatch')
    _, tables = _package(data); rows = journal.get('changes')
    if not isinstance(rows, list) or len(rows) != len(plan['objects']): raise FormatError('rollback object count mismatch')
    restored = bytearray(data[:plan['source_size']]); seen = set()
    for row in rows:
        index = row['object_index']
        if type(index) is not int or not 1 <= index <= len(tables['exports']) or index in seen:
            raise FormatError('invalid rollback object index')
        seen.add(index); e = tables['exports'][index - 1]; field = e['table_offset'] + 32
        old = bytes.fromhex(row['old_metadata_hex']); new = bytes.fromhex(row['new_metadata_hex'])
        if (row['table_offset'] != e['table_offset'] or row['object_path'] != e['path'] or row['class_path'] != e['class_path']
                or old != struct.pack('>II', row['before_size'], row['before_offset'])
                or new != struct.pack('>II', e['serial_size'], e['serial_offset']) or data[field:field + 8] != new
                or not 0 <= field < field + 8 <= len(restored)):
            raise FormatError('rollback export metadata mismatch')
        restored[field:field + 8] = old
    result = bytes(restored)
    if digest(result) != plan['source_sha256']: raise FormatError('rollback original SHA256 mismatch')
    replayed, replay_journal = apply(result, plan)
    if replayed != data or replay_journal != journal:
        raise FormatError('rollback canonical forward replay mismatch')
    return result, dict(schema_version=1, profile=PROFILE, input_sha256=digest(data), output_sha256=digest(result),
                        restored_source_size=len(result), fields=journal['fields'], byte_identical=True,
                        canonical_forward_replay=True, game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['apply', 'rollback']); p.add_argument('source', type=Path)
    for name in ('plan', 'output', 'report'): p.add_argument('--' + name, type=Path, required=True)
    for name in ('source-sha256', 'plan-sha256'): p.add_argument('--' + name, required=True)
    p.add_argument('--journal', type=Path); p.add_argument('--journal-sha256'); a = p.parse_args(argv)
    try:
        if (a.mode == 'rollback') != (a.journal is not None and a.journal_sha256 is not None):
            raise FormatError('rollback requires journal and journal hash; apply accepts neither')
        if a.mode == 'apply' and (a.journal is not None or a.journal_sha256 is not None):
            raise FormatError('apply accepts no rollback journal')
        inputs = [a.source, a.plan] + ([a.journal] if a.journal else [])
        output_paths = [a.output.resolve(), a.report.resolve()]
        if len(set(output_paths)) != 2 or set(output_paths) & {x.resolve() for x in inputs} or any(x.exists() or x.is_symlink() for x in (a.output, a.report)):
            raise FormatError('new distinct outputs required')
        source = locked(a.source, a.source_sha256, MAX_PACKAGE); plan_raw = locked(a.plan, a.plan_sha256, MAX_PLAN)
        snapshots = [(a.source, source), (a.plan, plan_raw)]; plan = json.loads(plan_raw, object_pairs_hook=unique)
        if a.mode == 'apply': result, report = apply(source, plan)
        else:
            raw = locked(a.journal, a.journal_sha256, MAX_PLAN); snapshots.append((a.journal, raw))
            result, report = rollback(source, plan, json.loads(raw, object_pairs_hook=unique))
        if any(path.read_bytes() != raw for path, raw in snapshots): raise FormatError('input changed before publication')
        encoded = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        if len(encoded) > MAX_PLAN: raise FormatError('rollback/report size bound exceeded')
        for path, value in [(a.output, result), (a.report, encoded)]:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream: stream.write(value)
            if path.read_bytes() != value: raise FormatError('output readback mismatch')
        if any(path.read_bytes() != raw for path, raw in snapshots): raise FormatError('input changed after publication')
        print(f'PASS rebuilt-tagged-strings {a.mode}; fields={report["fields"]}; byte_identical_inverse=true')
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error, OverflowError) as error:
        print('ERROR: ' + str(error)); return 2


if __name__ == '__main__': raise SystemExit(main())
