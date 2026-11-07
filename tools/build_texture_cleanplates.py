"""Replay hash-locked clean-plate integration into sparse restoration PNGs.

Production overlays consume the saved small patch/mask assets, not a complete
generated portrait. Full plates are caller-supplied development/research inputs.
"""
import argparse
import io
import json
from pathlib import Path

from .build_font_supplement import context
from .cleanplate_repair import reconcile_rgba
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .sparse_artifact_paths import validate_patch_paths
from .texture_layout import read_texture,decode_texture
from .texture_overlay import select_texture_export,rgba_crop
from .ue3_package import LzxDecoder


def build(recipe,root,output,decoder):
    from PIL import Image
    import importlib.metadata
    root,output=Path(root).resolve(),Path(output).resolve()
    if (set(recipe)!={'schema_version','kind','method','hidden_artwork','rasterizer_versions','cases'}
            or recipe['schema_version']!=1 or recipe['kind']!='texture-cleanplate-repair-v1'
            or recipe['method']!='premultiplied-harmonic-boundary-v1'
            or recipe['hidden_artwork']!='reconstruction-not-original'
            or not isinstance(recipe['cases'],list) or not 1<=len(recipe['cases'])<=64
            or set(recipe['rasterizer_versions'])!={'Pillow','numpy'}
            or any(importlib.metadata.version(k)!=v for k,v in recipe['rasterizer_versions'].items())):
        raise ValueError('unsupported or version-mismatched cleanplate recipe')
    if output.exists() or not output.is_relative_to(root) or output==root:
        raise ValueError('new project-contained cleanplate replay output required')
    validate_patch_paths(recipe['cases'],output)
    cache,snapshots,files,records={},{},{},[]

    def locked(ref):
        if set(ref)!={'path','sha256'}:
            raise ValueError('explicit cleanplate input path/SHA256 required')
        path=confined_path(root,ref['path']);raw=path.read_bytes()
        if digest(raw)!=ref['sha256']:
            raise ValueError('cleanplate dependency SHA256 mismatch')
        snapshots[path]=ref['sha256'];return raw

    ids=set()
    for case in recipe['cases']:
        if (set(case)!={'id','source','object','profile','dimensions','tiled_sha256','rect',
                        'source_rgba_sha256','mask','plate','plate_size','iterations','alpha_mode','patch'}
                or not isinstance(case['id'],str) or not case['id'] or case['id'] in ids):
            raise ValueError('invalid or duplicate cleanplate case')
        ids.add(case['id']);ref=case['source']
        if ref['path'] not in cache:cache[ref['path']]=context(locked(ref),decoder)
        c=cache[ref['path']]
        if c['sha256']!=ref['sha256']:raise ValueError('inconsistent cleanplate source identity')
        e=select_texture_export(c['tables'],case['object'])
        payload=c['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
        texture=read_texture(payload,c['tables']['names'],e['serial_offset'],case['profile'],decoder)
        size=[texture['width'],texture['height']]
        if size!=case['dimensions'] or digest(texture['tiles'])!=case['tiled_sha256']:
            raise ValueError('native cleanplate source identity changed')
        x,y,w,h=case['rect']
        if (any(type(v) is not int for v in (x,y,w,h)) or min(x,y)<0 or min(w,h)<=0
                or x+w>size[0] or y+h>size[1]):
            raise ValueError('cleanplate owned rectangle outside source')
        native=decode_texture(texture);crop=rgba_crop(native,size[0],case['rect'])
        if digest(crop)!=case['source_rgba_sha256']:
            raise ValueError('native cleanplate source crop changed')
        with Image.open(io.BytesIO(locked(case['mask']))) as mask_image:
            if mask_image.format!='PNG' or mask_image.mode!='L' or mask_image.size!=(w,h):
                raise ValueError('cleanplate binary mask geometry/mode mismatch')
            small_mask=mask_image.tobytes()
        with Image.open(io.BytesIO(locked(case['plate']))) as plate_image:
            if (plate_image.format!='PNG' or plate_image.mode!='RGBA'
                    or list(plate_image.size)!=case['plate_size']
                    or min(plate_image.size)<1 or max(plate_image.size)>4096):
                raise ValueError('cleanplate PNG geometry/mode mismatch')
            plate=plate_image.resize(tuple(size),Image.Resampling.LANCZOS)
        mask=Image.new('L',tuple(size));mask.paste(Image.frombytes('L',(w,h),small_mask),(x,y))
        # A one-pixel context is sufficient: all off-mask correction values are
        # fixed Dirichlet boundary conditions. Larger unseen portrait regions
        # are never considered, copied or written by the integration.
        bounds=mask.getbbox()
        if bounds is None:raise ValueError('empty cleanplate support')
        cx=max(0,bounds[0]-1);cy=max(0,bounds[1]-1)
        cr=min(size[0],bounds[2]+1);cb=min(size[1],bounds[3]+1)
        source_image=Image.frombytes('RGBA',tuple(size),native)
        small=reconcile_rgba(source_image.crop((cx,cy,cr,cb)).tobytes(),
                             plate.crop((cx,cy,cr,cb)).tobytes(),cr-cx,cb-cy,
                             mask.crop((cx,cy,cr,cb)).tobytes(),
                             case['iterations'],case['alpha_mode'])
        reconstructed=source_image.copy()
        reconstructed.paste(Image.frombytes('RGBA',(cr-cx,cb-cy),small),(cx,cy))
        restored=reconstructed.crop((x,y,x+w,y+h)).tobytes()
        sparse=b''.join(restored[i*4:i*4+4] if v else bytes(4) for i,v in enumerate(small_mask))
        buffer=io.BytesIO();Image.frombytes('RGBA',(w,h),sparse).save(buffer,format='PNG')
        raw=buffer.getvalue();name=case['patch']['path']
        if name in files or digest(raw)!=case['patch']['sha256']:
            raise ValueError('cleanplate patch replay mismatch or duplicate')
        files[name]=raw
        records.append(dict(id=case['id'],selected_pixels=small_mask.count(255),
                            patch_sha256=digest(raw),unmasked_source_preserved=True,
                            alpha_mode=case['alpha_mode']))
    if any(digest(p.read_bytes())!=sha for p,sha in snapshots.items()):
        raise ValueError('cleanplate dependency changed during integration')
    output.mkdir()
    for name,raw in files.items():
        p=confined_path(output,name);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(raw)
        if p.read_bytes()!=raw:raise ValueError('cleanplate patch readback mismatch')
    result=dict(schema_version=1,cases=records,hidden_artwork='reconstruction-not-original',
                game_rendering_verified=False)
    metadata=(json.dumps(result,indent=2)+'\n').encode('utf8')
    with (output/'manifest.json').open('xb') as stream:stream.write(metadata)
    if (output/'manifest.json').read_bytes()!=metadata:
        raise ValueError('cleanplate manifest readback mismatch')
    if any(confined_path(output,name).read_bytes()!=raw for name,raw in files.items()):
        raise ValueError('cleanplate patch changed after metadata publication')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('recipe','project-root','output-dir','lzx-library'):
        p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--recipe-sha256',required=True);a=p.parse_args();raw=a.recipe.read_bytes()
    if digest(raw)!=a.recipe_sha256:raise ValueError('cleanplate recipe SHA256 mismatch')
    result=build(json.loads(raw),a.project_root,a.output_dir,LzxDecoder(a.lzx_library))
    if a.recipe.read_bytes()!=raw:raise ValueError('cleanplate recipe changed during build')
    print(f"CLEANPLATES={len(result['cases'])} UNMASKED_PRESERVED=ALL RESULT=PASS")


if __name__=='__main__':main()
