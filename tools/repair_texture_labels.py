"""Rebuild explicitly selected label RGB blocks on verified package copies.

The recipe selects existing generated lettering, removes explicitly audited
interior gradient samples, and opts into the BC3 RGB fit. Font, geometry,
retained gradient stops and native alpha bytes are invariant. No game launch.
"""
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
from .reface_font import sha
from .replace_texture_regions import selected, replace_tiles
from .texture_layout import overlay_rect, decode_texture, rect_units
from .texture_overlay import render_label, rgba_crop
from .ue3_package import LzxDecoder
from .ue3_textures import png_rgba


def confined(root, relative):
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts:raise ValueError('relative workspace path required')
    p=(root/p).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('path outside workspace')
    return p


def locked(root, ref):
    p=confined(root,ref['path'])
    if not p.is_file() or p.stat().st_size>256*1024*1024:raise ValueError('input file size bound')
    data=p.read_bytes()
    if sha(data)!=ref['sha256']:raise ValueError('input SHA256 mismatch: '+ref['path'])
    return data


def revise(label, remove):
    if (not isinstance(remove,list) or len(remove)>32 or any(type(v) is not int for v in remove)
            or len(set(remove))!=len(remove)):
        raise ValueError('invalid removed gradient positions')
    before=label['appearance']['gradient']
    if not set(remove)<={p for p,_ in before[1:-1]}:
        raise ValueError('only existing interior gradient positions may be removed')
    after=copy.deepcopy(label)
    after['appearance']['gradient']=[stop for stop in before if stop[0] not in remove]
    return after


def gradient_valleys(label, threshold=20):
    stops=label['appearance']['gradient']
    return [b[0] for a,b,c in zip(stops,stops[1:],stops[2:])
            if min(a[1][0],c[1][0])-b[1][0]>=threshold]


