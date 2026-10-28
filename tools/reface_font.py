"""Re-face explicit existing Font mappings in a normalized package copy.

Reuses a selected existing atlas, preserves all other mappings and exports,
updates BOTH metric representations, and leaves the source font untouched.
The profile, not this tool, chooses a language, face, size or glyph aliases.
"""
from __future__ import annotations
import hashlib
import io
import struct
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from .build_font_supplement import context
from .ue3_fonts import parse_font_payload, read_properties
from .ue3_package import Reader, parse_summary
from .supplement_font import parse_atlas_payload
from .font_outline import embolden_glyph
from .font_shadow import shadow_pixels
from .texture_overlay import encode_rgba_block
from .ue3_textures import (encode_white_bc3_block, decode_dxt5,
                           xbox_tiled_block_offset)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raster_cells(font_path, expected_sha, spec, codepoints, previous_widths):
    raw = Path(font_path).read_bytes()
    if sha(raw) != expected_sha:
        raise ValueError('source font SHA256 mismatch')
    size, height = spec['font_size'], spec['metric_height']
    if any(type(n) is not int or not 1 <= n <= 128 for n in (size, height)):
        raise ValueError('font size/height outside bounds')
    aliases = spec.get('glyph_aliases', {})
    with TTFont(io.BytesIO(raw)) as tt:
        cmap = tt.getBestCmap()
    face = ImageFont.truetype(io.BytesIO(raw), size)
    range_faces = []
    for rule in spec.get('size_ranges', []):
        if (set(rule) != {'first','last','size'} or any(type(v) is not int for v in rule.values())
                or not 0 <= rule['first'] <= rule['last'] <= 65535 or not 1 <= rule['size'] <= size):
            raise ValueError('invalid explicit optical size range')
        range_faces.append((rule,ImageFont.truetype(io.BytesIO(raw),rule['size'])))
    def selected_face(source):
        matches=[f for rule,f in range_faces if rule['first']<=ord(source)<=rule['last']]
        if len(matches)>1:raise ValueError('overlapping optical size ranges')
        return matches[0] if matches else face
    rows = []
    for cp in sorted(codepoints):
        char = chr(cp)
        source = aliases.get(char, char)
        if len(source) != 1 or ord(source) not in cmap:
            raise ValueError('missing source glyph: U+%04X' % cp)
        blank = unicodedata.category(char) == 'Zs'
        glyph_face=selected_face(source)
        mask, offset = glyph_face.getmask2(source, mode='L', anchor='ls')
        ink = mask.getbbox()
        if ink is None and not blank:
            raise ValueError('empty non-space glyph: U+%04X' % cp)
        bounds = None if blank else (offset[0]+ink[0], offset[1]+ink[1],
                                    offset[0]+ink[2], offset[1]+ink[3])
        width = previous_widths[cp] if blank else bounds[2]-bounds[0]+5
        if unicodedata.east_asian_width(char) in ('W', 'F'):
            width = max(width, spec['wide_advance'])
        # Preserve accepted advance whenever it can contain this face with margins.
        width = max(width, previous_widths[cp])
        if not 1 <= width <= 128:
            raise ValueError('glyph width outside bounds')
        rows.append(dict(codepoint=cp, source_character=source, bounds=bounds,
                         metric_width=width, metric_height=height,
                         raster_size=glyph_face.size,width=(width+3)//4*4, height=(height+3)//4*4))
    boxes = [r['bounds'] for r in rows if r['bounds']]
    descent = max([b[3] for b in boxes]+[0])
    # One-pixel shadow room, if the complete foreground union allows it.
    baseline = height-descent-1
    if baseline+min(b[1] for b in boxes) < 0:
        baseline += 1
    if baseline+min(b[1] for b in boxes) < 0:
        raise ValueError('full glyph union exceeds metric height')
    for row in rows:
        w,h = row['width'], row['height']
        glyph_face=selected_face(row['source_character'])
        im = Image.new('L', (w,h))
        if row['bounds']:
            b = row['bounds']; left = 2+(row['metric_width']-(b[2]-b[0]+5))//2
            ImageDraw.Draw(im).text((left-b[0],baseline),row['source_character'],
                                   font=glyph_face,anchor='ls',fill=255)
        record = dict(raster_bbox=im.getbbox(),cell_baseline=baseline)
        cell = dict(width=w,height=h,metric_width=row['metric_width'],
                    character=row['source_character'])
        alpha,growth = embolden_glyph(glyph_face,cell,record,im.tobytes(),height,spec['stroke_em'])
        row.update(baseline=baseline,outline_growth=growth)
        # Verify that neither original nor weighted foreground is clipped.
        if record['raster_bbox'] and (record['raster_bbox'][3]>height or record['raster_bbox'][0]<0):
            raise ValueError('foreground clipping')
        linear = bytearray()
        for by in range(0,h,4):
            for bx in range(0,w,4):
                linear.extend(encode_white_bc3_block([alpha[(by+y)*w+bx+x] for y in range(4) for x in range(4)]))
        rgba = decode_dxt5(bytes(linear),w,h)
        row['shadow_pixels']=row['clipped_shadow_samples']=0
        if spec.get('shadow'):
            rgba,added,clipped=shadow_pixels(rgba,w,h,row['metric_width'],height)
            row.update(shadow_pixels=added,clipped_shadow_samples=clipped)
            linear = bytearray()
            for by in range(0,h,4):
                for bx in range(0,w,4):
                    block=b''.join(rgba[((by+y)*w+bx)*4:((by+y)*w+bx+4)*4] for y in range(4))
                    linear.extend(encode_rgba_block(block))
        row['linear']=bytes(linear)
        row['rgba_sha256']=sha(decode_dxt5(bytes(linear),w,h))
    return rows


def place_cells(width,height,preserved,cells):
    """First-fit block packing, reserving EVERY unselected visible glyph."""
    occupied=set()
    for g in preserved:
        for y in range(g['StartV']//4,(g['StartV']+g['VSize']+3)//4):
            for x in range(g['StartU']//4,(g['StartU']+g['USize']+3)//4):
                occupied.add((x,y))
    # Shelf packing makes allocation deterministic and bounded, without glyph overlap.
    x=y=shelf=0
    for c in cells:
        w,h=c['width']//4,c['height']//4
        while True:
            if x+w>width//4:
                x=0;y+=shelf or h;shelf=0
            if y+h>height//4:
                raise ValueError('atlas capacity exceeded')
            blocks={(xx,yy) for yy in range(y,y+h) for xx in range(x,x+w)}
            if not blocks & occupied:
                occupied.update(blocks);c.update(x=x*4,y=y*4);x+=w;shelf=max(shelf,h);break
            x+=1;shelf=max(shelf,h)
    return cells


def reface(data, expected_sha, font_object, font_path, font_sha, spec):
    if sha(data)!=expected_sha or parse_summary(data,len(data))['compression_flags']:
        raise ValueError('package SHA256/raw identity mismatch')
    ctx=context(data,None); names=ctx['tables']['names']
    es=[e for e in ctx['tables']['exports'] if e['path']==font_object]
    if len(es)!=1 or es[0]['class_path'] not in ('Font','Engine.Font'):
        raise ValueError('explicit Font export not found')
    e=es[0];start=e['serial_offset'];payload=data[start:start+e['serial_size']]
    font=parse_font_payload(payload,names)
    mapping={r['codepoint']:r['glyph_index'] for r in font['remap']}
    codepoints=spec['codepoints']
    if (not isinstance(codepoints,list) or not 1<=len(codepoints)<=4096
            or len(set(codepoints))!=len(codepoints) or any(cp not in mapping for cp in codepoints)):
        raise ValueError('explicit mapped codepoint selection required')
    selected={mapping[cp] for cp in codepoints}
    if len(selected)!=len(codepoints):
        raise ValueError('shared glyph-index aliases require explicit handling')
    ti=spec['texture_index'];ref=font['textures'][ti]
    ae=ctx['tables']['exports'][ref-1];at=ae['serial_offset']
    texture=parse_atlas_payload(data[at:at+ae['serial_size']],names,at)
    bulk=texture['mips'][0]['bulk']
    if bulk['flags'] or len(texture['mips'])!=1:
        raise ValueError('raw single-mip atlas required')
    w,h=texture['width'],texture['height']
    cells=raster_cells(font_path,font_sha,spec,codepoints,{cp:font['characters'][mapping[cp]]['USize'] for cp in codepoints})
    preserved=[g for i,g in enumerate(font['characters']) if i not in selected and g['TextureIndex']==ti]
    place_cells(w,h,preserved,cells)
    out=bytearray(data);changed=set()
    for cell in cells:
        g=font['characters'][mapping[cell['codepoint']]]
        values=dict(StartU=cell['x'],StartV=cell['y'],USize=cell['metric_width'],VSize=cell['metric_height'],TextureIndex=ti)
        reader=Reader(payload);reader.pos=g['tagged_offset']
        for prop in read_properties(reader,names):
            if prop['name'] not in values:raise ValueError('unexpected glyph field')
            val=values[prop['name']];pos=start+prop['value_offset']
            b=bytes([val]) if prop['name']=='TextureIndex' else struct.pack('>i',val)
            out[pos:pos+len(b)]=b
        pos=start+g['native_offset']
        out[pos:pos+17]=struct.pack('>iiiiB',*(values[k] for k in ['StartU','StartV','USize','VSize','TextureIndex']))
        cw=cell['width']//4
        for by in range(cell['height']//4):
            for bx in range(cw):
                off=xbox_tiled_block_offset(cell['x']//4+bx,cell['y']//4+by,((w+127)&~127)//4)*16
                pos=at+bulk['payload_offset']+off
                chunk=cell['linear'][(by*cw+bx)*16:(by*cw+bx+1)*16]
                out[pos:pos+16:2]=chunk[1::2]
                out[pos+1:pos+16:2]=chunk[::2]
                changed.add(off)
    result=bytes(out)
    actual=parse_font_payload(result[start:start+e['serial_size']],names)
    if actual['remap']!=font['remap']:raise ValueError('remap changed')
    # Independently gather the actual Xbox native blocks and compare decoded glyphs.
    for cell in cells:
        check=bytearray();cw=cell['width']//4
        g=actual['characters'][mapping[cell['codepoint']]]
        if [g[k] for k in ('StartU','StartV','USize','VSize','TextureIndex')] != [cell['x'],cell['y'],cell['metric_width'],cell['metric_height'],ti]:
            raise ValueError('rebuilt metric mismatch')
        for by in range(cell['height']//4):
            for bx in range(cw):
                off=xbox_tiled_block_offset(g['StartU']//4+bx,g['StartV']//4+by,((w+127)&~127)//4)*16
                pos=at+bulk['payload_offset']+off;b=result[pos:pos+16]
                check.extend(b''.join(b[i:i+2][::-1] for i in range(0,16,2)))
        if sha(decode_dxt5(bytes(check),cell['width'],cell['height']))!=cell['rgba_sha256']:
            raise ValueError('native glyph pixel roundtrip mismatch')
    for i,g in enumerate(font['characters']):
        if i not in selected and actual['characters'][i]!=g:raise ValueError('unselected metric changed')
    for other in ctx['tables']['exports']:
        if other['table_offset'] in (e['table_offset'],ae['table_offset']):continue
        p=other['serial_offset'];z=other['serial_size']
        if result[p:p+z]!=data[p:p+z]:raise ValueError('unselected export changed')
    proof=dict(kind='font-reface',input_sha256=sha(data),output_sha256=sha(result),
               font_object=font_object,atlas_object=ae['path'],source_font_sha256=font_sha,
               glyphs=[{k:v for k,v in c.items() if k!='linear'} for c in cells],
               remap_preserved=True,unselected_exports_preserved=True,
               changed_blocks=len(changed),game_rendering_verified=False)
    return result,proof
