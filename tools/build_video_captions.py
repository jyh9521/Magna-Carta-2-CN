"""Source-locked, bounded Bink caption builds with independent decoded replay.

Original movies and external tools are user-supplied. Locale data determines all
wording, geometry and effects. A single temporary AVI is streamed and removed
after each successful encoding; no full-game copy is made.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from .video_caption import (sha, bink_header, preserve_timing, render_layer,
    source_ink_mask, temporal_ink_mask, component_ink_mask, restore_masked, decoded_frames)
from .verify_resource_phase import hash_value, unique, relative as canonical_relative


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def verify_report_fields(previous,current,fields):
    """Compare persisted JSON values, including tuple-valued Pillow bounds."""
    for key in fields:
        if previous[key]!=json.loads(encoded(current[key])):
            raise ValueError('Independent movie report mismatch: '+key)


def encoded_size_limit(entry):
    """Keep legacy 64-MiB limit; longer clips require an explicit bounded cap."""
    limit=entry.get('maximum_encoded_bytes',64*1024*1024)
    if type(limit) is not int or not 1<=limit<=512*1024*1024:
        raise ValueError('Encoded movie size limit bound')
    return limit


def frame_count_limit(entry):
    """Long cutscenes are opt-in; old loading plans retain their 600-frame cap."""
    limit=entry.get('maximum_frames',600)
    if type(limit) is not int or not 1<=limit<=6144:
        raise ValueError('Explicit movie frame count limit bound')
    return limit


def encoder_time_limit(entry):
    limit=entry.get('encoder_timeout_seconds',180)
    if type(limit) is not int or not 1<=limit<=1800:
        raise ValueError('Explicit movie encoder timeout bound')
    return limit


def encoding_first_frame(entry, frame_count):
    first = entry.get('encode_from_frame', 0)
    if type(first) is not int or not 0 <= first < frame_count:
        raise ValueError('Encoded tail source frame bound')
    if first:
        from .video_title_caption import active_frame_indices
        for caption in entry['captions']:
            active = active_frame_indices(caption.get('frame_alpha'), frame_count)
            if any(index < first for index in active) or 'frame_repairs' not in caption['erase']:
                raise ValueError('Encoded tail requires source-identical prefix and explicit frame repairs')
    return first


def encoding_guard_frames(entry, frame_count):
    count=entry.get('encoder_guard_frames',0)
    if (type(count)is not int or not 0<=count<=2
            or frame_count-encoding_first_frame(entry,frame_count)+count>6144):
        raise ValueError('Explicit duplicate encoder guard-frame bound')
    return count


def scratch_space_required(header,entry):
    """New long-clip plans reserve space for the complete raw AVI plus headroom."""
    if not {'scratch_reserve_bytes','minimum_start_free_bytes'} & set(entry):
        return 8*1024**3
    reserve=entry.get('scratch_reserve_bytes',8*1024**3)
    minimum=entry.get('minimum_start_free_bytes',8*1024**3)
    if any(type(value) is not int or not 0<=value<=64*1024**3 for value in (reserve,minimum)):
        raise ValueError('Explicit movie scratch free-space bound')
    raw=header['width']*header['height']*3*(header['frames']-encoding_first_frame(entry,header['frames'])
          +encoding_guard_frames(entry,header['frames']))
    return max(minimum,raw+128*1024**2+reserve)


def locked_file(path, expected, limit=512*1024*1024):
    path=Path(path).resolve(strict=True)
    if not path.is_file() or not 0<path.stat().st_size<=limit:
        raise ValueError('Input file size bound: '+str(path))
    # The file may grow after stat: bound the actual allocation as well as the
    # declared size. One extra byte distinguishes an exact-limit input from an
    # oversized one without reading the rest of an unexpectedly large file.
    with path.open('rb') as stream:
        raw=stream.read(limit+1)
    if not 0<len(raw)<=limit:
        raise ValueError('Input file size bound: '+str(path))
    if sha(raw)!=hash_value(expected):
        raise ValueError('Input SHA256 mismatch: '+str(path))
    return raw


def member(root, relative):
    canonical_relative(relative)
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts or '.' in p.parts or p.as_posix()!=relative:
        raise ValueError('Member traversal')
    result=(Path(root)/p).resolve()
    if not result.is_relative_to(Path(root).resolve()):
        raise ValueError('Member escapes root')
    return result


def first_frame(ffmpeg, source, header):
    from PIL import Image
    iterator=decoded_frames(ffmpeg,source,header)
    try:
        return Image.frombytes('RGB',(header['width'],header['height']),next(iterator))
    finally:
        iterator.close()


def load_plan(path, expected):
    raw=locked_file(path,expected,8*1024*1024)
    plan=json.loads(raw,object_pairs_hook=unique)
    if (plan.get('schema_version')!=1 or plan.get('kind')!='bink-caption-plan'
            or not isinstance(plan.get('entries'),list) or not 1<=len(plan['entries'])<=64):
        raise ValueError('Unsupported video caption plan')
    ids=[e['id'] for e in plan['entries']]
    files=[canonical_relative(e['source']['file']).casefold() for e in plan['entries']]
    if len(set(ids))!=len(ids) or len(set(files))!=len(files):
        raise ValueError('Duplicate movie entry')
    for entry in plan['entries']:
        if (not entry['id'] or len(entry['id'])>64
                or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in entry['id'])
                or not 1<=len(entry['captions'])<=8):
            raise ValueError('Movie identifier/caption bound')
        encoded_size_limit(entry)
        frame_count_limit(entry)
        encoder_time_limit(entry)
    return plan,raw


def render_caption_layer(caption,font,canvas):
    """Choose one explicit renderer; never silently mix legacy/new style data."""
    if 'parts' in caption:
        from .video_title_caption import render_title_parts
        if any(key in caption for key in ('appearance', 'font_size', 'style')):
            raise ValueError('Caption parts must replace its single-run style')
        return render_title_parts(font, caption['text'], canvas, caption['parts'])
    if 'appearance' in caption or 'font_size' in caption:
        from .video_title_caption import render_title_layer
        if ('appearance' not in caption or 'font_size' not in caption or 'style' in caption
                or not isinstance(caption['appearance'],dict)
                or type(caption['font_size']) is not int):
            raise ValueError('Caption appearance/font_size must replace its legacy style')
        return render_title_layer(font,caption['text'],canvas,font_size=caption['font_size'],
                                  appearance=caption['appearance'])
    return render_layer(caption['text'],font,canvas,caption['style'])


def frame_repair_metadata(caption,frame_count,canvas,root):
    """Preflight every record and size/path bound before reading any repair PNG."""
    erase=caption['erase']
    if 'frame_exposure' in caption:
        from .video_title_caption import active_frame_indices,frame_exposure_values
        if 'frame_alpha' not in caption or 'native_screen' in erase:
            raise ValueError('Frame exposure requires an explicit timed frame_alpha caption')
        active_frame_indices(caption['frame_alpha'],frame_count)
        frame_exposure_values(caption['frame_exposure'],frame_count)
    if 'frame_repairs' not in erase:return None
    from .video_frame_repairs import MAX_PATCH_BYTES,MAX_RECT_PIXELS
    from .video_title_caption import active_frame_indices
    if 'frame_alpha' not in caption:
        raise ValueError('Frame repairs require an explicit frame_alpha curve')
    if 'native_screen' in erase:
        raise ValueError('Frame repairs and native indicator models are distinct operations')
    active=active_frame_indices(caption['frame_alpha'],frame_count)
    specification=erase['frame_repairs']
    if (not isinstance(specification,dict) or set(specification)!={'method','records'}
            or specification['method']!='sparse-frame-rgba-v1'):
        raise ValueError('Unsupported or malformed sparse frame repair specification')
    rect=erase['rect']
    if (not isinstance(rect,list) or len(rect)!=4 or any(type(v)is not int for v in rect)
            or min(rect[:2])<0 or min(rect[2:])<1 or rect[2]*rect[3]>MAX_RECT_PIXELS
            or rect[0]+rect[2]>canvas[0] or rect[1]+rect[3]>canvas[1]):
        raise ValueError('Sparse frame repair rectangle bound')
    records=specification['records']
    if (not isinstance(records,list) or not len(active)<=len(records)<=frame_count
            or len(records)*rect[2]*rect[3]*4>MAX_PATCH_BYTES):
        raise ValueError('Sparse frame repair record count or total RGBA byte bound')
    seen=set();paths=set();metadata=[];active_set=set(active)
    for record in records:
        if not isinstance(record,dict) or set(record)!={'index','source_crop_sha256','patch'}:
            raise ValueError('Sparse frame repair record has unknown or missing fields')
        index=record['index']
        if type(index)is not int or not 0<=index<frame_count or index in seen:
            raise ValueError('Duplicate or out-of-range sparse frame repair record')
        digest=hash_value(record['source_crop_sha256'])
        asset=record['patch']
        if not isinstance(asset,dict) or set(asset)!={'path','sha256'}:
            raise ValueError('Sparse frame repair patch must have exactly path and sha256')
        patch_digest=hash_value(asset['sha256'])
        path=member(root,asset['path'])
        identity=path.as_posix().casefold()
        if path.suffix.lower()!='.png' or identity in paths:
            raise ValueError('Sparse frame repair requires distinct canonical PNG paths')
        seen.add(index);paths.add(identity)
        metadata.append(dict(index=index,source_crop_sha256=digest,path=path,sha256=patch_digest))
    if not active_set.issubset(seen):raise ValueError('Sparse frame repairs must cover every active text frame')
    # A small bounded PNG overhead permits incompressible RGBA without permitting
    # enormous ancillary metadata. Header geometry is checked again before load.
    limit=rect[2]*rect[3]*4+64*1024
    encoded_total=0
    for record in metadata:
        path=record['path'];size=path.stat().st_size
        if not path.is_file() or not 0<size<=limit:
            raise ValueError('Sparse frame repair PNG file size bound')
        encoded_total+=size
    if encoded_total>MAX_PATCH_BYTES:
        raise ValueError('Sparse frame repair encoded PNG total exceeds byte bound')
    return metadata


def prepare_frame_repairs(metadata,caption,mask,frame_count,canvas):
    """Load source-locked PNGs, retaining their strict RGBA mode and dimensions."""
    from PIL import Image
    from .video_frame_repairs import VideoFrameRepairs
    from .video_title_caption import active_frame_indices
    rect=caption['erase']['rect'];size=(rect[2],rect[3]);records=[]
    repair_active=[record['index'] for record in metadata]
    if not set(active_frame_indices(caption['frame_alpha'],frame_count)).issubset(repair_active):
        raise ValueError('Sparse frame repairs must cover every active text frame')
    limit=size[0]*size[1]*4+64*1024
    for record in metadata:
        raw=locked_file(record['path'],record['sha256'],limit)
        with Image.open(io.BytesIO(raw)) as patch:
            if (patch.format!='PNG' or patch.mode!='RGBA' or patch.size!=size
                    or getattr(patch,'n_frames',1)!=1):
                raise ValueError('Sparse frame repair patch must be a single rectangle-sized RGBA PNG')
            patch.load()
            records.append(dict(index=record['index'],source_crop_sha256=record['source_crop_sha256'],patch=patch.copy()))
    return VideoFrameRepairs(rect,mask,frame_count,repair_active,records,canvas)


def load_mask_asset(reference, rect, root):
    """Read an explicit binary support mask; no image-content threshold guesses."""
    from PIL import Image
    import numpy as np
    if (not isinstance(reference,dict) or set(reference)!={'path','sha256','pixels_sha256','pixels'}
            or not isinstance(rect,list) or len(rect)!=4 or any(type(v)is not int for v in rect)
            or min(rect[:2])<0 or min(rect[2:])<1 or rect[2]*rect[3]>256*1024
            or type(reference['pixels'])is not int or not 0<reference['pixels']<rect[2]*rect[3]):
        raise ValueError('Explicit bounded proper binary mask asset required')
    expected=hash_value(reference['pixels_sha256'])
    raw=locked_file(member(root,reference['path']),reference['sha256'],rect[2]*rect[3]+64*1024)
    with Image.open(io.BytesIO(raw)) as image:
        if (image.format!='PNG' or image.mode!='L' or image.size!=tuple(rect[2:])
                or getattr(image,'n_frames',1)!=1):
            raise ValueError('Mask asset must be a single native-size grayscale PNG')
        values=np.asarray(image)
        if not np.isin(values,[0,255]).all():raise ValueError('Mask asset contains nonbinary pixels')
        mask=values>0
    if sha(mask.tobytes())!=expected or int(mask.sum())!=reference['pixels']:
        raise ValueError('Mask asset pixel identity mismatch')
    return mask


def prepare_native_indicator(caption,mask,font,original,source,header,root,source_root,ffmpeg):
    from PIL import Image,ImageFilter
    import numpy as np
    from .video_screen_underlay import extract_glyph_matte,inverse_screen
    from .video_native_indicator import NativeIndicator
    erase=caption['erase'];spec=erase['native_screen'];ref=erase['reference']
    if spec.get('method')!='boundary-compensated-screen-v1':raise ValueError('Unsupported native screen method')
    x,y,w,h=erase['rect'];rx,ry,rw,rh=ref['rect'];cx,cy,cw,ch=spec['context_rect']
    if (rw,rh)!=(w,h) or min(rx-cx,ry-cy)<0 or rx+w>cx+cw or ry+h>cy+ch:
        raise ValueError('Native screen source context does not contain caption')
    path=member(source_root,ref['file']);data=locked_file(path,ref['sha256']);fh=bink_header(data)
    if cx<0 or cy<0 or cx+cw>fh['width'] or cy+ch>fh['height']:raise ValueError('Native screen context outside reference')
    fullmask=np.zeros((ch,cw),bool);ox=rx-cx;oy=ry-cy;fullmask[oy:oy+h,ox:ox+w]=mask
    frames=(np.asarray(Image.frombytes('RGB',(fh['width'],fh['height']),raw).crop((cx,cy,cx+cw,cy+ch)))
            for raw in decoded_frames(ffmpeg,path,fh))
    inference=extract_glyph_matte(frames,fullmask)
    matte=inference['matte_rgb'][oy:oy+h,ox:ox+w].copy()
    threshold=spec['minimum_transmittance'];tolerance=spec['invalid_tolerance']
    if type(tolerance)is not int or not 0<=tolerance<=8:raise ValueError('Native screen inconsistency tolerance')
    invalid=np.zeros((h,w),bool)
    for raw in decoded_frames(ffmpeg,source,header):
        crop=np.asarray(Image.frombytes('RGB',original.size,raw).crop((x,y,x+w,y+h)))
        invalid|=(matte.astype(np.int16)>crop.astype(np.int16)+tolerance).any(2)&mask
    anchor=np.asarray(original.crop((x,y,x+w,y+h)))
    unknown=inverse_screen(anchor,matte,minimum_transmittance=threshold)['unknown']|invalid
    if sha(matte.tobytes())!=spec['matte_sha256'] or sha(unknown.tobytes())!=spec['repair_mask_sha256']:
        raise ValueError('Native screen matte or repair support changed')
    asset=spec['core_patch'];raw_patch=locked_file(member(root,asset['path']),asset['sha256'],1024*1024)
    patch=Image.open(io.BytesIO(raw_patch));patch.load()
    states=spec['text_states']
    if len(states)!=3 or states[-1]!=caption['text'] or any(not isinstance(s,str) or not s for s in states):
        raise ValueError('Native indicator needs three explicit complete text states')
    layers=[]
    for state in states:
        rendered,_=render_caption_layer({**caption,'text':state},font,original.size)
        bounds=rendered.getbbox()
        if bounds and (bounds[0]<x or bounds[1]<y or bounds[2]>x+w or bounds[3]>y+h):
            raise ValueError('Native indicator glow leaves its bounded canvas')
        layers.append(rendered.crop((x,y,x+w,y+h)))
    method=spec.get('temporal_lighting','nearest-known-v1')
    operation_rect=erase['rect'];weight=None
    if method=='harmonic-feathered-v1':
        feather=spec.get('lighting_feather')
        if (not isinstance(feather,dict) or set(feather)!={'padding','dilation','blur_radius','cutoff'}
                or not isinstance(feather['padding'],list) or len(feather['padding'])!=4
                or any(type(v)is not int or not 0<=v<=64 for v in feather['padding'])
                or type(feather['dilation'])is not int or not 1<=feather['dilation']<=16
                or type(feather['blur_radius'])is not int or not 1<=feather['blur_radius']<=8
                or type(feather['cutoff'])is not int or not 1<=feather['cutoff']<=16):
            raise ValueError('invalid bounded lighting feather')
        # Keep the left-hand native spinner outside the operation. Top/right/
        # bottom light-only feathering removes a glyph-shaped temporal seam.
        left,top,right,bottom=feather['padding'];new_h=h+top+bottom;new_w=w+left+right
        new_x,new_y=x-left,y-top
        if min(new_x,new_y)<0 or new_x+new_w>original.width or new_y+new_h>original.height:
            raise ValueError('lighting feather leaves movie bounds')
        expanded=np.zeros((new_h,new_w),bool);expanded[top:top+h,left:left+w]=mask
        weight=np.asarray(Image.fromarray(expanded.astype(np.uint8)*255)
            .filter(ImageFilter.MaxFilter(2*feather['dilation']+1))
            .filter(ImageFilter.GaussianBlur(feather['blur_radius']))).copy()
        weight[weight<feather['cutoff']]=0;weight[expanded]=255
        padded=np.zeros((new_h,new_w,3),np.uint8);padded[top:top+h,left:left+w]=matte;matte=padded
        padded=np.zeros((new_h,new_w),bool);padded[top:top+h,left:left+w]=invalid;invalid=padded
        p=Image.new('RGBA',(new_w,new_h));p.paste(patch,(left,top));patch=p
        layers=[Image.new('RGBA',(new_w,new_h)) for _ in states]
        for output,state in zip(layers,states):
            full,_=render_caption_layer({**caption,'text':state},font,original.size)
            output.paste(full.crop((new_x,new_y,new_x+new_w,new_y+new_h)),(0,0))
        mask=expanded;operation_rect=[new_x,new_y,new_w,new_h]
        anchor=np.asarray(original.crop((new_x,new_y,new_x+new_w,new_y+new_h)))
    operation=NativeIndicator(operation_rect,mask,matte,anchor,patch,layers,header['frames'],threshold,invalid,
        temporal_lighting=method,lighting_weight=weight)
    evidence=operation.proof();evidence.update(core_patch_sha256=asset['sha256'],invalid_model_pixels=int(invalid.sum()),
        matte_inference={k:v for k,v in inference.items() if not isinstance(v,np.ndarray)})
    return operation,evidence


def prepare_layers(plan,entry,root,source_root,ffmpeg):
    from PIL import Image
    import numpy as np
    import PIL
    import fontTools
    versions={'Pillow':PIL.__version__,'numpy':np.__version__,'fontTools':fontTools.__version__}
    if 'rasterizer_versions' in plan and plan['rasterizer_versions']!=versions:
        raise ValueError('Caption rasterizer versions changed')
    source=member(source_root,entry['source']['file'])
    raw=locked_file(source,entry['source']['sha256'])
    if len(raw)!=entry['source']['size']: raise ValueError('Movie source size mismatch')
    header=bink_header(raw,maximum_frames=frame_count_limit(entry))
    repair_metadata=[frame_repair_metadata(caption,header['frames'],(header['width'],header['height']),root)
                     for caption in entry['captions']]
    fonts={k:locked_file(member(root,v['path']),v['sha256'],40*1024*1024)
           for k,v in plan['fonts'].items()}
    original=first_frame(ffmpeg,source,header)
    if sha(original.tobytes())!=entry['source']['first_rgb_sha256']:
        raise ValueError('Decoded original frame identity mismatch')
    canvas=original.size
    layer=Image.new('RGBA',canvas)
    changed=np.zeros((canvas[1],canvas[0]),dtype=bool)
    masks=[]; proofs=[]
    for caption,repair_records in zip(entry['captions'],repair_metadata):
        font=fonts[caption['font']]
        # A real Unicode cmap, not a tofu-shaped fallback, must cover all text.
        from fontTools.ttLib import TTFont
        with TTFont(io.BytesIO(font)) as tt:
            cmap=tt.getBestCmap()
            texts=[caption['text']]+caption.get('erase',{}).get('native_screen',{}).get('text_states',[])
            if any(not ch.isspace() and ord(ch) not in cmap for text in texts for ch in text):
                raise ValueError('Caption font has missing glyphs')
        rendered,proof=render_caption_layer(caption,font,canvas)
        erase=caption['erase']; rect=erase['rect']
        if 'mask_asset' in erase:
            if any(key in erase for key in ('temporal_static','reference','selection','native_screen')):
                raise ValueError('Explicit mask assets cannot have another inference model')
            mask=load_mask_asset(erase['mask_asset'],rect,root)
        elif 'temporal_static' in erase:
            from .worldmap_caption import temporal_static_mask
            from .video_title_caption import reference_window
            window=reference_window(erase,header['frames'])
            frames=(Image.frombytes('RGB',canvas,data) for index,data in enumerate(decoded_frames(ffmpeg,source,header))
                    if window[0]<=index<window[1])
            mask=temporal_static_mask(frames,rect,erase['temporal_static'],window[1]-window[0])
        elif 'reference' in erase:
            ref=erase['reference']; path=member(source_root,ref['file'])
            data=locked_file(path,ref['sha256']); ref_header=bink_header(data)
            sampling=ref.get('sampling','first-frame')
            if sampling=='all-frames-union':
                frames=(Image.frombytes('RGB',(ref_header['width'],ref_header['height']),raw)
                        for raw in decoded_frames(ffmpeg,path,ref_header))
                mask=temporal_ink_mask(frames,ref['rect'],erase['threshold'],erase['radius'],ref_header['frames'])
            elif sampling=='first-frame':
                frame=first_frame(ffmpeg,path,ref_header)
                mask=source_ink_mask(frame,ref['rect'],erase['threshold'],erase['radius'])
            else:raise ValueError('Unsupported reference mask sampling')
            if tuple(mask.shape)!=(rect[3],rect[2]): raise ValueError('Reference mask geometry mismatch')
        elif 'selection' in erase:
            mask=component_ink_mask(original,rect,erase['selection'],erase['radius'])
        else:
            mask=source_ink_mask(original,rect,erase['threshold'],erase['radius'])
        if not mask.any(): raise ValueError('Source text mask is empty')
        x,y,w,h=rect
        if x<0 or y<0 or x+w>canvas[0] or y+h>canvas[1]: raise ValueError('Erase rectangle outside movie')
        changed[y:y+h,x:x+w]|=mask
        if 'frame_alpha' in caption:
            if 'native_screen' in erase:
                raise ValueError('Timed captions and native indicator models are distinct operations')
            from .video_title_caption import VideoTitleCaption
            repairs=(prepare_frame_repairs(repair_records,caption,mask,header['frames'],canvas)
                     if repair_records is not None else None)
            operation=VideoTitleCaption(rect,mask,rendered,caption['frame_alpha'],header['frames'],repairs=repairs,
                                        frame_exposure=caption.get('frame_exposure'))
            masks.append(operation);proof['timed_caption']=operation.proof()
            changed|=np.asarray(rendered.getchannel('A'))>0
        elif 'native_screen' in erase:
            operation,evidence=prepare_native_indicator(caption,mask,font,original,source,header,root,source_root,ffmpeg)
            masks.append(operation);proof['native_screen']=evidence
            xx,yy,ww,hh=operation.rect
            changed[yy:yy+hh,xx:xx+ww]|=operation.mask
            for state in operation.layers:changed[yy:yy+hh,xx:xx+ww]|=np.asarray(state.getchannel('A'))>0
        else:
            masks.append((rect,mask))
            layer=Image.alpha_composite(layer,rendered)
        proof.update(text=caption['text'],font_sha256=sha(font),mask_sha256=sha(mask.tobytes()),
                     mask_pixels=int(mask.sum()),erase_rect=rect)
        proofs.append(proof)
    changed|=np.asarray(layer.getchannel('A'))>0
    if changed.mean()>.2: raise ValueError('Caption edit exceeds bounded movie area')
    return source,raw,header,masks,layer,changed,proofs


def composite(frame,masks,layer,changed,frame_index=0):
    from PIL import Image
    import numpy as np
    result=frame
    from .video_native_indicator import NativeIndicator
    from .video_title_caption import VideoTitleCaption
    for operation in masks:
        if isinstance(operation,(NativeIndicator,VideoTitleCaption)):result=operation.apply(result,frame_index)
        else:
            rect,mask=operation;result,_=restore_masked(result,rect,mask)
    result=Image.alpha_composite(result.convert('RGBA'),layer).convert('RGB')
    if not np.array_equal(np.asarray(frame)[~changed],np.asarray(result)[~changed]):
        raise ValueError('Movie artwork changed outside text support')
    return result


def avi_transport_rate(header):
    """Avoid AVI microsecond rounding dropping the final frame in RAD's reader.

    Near-integer source rates travel at that exact integer. Only the Bink time
    numerator/denominator are then restored, after matching all frame counts.
    Other rates need a separately verified transport, rather than silent retime.
    """
    rate=header['numerator']/header['denominator']; integer=round(rate)
    if not 1<=integer<=240 or abs(rate-integer)/rate>.0001:
        raise ValueError('Unverified fractional AVI transport rate')
    return integer


def write_avi(ffmpeg,source,header,masks,layer,changed,path,first_frame=0,guard_frames=0):
    from PIL import Image
    command=[str(ffmpeg),'-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',
        f"{header['width']}x{header['height']}",'-r',
        str(avi_transport_rate(header)),'-i','pipe:0','-an',
        '-c:v','rawvideo','-pix_fmt','bgr24','-threads','1','-f','avi','-n',str(path)]
    p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    hashes=[]; preview=None
    try:
        for index,data in enumerate(decoded_frames(ffmpeg,source,header)):
            frame=Image.frombytes('RGB',(header['width'],header['height']),data)
            result=composite(frame,masks,layer,changed,index)
            if index==0: preview=result
            content=result.tobytes(); hashes.append(sha(content))
            if index < first_frame:
                if content != data:raise ValueError('Encoded tail would discard a modified prefix frame')
            else:p.stdin.write(content)
        for _ in range(guard_frames):p.stdin.write(content)
        p.stdin.close();errors=p.stderr.read();code=p.wait(timeout=60)
        if code: raise ValueError('AVI encoding failed: '+errors.decode(errors='replace'))
    finally:
        if p.poll() is None: p.kill();p.wait()
        if p.stdin and not p.stdin.closed:p.stdin.close()
        p.stderr.close()
    return command,hashes,preview


def replay(ffmpeg,source,output,header,masks,layer,changed,review_frames=()):
    from PIL import Image
    import numpy as np
    encoded_header=bink_header(output.read_bytes(),maximum_frames=header['frames'])
    if encoded_header!=header: raise ValueError('Final Bink structure/timing mismatch')
    if (not isinstance(review_frames,(list,tuple)) or len(review_frames)>32
            or len(set(review_frames))!=len(review_frames)
            or any(type(index) is not int or not 0<=index<header['frames'] for index in review_frames)):
        raise ValueError('Explicit decoded review frame bound')
    selected_frames=set(review_frames)|{0,header['frames']//2,header['frames']-1}
    before=decoded_frames(ffmpeg,source,header); after=decoded_frames(ffmpeg,output,header)
    rows=[]; samples={}
    try:
        for index,(a,b) in enumerate(zip(before,after,strict=True)):
            frame=Image.frombytes('RGB',(header['width'],header['height']),a)
            expected=composite(frame,masks,layer,changed,index)
            actual=Image.frombytes('RGB',frame.size,b)
            delta=np.abs(np.asarray(expected).astype('int16')-np.asarray(actual).astype('int16'))
            rows.append(dict(index=index,expected_rgb_sha256=sha(expected.tobytes()),
                decoded_rgb_sha256=sha(b),mean_error=float(delta.mean()),
                text_support_mean_error=float(delta[changed].mean()),
                background_mean_error=float(delta[~changed].mean()),
                outside_support_preencode_changed_pixels=0))
            if index in selected_frames: samples[index]=actual
    finally:
        before.close();after.close()
    if len(rows)!=header['frames']: raise ValueError('Decoded movie frame count mismatch')
    if any(r['background_mean_error']>6 or r['text_support_mean_error']>10 for r in rows):
        raise ValueError('Decoded movie exceeds explicit compression error bound')
    return rows,samples


def run(args):
    from PIL import Image
    import PIL
    import numpy as np
    from .isolated_gui_process import run as isolated
    root=args.project_root.resolve(); source_root=args.source_root.resolve(); out=args.output_dir.resolve()
    if not out.is_relative_to(root) or out==root: raise ValueError('Output must stay inside project')
    plan,plan_raw=load_plan(args.plan,args.plan_sha256)
    selected=[e for e in plan['entries'] if args.entry is None or e['id']==args.entry]
    if not selected: raise ValueError('Unknown movie identifier')
    ffmpeg=args.ffmpeg.resolve(strict=True)
    locked_file(ffmpeg,args.ffmpeg_sha256,256*1024*1024)
    if not args.verify and not args.preview:
        encoder=args.encoder.resolve(strict=True)
        locked_file(encoder,args.encoder_sha256,256*1024*1024)
    else: encoder=None
    out.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for entry in selected:
        output=out/(entry['id']+'.bik'); report_path=out/(entry['id']+'.json')
        if not args.verify and (output.exists() or report_path.exists()):
            raise ValueError('Movie output already exists; verify it or use a new directory')
        source,source_raw,header,masks,layer,changed,proofs=prepare_layers(plan,entry,root,source_root,ffmpeg)
        encode_from=encoding_first_frame(entry,header['frames'])
        guard_frames=encoding_guard_frames(entry,header['frames'])
        if args.preview:
            frame=first_frame(ffmpeg,source,header)
            composite(frame,masks,layer,changed).save(out/(entry['id']+'.preview.png'))
            (out/(entry['id']+'.preview.json')).write_bytes(encoded(dict(id=entry['id'],plan_sha256=args.plan_sha256,captions=proofs)))
            print(json.dumps(dict(id=entry['id'],status='PREVIEW',game_rendering_verified=False)),flush=True)
            continue
        if args.verify:
            previous=json.loads(report_path.read_bytes(),object_pairs_hook=unique)
            locked_file(output,previous['output_sha256'])
            if previous['plan_sha256']!=args.plan_sha256 or previous['source_sha256']!=sha(source_raw):
                raise ValueError('Movie replay identity mismatch')
            encoder_result=previous['encoder_result']; commands=previous['commands']
        else:
            if shutil.disk_usage(out).free<scratch_space_required(header,entry):
                raise ValueError('Insufficient declared movie scratch/reserve space; stop before AVI creation')
            scratch=out/(entry['id']+'.scratch.avi')
            if scratch.exists(): raise ValueError('Prior AVI scratch exists; inspect before retrying')
            command,expected_hashes,preview=write_avi(ffmpeg,source,header,masks,layer,changed,scratch,encode_from,guard_frames)
            encoder_command=[str(encoder),'binkc',str(scratch),str(output),'/V100','/D6000000','/L-1','/U4','/#']
            encoder_result=isolated(encoder_command,timeout=encoder_time_limit(entry),cwd=out)
            (out/(entry['id']+'.encoder.json')).write_bytes(encoded(encoder_result))
            if (encoder_result['exit_code']!=0 or encoder_result['timed_out']
                    or not encoder_result['input_desktop_unchanged'] or not output.is_file()):
                raise ValueError('Isolated movie encoding failed; batch stopped')
            if output.stat().st_size>encoded_size_limit(entry): raise ValueError('Encoded movie exceeds declared size limit')
            if guard_frames:
                from .bink_audio import trim_silent_guard_frames
                output.write_bytes(trim_silent_guard_frames(output.read_bytes(),header['frames']-encode_from,guard_frames))
            if encode_from:
                from .bink_audio import replace_video_tail
                output.write_bytes(replace_video_tail(source_raw,output.read_bytes(),encode_from))
            else:
                output.write_bytes(preserve_timing(source_raw,output.read_bytes(),maximum_frames=frame_count_limit(entry)))
            if output.stat().st_size>encoded_size_limit(entry):raise ValueError('Assembled movie exceeds declared size limit')
            preview.save(out/(entry['id']+'.preencode.png'))
            commands={'decode':[str(ffmpeg),'-v','error','-i',str(source),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],
                      'avi':command,'encode':encoder_command}
        rows,samples=replay(ffmpeg,source,output,header,masks,layer,changed,entry.get('review_frames',()))
        if not args.verify and [r['expected_rgb_sha256'] for r in rows]!=expected_hashes:
            raise ValueError('Independent caption replay differs from encoder input')
        if not args.verify:
            # Retain the one owned AVI on failed replay; remove it only after
            # independent native decode and encoder-input equality both pass.
            if scratch.parent!=out or scratch.name!=entry['id']+'.scratch.avi': raise ValueError('Scratch identity changed')
            scratch.unlink()
        for index,frame in samples.items():frame.save(out/(entry['id']+f'.decoded-{index:03}.png'))
        report=dict(schema_version=1,kind='bink-caption-verification',id=entry['id'],status='PASS',
            plan_sha256=args.plan_sha256,source_sha256=sha(source_raw),source_size=len(source_raw),
            output_sha256=sha(output.read_bytes()),output_size=output.stat().st_size,header=header,
            original_member=entry['source']['member'],ffmpeg_sha256=args.ffmpeg_sha256,
            encoder_sha256=args.encoder_sha256,encoder_result=encoder_result,commands=commands,
            rasterizers={'Pillow':PIL.__version__,'numpy':np.__version__},captions=proofs,
            changed_support_pixels=int(changed.sum()),frames=rows,independent_replay=True,
            visual_style_acceptance=False,game_rendering_verified=False,
            source_font_identity_recovered=False,hidden_background_reconstructed=True,
            scratch_retained=False)
        if encode_from:
            from .bink_audio import inspect as inspect_bink
            original_packets=inspect_bink(source_raw)['frames'][:encode_from]
            delivered_packets=inspect_bink(output.read_bytes())['frames'][:encode_from]
            if delivered_packets!=original_packets:raise ValueError('Native movie prefix packets changed')
            if any(row['expected_rgb_sha256']!=row['decoded_rgb_sha256'] for row in rows[:encode_from]):
                raise ValueError('Native movie prefix decoded pixels changed')
            report['native_prefix']=dict(frames=encode_from,packets_byte_identical=True,decoded_pixels_byte_identical=True,
                                         tail_starts_at_independent_keyframe=True)
        if guard_frames:
            report['encoder_guards']=dict(duplicate_last_raw_frames=guard_frames,
                retained_intended_frames=header['frames']-encode_from,
                trailing_guard_packets_removed_before_replay=True)
        if args.verify:
            verify_report_fields(previous,report,('header','output_sha256','output_size','captions','frames','changed_support_pixels'))
        else:report_path.write_bytes(encoded(report))
        if sha(source.read_bytes())!=entry['source']['sha256'] or args.plan.read_bytes()!=plan_raw:
            raise ValueError('Original movie or plan changed during build')
        summary=dict(id=entry['id'],status='PASS',frames=len(rows),bytes=report['output_size'],
                     independently_replayed=True,visible_desktop_unchanged=True)
        summaries.append(summary);print(json.dumps(summary),flush=True)
    return summaries


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--entry')
    mode=p.add_mutually_exclusive_group();mode.add_argument('--verify',action='store_true');mode.add_argument('--preview',action='store_true')
    p.add_argument('--ffmpeg',type=Path,required=True);p.add_argument('--ffmpeg-sha256',required=True)
    p.add_argument('--encoder',type=Path);p.add_argument('--encoder-sha256',required=True)
    a=p.parse_args(argv)
    try:
        if not a.verify and not a.preview and a.encoder is None:raise ValueError('Explicit Bink encoder required for build')
        run(a);return 0
    except (ValueError,OSError,KeyError,TypeError,ImportError,subprocess.SubprocessError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
