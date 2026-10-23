"""Copyright 2022 Ben Vanik. All rights reserved.

Explicit bounded Xbox inline single-mip BC1/BC3 profile.

Packed origin adapted from Xenia GetPackedMipOffset (Ben Vanik, BSD-3-Clause),
commit28b69c21; see NOTICE.md, references/texture-layout-research.lock.json and
licenses/Xenia-BSD-3-Clause.txt. Tiled unit addressing is the existing attributed
UEViewer implementation. No game-specific object, locale or dimensions here.
"""
import io
import struct
from .ue3_package import Reader,FormatError
from .ue3_fonts import read_properties,unique_properties,int_property
from .ue3_textures import compressed_chunk,xbox_tiled_block_offset,decode_dxt5
from .lzx_stored import wrap_ue3_chunk

PROFILE='xbox-inline-bc-v1'
MAX_BYTES=64*1024*1024
MAX_UNITS=1024*1024

def validate_profile(profile):
    if (not isinstance(profile,dict) or set(profile)!={'kind','format'}
            or profile['kind']!=PROFILE or type(profile['format']) is not int
            or profile['format'] not in (5,7)):
        raise FormatError('explicit supported Xbox BC profile required')
    return profile['format']

def unit_layout(width,height,fmt):
    if (type(fmt) is not int or fmt not in (5,7)
            or any(type(v) is not int or not 4<=v<=8192 or v&(v-1) for v in (width,height))):
        raise FormatError('Xbox BC power-of-two dimensions/format bound')
    aw,ah=(width+127)&~127,(height+127)&~127
    bs=8 if fmt==5 else 16
    size=aw*ah*bs//16
    count=width*height//16
    if size>MAX_BYTES or count>MAX_UNITS:raise FormatError('Xbox BC allocation/unit bound')
    # Single level: Xenia's first packed level starts sixteen texels along the
    # short axis whenever either base dimension is sixteen or smaller.
    ox,oy=((0,4) if width>height else (4,0)) if min(width,height)<=16 else (0,0)
    offsets=[xbox_tiled_block_offset(x+ox,y+oy,aw//4,3 if fmt==5 else 4)*bs
             for y in range(height//4) for x in range(width//4)]
    if len(set(offsets))!=len(offsets) or any(o<0 or o+bs>size for o in offsets):
        raise FormatError('Xbox BC addressed units overlap/outside allocation')
    return dict(width=width,height=height,format=fmt,unit_bytes=bs,offsets=offsets,
                origin_blocks=[ox,oy],storage_bytes=size)

def read_texture(payload,names,serial_offset,profile,decoder):
    fmt=validate_profile(profile)
    r=Reader(payload);r.i32();props=unique_properties(read_properties(r,names))
    if not {'SizeX','SizeY','Format'}<=set(props):raise FormatError('Xbox BC texture properties missing')
    w,h=int_property(props['SizeX']),int_property(props['SizeY']);f=props['Format']
    if f['type']!='ByteProperty' or f['raw']!=bytes([fmt]):raise FormatError('Xbox BC format mismatch')
    layout=unit_layout(w,h,fmt);so=r.pos
    if [r.u32() for _ in range(4)]!=[0,0,0,serial_offset+so+16]:
        raise FormatError('Xbox BC requires empty inline SourceArt')
    if r.count(16)!=1:raise FormatError('Xbox BC profile requires one mip')
    bo=r.pos;flags,count,size,at=[r.u32() for _ in range(4)];po=r.pos
    if flags not in (0,64) or count!=layout['storage_bytes'] or not 0<size<=MAX_BYTES or at!=serial_offset+po:
        raise FormatError('Xbox BC inline bulk profile mismatch')
    stored=r.read(size)
    if (r.u32(),r.u32())!=(w,h) or r.pos!=len(payload):raise FormatError('Xbox BC native size/export termination mismatch')
    if flags==64:
        raw=compressed_chunk(stored,count,decoder)[1]
        if raw is None:raise FormatError('Xbox BC decoder required')
    else:
        if size!=count:raise FormatError('Xbox BC raw bulk length mismatch')
        raw=stored
    if len(raw)!=layout['storage_bytes']:raise FormatError('Xbox BC decoded allocation mismatch')
    return dict(width=w,height=h,format=fmt,layout=layout,tiles=raw,
                source_offset=so,bulk_offset=bo,payload_offset=po,stored_size=size,flags=flags)

def extract(raw,layout):
    if not isinstance(raw,bytes) or len(raw)!=layout['storage_bytes']:raise FormatError('Xbox BC tiled length mismatch')
    bs=layout['unit_bytes']
    return b''.join(raw[o:o+bs][i+1:i+2]+raw[o:o+bs][i:i+1]
                    for o in layout['offsets'] for i in range(0,bs,2))

def decode_texture(texture,raw=None):
    from PIL import Image
    layout=texture['layout'];w,h=layout['width'],layout['height']
    linear=extract(texture['tiles'] if raw is None else raw,layout)
    if layout['format']==7:return decode_dxt5(linear,w,h)
    hdr=bytearray(128);hdr[:4]=b'DDS '
    struct.pack_into('<7I',hdr,4,124,0x81007,h,w,len(linear),0,1)
    struct.pack_into('<II4s',hdr,76,32,4,b'DXT1');struct.pack_into('<I',hdr,108,0x1000)
    with Image.open(io.BytesIO(bytes(hdr)+linear)) as im:return im.convert('RGBA').tobytes()

def rect_units(layout,rect):
    if not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect):
        raise FormatError('Xbox BC integer rectangle required')
    x,y,w,h=rect;tw,th=layout['width'],layout['height']
    if min(x,y)<0 or min(w,h)<=0 or any(v%4 for v in rect) or x+w>tw or y+h>th:
        raise FormatError('Xbox BC rectangle outside logical image')
    return [layout['offsets'][(y//4+j)*(tw//4)+x//4+i] for j in range(h//4) for i in range(w//4)]

def overlay_rect(raw,layout,rect,rgba,cache=None):
    from .texture_overlay import encode_rgba_block
    offsets=rect_units(layout,rect);w,h=rect[2:]
    if not isinstance(rgba,bytes) or len(rgba)!=w*h*4:raise FormatError('Xbox BC RGBA region length mismatch')
    if len(raw)!=layout['storage_bytes']:raise FormatError('Xbox BC original allocation mismatch')
    fmt=layout['format'];bs=layout['unit_bytes'];key=('xbox-bc',fmt,w,h,rgba)
    linear=None if cache is None else cache.get(key)
    if linear is None:
        out=bytearray()
        for j in range(h//4):
            for i in range(w//4):
                cell=b''.join(rgba[((j*4+k)*w+i*4)*4:((j*4+k)*w+i*4+4)*4] for k in range(4))
                if fmt==5 and any(v!=255 for v in cell[3::4]):raise FormatError('opaque BC1 writing requires opaque pixels')
                block=encode_rgba_block(cell)
                if fmt==5:
                    block=block[8:];c0,c1=struct.unpack('<HH',block[:4])
                    if c0<c1:raise FormatError('opaque BC1 endpoint order')
                    if c0==c1:block=block[:4]+bytes(4)
                out.extend(block)
        linear=bytes(out)
        if cache is not None:cache[key]=linear
    if not isinstance(linear,bytes) or len(linear)!=len(offsets)*bs:raise FormatError('Xbox BC encoding cache mismatch')
    output=bytearray(raw)
    for i,o in enumerate(offsets):
        b=linear[i*bs:(i+1)*bs];output[o:o+bs]=b''.join(b[k:k+2][::-1] for k in range(0,bs,2))
    output=bytes(output);allowed=set(offsets)
    changed={i for i in range(0,len(raw),bs) if raw[i:i+bs]!=output[i:i+bs]}
    if not changed<=allowed:raise FormatError('Xbox BC edit escaped authorized units')
    return output,dict(rect=rect,changed_blocks=len(changed),authorized_blocks=len(allowed),
                       untouched_blocks_preserved=True,alignment_padding_preserved=True)

def rebuild_payload(payload,texture,raw,target):
    if len(raw)!=texture['layout']['storage_bytes']:raise FormatError('Xbox BC rebuild allocation mismatch')
    stored=wrap_ue3_chunk(raw) if texture['flags']==64 else raw
    po=texture['payload_offset'];end=po+texture['stored_size']
    out=bytearray(payload[:po]+stored+payload[end:])
    struct.pack_into('>I',out,texture['source_offset']+12,target+texture['source_offset']+16)
    struct.pack_into('>I',out,texture['bulk_offset']+8,len(stored))
    struct.pack_into('>I',out,texture['bulk_offset']+12,target+po)
    return bytes(out)
