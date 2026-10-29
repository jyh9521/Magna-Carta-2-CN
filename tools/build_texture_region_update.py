"""Rebuild bounded label regions and transplant native tiles into current raw packages.

The overlay plan supplies locale data. All current packages are SHA-locked;
donor packages never replace unrelated current exports, text or font revisions.
"""
from pathlib import Path
import argparse,json
from .build_texture_overlay import prepare
from .font_binding_plan import confined_path,parse_json_object
from .reface_font import sha
from .replace_texture_regions import selected,replace_tiles
from .runtime_package import normalize_package
from .runtime_envelope import ALIGNMENT,require_raw_envelope
from .texture_layout import rect_units,decode_texture
from .ue3_textures import png_rgba
from .ue3_package import LzxDecoder


def transfer(data,expected_sha256,obj,donor,donor_obj,rectangles,decoder):
    if sha(data)!=expected_sha256:raise ValueError('current package SHA256 mismatch')
    require_raw_envelope(data)
    donor,normalization=normalize_package(donor,sha(donor),decoder)
    _,_,_,before=selected(data,obj,decoder);_,_,_,generated=selected(donor,donor_obj,decoder)
    if (before['width'],before['height'],before['format'])!=(generated['width'],generated['height'],generated['format']):
        raise ValueError('texture donor geometry/profile mismatch')
    if not isinstance(rectangles,list) or not 1<=len(rectangles)<=32:raise ValueError('rectangle count outside bound')
    units=set()
    for rectangle in rectangles:
        new=set(rect_units(before['layout'],rectangle))
        if new&units:raise ValueError('duplicate/overlapping native rectangles')
        units.update(new)
    tiles=bytearray(before['tiles']);size=before['layout']['unit_bytes']
    for offset in units:tiles[offset:offset+size]=generated['tiles'][offset:offset+size]
    output,proof=replace_tiles(data,expected_sha256,obj,bytes(tiles),rectangles,decoder)
    padding=(-len(output))%ALIGNMENT;output+=bytes(padding)
    require_raw_envelope(output)
    _,_,_,after=selected(output,obj,decoder)
    proof.update(output_sha256=sha(output),tail_padding=padding,donor_normalization=normalization,
                 source_size=len(data),output_size=len(output),game_started=False)
    return output,proof,(before,after)


def build(profile,project_root,input_root,output,decoder):
    root=Path(project_root).resolve();current=Path(input_root).resolve();out=Path(output).resolve()
    if (type(profile.get('schema_version')) is not int or profile.get('schema_version')!=1
            or profile.get('kind')!='native-texture-region-update'
            or profile.get('game_rendering_verified') is not False):raise ValueError('unsupported region update profile')
    if (Path(output).is_symlink() or out.exists() or out==root or not out.is_relative_to(root)
            or out.is_relative_to(current) or current.is_relative_to(out)):
        raise ValueError('output must be new, inside project, disjoint from current resources')
    ref=profile['overlay_plan'];plan_path=confined_path(root,ref['path']);raw=plan_path.read_bytes()
    if sha(raw)!=ref['sha256']:raise ValueError('overlay plan SHA256 mismatch')
    plan=parse_json_object(raw);resources=profile['resources']
    if not isinstance(resources,list) or not 1<=len(resources)<=256:raise ValueError('region resource count outside bound')
    disc=profile['disc']
    if type(disc) is not int or disc not in (1,2):raise ValueError('explicit source disc required')
    donors,donor_manifest,snapshots=prepare(plan,root,decoder,disc)
    source_discs={s['path']:s.get('discs',[1,2]) for s in plan['sources']}
    files={};proofs=[];seen=set()
    for record in resources:
        name=record['path'];source=confined_path(current,name)
        if record['discs']!=source_discs.get(name) or disc not in record['discs']:
            raise ValueError('region disc provenance mismatch')
        if name.casefold() in seen:raise ValueError('duplicate region resource')
        seen.add(name.casefold())
        if not name.casefold().endswith('.xxx'):raise ValueError('only declared UE3 package copies supported')
        data=source.read_bytes();snapshots.append((source,record['input_sha256']))
        output_bytes,proof,(before,after)=transfer(data,record['input_sha256'],record['object'],
            donors['candidate/'+name],record['donor_object'],record['rectangles'],decoder)
        files['candidate/'+name]=output_bytes;files['baseline/'+name]=data
        for phase,texture in [('before',before),('after',after)]:
            files[f'previews/{len(proofs):03d}-{phase}.png']=png_rgba(decode_texture(texture),texture['width'],texture['height'])
        proofs.append(dict(path=name,discs=record['discs'],**proof))
    for path,expected in snapshots:
        if sha(path.read_bytes())!=expected:raise ValueError('region input changed before publication')
    if plan_path.read_bytes()!=raw:raise ValueError('overlay plan changed')
    manifest=dict(schema_version=1,kind='native-texture-region-update-result',resources=proofs,
        input_profile_sha256=sha(json.dumps(profile,sort_keys=True).encode()),
        overlay_manifest=donor_manifest,game_started=False,game_rendering_verified=False,
        member_sha256={name:sha(value)for name,value in files.items()})
    files['manifest.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    out.mkdir(parents=True)
    for name,value in files.items():
        path=confined_path(out,name);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(value)
        if path.read_bytes()!=value:raise ValueError('region output reopening mismatch')
    for path,expected in snapshots:
        if sha(path.read_bytes())!=expected:raise ValueError('region input changed after publication')
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--profile-sha256',required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--input-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--lzx-library',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        raw=a.profile.read_bytes()
        if len(raw)>1024*1024 or sha(raw)!=a.profile_sha256:raise ValueError('revision profile hash/size mismatch')
        result=build(parse_json_object(raw),a.project_root,a.input_root,a.output,LzxDecoder(a.lzx_library))
        if a.profile.read_bytes()!=raw:raise ValueError('revision profile changed')
        print(json.dumps(dict(resources=len(result['resources']),unselected_exports_preserved=True,
                             outside_blocks_preserved=True,game_started=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
