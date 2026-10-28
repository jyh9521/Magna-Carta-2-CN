"""Compose a bounded post-localization resource revision without deployment."""
import argparse
import json
from pathlib import Path
from .font_binding_plan import confined_path
from .build_font_reface import build as build_fonts
from .build_texture_overlay import build as build_textures
from .build_coalesced import rebuild, resolve_changes
from .subtitle_text import rebuild_reversible
from .replace_texture_regions import replace
from .runtime_package import normalize_package
from .reface_font import sha
from .ue3_package import LzxDecoder


def build(profile,source_root,project_root,output,decoder):
    source_root=Path(source_root).resolve();project_root=Path(project_root).resolve();output=Path(output).resolve()
    if (output.exists() or output.is_relative_to(source_root)
            or source_root.is_relative_to(output)):
        raise ValueError('new disjoint output required')
    p=json.loads(Path(profile).read_bytes())
    if p.get('kind')!='gameplay-resource-revision' or p.get('schema_version')!=1:raise ValueError('revision schema')
    output.mkdir(parents=True)
    def read(name):return json.loads(confined_path(project_root,name).read_bytes())
    fp=confined_path(project_root,p['font_profile'])
    fonts=build_fonts(fp,sha(fp.read_bytes()),source_root,project_root,output/'fonts')
    tp=read(p['texture_plan'])
    build_textures(tp,project_root,output/'textures',decoder,1)
    donor=(output/'textures/candidate'/p['texture_donor']['path']).read_bytes()
    donor,_=normalize_package(donor,sha(donor),decoder)
    files={r['path']:(output/'fonts/candidate'/r['path']).read_bytes() for r in fonts['resources']}
    proofs=[]
    for t in p['texture_targets']:
        before=confined_path(source_root,t['path']).read_bytes()
        if sha(before)!=t['before_sha256']:raise ValueError('texture baseline mismatch')
        current=files.get(t['path'],before)
        current,_=normalize_package(current,sha(current),decoder)
        files[t['path']],proof=replace(current,sha(current),t['object'],donor,sha(donor),
                                      p['texture_donor']['object'],p['texture_rects'],decoder)
        proofs.append(proof)
    text=read(p['text_plan']);data=confined_path(source_root,text['resource']).read_bytes()
    files[text['resource']]=rebuild(data,resolve_changes(data,text))
    for ref in p['subtitle_plans']:
        spec=read(ref);data=confined_path(source_root,spec['resource']).read_bytes()
        files[spec['resource']],proof=rebuild_reversible(data,spec);proofs.append(proof)
    resources=[]
    for path,data in sorted(files.items()):
        data,normalization=normalize_package(data,sha(data),decoder) if path.lower().endswith('.xxx') else (data,{})
        f=confined_path(output,'candidate/'+path);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
        if f.read_bytes()!=data:raise ValueError('candidate reopening mismatch')
        resources.append(dict(path=path,before_sha256=sha(confined_path(source_root,path).read_bytes()),
                              sha256=sha(data),size=len(data),normalization=normalization))
    manifest=dict(schema_version=1,kind='gameplay-resource-revision-build',resources=resources,
                  proofs=proofs,game_started=False,game_rendering_verified=False)
    (output/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('profile','source-root','output','lzx-library'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'));a=p.parse_args()
    m=build(a.profile,a.source_root,a.project_root,a.output,LzxDecoder(a.lzx_library))
    print(json.dumps(dict(status='PASS',resources=len(m['resources']),game_started=False)))


if __name__=='__main__':main()
