"""Bounded, source-locked caption replacement for silent Bink 1 loading loops.

Language, typography, measured source rectangles and tool identities are data.
Decoded frames are streamed; one reusable AVI is the only uncompressed output.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import math


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bink_header(data):
    if len(data) < 48 or data[:4] != b'BIKi':
        raise ValueError('Expected supported Bink 1 revision i')
    size, frames, largest, repeated, width, height, numerator, denominator, flags, audio = struct.unpack_from('<10I', data, 4)
    if size+8 != len(data) or frames != repeated or not 1 <= frames <= 600:
        raise ValueError('Invalid Bink size/frame fields')
    if not 1 <= width <= 1920 or not 1 <= height <= 1080 or not numerator or not denominator or audio or flags:
        raise ValueError('Only bounded silent non-alpha Bink clips are supported')
    if 44 + 4*(frames+1) > len(data): raise ValueError('Truncated Bink frame table')
    offsets = [x & ~1 for x in struct.unpack_from('<'+'I'*(frames+1), data, 44)]
    if (offsets[0] < 44+4*(frames+1) or offsets[-1] != len(data)
            or any(a >= b for a,b in zip(offsets, offsets[1:]))):
        raise ValueError('Invalid Bink frame offsets')
    if max(b-a for a,b in zip(offsets, offsets[1:])) != largest:
        raise ValueError('Bink largest frame mismatch')
    return dict(width=width,height=height,frames=frames,numerator=numerator,
                denominator=denominator,magic='BIKi',audio_tracks=audio)


def preserve_timing(source, encoded):
    old = bink_header(source); new = bink_header(encoded)
    for key in ('width','height','frames','magic','audio_tracks'):
        if old[key] != new[key]: raise ValueError('Encoded clip changed '+key)
    a = old['numerator']/old['denominator']; b = new['numerator']/new['denominator']
    if abs(a-b)/a > .0001: raise ValueError('Encoder changed frame rate')
    out = bytearray(encoded)
    struct.pack_into('<II', out, 28, old['numerator'], old['denominator'])
    if bink_header(out) != old: raise ValueError('Timing restoration failed')
    return bytes(out)


def wrap_text(text, font, max_width):
    """Respect explicit paragraphs and keep closing punctuation off new lines."""
    if not isinstance(text, str) or not text.strip() or len(text)>4000 or not math.isfinite(max_width) or max_width<=0:
        raise ValueError('Caption text/width bound')
    closing = set('，。！？；：、）】》」』”’…,.!?;:)]}')
    opening = set('（【《「『“‘([{')
    result=[]
    for paragraph in text.split('\n'):
        if not paragraph:
            result.append('');continue
        remaining=paragraph
        while remaining:
            end=0
            while end<len(remaining) and font.getlength(remaining[:end+1])<=max_width:
                end+=1
            if end<len(remaining):
                while end and (remaining[end] in closing or remaining[end-1] in opening):
                    end-=1
            if not end:raise ValueError('Unbreakable caption punctuation/width')
            result.append(remaining[:end]);remaining=remaining[end:]
    if any(font.getlength(line)>max_width for line in result): raise ValueError('Unbreakable caption width')
    return result


def render_layer(text, font_bytes, canvas, style):
    """Render explicit gradient, outline, highlight/glow and offset shadow."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
    scale=4; width,height=canvas
    if any(type(v) is not int or v<1 for v in canvas) or width>1920 or height>1080:
        raise ValueError('Caption canvas bound')
    if type(style['font_size']) is not int or not 4<=style['font_size']<=128:
        raise ValueError('Caption font size bound')
    for field in ('line_height','outline_width','shadow_radius','glow_radius','weight','inner_edge_width'):
        v=style.get(field,0)
        if not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or v>256:
            raise ValueError('Caption style bound: '+field)
    if style['line_height']<=0 or style['outline_width']>8 or style['shadow_radius']>16 or style['glow_radius']>16:
        raise ValueError('Caption effect bound')
    for rgba in [style['outline'],style['shadow'],style['glow'],style.get('inner_edge',[0,0,0,0])]+[s[1] for s in style['gradient']]:
        if len(rgba)!=4 or any(type(v) is not int or not 0<=v<=255 for v in rgba):
            raise ValueError('Caption colour bound')
    stops=[s[0] for s in style['gradient']]
    if len(stops)<2 or stops[0]!=0 or stops[-1]!=1000 or any(a>=b for a,b in zip(stops,stops[1:])):
        raise ValueError('Gradient stops')
    font=ImageFont.truetype(io.BytesIO(font_bytes),style['font_size']*scale)
    x,y,w,h=style['rect']; align=style['align']
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in style['rect']) or w<=0 or h<=0 or align not in ('left','right','center') or x<0 or y<0 or x+w>width or y+h>height: raise ValueError('Caption geometry')
    lines=wrap_text(text,font,(w-2*style['outline_width'])*scale)
    mask=Image.new('L',(width*scale,height*scale)); draw=ImageDraw.Draw(mask)
    line_height=style['line_height']; ink_boxes=[]
    for i,line in enumerate(lines):
        box=font.getbbox(line); ink_w=box[2]-box[0]; ink_h=box[3]-box[1]
        left=x*scale if align=='left' else (x+w)*scale-ink_w if align=='right' else (x+w/2)*scale-ink_w/2
        top=(y+i*line_height)*scale
        if top+ink_h>(y+h)*scale: raise ValueError('Caption height overflow')
        draw.text((round(left-box[0]),round(top-box[1])),line,font=font,fill=255)
        ink_boxes.append([left/scale,top/scale,ink_w/scale,ink_h/scale])
    if style.get('weight',0):
        mask=mask.filter(ImageFilter.MaxFilter(2*round(style['weight']*scale)+1))
    outline=mask.filter(ImageFilter.MaxFilter(2*round(style['outline_width']*scale)+1))
    def colour(m,rgba):
        image=Image.new('RGBA',m.size,tuple(rgba)); image.putalpha(m.point(lambda a:round(a*rgba[3]/255)));return image
    image=Image.new('RGBA',mask.size)
    shadow_mask=Image.new('L',mask.size); sx,sy=style['shadow_offset']
    shadow_mask.paste(outline,(round(sx*scale),round(sy*scale)))
    image=Image.alpha_composite(image,colour(shadow_mask.filter(ImageFilter.GaussianBlur(style['shadow_radius']*scale)),style['shadow']))
    if style['glow_radius'] and style['glow'][3]:
        image=Image.alpha_composite(image,colour(outline.filter(ImageFilter.GaussianBlur(style['glow_radius']*scale)),style['glow']))
    image=Image.alpha_composite(image,colour(outline,style['outline']))
    fill=Image.new('RGBA',mask.size); fd=ImageDraw.Draw(fill)
    gradient=style['gradient']
    if gradient[0][0]!=0 or gradient[-1][0]!=1000: raise ValueError('Gradient endpoints')
    for box in ink_boxes:
        _,top,_,ink_h=box
        for row in range(round(top*scale),round((top+ink_h)*scale)+1):
            t=max(0,min(1000,(row/scale-top)*1000/max(1,ink_h)))
            lo,hi=next((a,b) for a,b in zip(gradient,gradient[1:]) if a[0]<=t<=b[0])
            f=(t-lo[0])/(hi[0]-lo[0]); rgba=tuple(round(a+(b-a)*f) for a,b in zip(lo[1],hi[1]))
            fd.line((0,row,width*scale,row),fill=rgba)
    fill.putalpha(ImageChops.multiply(mask,fill.getchannel('A')))
    image=Image.alpha_composite(image,fill)
    if style.get('inner_edge_width',0):
        inner=mask.filter(ImageFilter.MinFilter(2*round(style['inner_edge_width']*scale)+1))
        edge=ImageChops.subtract(mask,inner)
        image=Image.alpha_composite(image,colour(edge,style['inner_edge']))
    image=image.resize(canvas,Image.Resampling.LANCZOS)
    return image, dict(lines=lines,ink_boxes=ink_boxes,style=style,alpha_bbox=image.getbbox())


