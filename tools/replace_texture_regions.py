"""Transfer verified native blocks between matching textures on package copies."""
import struct
from .build_font_supplement import context
from .texture_layout import read_texture, rect_units
from .reface_font import sha


def selected(data,obj,decoder):
    c=context(data,decoder)
    if c['logical']!=data:raise ValueError('normalized raw package required')
    es=[e for e in c['tables']['exports'] if e['path']==obj]
    if len(es)!=1:raise ValueError('explicit texture export not found')
    e=es[0];off=e['serial_offset'];p=data[off:off+e['serial_size']]
    t=read_texture(p,c['tables']['names'],off,{'kind':'xbox-inline-bc-v1','format':7},decoder)
    return c,e,p,t


def replace(data,expected_sha,obj,donor,donor_sha,donor_obj,rects,decoder):
    if sha(data)!=expected_sha or sha(donor)!=donor_sha:raise ValueError('texture package SHA256 mismatch')
    _,_,_,t=selected(data,obj,decoder);_,_,_,d=selected(donor,donor_obj,decoder)
    if (t['width'],t['height'])!=(d['width'],d['height']):raise ValueError('texture geometry mismatch')
    return replace_tiles(data,expected_sha,obj,d['tiles'],rects,decoder)


def replace_tiles(data,expected_sha,obj,new,rects,decoder):
    """Install bounded regenerated blocks into a hash-locked package copy."""
    if sha(data)!=expected_sha:raise ValueError('texture package SHA256 mismatch')
    c,e,p,t=selected(data,obj,decoder)
    if not isinstance(new,bytes) or len(new)!=len(t['tiles']):raise ValueError('native tile size mismatch')
    if not isinstance(rects,list) or not 1<=len(rects)<=32:raise ValueError('rectangle count bound')
    allowed=set()
    for r in rects:
        units=set(rect_units(t['layout'],r))
        if units & allowed:raise ValueError('authorized rectangles overlap')
        allowed.update(units)
    old=t['tiles'];bs=t['layout']['unit_bytes']
    changes={i for i in range(0,len(old),bs) if old[i:i+bs]!=new[i:i+bs]}
    if not changes or not changes<=allowed:raise ValueError('donor changes outside selected regions')
    out=bytearray(data)
    if t['flags']==0:
        at=e['serial_offset']+t['payload_offset']
        out[at:at+len(new)]=new
    else:
        target=(len(out)+3)&~3;at=t['payload_offset'];size=t['stored_size']
        patched=bytearray(p[:at]+new+p[at+size:])
        struct.pack_into('>I',patched,t['source_offset']+12,target+t['source_offset']+16)
        struct.pack_into('>IIII',patched,t['bulk_offset'],0,len(new),len(new),target+at)
        out.extend(bytes(target-len(out))+patched)
        struct.pack_into('>II',out,e['table_offset']+32,len(patched),target)
    result=bytes(out);_,_,_,checked=selected(result,obj,decoder)
    if checked['tiles']!=new:raise ValueError('native block roundtrip mismatch')
    for other in c['tables']['exports']:
        if other['table_offset']==e['table_offset']:continue
        x=other['serial_offset'];n=other['serial_size']
        if result[x:x+n]!=data[x:x+n]:raise ValueError('unselected export changed')
    return result,dict(input_sha256=sha(data),output_sha256=sha(result),object=obj,
                        changed_blocks=len(changes),authorized_rectangles=rects,
                        unselected_exports_preserved=True,outside_blocks_preserved=True,
                        game_rendering_verified=False)
