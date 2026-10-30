"""Offline serialized anchor/alpha contracts; not a claim of runtime rendering."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from .build_font_supplement import context
from .patch_tagged_fields import select_field
from .replace_texture_regions import selected
from .texture_layout import decode_texture


def audit(root, plan):
    if plan.get('schema_version') != 1 or plan.get('kind') != 'ui-geometry-contracts':
        raise ValueError('unsupported geometry contract')
    raw = {}; contexts = {}; rows = []
    for key, name in plan['packages'].items():
        path = Path(root) / name
        raw[key] = path.read_bytes()
        contexts[key] = context(raw[key], None)
    def value(term):
        c = contexts[term['package']]
        matches = [e for e in c['tables']['exports'] if e['path'] == term['object']]
        if len(matches) != 1: raise ValueError('ambiguous contract object')
        e = matches[0]; payload = c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        kind, _, data = select_field(payload, c['tables']['names'], term.get('prefix', 4),
                                   [dict(name=p[0], array_index=p[1]) for p in term['field']])
        if kind not in ('FloatProperty', 'ByteProperty', 'IntProperty'):
            raise ValueError('non-scalar contract field')
        return struct.unpack({'FloatProperty':'>f','ByteProperty':'>B','IntProperty':'>i'}[kind], data)[0]
    for case in plan['anchors']:
        actual = sum(value(t) for t in case['terms']) + case.get('offset', 0)
        rows.append(dict(name=case['name'], actual=actual, expected=case['expected'],
                         passed=abs(actual-case['expected']) <= case.get('tolerance', .01)))
    for case in plan.get('alpha_bounds', []):
        _, _, _, texture = selected(raw[case['package']], case['object'], None)
        pixels = decode_texture(texture); w, h = texture['width'], texture['height']
        x,y,cw,ch = case['clip']; outside = 0
        for yy in range(h):
            for xx in range(w):
                if not (x<=xx<x+cw and y<=yy<y+ch) and pixels[(yy*w+xx)*4+3]: outside += 1
        rows.append(dict(name=case['name'], outside_alpha_pixels=outside, passed=outside == 0))
    return dict(passed=all(r['passed'] for r in rows), checks=rows,
                input_sha256={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},
                game_rendering_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    result=audit(a.root,json.loads(a.plan.read_bytes()))
    with a.report.open('x',encoding='utf-8') as out:json.dump(result,out,ensure_ascii=False,indent=2)
    failures=sum(not c['passed'] for c in result['checks'])
    print(f'CHECKS={len(result["checks"])} FAILURES={failures} RESULT={"PASS" if result["passed"] else "FAIL"}')
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
