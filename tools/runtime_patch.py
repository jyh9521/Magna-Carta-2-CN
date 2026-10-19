"""Guarded, locale-neutral PPC runtime patch bundles; never edit source XEX."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import tomllib


def digest(data):return hashlib.sha256(data).hexdigest()


def hash_value(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise ValueError('invalid SHA256')
    return value


def read_bundle(root,manifest_sha256,game,exe,config):
    """Preflight actual bytes before creating a run. The launcher pins metadata."""
    root=Path(root).resolve();m_path=root/'manifest.json'
    if m_path.is_symlink() or m_path.stat().st_size>1024*1024:raise ValueError('invalid runtime manifest file')
    raw=m_path.read_bytes()
    if digest(raw)!=hash_value(manifest_sha256):raise ValueError('runtime patch manifest SHA256 mismatch')
    m=json.loads(raw)
    if m.get('schema_version')!=1 or m.get('kind')!='xenia-runtime-patch-bundle':
        raise ValueError('unsupported runtime patch bundle')
    for path,key in [(game,'game_sha256'),(exe,'emulator_sha256')]:
        if digest(Path(path).read_bytes())!=hash_value(m[key]):raise ValueError('runtime patch '+key+' mismatch')
    if tomllib.loads(config.decode('utf-8-sig')).get('General',{}).get('apply_patches',True) is not True:
        raise ValueError('runtime patch requires apply_patches=true in existing config')
    files=m.get('patches')
    if not isinstance(files,dict) or not 1<=len(files)<=8:raise ValueError('invalid runtime patch inventory')
    payloads={}
    for name,h in files.items():
        if not isinstance(name,str) or not re.fullmatch('[A-F0-9]{8} - [A-Za-z0-9 _-]+[.]patch[.]toml',name):
            raise ValueError('invalid runtime patch filename')
        path=root/name
        if path.is_symlink() or not path.is_file():raise ValueError('runtime patch must be a regular file')
        data=path.read_bytes()
        if digest(data)!=hash_value(h):raise ValueError('runtime patch file SHA256 mismatch')
        t=tomllib.loads(data.decode('utf8'))
        if t.get('title_id')!=m['title_id'] or t.get('hash')!=m['module_hash']:
            raise ValueError('runtime patch module identity mismatch')
        payloads[name]=data
    if m_path.read_bytes()!=raw:raise ValueError('runtime patch metadata changed')
    return m,payloads


def apply_image(image,plan,reverse=False):
    """Expected-byte and whole-image guarded reversible changes on a copy."""
    if plan.get('schema_version')!=1 or plan.get('kind')!='ppc-runtime-patch':raise ValueError('unsupported runtime plan')
    base=plan['image_base']
    if type(base) is not int or not 0<=base<2**32:raise ValueError('invalid image base')
    if not reverse and digest(image)!=hash_value(plan['image_sha256']):raise ValueError('runtime image SHA256 mismatch')
    def offset(a,n):
        if type(a) is not int or a%4 or not 0<=a-base<=len(image)-n:raise ValueError('runtime patch range outside image')
        return a-base
    if not reverse:
        for w in plan['windows']:
            at=offset(w['address'],w['size'])
            if digest(image[at:at+w['size']])!=hash_value(w['sha256']):raise ValueError('runtime context window mismatch')
    writes=plan['writes']
    if not isinstance(writes,list) or not 1<=len(writes)<=32:raise ValueError('runtime write count outside bound')
    out=bytearray(image);used=set()
    for write in writes:
        old,new=bytes.fromhex(write['expected']),bytes.fromhex(write['replacement'])
        if not old or len(old)!=len(new) or len(old)%4:raise ValueError('runtime patch size mismatch')
        at=offset(write['address'],len(old));span=set(range(at,at+len(old)))
        if span&used:raise ValueError('overlapping runtime writes')
        used.update(span)
        if reverse:old,new=new,old
        if image[at:at+len(old)]!=old:raise ValueError('runtime expected bytes mismatch')
        out[at:at+len(new)]=new
    result=bytes(out)
    if reverse and digest(result)!=plan['image_sha256']:raise ValueError('runtime restoration image mismatch')
    return result


def patch_toml(plan):
    # JSON strings are valid TOML basic strings for these pinned ASCII fields.
    q=lambda s:json.dumps(s,ensure_ascii=True)
    lines=['title_name = '+q(plan['title_name']),'title_id = '+q(plan['title_id']),
           'hash = '+q(plan['module_hash']),'','[[patch]]','name = '+q(plan['name']),
           'desc = "Subtract the line origin from forced intra-token wrap extents"','is_enabled = true']
    for w in plan['writes']:
        value=bytes.fromhex(w['replacement'])
        for i in range(0,len(value),4):
            lines+=['','[[patch.be32]]',f"address = 0x{w['address']+i:08x}",f'value = 0x{value[i:i+4].hex()}']
    return ('\n'.join(lines)+'\n').encode('utf8')


def build(image,plan,game,exe,output):
    output=Path(output).resolve()
    if output.exists():raise ValueError('runtime bundle output must be new')
    if (not isinstance(plan.get('title_id'),str) or not re.fullmatch('[A-F0-9]{8}',plan['title_id'])
            or not isinstance(plan.get('module_hash'),str) or not re.fullmatch('[A-F0-9]{16}',plan['module_hash'])
            or not isinstance(plan.get('title_name'),str) or not re.fullmatch('[A-Za-z0-9 _-]{1,80}',plan['title_name'])):
        raise ValueError('invalid runtime title/module identity')
    if len(image)>256*1024*1024:raise ValueError('runtime image exceeds bounded size')
    for path,key in [(game,'game_sha256'),(exe,'emulator_sha256')]:
        if digest(Path(path).read_bytes())!=hash_value(plan[key]):raise ValueError('runtime source '+key+' mismatch')
    if 'cave' in plan:
        try:
            from .xex_image import parse_xex,inspect_pe
            from .ppc_pdata import read_pdata
        except ImportError:
            from xex_image import parse_xex,inspect_pe
            from ppc_pdata import read_pdata
        meta=parse_xex(Path(game).read_bytes(),plan['game_sha256'])
        if meta['image_base']!=plan['image_base']:raise ValueError('runtime XEX/image base mismatch')
        base=plan['image_base'];c=plan['cave'];a,n=c['address'],c['size']
        ranges=[[base+r['offset'],base+r['offset']+r['size']] for r in meta['page_ranges'] if r['kind']==1]
        if not any(start<=a and a+n<=end for start,end in ranges):raise ValueError('runtime cave outside XEX executable pages')
        records=read_pdata(image,base,ranges)['records']
        if any(a<r['end'] and r['start']<a+n for r in records):raise ValueError('runtime cave overlaps declared function')
        sections=inspect_pe(image,base,None)['sections'];text=next(s for s in sections if s['name']=='.text')
        end=base+text['rva']+text['virtual_size'];next_start=min(base+s['rva'] for s in sections if base+s['rva']>=end)
        if not end<=a<a+n<=next_start or any(image[end-base:next_start-base]):
            raise ValueError('runtime cave is not verified zero text alignment padding')
        if image[a-base:a-base+n]!=bytes.fromhex(c['expected']):raise ValueError('runtime cave expected bytes mismatch')
    modified=apply_image(image,plan)
    if apply_image(modified,plan,True)!=image:raise ValueError('runtime patch rollback mismatch')
    patch=patch_toml(plan);name=plan['title_id']+' - '+plan['title_name']+'.patch.toml'
    # Validate generated TOML before publication, not only its digest.
    parsed=tomllib.loads(patch.decode('utf8'));assert len(parsed['patch'][0]['be32'])==sum(len(bytes.fromhex(w['replacement']))//4 for w in plan['writes'])
    manifest=dict(schema_version=1,kind='xenia-runtime-patch-bundle',game_sha256=plan['game_sha256'],
        emulator_sha256=plan['emulator_sha256'],title_id=plan['title_id'],module_hash=plan['module_hash'],
        image_sha256=plan['image_sha256'],modified_image_sha256=digest(modified),patches={name:digest(patch)},
        game_started=False,game_rendering_verified=False)
    output.mkdir(parents=True,exist_ok=False)
    members={name:patch,'original.bin':image,'modified.bin':modified,
             'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode()}
    for name,data in members.items():
        path=output/name
        with path.open('xb') as f:f.write(data)
        if path.read_bytes()!=data:raise ValueError('runtime bundle reopening mismatch')
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['image','plan','game','exe','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(argv)
    try:
        inputs=[a.image,a.plan,a.game,a.exe];hashes=[digest(f.read_bytes()) for f in inputs]
        if any(a.output.resolve().is_relative_to(f.resolve()) for f in inputs):raise ValueError('runtime output aliases input')
        plan=json.loads(a.plan.read_bytes());m=build(a.image.read_bytes(),plan,a.game,a.exe,a.output)
        if [digest(f.read_bytes()) for f in inputs]!=hashes:raise ValueError('runtime source changed')
        count=sum(len(bytes.fromhex(w['replacement']))//4 for w in plan['writes'])
        print(json.dumps(dict(writes=count,modified_image_sha256=m['modified_image_sha256'],game_started=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