def source_ink_mask(frame, rect, threshold, radius):
    import numpy as np
    from PIL import Image, ImageFilter
    if (len(rect)!=4 or any(type(v) is not int for v in rect)
            or min(rect[:2])<0 or min(rect[2:])<=0
            or rect[0]+rect[2]>frame.width or rect[1]+rect[3]>frame.height
            or type(radius) is not int or not 0<=radius<=8):
        raise ValueError('Source ink geometry')
    x,y,w,h=rect
    crop=np.asarray(frame.convert('RGB').crop((x,y,x+w,y+h)))
    neutral=crop.max(axis=2).astype(int)-crop.min(axis=2).astype(int)<45
    cut=np.asarray(threshold)
    if cut.ndim>1 or not np.isfinite(cut).all() or cut.min()<0 or cut.max()>256:
        raise ValueError('Source ink threshold')
    if cut.ndim==1:
        if len(cut)!=h: raise ValueError('Source ink threshold height mismatch')
        cut=cut[:,None]
    seed=(crop.min(axis=2)>=cut)&neutral
    return np.asarray(Image.fromarray(seed.astype('uint8')*255).filter(ImageFilter.MaxFilter(radius*2+1)))>0


def component_ink_mask(frame, rect, selection, radius):
    """Select audited connected glyph components, never a bright backdrop.

    Component boxes and thresholds are source-relative observations in locale
    data. Requiring every exact component prevents an altered image or a broad
    brightness erase from consuming a face, white armor or ornamental ribbon.
    """
    from collections import deque
    import numpy as np
    from PIL import Image, ImageFilter
    roi=selection['roi']; x,y,right,bottom=roi
    if (len(roi)!=4 or any(type(v) is not int for v in roi) or min(x,y)<0
            or right<=x or bottom<=y or right>frame.width or bottom>frame.height
            or type(radius) is not int or not 0<=radius<=8):raise ValueError('Component geometry')
    threshold=selection['threshold'];chroma=selection['chroma'];minimum=selection['min_area']
    if not 0<=threshold<=255 or not 0<chroma<=255 or not 1<=minimum<=1000:
        raise ValueError('Component selection bound')
    wanted={tuple(b) for b in selection['boxes']}
    if not wanted or len(wanted)!=len(selection['boxes']): raise ValueError('Duplicate or empty component selection')
    rgb=np.asarray(frame.convert('RGB'));a=rgb[y:bottom,x:right].astype('int16')
    seed=(a.min(2)>threshold)&(a.max(2)-a.min(2)<chroma)
    seen=np.zeros(seed.shape,bool);height,width=seed.shape; selected=[];found=set()
    for v,u in zip(*np.where(seed)):
        if seen[v,u]:continue
        seen[v,u]=True;todo=deque([(int(v),int(u))]);pixels=[]
        while todo:
            yy,xx=todo.popleft();pixels.append((y+yy,x+xx))
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=yy+dy,xx+dx
                if 0<=ny<height and 0<=nx<width and seed[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;todo.append((ny,nx))
        if len(pixels)<minimum:continue
        pp=np.asarray(pixels);box=(int(pp[:,1].min()),int(pp[:,0].min()),int(pp[:,1].max()+1),int(pp[:,0].max()+1))
        if box in wanted:selected.extend(pixels);found.add(box)
    if found!=wanted:raise ValueError('Audited glyph components changed')
    rx,ry,rw,rh=rect
    if min(rx,ry)<0 or min(rw,rh)<=0 or rx+rw>frame.width or ry+rh>frame.height:
        raise ValueError('Component destination geometry')
    mask=np.zeros((rh,rw),np.uint8)
    for py,px in selected:
        if not rx<=px<rx+rw or not ry<=py<ry+rh:raise ValueError('Component outside restoration rectangle')
        mask[py-ry,px-rx]=255
    return np.asarray(Image.fromarray(mask).filter(ImageFilter.MaxFilter(radius*2+1)))>0


def restore_masked(frame, rect, mask):
    """Interpolate only a bounded source-ink mask; retain all unmasked pixels.

    Hidden artwork is reconstructed, not claimed as original. A byte-identical
    outside-mask assertion is independent of later lossy video compression.
    """
    import numpy as np
    from PIL import Image
    x,y,w,h=rect
    if (min(x,y)<0 or min(w,h)<=0 or x+w>frame.width or y+h>frame.height
            or mask.shape!=(h,w) or mask.dtype!=np.dtype('bool')):
        raise ValueError('Restoration mask geometry')
    crop=np.asarray(frame.convert('RGB').crop((x,y,x+w,y+h))).copy()
    values=crop.astype('float64'); known=~mask; pending=mask.copy()
    # Average the known front into the hole; no wrapping across crop boundaries.
    for _ in range(w+h):
        if not pending.any(): break
        total=np.zeros_like(values); count=np.zeros((h,w),dtype='float64')
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ys=slice(max(0,dy),min(h,h+dy));xs=slice(max(0,dx),min(w,w+dx))
            yt=slice(max(0,-dy),min(h,h-dy));xt=slice(max(0,-dx),min(w,w-dx))
            weight=known[ys,xs];count[yt,xt]+=weight
            total[yt,xt]+=values[ys,xs]*weight[:,:,None]
        ready=pending&(count>0)
        if not ready.any(): raise ValueError('Ink mask has no exterior samples')
        values[ready]=total[ready]/count[ready,None];known[ready]=True;pending[ready]=False
    for _ in range(24):
        padded=np.pad(values,((1,1),(1,1),(0,0)),mode='edge')
        avg=(padded[:-2,1:-1]+padded[2:,1:-1]+padded[1:-1,:-2]+padded[1:-1,2:])/4
        values[mask]=avg[mask]
    repaired=np.rint(values).clip(0,255).astype('uint8')
    if not np.array_equal(repaired[~mask],crop[~mask]): raise ValueError('Restoration touched unmasked artwork')
    out=frame.copy();out.paste(Image.fromarray(repaired),(x,y))
    return out,mask


def restore_source_ink(frame, rect, threshold, radius):
    return restore_masked(frame,rect,source_ink_mask(frame,rect,threshold,radius))


def decoded_frames(ffmpeg, source, header):
    command=[str(ffmpeg),'-v','error','-i',str(source),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']
    p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    size=header['width']*header['height']*3
    try:
        for _ in range(header['frames']):
            data=p.stdout.read(size)
            if len(data)!=size: raise ValueError('Short decoded frame')
            yield data
        if p.stdout.read(1): raise ValueError('Extra decoded frames')
        errors=p.stderr.read(); code=p.wait(timeout=30)
        if code: raise ValueError('Frame decode failed: '+errors.decode(errors='replace'))
    finally:
        if p.poll() is None: p.kill();p.wait()
        p.stdout.close();p.stderr.close()
