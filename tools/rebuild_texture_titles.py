"""Hash-locked sparse rebuild of clean lettering islands and protected map art."""
import argparse
import copy
import importlib.metadata
import io
import json
from pathlib import Path

from PIL import Image

from .audit_texture_alignment import foreground_span, anchor
from .bc3_error_bound import refine
from .build_font_supplement import context
from .font_binding_plan import confined_path
from .lettering_layers import box, source_ink, font_ink, effects
from .map_underlay import retained_art, scanline_art
from .patch_tagged_fields import digest
from .replace_texture_regions import selected, replace_tiles
from .runtime_envelope import ALIGNMENT, require_raw_envelope
from .texture_layout import decode_texture, read_texture, overlay_rect, rect_units
from .texture_overlay import select_texture_export, compose_restored_region
from .ue3_package import LzxDecoder


def locked(project, ref, assets):
    key = ref['path'], ref['sha256']
    if key not in assets:
        raw = confined_path(project, ref['path']).read_bytes()
        if digest(raw) != ref['sha256']:
            raise ValueError('dependency SHA256 mismatch: '+ref['path'])
        assets[key] = raw
    return assets[key]


def compose_island(original, spec, assets):
    x,y,w,h = spec['rect']; bounds = box(spec['rect'], original.size)
    background = Image.new('RGBA', (w,h))
    if spec['background']['kind'] == 'restored-art':
        ref = spec['background']['label']; label = copy.deepcopy(ref)
        for name, mode, dest in [('patch','RGBA','_repair_pixels'), ('mask','L','_repair_mask')]:
            r = ref['restoration'][name]
            with Image.open(io.BytesIO(assets[r['path'],r['sha256']])) as im:
                if im.mode != mode or im.size != (w,h):
                    raise ValueError('background geometry/mode mismatch')
                label[dest] = im.tobytes()
        background = Image.frombytes('RGBA', (w,h), compose_restored_region(
            label, background.tobytes(), original.tobytes(), original.width))
        if 'retain_rects' in spec['background']:
            background = retained_art(background, spec['background']['retain_rects'])
    elif spec['background']['kind'] == 'scanline-map-art-v1':
        background = scanline_art(original, spec['rect'], spec['background'])
    elif spec['background'] != {'kind':'transparent'}:
        raise ValueError('unknown background mode')
    result = background.copy(); rendered=[]
    for layer in spec['layers']:
        if layer['kind'] == 'source-ink':
            cx,cy,cw,ch = layer['core']
            ink = source_ink(original.crop(bounds), [cx-x,cy-y,cw,ch], layer['ink_floor'])
        elif layer['kind'] == 'font':
            ref = layer['font']; ink = font_ink(assets[ref['path'],ref['sha256']], layer['label'])
            if 'anchor' in layer:
                a = layer['anchor']; span = foreground_span(ink,[0,0,*ink.size],160,128)
                shift = round(a['target'] - anchor(span,a['mode']))
                bb = ink.getbbox()
                if not bb or bb[0]+shift < 0 or bb[2]+shift > ink.width:
                    raise ValueError('glyph placement clips ink')
                moved=Image.new('RGBA',ink.size);moved.paste(ink,(shift,0));ink=moved
        else:
            raise ValueError('unknown glyph mode')
        final, parts = effects(ink, layer['effects'])
        if 'crop' in layer:
            b = box(layer['crop'], ink.size)
            final=final.crop(b);parts={k:v.crop(b) for k,v in parts.items()}
        if final.size != (w,h):
            raise ValueError('layer/island size mismatch')
        result=Image.alpha_composite(result,final)
        rendered.append(dict(id=layer['id'],kind=layer['kind'],parts=parts,final=final,
                             full_ink=ink,crop=layer.get('crop')))
    return result, background, rendered


def visible_equal(a,b):
    return all(x[3]==y[3] and (x[3]==0 or x[:3]==y[:3])
               for x,y in zip(a.get_flattened_data(),b.get_flattened_data(),strict=True))


