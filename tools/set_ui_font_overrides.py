"""Set explicit local Font overrides on hash-guarded UI string renderers.

Append relocated selected payloads; retain original payloads and every other
export. No name/import/export is added and no shared UIStyle is changed.
"""
import argparse
import json
import struct
from pathlib import Path

from .build_font_supplement import context
from .patch_tagged_fields import digest, select_field
from .ue3_fonts import read_properties
from .ue3_package import Reader


def override_payload(payload, names, prefix, font_index):
    if prefix != 8 or type(font_index) is not int or font_index <= 0:
        raise ValueError('explicit renderer prefix/local font required')
    r = Reader(payload); r.seek(prefix)
    found = [p for p in read_properties(r, names) if p['name'] == 'TextStyleCustomization']
    if len(found) != 1 or found[0]['type'] != 'StructProperty' or found[0]['struct'] != 'UITextStyleOverride':
        raise ValueError('expected one UITextStyleOverride')
    p = found[0]
    nested = Reader(p['raw']); children = read_properties(nested, names)
    if nested.pos != len(p['raw']) or any(c['name'] in ('DrawFont', 'bOverrideDrawFont') for c in children):
        raise ValueError('existing/malformed font override')
    def fname(name):
        if names.count(name) != 1:
            raise ValueError('missing/ambiguous field name')
        return struct.pack('>II', names.index(name), 0)
    addition = (fname('DrawFont') + fname('ObjectProperty') + struct.pack('>IIi', 4, 0, font_index)
                + fname('bOverrideDrawFont') + fname('BoolProperty') + struct.pack('>III', 0, 0, 1))
    new_value = p['raw'][:-8] + addition + p['raw'][-8:]
    out = bytearray(payload[:p['value_offset']] + new_value + payload[p['value_offset'] + p['size']:])
    struct.pack_into('>I', out, p['offset'] + 16, len(new_value))
    result = bytes(out)
    for field, expected in [('DrawFont', struct.pack('>i', font_index)), ('bOverrideDrawFont', struct.pack('>I', 1))]:
        path = [dict(name=n, array_index=0) for n in ('TextStyleCustomization', field)]
        if select_field(result, names, prefix, path)[2] != expected:
            raise ValueError('font override readback failed')
    return result


def apply(data, plan):
    if (plan.get('kind') != 'ui-font-overrides-v1' or plan.get('schema_version') != 1
            or digest(data) != plan['source_sha256']):
        raise ValueError('font override source/profile mismatch')
    ctx = context(data, None)
    if ctx['logical'] != data:
        raise ValueError('normalized package required')
    exports = ctx['tables']['exports']; names = ctx['tables']['names']
    fonts = [(i, e) for i, e in enumerate(exports, 1) if e['path'] == plan['font_object']]
    if len(fonts) != 1 or fonts[0][1]['class_path'] not in ('Font', 'Engine.Font'):
        raise ValueError('exact local Font required')
    selections = plan['renderers']
    if not 1 <= len(selections) <= 128 or len({s['object'] for s in selections}) != len(selections):
        raise ValueError('renderer selection bound/duplicate')
    out = bytearray(data); changes = []
    for s in selections:
        matches = [e for e in exports if e['path'] == s['object']]
        if len(matches) != 1 or matches[0]['class_path'] != 'Engine.UIComp_DrawString':
            raise ValueError('exact string renderer required')
        e = matches[0]; at, size = e['serial_offset'], e['serial_size']; old = data[at:at+size]
        if digest(old) != s['before_sha256']:
            raise ValueError('renderer payload mismatch')
        new = override_payload(old, names, 8, fonts[0][0])
        offset = (len(out) + 3) // 4 * 4
        out.extend(bytes(offset-len(out)) + new)
        struct.pack_into('>II', out, e['table_offset']+32, len(new), offset)
        changes.append(dict(object=s['object'], table_offset=e['table_offset'],
                            before_sha256=digest(old), after_sha256=digest(new),
                            before_offset=at, before_size=size, after_offset=offset, after_size=len(new)))
    result = bytes(out); check = context(result, None)
    allowed = {r['table_offset']+i for r in changes for i in range(32, 40)}
    if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(data, result))):
        raise ValueError('unexpected original byte change')
    selected = {r['object'] for r in changes}
    for old, new in zip(exports, check['tables']['exports'], strict=True):
        if old['path'] not in selected and old != new:
            raise ValueError('unselected export changed')
    restored = bytearray(result[:len(data)])
    for r in changes:
        struct.pack_into('>II', restored, r['table_offset']+32, r['before_size'], r['before_offset'])
    if bytes(restored) != data:
        raise ValueError('inverse font override mismatch')
    return result, dict(changes=changes, original_size=len(data), before_sha256=digest(data),
                        sha256=digest(result), font_object=plan['font_object'],
                        unselected_exports_preserved=True, inverse_byte_identical=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'plan', 'output', 'report'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.report.exists() or a.output.resolve() == a.report.resolve():
        raise ValueError('distinct new outputs required')
    raw = a.source.read_bytes(); result, proof = apply(raw, json.loads(a.plan.read_bytes()))
    for path, value in [(a.output, result), (a.report, (json.dumps(proof, indent=2)+'\n').encode())]:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(value)
        if path.read_bytes() != value:
            raise ValueError('output readback mismatch')
    if a.source.read_bytes() != raw:
        raise ValueError('source changed')
    print(f"FONT_OVERRIDES={len(proof['changes'])} INVERSE=PASS RESULT=PASS")


if __name__ == '__main__':
    main()
