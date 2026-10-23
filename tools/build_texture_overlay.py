"""Reproducible, hash-locked text-region overlays for explicitly selected textures."""
from pathlib import Path
import argparse
import json
import importlib.metadata
from .font_binding_plan import confined_path,_relative,_hash,parse_json_object
from .build_font_route_probe import encoded
from .build_font_supplement import context,restore_copy
from .ue3_package import LzxDecoder
from .supplement_font import parse_atlas_payload,atlas_tiles
from .ue3_textures import decode_dxt5,untile_dxt5,png_rgba
from .texture_overlay import digest,render_label,patch_package,image_id,edit_pixels,render_area,MAX_TEXTURE_SOURCES,MAX_TEXT_LAYERS
from .verify_locale_candidate import scan_tree

KIND='offline-texture-overlay-bundle'


def select_sources(sources,disc=None):
    """Explicit per-disc inventory; absent declarations preserve legacy bundles."""
    if not isinstance(sources,list) or not 1<=len(sources)<=MAX_TEXTURE_SOURCES:raise ValueError('texture source bound')
    if disc is not None and (type(disc) is not int or disc not in (1,2)):raise ValueError('invalid texture disc')
    selected=[]
    for source in sources:
        if not isinstance(source,dict):raise ValueError('invalid texture source')
        if 'discs' in source:
            ds=source['discs']
            if (not isinstance(ds,list) or not ds or any(type(d) is not int or d not in (1,2) for d in ds)
                    or len(set(ds))!=len(ds)):raise ValueError('invalid texture source discs')
            if disc is None:raise ValueError('disc-scoped texture sources require explicit disc')
        else:ds=[1,2]
        if disc is None or disc in ds:selected.append(source)
    if not selected:raise ValueError('texture disc has no sources')
    return selected


