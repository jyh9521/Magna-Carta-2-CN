"""Explicit locale-neutral source-style rasterization; legacy labels are untouched.

Colours are measured and serialized by the caller, not guessed from a game ID.
Only the owned text mask is rasterized. Native restoration and BC/pixel guards
remain in texture_overlay and apply after this stage.
"""
import io
import math
from .ue3_package import FormatError


def validate(appearance, width, height):
    if not isinstance(appearance,dict):raise FormatError('invalid text appearance')
    if appearance=={'kind':'preserve-source-v1'}:return
    keys={'kind','ink_box','align','gradient','outline','outline_width','glow',
          'glow_radius','shadow','shadow_offset','shadow_radius','italic',
          'tracking','weight','motion','spans'}
    required=keys-{'spans'}
    if set(appearance)-keys or not required<=set(appearance) or appearance['kind']!='source-style-v1':
        raise FormatError('unknown or missing text appearance fields')
    def number(v,lo,hi):return type(v) in (int,float) and math.isfinite(v) and lo<=v<=hi
    box=appearance['ink_box']
    if (not isinstance(box,list) or len(box)!=4 or any(type(v) is not int for v in box)
            or min(box[:2])<0 or min(box[2:])<1 or box[0]+box[2]>width or box[1]+box[3]>height):
        raise FormatError('appearance ink box outside canvas')
    if appearance['align'] not in ('left','right','center'):raise FormatError('appearance alignment')
    def rgba(v):return isinstance(v,list) and len(v)==4 and all(type(c) is int and 0<=c<=255 for c in v)
    stops=appearance['gradient']
    if (not isinstance(stops,list) or not 2<=len(stops)<=256
            or any(not isinstance(s,list) or len(s)!=2 or type(s[0]) is not int or not 0<=s[0]<=1000 or not rgba(s[1]) for s in stops)
            or [s[0] for s in stops]!=sorted(set(s[0] for s in stops))
            or stops[0][0]!=0 or stops[-1][0]!=1000):raise FormatError('appearance gradient stops')
    if any(not rgba(appearance[k]) for k in ['outline','glow','shadow']):raise FormatError('appearance RGBA bytes')
    for k,lo,hi in [('outline_width',0,4),('glow_radius',0,12),('shadow_radius',0,8),
                    ('italic',-0.5,0.5),('tracking',-2,32),('weight',0,2),('motion',0,16)]:
        if not number(appearance[k],lo,hi):raise FormatError('appearance numeric bound: '+k)
    shift=appearance['shadow_offset']
    if not isinstance(shift,list) or len(shift)!=2 or any(not number(v,-8,8) for v in shift):
        raise FormatError('appearance shadow offset')
    spans=appearance.get('spans',[])
    if not isinstance(spans,list) or len(spans)>8:raise FormatError('appearance spans bound')
    for s in spans:
        if (not isinstance(s,dict) or set(s)!={'start','end','scale'}
                or any(type(s[k]) is not int for k in ['start','end'])
                or not 0<=s['start']<s['end']<=128 or not number(s['scale'],0.4,1.5)):
            raise FormatError('appearance span geometry')


