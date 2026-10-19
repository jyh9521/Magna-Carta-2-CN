"""Decode actual BC3 alpha for requested remapped glyphs; mapping alone is not ink."""
from .supplement_font import parse_atlas_payload,atlas_tiles
from .ue3_textures import untile_dxt5,decode_dxt5

def ink_records(ctx,font,codepoints,decoder):
    mapping={r['codepoint']:r['glyph_index'] for r in font['remap']};cache={};result=[]
    for cp in sorted(set(codepoints)):
        if chr(cp).isspace():continue
        if cp not in mapping:
            result.append(dict(codepoint=cp,status='missing-remap'));continue
        index=mapping[cp];g=font['characters'][index];ti=g['TextureIndex']
        if ti not in cache:
            ref=font['textures'][ti]
            if not 1<=ref<=len(ctx['tables']['exports']):raise ValueError('glyph atlas reference is not local')
            e=ctx['tables']['exports'][ref-1];b=ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
            t=parse_atlas_payload(b,ctx['tables']['names'],e['serial_offset']);w,h=t['width'],t['height'];tiles=atlas_tiles(b,t,decoder)
            cache[ti]=(w,h,decode_dxt5(untile_dxt5(tiles,w,h),w,h))
        w,h,rgba=cache[ti];x,y,gw,gh=(g[k] for k in ('StartU','StartV','USize','VSize'))
        if min(x,y,gw,gh)<0 or x+gw>w or y+gh>h:raise ValueError('glyph rectangle outside atlas')
        visible=sum(rgba[((y+iy)*w+x+ix)*4+3]>0 for iy in range(gh) for ix in range(gw))
        result.append(dict(codepoint=cp,glyph_index=index,status='ink' if visible else 'transparent',visible_pixels=visible))
    return result

def main():
    import argparse,json
    from pathlib import Path
    from .build_font_supplement import context
    from .ue3_fonts import parse_font_payload
    from .ue3_package import LzxDecoder
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path);p.add_argument('--font-object',required=True);p.add_argument('--characters',required=True);p.add_argument('--lzx-library',type=Path,required=True)
    a=p.parse_args();decoder=LzxDecoder(a.lzx_library);ctx=context(a.package.read_bytes(),decoder)
    es=[e for e in ctx['tables']['exports'] if e['path']==a.font_object]
    if len(es)!=1:raise ValueError('font identity must be unique')
    e=es[0];font=parse_font_payload(ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']],ctx['tables']['names'])
    rs=ink_records(ctx,font,map(ord,a.characters),decoder);fail=[r for r in rs if r['status']!='ink']
    print(json.dumps(dict(glyphs=len(rs),failures=fail,all_have_ink=not fail),sort_keys=True))
    return int(bool(fail))

if __name__=='__main__':raise SystemExit(main())