def build(recipe,root,decoder):
    if (set(recipe)!={'schema_version','kind','label_plan','source_tiled_sha256','dimensions','labels','resources'}
            or recipe.get('schema_version')!=1 or recipe.get('kind')!='bounded-label-rgb-repair-v1'):
        raise ValueError('unsupported label repair recipe')
    source=json.loads(locked(root,recipe['label_plan']))
    versions=source.get('rasterizer_versions')
    if not isinstance(versions,dict) or set(versions)!={'Pillow','fonttools'}:
        raise ValueError('explicit rasterizer version locks required')
    if any(importlib.metadata.version(k)!=v for k,v in versions.items()):
        raise ValueError('rasterizer version mismatch')
    labels={l['id']:l for l in source['labels']}
    requests=recipe['labels']; resources=recipe['resources']
    if not isinstance(requests,list) or not 1<=len(requests)<=32:raise ValueError('label count bound')
    if not isinstance(resources,list) or not 1<=len(resources)<=16:raise ValueError('resource count bound')
    resolved=[]; seen=set()
    for row in requests:
        if set(row)!={'id','remove_gradient_positions'} or row['id'] in seen:raise ValueError('label request shape/duplicate')
        seen.add(row['id']); before=labels[row['id']]
        if 'glyph_mask' in before or before['appearance']['kind']!='source-style-v1':
            raise ValueError('explicit raster font label required')
        after=revise(before,row['remove_gradient_positions'])
        font=locked(root,before.get('font',source['font']))
        old=render_label(font,before); new=render_label(font,after)
        if old[3::4]!=new[3::4]:raise ValueError('glyph/effect alpha changed')
        if gradient_valleys(after):raise ValueError('gradient still contains a dark valley')
        resolved.append((before,after,new))
    products={}; proofs=[]; alias_tiles=None; preview=None
    for resource in resources:
        if set(resource)!={'path','object','input'}:raise ValueError('resource request shape')
        relative=resource['path']
        if relative in products:raise ValueError('duplicate output resource')
        confined(root,relative)
        data=locked(root,resource['input'])
        _,_,_,texture=selected(data,resource['object'],decoder)
        if sha(texture['tiles'])!=recipe['source_tiled_sha256']:raise ValueError('source texture SHA256 mismatch')
        if [texture['width'],texture['height']]!=recipe['dimensions']:raise ValueError('texture geometry mismatch')
        layout=texture['layout']; old_tiles=texture['tiles']; tiles=old_tiles; allowed=set()
        metrics=[]; original=decode_texture(texture)
        for before,after,rgba in resolved:
            units=set(rect_units(layout,after['rect']))
            if units & allowed:raise ValueError('label rectangles overlap')
            allowed.update(units)
            tiles,_=overlay_rect(tiles,layout,after['rect'],rgba,rgb_encoding='weighted-fit-v1')
        # Only RGB is being repaired: preserve each original 8-byte alpha block,
        # including coverage, clipping and effects, exactly rather than refitting.
        native=bytearray(tiles)
        for at in allowed:native[at:at+8]=old_tiles[at:at+8]
        for before,after,rgba in resolved:
            rect=after['rect']; rw,rh=rect[2:]; units=rect_units(layout,rect)
            for j in range(rh//4):
                for i in range(rw//4):
                    cell=b''.join(rgba[((j*4+k)*rw+i*4)*4:((j*4+k)*rw+i*4+4)*4] for k in range(4))
                    if not any(cell[3::4]):
                        at=units[j*(rw//4)+i];native[at:at+16]=old_tiles[at:at+16]
        tiles=bytes(native)
        if alias_tiles is not None and tiles!=alias_tiles:raise ValueError('texture aliases differ')
        alias_tiles=tiles
        output,proof=replace_tiles(data,resource['input']['sha256'],resource['object'],tiles,
                                   [a['rect'] for _,a,_ in resolved],decoder)
        checked=selected(output,resource['object'],decoder)[3]
        decoded=decode_texture(checked)
        if original[3::4]!=decoded[3::4]:raise ValueError('decoded alpha changed')
        for before,after,rgba in resolved:
            def rgb_error(pixels):
                return sum(rgba[i+3]**2*sum((rgba[i+k]-pixels[i+k])**2 for k in range(3))
                           for i in range(0,len(rgba),4))
            old_error=rgb_error(rgba_crop(original,texture['width'],after['rect']))
            new_error=rgb_error(rgba_crop(decoded,texture['width'],after['rect']))
            if new_error>=old_error:raise ValueError('RGB repair did not improve selected label: '+after['id'])
            metrics.append(dict(id=after['id'],text=after['text'],
                                before_weighted_rgb_error=old_error,after_weighted_rgb_error=new_error,
                                before_gradient_valleys=gradient_valleys(before),
                                after_gradient_valleys=gradient_valleys(after),
                                font_geometry_and_effects_unchanged=True))
        proof.update(path=relative,labels=metrics,native_alpha_blocks_preserved=True,
                     before_tiled_sha256=sha(old_tiles),after_tiled_sha256=sha(tiles))
        products[relative]=output; proofs.append(proof)
        preview=png_rgba(decoded,texture['width'],texture['height'])
    return products,dict(status='PASS',resources=proofs,game_started=False,game_rendering_verified=False),preview


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recipe',type=Path,required=True); p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--lzx-library',type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path); group.add_argument('--verify-root',type=Path)
    a=p.parse_args(argv)
    try:
        if a.output and a.output.exists():raise ValueError('output already exists')
        products,proof,preview=build(json.loads(a.recipe.read_bytes()),a.root.resolve(),LzxDecoder(a.lzx_library))
        if a.verify_root:
            for relative,data in products.items():
                if confined(a.verify_root,relative).read_bytes()!=data:raise ValueError('independent rebuild mismatch')
            print('PASS: independent rebuild matches all resources');return 0
        for relative,data in products.items():
            target=confined(a.output,relative);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        (a.output/'report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (a.output/'preview-native.png').write_bytes(preview)
        print('PASS: repaired %d labels in %d resources; native alpha and outside blocks preserved' %
              (len(proof['resources'][0]['labels']),len(products)))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
