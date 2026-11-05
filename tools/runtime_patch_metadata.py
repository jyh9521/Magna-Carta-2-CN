"""Refresh generated BE32 patch metadata while guarding identity and user toggles.

This edits a new copy only. Deployment and rollback remain explicit operations.
No game process, executable or native image is loaded or changed by this tool.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import tomllib

try:
    from .runtime_patch import digest,hash_value,patch_toml
except ImportError:
    from runtime_patch import digest,hash_value,patch_toml


def _read(data):
    if not isinstance(data,bytes) or not 0<len(data)<=1024*1024:raise ValueError('invalid patch file size')
    text=data.decode('utf-8-sig');doc=tomllib.loads(text)
    if set(doc)!={'title_name','title_id','hash','patch'}:raise ValueError('unsupported patch header fields')
    patches=doc['patch']
    if not isinstance(patches,list) or not 1<=len(patches)<=8:raise ValueError('invalid patch section count')
    groups=[];used=set()
    for section in patches:
        if set(section)-{'name','desc','author','is_enabled','be32'}:raise ValueError('unsupported patch fields/type')
        if type(section.get('is_enabled')) is not bool:raise ValueError('patch enable flag must be boolean')
        if not isinstance(section.get('name'),str):raise ValueError('invalid patch name')
        writes=section.get('be32')
        if not isinstance(writes,list) or not 1<=len(writes)<=32:raise ValueError('invalid BE32 patch writes')
        pairs=[]
        for w in writes:
            if (not isinstance(w,dict) or set(w)!={'address','value'}
                    or type(w['address']) is not int or not 0<=w['address']<2**32 or w['address']%4
                    or type(w['value']) is not int or not 0<=w['value']<2**32
                    or w['address'] in used):raise ValueError('invalid or overlapping BE32 write')
            used.add(w['address']);pairs.append((w['address'],w['value']))
        groups.append((tuple(sorted(pairs)),section))
    return text,doc,groups


def machine_signature(data):
    _,doc,groups=_read(data)
    return tuple(doc[k] for k in ('title_name','title_id','hash')),tuple(sorted(k for k,_ in groups))


def profile(data,plan):
    expected=patch_toml(plan)
    if machine_signature(data)!=machine_signature(expected):raise ValueError('patch identity or machine writes mismatch')
    text,_,groups=_read(data);_,_,ordered=_read(expected);by_key=dict(groups)
    enabled=[by_key[k]['is_enabled'] for k,_ in ordered]
    return dict(enabled=enabled,literal_utf8=any(ord(c)>127 for c in text),
                comments=sum(l.lstrip().startswith('#') for l in text.splitlines()),
                writes=sum(len(k) for k,_ in groups))


def format_profile(result):
    return ('enabled='+''.join('1' if v else '0' for v in result['enabled'])
            +'; literal_utf8='+str(result['literal_utf8']).lower()
            +f"; comments={result['comments']}; writes={result['writes']}")


def refresh(data,plan,enable=()):
    profile(data,plan);_,_,groups=_read(data);by_key=dict(groups)
    enabled_addresses=set(enable)
    known={a for k,_ in groups for a,_ in k}
    if any(type(a) is not int or a not in known for a in enabled_addresses):raise ValueError('unknown enable selector')
    out=copy.deepcopy(plan)
    if not isinstance(out.get('patch_sections'),list):raise ValueError('metadata refresh requires named sections')
    _,_,expected_groups=_read(patch_toml(plan))
    for section,(key,_) in zip(out['patch_sections'],expected_groups):
        # A guarded write can span several BE32 words (for example a cave).
        # Match the serialized partition, not just each write's start address.
        addresses={a for a,_ in key}
        section['is_enabled']=by_key[key]['is_enabled'] or bool(addresses&enabled_addresses)
    result=patch_toml(out)
    if machine_signature(result)!=machine_signature(data):raise ValueError('metadata refresh changed machine writes')
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ('inspect','refresh'):
        cmd=sub.add_parser(name);cmd.add_argument('patch',type=Path);cmd.add_argument('--plan',required=True,type=Path)
        if name=='refresh':
            cmd.add_argument('--sha256',required=True);cmd.add_argument('--output',required=True,type=Path)
            cmd.add_argument('--enable',action='append',type=lambda x:int(x,0),default=[])
    a=p.parse_args(argv)
    try:
        data=a.patch.read_bytes();plan=json.loads(a.plan.read_bytes())
        if a.command=='inspect':print(format_profile(profile(data,plan)));return 0
        if digest(data)!=hash_value(a.sha256.lower()):raise ValueError('patch source SHA256 mismatch')
        if a.output.resolve()==a.patch.resolve() or a.output.exists() or a.output.is_symlink():
            raise ValueError('metadata output must be a distinct new file')
        result=refresh(data,plan,a.enable)
        if a.patch.read_bytes()!=data:raise ValueError('patch source changed before writing')
        with a.output.open('xb') as f:f.write(result)
        if a.output.read_bytes()!=result or a.patch.read_bytes()!=data:raise ValueError('metadata reopening/source check failed')
        print(format_profile(profile(result,plan)));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
