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
    raw = {}; contexts = {}; rows = []; textures = {}
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
        if kind not in ('FloatProperty', 'ByteProperty', 'IntProperty', 'BoolProperty', 'ObjectProperty'):
            raise ValueError('non-scalar contract field')
        return struct.unpack({'FloatProperty':'>f','ByteProperty':'>B','IntProperty':'>i',
                              'BoolProperty':'>I','ObjectProperty':'>i'}[kind], data)[0]
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
    for case in plan.get('equal_fields', []):
        actual = [value(t) for t in case['terms']]
        if len(actual)<2:raise ValueError('equality contract needs two fields')
        rows.append(dict(name=case['name'],actual=actual,
                         passed=max(actual)-min(actual)<=case.get('tolerance',.00001)))
    for case in plan.get('image_labels', []):
        package=case['package']; obj=case['object']; c=contexts[package]
        def field(path,fields,prefix=4):
            return value(dict(package=package,object=path,field=fields,prefix=prefix))
        def reference(path,name,prefix,expected_class):
            index=field(path,[[name,0]],prefix)
            if not 1<=index<=len(c['tables']['exports']):raise ValueError('image reference is not a local export')
            export=c['tables']['exports'][index-1]
            if export['class_path']!=expected_class:raise ValueError('image reference class mismatch')
            return export['path']
        component=reference(obj,'ImageComponent',4,'Engine.UIComp_DrawImage')
        image=reference(component,'ImageRef',8,'Engine.UITexture')
        index=field(image,[['ImageTexture',0]])
        if not -len(c['tables']['imports'])<=index<0:raise ValueError('expected explicit imported texture')
        imported=c['tables']['imports'][-index-1]['path']
        override=field(component,[['StyleCustomization',0],['bOverrideCoordinates',0]],8)
        uv=[field(component,[['StyleCustomization',0],['Coordinates',0],[n,0]],8) for n in ('U','V','UL','VL')]
        x,y,width,height=[field(obj,[['Position',0],['Value',i]]) for i in range(4)]
        u,v,uw,vh=uv
        if min(uw,vh,width,height)<=0:raise ValueError('invalid sampled image dimensions')
        scale=[width/uw,height/vh]
        for source in case['textures']:
            key=(source['package'],source['object'])
            if key not in textures:
                _,_,_,texture=selected(raw[key[0]],key[1],None)
                textures[key]=(texture,decode_texture(texture))
            texture,pixels=textures[key];tw,th=texture['width'],texture['height']
            rx,ry,rw,rh=case['ink_region']
            if (any(type(n) is not int for n in (rx,ry,rw,rh)) or min(rw,rh)<=0
                    or not (0<=u<=rx<rx+rw<=u+uw<=tw and 0<=v<=ry<ry+rh<=v+vh<=th)):
                raise ValueError('ink region outside actual consumer UV/texture')
            threshold=case['rgba_min']
            if len(threshold)!=4 or any(type(n) is not int or not 0<=n<=255 for n in threshold):
                raise ValueError('invalid ink threshold')
            points=[(xx,yy) for yy in range(ry,ry+rh) for xx in range(rx,rx+rw)
                    if all(pixels[(yy*tw+xx)*4+i]>=threshold[i] for i in range(4))]
            if not points:raise ValueError('empty native label ink')
            bounds=[min(p[0] for p in points),min(p[1] for p in points),
                    max(p[0] for p in points)+1,max(p[1] for p in points)+1]
            actual=dict(right=x+(bounds[2]-u)*scale[0],height=(bounds[3]-bounds[1])*scale[1],
                        bottom=(bounds[3]-v)*scale[1])
            passed=(override==1 and imported==case['texture_import'] and scale==case['scale']
                    and all(abs(actual[n]-expected)<=case.get('tolerance',.01) for n,expected in case['expected'].items()))
            rows.append(dict(name=case['name']+' / '+source['package'],native_bounds=bounds,
                             imported_texture=imported,coordinates_override=override,uv=uv,scale=scale,actual=actual,
                             expected=case['expected'],passed=passed))
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