def render(font_bytes,label):
    from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
    from .texture_overlay import render_geometry,render_text,font_codepoints
    w,h,crop=render_geometry(label);a=label['appearance'];validate(a,w,h)
    if a['kind']=='preserve-source-v1':return bytes(label['rect'][2]*label['rect'][3]*4)
    text=label['text'];size=label['font_size']
    if (not isinstance(text,str) or not text or len(text)>128 or any(ord(c)<32 for c in text)
            or type(size) is not int or not 1<=size<=128):raise FormatError('invalid text layer or font size')
    if any(ord(c) not in font_codepoints(font_bytes) for c in text):raise FormatError('text layer font has missing glyphs')
    if any(s['end']>len(text) for s in a.get('spans',[])):raise FormatError('appearance span outside text')
    visual=render_text(label);scale=4
    font=ImageFont.truetype(io.BytesIO(font_bytes),size*scale)
    # Rasterize independent glyphs to retain explicit tracking and reduced runs.
    glyphs=[];index=0
    for line in visual.split('\n'):
        row=[]
        for c in line:
            factor=next((s['scale'] for s in a.get('spans',[]) if s['start']<=index<s['end']),1)
            f=font if factor==1 else ImageFont.truetype(io.BytesIO(font_bytes),max(1,round(size*scale*factor)))
            row.append((c,f));index+=1
        glyphs.append(row)
    widths=[sum(f.getlength(c) for c,f in row)+max(0,len(row)-1)*a['tracking']*scale for row in glyphs]
    mw=math.ceil(max(widths)+size*scale);mh=math.ceil(len(glyphs)*size*scale*1.25+size*scale)
    if mw*mh>32*1024*1024:raise FormatError('appearance mask allocation bound')
    mask=Image.new('L',(mw,mh));draw=ImageDraw.Draw(mask)
    for j,row in enumerate(glyphs):
        x=0 if a['align']=='left' else max(widths)-widths[j] if a['align']=='right' else (max(widths)-widths[j])/2
        for c,f in row:
            draw.text((round(x),round((j+1)*size*scale*1.25)),c,font=f,fill=255,anchor='ls')
            x+=f.getlength(c)+a['tracking']*scale
    box=mask.getbbox()
    if box is None:raise FormatError('empty text layer')
    mask=mask.crop(box)
    bx,by,bw,bh=a['ink_box'];inkheight=bh
    mask=mask.resize((max(1,round(mask.width*inkheight/mask.height*scale)),inkheight*scale),Image.Resampling.LANCZOS)
    if a['weight']:
        k=round(a['weight']*scale)*2+1
        if k>1:mask=mask.filter(ImageFilter.MaxFilter(k))
    if a['italic']:
        shift=math.ceil(abs(a['italic'])*mask.height)
        mask=mask.transform((mask.width+shift,mask.height),Image.Transform.AFFINE,
            (1,a['italic'], -shift if a['italic']>0 else 0,0,1,0),Image.Resampling.BICUBIC)
    ow=a['outline_width'];margin=max(0,math.ceil(ow))
    limit=max(1,bw-2*margin)
    iw=min(limit,max(1,round(mask.width/scale)));ih=inkheight
    mask=mask.resize((iw,ih),Image.Resampling.LANCZOS)
    x=bx+margin if a['align']=='left' else bx+bw-iw-margin if a['align']=='right' else bx+(bw-iw)//2
    mask_full=Image.new('L',(w,h));mask_full.paste(mask,(x,by))
    if ow:
        hi=mask_full.resize((w*scale,h*scale),Image.Resampling.LANCZOS)
        outline=hi.filter(ImageFilter.MaxFilter(round(ow*scale)*2+1)).resize((w,h),Image.Resampling.LANCZOS)
    else:outline=mask_full
    def coloured(mask,colour):
        im=Image.new('RGBA',(w,h),tuple(colour));im.putalpha(mask.point(lambda v:round(v*colour[3]/255)));return im
    image=Image.new('RGBA',(w,h))
    if a['shadow'][3]:
        # Paste avoids ImageChops.offset wrapping the shadow to the opposite edge.
        sm=Image.new('L',(w,h));sm.paste(outline,(round(a['shadow_offset'][0]),round(a['shadow_offset'][1])))
        image=Image.alpha_composite(image,coloured(sm.filter(ImageFilter.GaussianBlur(a['shadow_radius'])),a['shadow']))
    if a['motion']:
        trail=Image.new('L',(w,h))
        for dx in range(1,round(a['motion'])+1):
            part=Image.new('L',(w,h));part.paste(mask_full,(-dx,0))
            trail=ImageChops.lighter(trail,part.point(lambda v:round(v*0.35*(1-dx/(a['motion']+1)))))
        image=Image.alpha_composite(image,coloured(trail.filter(ImageFilter.GaussianBlur(0.65)),a['glow']))
    if a['glow'][3] and a['glow_radius']:
        image=Image.alpha_composite(image,coloured(outline.filter(ImageFilter.GaussianBlur(a['glow_radius'])),a['glow']))
    if ow:image=Image.alpha_composite(image,coloured(outline,a['outline']))
    rows=[];stops=a['gradient'];i=0
    for y in range(h):
        t=max(0,min(1000,round((y-by)*1000/max(1,ih-1))))
        while i+1<len(stops)-1 and t>stops[i+1][0]:i+=1
        lo,hi=stops[i],stops[i+1];f=(t-lo[0])/(hi[0]-lo[0])
        rows.extend(bytes(round(c+(d-c)*f) for c,d in zip(lo[1],hi[1]))*w)
    fill=Image.frombytes('RGBA',(w,h),bytes(rows));fill.putalpha(ImageChops.multiply(fill.getchannel('A'),mask_full))
    image=Image.alpha_composite(image,fill)
    if crop is not None:
        x,y,cw,ch=crop;image=image.crop((x,y,x+cw,y+ch))
    return image.tobytes()