def prepare(plan,root,decoder,disc=None):
    root=Path(root).resolve();snapshots=[]
    if (type(plan.get('schema_version')) is not int or plan['schema_version']!=1
            or plan.get('kind')!='texture-text-overlay-plan' or plan.get('game_rendering_verified') is not False):
        raise ValueError('invalid texture overlay plan')
    versions=plan.get('rasterizer_versions')
    if not isinstance(versions,dict) or set(versions)!={'Pillow','fonttools'}:
        raise ValueError('explicit rasterizer version locks required')
    if any(importlib.metadata.version(k)!=v for k,v in versions.items()):raise ValueError('rasterizer version mismatch')
    def locked_bytes(ref):
        _relative(ref['path']);_hash(ref['sha256']);p=confined_path(root,ref['path']);b=p.read_bytes()
        if digest(b)!=ref['sha256']:raise ValueError('texture input hash mismatch')
        snapshots.append((p,ref['sha256']));return b
    labels=plan.get('labels');sources=plan.get('sources')
    if (not isinstance(labels,list) or not 1<=len(labels)<=MAX_TEXT_LAYERS or not isinstance(sources,list)
            or not 1<=len(sources)<=MAX_TEXTURE_SOURCES):raise ValueError('texture label/source bound')
    sources=select_sources(sources,disc)
    font=locked_bytes(plan['font']);layers={}
    if len(font)>64*1024*1024:raise ValueError('font size bound')
    if sum(render_area(l) for l in labels)>16*1024*1024:raise ValueError('text layer total bound')
    for label in labels:
        if not isinstance(label['id'],str) or not label['id'] or label['id'] in layers:raise ValueError('duplicate/invalid text layer id')
        layers[label['id']]=(label,render_label(font,label))
    files={};rows=[];seen=set();reports=[];alias_pixels={};encoding_cache={}
    for source in sources:
        path=_relative(source['path'])
        if path.casefold() in seen:raise ValueError('duplicate texture resource')
        seen.add(path.casefold());original=locked_bytes(source['original']);base=locked_bytes(source['base'])
        candidate,proof=patch_package(base,source['base']['sha256'],source['textures'],layers,decoder,encoding_cache)
        files['candidate/'+path]=candidate;files['rollback-check/'+path]=base
        rows.append(dict(path=path,original_sha256=digest(original),base_sha256=digest(base),candidate_sha256=digest(candidate),
                         original_size=len(original),candidate_size=len(candidate)))
        reports.append(dict(path=path,**proof))
        for phase,data in [('before',base),('after',candidate)]:
            ctx=context(data,decoder)
            for index,edit in enumerate(source['textures']):
                matches=[e for e in ctx['tables']['exports'] if e['path'].casefold()==edit['object'].casefold()]
                if len(matches)!=1:raise ValueError('texture preview object mismatch')
                e=matches[0];payload=ctx['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
                width,height,rgba=edit_pixels(payload,ctx['tables']['names'],e['serial_offset'],edit,decoder)
                files[f'previews/{phase}-{len(rows):02d}-{index:02d}.png']=png_rgba(rgba,width,height)
                key=(phase,image_id(edit));h=digest(rgba)
                if key in alias_pixels and alias_pixels[key]!=h:raise ValueError('selected alias decoded pixels differ')
                alias_pixels[key]=h
    files['reports/texture-proofs.json']=encoded(reports)
    manifest=dict(schema_version=1,kind=KIND,game_rendering_verified=False,deployment_performed=False,
                  plan_canonical_sha256=digest(encoded(plan)),resources=rows,labels=len(layers),
                  alias_rgba_sha256={a+':'+b:h for (a,b),h in alias_pixels.items()},
                  member_sha256={p:digest(b) for p,b in files.items()})
    if any('regions' in edit for source in sources for edit in source['textures']):
        manifest['image_groups']=len({image_id(e) for source in sources for e in source['textures']})
    if disc is not None:manifest['disc']=disc
    files['manifest.json']=encoded(manifest)
    for p,h in snapshots:
        if digest(p.read_bytes())!=h:raise ValueError('texture overlay input changed')
    return files,manifest,snapshots


def build(plan,root,output,decoder,disc=None):
    root=Path(root).resolve();output=Path(output).resolve()
    if output.exists() or output.is_symlink() or not output.is_relative_to(root) or output==root:raise ValueError('texture output must be new and inside project')
    files,m,snapshots=prepare(plan,root,decoder,disc);output.mkdir()
    bases={s['path']:s['base'] for s in plan['sources']}
    for name,data in files.items():
        p=confined_path(output,name);p.parent.mkdir(parents=True,exist_ok=True)
        if name.startswith('rollback-check/'):
            rel=name[len('rollback-check/'):];base=bases[rel]
            restore_copy(output/'candidate'/rel,confined_path(root,base['path']),p,digest(files['candidate/'+rel]),base['sha256'])
        else:
            with p.open('xb') as f:f.write(data)
        if p.read_bytes()!=data:raise ValueError('texture output reopening mismatch')
    for p,h in snapshots:
        if digest(p.read_bytes())!=h:raise ValueError('texture source changed at publication')
    return m


def verify(plan,root,output,decoder,disc=None):
    files,m,snapshots=prepare(plan,root,decoder,disc);scan_tree(Path(output),set(files))
    for name,data in files.items():
        if confined_path(Path(output),name).read_bytes()!=data:raise ValueError('texture independent replay mismatch')
    return m


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--disc',type=int,choices=(1,2))
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--lzx-library',type=Path,required=True)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--output-dir',type=Path);g.add_argument('--verify-root',type=Path)
    a=p.parse_args(argv)
    try:
        b=a.plan.read_bytes();plan=parse_json_object(b);decoder=LzxDecoder(a.lzx_library)
        m=build(plan,a.project_root,a.output_dir,decoder,a.disc) if a.output_dir else verify(plan,a.project_root,a.verify_root,decoder,a.disc)
        if a.plan.read_bytes()!=b:raise ValueError('texture plan changed')
        result=dict(resources=len(m['resources']),labels=m['labels'],verified=bool(a.verify_root),game_rendering_verified=False)
        if 'image_groups' in m:result['image_groups']=m['image_groups']
        print(json.dumps(result));return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