def rebuild_tiles(current, original, islands, assets):
    if (current['format'] != 7 or original['format'] != 7
            or (current['width'],current['height']) != (original['width'],original['height'])):
        raise ValueError('matching BC3 textures required')
    size=current['width'],current['height']
    before=Image.frombytes('RGBA',size,decode_texture(current))
    source=Image.frombytes('RGBA',size,decode_texture(original))
    raw=current['tiles'];used=set();proofs=[];cache={}
    for spec in islands:
        units=set(rect_units(current['layout'],spec['rect']))
        if used & units:raise ValueError('lettering islands overlap')
        used |= units
        wanted,background,layers=compose_island(source,spec,assets)
        raw,_=overlay_rect(raw,current['layout'],spec['rect'],wanted.tobytes(),cache,
                           alpha_encoding='adaptive-range',rgb_encoding='weighted-fit-v1')
        x,y,w,h=spec['rect'];out=bytearray(raw);kept=0
        for yy in range(0,h,4):
            for xx in range(0,w,4):
                world=(x+xx,y+yy,x+xx+4,y+yy+4)
                at=current['layout']['offsets'][((y+yy)//4)*(size[0]//4)+(x+xx)//4]
                if visible_equal(wanted.crop((xx,yy,xx+4,yy+4)),before.crop(world)):
                    out[at:at+16]=current['tiles'][at:at+16];kept+=1
                else:
                    block=bytes(out[at:at+16])
                    linear=b''.join(block[k:k+2][::-1] for k in range(0,16,2))
                    improved=refine(wanted.crop((xx,yy,xx+4,yy+4)).tobytes(),linear,spec['max_premultiplied_delta'])
                    out[at:at+16]=b''.join(improved[k:k+2][::-1] for k in range(0,16,2))
        raw=bytes(out)
        actual=Image.frombytes('RGBA',size,decode_texture(current,raw)).crop((x,y,x+w,y+h))
        a=list(wanted.get_flattened_data());b=list(actual.get_flattened_data())
        alpha=max(abs(p[3]-q[3])for p,q in zip(a,b,strict=True))
        rgb=max(abs(p[c]*p[3]-q[c]*q[3])/255 for p,q in zip(a,b,strict=True)for c in range(3))
        if alpha>spec['max_alpha_delta'] or rgb>spec['max_premultiplied_delta']:
            raise ValueError(f"native error budget {spec['id']}: alpha={alpha} rgb={rgb}")
        if any(q[3]for p,q in zip(a,b,strict=True)if p[3]==0):
            raise ValueError('native encoder filled a transparent pixel')
        proofs.append(dict(id=spec['id'],name=spec['name'],decoded_rgba_sha256=digest(actual.tobytes()),
                           expected_rgba_sha256=digest(wanted.tobytes()),alpha_max_delta=alpha,
                           premultiplied_max_delta=rgb,current_blocks_preserved=kept,
                           layers=[dict(id=l['id'],kind=l['kind'],ink_sha256=digest(l['parts']['ink'].tobytes()),
                                        original_shadow_pixels_copied=0) for l in layers]))
    return raw,proofs


def load_inputs(plan,project,source,decoder):
    if (set(plan)!={'schema_version','kind','rasterizer_versions','resources'}
            or plan['schema_version']!=1 or plan['kind']!='clean-lettering-v1'):
        raise ValueError('unsupported clean lettering profile')
    if set(plan['rasterizer_versions'])!={'Pillow','fonttools'}:
        raise ValueError('rasterizer locks required')
    if any(importlib.metadata.version(k)!=v for k,v in plan['rasterizer_versions'].items()):
        raise ValueError('rasterizer version mismatch')
    assets={};rows=[];seen=set()
    if not 1<=len(plan['resources'])<=128:raise ValueError('resource bound')
    for r in plan['resources']:
        if (set(r)!={'path','sha256','original','discs','textures'} or r['path'].casefold()in seen
                or r['discs'] not in ([1],[2],[1,2])):raise ValueError('duplicate resource or invalid fields')
        seen.add(r['path'].casefold())
        base=confined_path(source,r['path']).read_bytes();orig=locked(project,r['original'],assets)
        if digest(base)!=r['sha256']:raise ValueError('source SHA256 mismatch: '+r['path'])
        require_raw_envelope(base);ctx=context(orig,decoder);textures=[];objects=set()
        for t in r['textures']:
            if (set(t)!={'object','profile','tiled_sha256','original_tiled_sha256','islands'}
                    or t['object']in objects):raise ValueError('duplicate texture')
            objects.add(t['object'])
            if not 1<=len(t['islands'])<=64:raise ValueError('island bound')
            for i in t['islands']:
                if (set(i)!={'id','name','rect','background','layers','max_alpha_delta','max_premultiplied_delta'}
                        or not 0<=i['max_alpha_delta']<=32 or not 0<=i['max_premultiplied_delta']<=64
                        or not 1<=len(i['layers'])<=8):raise ValueError('island fields/bounds')
                if i['background']['kind']=='restored-art':
                    for ref in ('mask','patch'):locked(project,i['background']['label']['restoration'][ref],assets)
                for l in i['layers']:
                    if l['kind']=='font':locked(project,l['font'],assets)
                    if l['kind']not in ('font','source-ink'):raise ValueError('unknown glyph layer')
            current=selected(base,t['object'],None)[3]
            e=select_texture_export(ctx['tables'],t['object']);off=e['serial_offset']
            original=read_texture(ctx['logical'][off:off+e['serial_size']],ctx['tables']['names'],off,t['profile'],decoder)
            if digest(current['tiles'])!=t['tiled_sha256']or digest(original['tiles'])!=t['original_tiled_sha256']:
                raise ValueError('texture SHA256 mismatch')
            textures.append((t,current,original))
        rows.append((r,base,textures))
    return assets,rows


def build(plan,project,source,output,decoder):
    project,source,output=(Path(p).resolve()for p in(project,source,output))
    if output.exists()or output.is_relative_to(source)or source.is_relative_to(output):
        raise ValueError('new disjoint output required')
    assets,rows=load_inputs(plan,project,source,decoder);resources=[];proofs=[];blobs={}
    for r,base,textures in rows:
        data=base
        for t,current,original in textures:
            tiles,records=rebuild_tiles(current,original,t['islands'],assets)
            data,proof=replace_tiles(data,digest(data),t['object'],tiles,[i['rect']for i in t['islands']],None)
            proofs.append(dict(resource=r['path'],islands=records,**proof))
        data+=bytes((-len(data))%ALIGNMENT);require_raw_envelope(data)
        resources.append(dict(path=r['path'],file='candidate/'+r['path'],before_sha256=digest(base),
                              sha256=digest(data),size=len(data),discs=r['discs']))
        blobs['candidate/'+r['path']]=data
    for r,base,_ in rows:
        if confined_path(source,r['path']).read_bytes()!=base:raise ValueError('source changed during build')
    for (path,expected),raw in assets.items():
        if confined_path(project,path).read_bytes()!=raw:raise ValueError('dependency changed during build')
    manifest=dict(schema_version=1,resources=resources,proofs=proofs,game_started=False,game_rendering_verified=False)
    files={'manifest.json':manifest}
    for disc in (1,2):
        files[f'replacements-disc{disc}.json']=dict(schema_version=1,kind='incremental-comparison-replacements',
            disc=disc,toc_path='MC2Game/Xbox360TOC.txt',resources=[{k:v for k,v in r.items()if k!='discs'}
            for r in resources if disc in r['discs']])
    for name,obj in files.items():blobs[name]=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    output.mkdir(parents=True)
    for name,data in blobs.items():
        p=confined_path(output,name);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb')as f:f.write(data)
        if p.read_bytes()!=data:raise ValueError('output readback mismatch')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('profile','project-root','source-root','output','lzx-library'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--profile-sha256',required=True)
    a=p.parse_args();raw=a.profile.read_bytes()
    if digest(raw)!=a.profile_sha256:raise ValueError('profile SHA256 mismatch')
    result=build(json.loads(raw),a.project_root,a.source_root,a.output,LzxDecoder(a.lzx_library))
    if a.profile.read_bytes()!=raw:raise ValueError('profile changed during build')
    print(f"RESOURCES={len(result['resources'])} TEXTURES={len(result['proofs'])} "
          f"ISLANDS={sum(len(p['islands'])for p in result['proofs'])} RESULT=PASS")


if __name__=='__main__':main()
