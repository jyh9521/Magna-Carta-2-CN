"""Bounded BC3 text-region replacement; original tile blocks stay byte-identical.

Uses the existing attributed Xbox layout and BC3 decoder. RGB compression is
deterministic and lossy; previews always decode the encoded output, not the draw.
"""
import hashlib
import io
import struct
from .ue3_package import FormatError, parse_summary, parse_tables
from .ue3_textures import (encode_white_bc3_block, scatter_linear_dxt5_cell,
                          untile_dxt5, decode_dxt5, xbox_tiled_block_offset)
from .supplement_font import (parse_atlas_payload, atlas_tiles, decode_logical,
                              repack_append_only)
from .lzx_stored import wrap_ue3_chunk


# Finite bounds cover the audited multi-package image families, not game-specific IDs.
MAX_TEXTURE_SOURCES=512
MAX_TEXT_LAYERS=1024
MAX_TEXTURE_EDITS=512
MAX_TEXTURE_REGIONS=32

def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode_rgba_block(rgba):
    if not isinstance(rgba, bytes) or len(rgba) != 64:
        raise FormatError('BC3 requires sixteen RGBA byte samples')
    pixels = [tuple(rgba[i:i+4]) for i in range(0,64,4)]
    colors = sorted({p[:3] for p in pixels if p[3]}) or [(0,0,0)]
    a,b = max(((a,b) for a in colors for b in colors),
              key=lambda pair: sum((x-y)**2 for x,y in zip(*pair)))
    pack = lambda p: (((p[0]*31+127)//255)<<11) | (((p[1]*63+127)//255)<<5) | ((p[2]*31+127)//255)
    def unpack(v):
        r,g,b = (v>>11)&31,(v>>5)&63,v&31
        return (r*8+r//4,g*4+g//16,b*8+b//4)
    c0,c1 = sorted((pack(a),pack(b)),reverse=True)
    palette = [unpack(c0),unpack(c1)]
    palette += [tuple((2*x+y)//3 for x,y in zip(*palette)),
                tuple((x+2*y)//3 for x,y in zip(*palette))]
    indices = 0
    for i,p in enumerate(pixels):
        choice = min(range(4),key=lambda j: sum((p[k]-palette[j][k])**2 for k in range(3)))
        indices |= choice << (2*i)
    return encode_white_bc3_block([p[3] for p in pixels])[:8]+struct.pack('<HHI',c0,c1,indices)


def overlay_tiles(tiled,width,height,rect,rgba,encoding_cache=None):
    if (not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect)
            or not isinstance(rgba,bytes)):
        raise FormatError('explicit integer rectangle and RGBA bytes required')
    x,y,w,h = rect
    if (any(type(v) is not int for v in (width,height)) or min(width,height)<32
            or max(width,height)>8192 or any(v%4 for v in (width,height,x,y,w,h))
            or min(x,y)<0 or x+w>width or y+h>height
            or min(w,h)<=0 or max(w,h)>8192 or len(rgba)!=w*h*4):
        raise FormatError('overlay dimensions or RGBA length mismatch')
    key=(w,h,rgba)
    linear=None if encoding_cache is None else encoding_cache.get(key)
    if linear is None:
        encoded=bytearray()
        for by in range(h//4):
            for bx in range(w//4):
                block=b''.join(rgba[((by*4+iy)*w+bx*4)*4:((by*4+iy)*w+bx*4+4)*4] for iy in range(4))
                encoded.extend(encode_rgba_block(block))
        linear=bytes(encoded)
        if encoding_cache is not None:encoding_cache[key]=linear
    if not isinstance(linear,bytes) or len(linear)!=w*h:raise FormatError('invalid cached BC3 region')
    output=scatter_linear_dxt5_cell(tiled,width,height,x,y,w,h,linear)
    allowed={xbox_tiled_block_offset(x//4+bx,y//4+by,((width+127)&~127)//4)*16
             for by in range(h//4) for bx in range(w//4)}
    changed=[i for i in range(0,len(tiled),16) if tiled[i:i+16]!=output[i:i+16]]
    if not set(changed)<=allowed:
        raise FormatError('texture block escaped authorized rectangle')
    return output,dict(rect=rect,changed_blocks=len(changed),authorized_blocks=len(allowed),
                       untouched_blocks_preserved=True,alignment_padding_preserved=True)


def layer_ids(edit):
    """One legacy label or explicit ordered, disjoint labels for one image."""
    if ('label' in edit)==('regions' in edit):raise FormatError('exactly one label or region list required')
    ids=[edit['label']] if 'label' in edit else edit['regions']
    if (not isinstance(ids,list) or not 1<=len(ids)<=MAX_TEXTURE_REGIONS
            or any(not isinstance(v,str) or not v or len(v)>128 for v in ids)
            or len(set(ids))!=len(ids)):raise FormatError('invalid texture region labels')
    if 'regions' in edit and (not isinstance(edit.get('image_id'),str) or not edit['image_id'] or len(edit['image_id'])>128):
        raise FormatError('multi-region image requires explicit image_id')
    return ids


def image_id(edit):
    ids=layer_ids(edit)
    return edit['image_id'] if 'regions' in edit else ids[0]


def region_offsets(width,height,rect):
    if (not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect)
            or any(type(v) is not int for v in (width,height))):raise FormatError('invalid region rectangle')
    x,y,w,h=rect
    if (min(width,height)<32 or max(width,height)>8192 or any(v%4 for v in (width,height,x,y,w,h))
            or min(x,y)<0 or min(w,h)<=0 or x+w>width or y+h>height):raise FormatError('region rectangle outside texture')
    return {xbox_tiled_block_offset(x//4+bx,y//4+by,((width+127)&~127)//4)*16
            for by in range(h//4) for bx in range(w//4)}


def rgba_crop(rgba,width,rect):
    x,y,w,h=rect
    return b''.join(rgba[((y+dy)*width+x)*4:((y+dy)*width+x+w)*4] for dy in range(h))


def overlay_regions(tiles,width,height,edit,layers,encoding_cache=None):
    ids=layer_ids(edit);protected=edit.get('protected_regions',[])
    if not isinstance(protected,list) or len(protected)>16:raise FormatError('protected region bound')
    allowed=set();resolved=[]
    for name in ids:
        if name not in layers:raise FormatError('texture region label missing')
        label,rgba=layers[name];blocks=region_offsets(width,height,label['rect'])
        if blocks & allowed:raise FormatError('texture regions overlap')
        allowed.update(blocks);resolved.append((label,rgba))
    protected_blocks=set();protected_ids=set()
    for row in protected:
        if (not isinstance(row,dict) or set(row)!={'id','rect','rgba_sha256'}
                or not isinstance(row['id'],str) or not row['id'] or len(row['id'])>128
                or row['id'] in protected_ids):raise FormatError('invalid protected region')
        protected_ids.add(row['id']);blocks=region_offsets(width,height,row['rect'])
        if blocks & (allowed|protected_blocks):raise FormatError('protected region overlaps edit or another protection')
        protected_blocks.update(blocks)
    patched=tiles;proofs=[]
    for label,rgba in resolved:
        patched,proof=overlay_tiles(patched,width,height,label['rect'],rgba,encoding_cache);proofs.append(proof)
    # Keep legacy manifest/report bytes exactly stable when no new features apply.
    if 'label' in edit and not protected:return patched,proofs[0]
    changed={i for i in range(0,len(tiles),16) if tiles[i:i+16]!=patched[i:i+16]}
    if not changed<=allowed:raise FormatError('composite edit escaped authorized region union')
    result=dict(regions=proofs,changed_blocks=len(changed),authorized_blocks=len(allowed),
                untouched_blocks_preserved=True,alignment_padding_preserved=True)
    if protected:
        before=decode_dxt5(untile_dxt5(tiles,width,height),width,height)
        after=decode_dxt5(untile_dxt5(patched,width,height),width,height);checks=[]
        for row in protected:
            blocks=region_offsets(width,height,row['rect']);a=rgba_crop(before,width,row['rect']);b=rgba_crop(after,width,row['rect'])
            if (digest(a)!=row['rgba_sha256'] or a!=b
                    or any(tiles[i:i+16]!=patched[i:i+16] for i in blocks)):
                raise FormatError('protected region block/pixel hash mismatch')
            checks.append(dict(id=row['id'],rect=row['rect'],before_rgba_sha256=digest(a),after_rgba_sha256=digest(b),blocks_preserved=True))
        result['protected_regions']=checks
    return patched,result


def label_style(label):
    """Locale-neutral RGBA palette; defaults retain the first overlay style."""
    defaults=dict(fill=(236,236,236,255),stroke_fill=(25,25,25,230),shadow_fill=(0,0,0,180))
    style=label.get('style',{})
    if not isinstance(style,dict) or set(style)-set(defaults):raise FormatError('unknown text layer style')
    result={}
    for key,value in defaults.items():
        rgba=style.get(key,value)
        if (not isinstance(rgba,(list,tuple)) or len(rgba)!=4
                or any(type(c) is not int or not 0<=c<=255 for c in rgba)):
            raise FormatError('text layer style requires four RGBA byte integers')
        result[key]=tuple(rgba)
    return result


def text_position(width,height,box,align='center'):
    """Place actual ink inside four-pixel margins; legacy centering is unchanged."""
    if (type(width) is not int or type(height) is not int or min(width,height)<=0
            or max(width,height)>2048 or not isinstance(box,(list,tuple)) or len(box)!=4
            or any(type(v) is not int for v in box) or box[2]<=box[0] or box[3]<=box[1]):
        raise FormatError('invalid text ink geometry')
    if not isinstance(align,str) or align not in ('left','center','right'):
        raise FormatError('invalid text alignment')
    iw=box[2]-box[0];ih=box[3]-box[1]
    if iw+8>width or ih+8>height:raise FormatError('text layer ink does not fit')
    x={'left':4,'center':(width-iw)//2,'right':width-4-iw}[align]-box[0]
    return x,(height-ih)//2-box[1]


def render_label(font_bytes,label):
    """Render an owned text layer only; no original image is fed to the rasterizer."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    from fontTools.ttLib import TTFont
    text=label['text'];rect=label['rect'];size=label['font_size'];style=label_style(label)
    if (not isinstance(text,str) or not text or len(text)>128 or any(ord(c)<32 for c in text)
            or type(size) is not int or not 1<=size<=128):
        raise FormatError('invalid text layer or font size')
    if not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect):
        raise FormatError('invalid text layer rectangle')
    _,_,w,h=rect
    if min(w,h)<=0 or max(w,h)>2048:raise FormatError('text layer bound')
    ft=TTFont(io.BytesIO(font_bytes));cmap=ft.getBestCmap();missing=[ord(c) for c in text if ord(c) not in cmap];ft.close()
    if missing:raise FormatError('text layer font has missing glyphs')
    font=ImageFont.truetype(io.BytesIO(font_bytes),size)
    image=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(image)
    box=draw.textbbox((0,0),text,font=font,stroke_width=1)
    pos=text_position(w,h,box,label.get('align','center'))
    shadow=Image.new('RGBA',(w,h));sd=ImageDraw.Draw(shadow)
    sd.text((pos[0]+1,pos[1]+2),text,font=font,fill=style['shadow_fill'],stroke_width=2,stroke_fill=style['shadow_fill'])
    image=Image.alpha_composite(image,shadow.filter(ImageFilter.GaussianBlur(1)))
    ImageDraw.Draw(image).text(pos,text,font=font,fill=style['fill'],stroke_width=1,stroke_fill=style['stroke_fill'])
    if image.getbbox() is None:raise FormatError('empty text layer')
    return image.tobytes()


def patch_package(data,expected_hash,edits,layers,decoder,encoding_cache=None):
    if digest(data)!=expected_hash:raise FormatError('texture base SHA256 mismatch')
    if not isinstance(edits,list) or not 1<=len(edits)<=MAX_TEXTURE_EDITS:raise FormatError('texture edit bound')
    summary=parse_summary(data,len(data));logical=decode_logical(data,summary,decoder)
    tables=parse_tables(logical,summary,len(logical));new=bytearray(logical);selected=set();records=[]
    for edit in edits:
        matches=[e for e in tables['exports'] if e['path'].casefold()==edit['object'].casefold()]
        if len(matches)!=1 or matches[0]['class_path']!='Engine.Texture2D':raise FormatError('texture object missing/ambiguous/wrong class')
        ex=matches[0]
        if ex['table_offset'] in selected:raise FormatError('duplicate texture object')
        selected.add(ex['table_offset']);off=ex['serial_offset'];old=logical[off:off+ex['serial_size']]
        if digest(old)!=edit['payload_sha256']:raise FormatError('texture export payload mismatch')
        texture=parse_atlas_payload(old,tables['names'],off);tiles=atlas_tiles(old,texture,decoder)
        if digest(tiles)!=edit['tiled_sha256']:raise FormatError('texture original tiles mismatch')
        if [texture['width'],texture['height']]!=edit['dimensions']:raise FormatError('texture dimensions mismatch')
        patched,proof=overlay_regions(tiles,texture['width'],texture['height'],edit,layers,encoding_cache)
        if patched==tiles:raise FormatError('texture edit is a no-op')
        bulk=texture['mips'][0]['bulk'];stored=wrap_ue3_chunk(patched) if bulk['flags']==0x40 else patched
        payload=bytearray(old[:bulk['payload_offset']]+stored+old[bulk['payload_offset']+bulk['size_on_disk']:])
        target=(len(new)+3)&~3
        struct.pack_into('>I',payload,bulk['size_on_disk_field_offset'],len(stored))
        for header in [texture['source_art'],bulk]:
            struct.pack_into('>I',payload,header['data_offset_field_offset'],target+header['payload_offset'])
        check=parse_atlas_payload(bytes(payload),tables['names'],target)
        if atlas_tiles(bytes(payload),check,decoder)!=patched:raise FormatError('texture bulk roundtrip failed')
        new.extend(bytes(target-len(new))+payload)
        struct.pack_into('>II',new,ex['table_offset']+32,len(payload),target)
        pixels=decode_dxt5(untile_dxt5(patched,texture['width'],texture['height']),texture['width'],texture['height'])
        records.append(dict(object=ex['path'],old_serial_offset=off,new_serial_offset=target,
                            before_tiled_sha256=digest(tiles),after_tiled_sha256=digest(patched),
                            decoded_rgba_sha256=digest(pixels),**proof))
    nt=parse_tables(bytes(new),summary,len(new))
    for a,b in zip(tables['exports'],nt['exports']):
        if a['table_offset'] not in selected and (a!=b or logical[a['serial_offset']:a['serial_offset']+a['serial_size']]!=new[b['serial_offset']:b['serial_offset']+b['serial_size']]):
            raise FormatError('nonselected export changed')
    allowed={p+i for p in selected for i in range(32,40)}
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(logical,new))):raise FormatError('original logical prefix changed')
    output,packing=repack_append_only(data,summary,logical,bytes(new))
    output_summary=parse_summary(output,len(output))
    check=decode_logical(output,output_summary,decoder)
    expected=bytearray(new)
    if summary['compression_flags']:
        count_field=summary['summary_end']-16*len(summary['compressed_chunks'])-4
        struct.pack_into('>I',expected,count_field,len(output_summary['compressed_chunks']))
    if check!=bytes(expected):raise FormatError('texture package independent reopening mismatch')
    return output,dict(base_sha256=expected_hash,candidate_sha256=digest(output),textures=records,
                       nonselected_exports_preserved=len(tables['exports'])-len(selected),packing=packing,
                       game_rendering_verified=False)
