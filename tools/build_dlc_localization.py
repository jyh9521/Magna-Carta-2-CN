"""Reproducibly localize source-locked STFS packages into a new output tree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from .content_bundle import check_no_links
from .stfs_package import StfsPackage
from .ue3_package import LzxDecoder
from .ue3_subtitle_refs import patch_package
from .xdbf_strings import Xdbf, rebuild, sha


def json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8')


def read_json(path):
    def unique(pairs):
        value={}
        for k,v in pairs:
            if k in value:
                raise ValueError('duplicate JSON field')
            value[k]=v
        return value
    return json.loads(path.read_bytes(),object_pairs_hook=unique)


def project_file(root,path):
    if not isinstance(path,str) or not path or '\\' in path or ':' in path or any(p in ('','..','.') for p in path.split('/')):
        raise ValueError('invalid project-relative DLC path')
    target=check_no_links(root/path)
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError('DLC dependency outside project or missing')
    return target


def validate_strings(data,shared):
    if (type(shared.get('schema_version')) is not int or shared['schema_version']!=1
            or shared.get('kind')!='shared-xdbf-string-translations'):
        raise ValueError('unsupported shared XDBF translation schema')
    tables=Xdbf(data).strings();language=shared['source_language_id']
    if type(language) is not int or set(tables)!={language}:
        raise ValueError('unexpected XDBF language tables')
    rows={r['id']:r['text'] for r in tables[language]}
    edited=[e['id'] for e in shared['entries']];kept=[e['id']for e in shared['preserved_ids']]
    if (len(set(edited+kept))!=len(edited+kept) or set(edited+kept)!=set(rows)
            or any(e['language']!=language for e in shared['entries'])):
        raise ValueError('incomplete or duplicate XDBF translation coverage')
    for e in shared['preserved_ids']:
        if sha(rows[e['id']].encode())!=e['source_sha256']:
            raise ValueError('preserved XDBF source mismatch')
    return dict(schema_version=1,kind='xdbf-string-localization',input_sha256=sha(data),entries=shared['entries'])


def build(source_root,profile_path,project_root,output,decoder=None):
    source_root,project_root=check_no_links(source_root),check_no_links(project_root)
    profile_path=check_no_links(profile_path);output=check_no_links(output)
    if output.exists() or output==source_root or output.is_relative_to(source_root):
        raise ValueError('new output outside source directory required')
    p=read_json(profile_path)
    required={'schema_version','kind','title_id','content_type','strings','strings_sha256','assets','assets_sha256','packages'}
    if (set(p)!=required or type(p['schema_version']) is not int or p['schema_version']!=1
            or p['kind']!='stfs-dlc-localization' or re.fullmatch('[0-9A-F]{8}',p['title_id']) is None
            or type(p['content_type']) is not int or p['content_type']!=2 or not p['packages']):
        raise ValueError('unsupported DLC build profile')
    tracked={profile_path:sha(profile_path.read_bytes())}
    strings_path=project_file(project_root,p['strings']);assets_path=project_file(project_root,p['assets'])
    for path,key in ((strings_path,'strings_sha256'),(assets_path,'assets_sha256')):
        if sha(path.read_bytes())!=p[key]:
            raise ValueError('DLC dependency SHA256 mismatch')
        tracked[path]=p[key]
    strings,assets=read_json(strings_path),read_json(assets_path)
    if (type(assets.get('schema_version')) is not int or assets['schema_version']!=1
            or assets.get('kind')!='ue3-subtitle-reference-revision'):
        raise ValueError('unsupported DLC asset profile')
    names=[x['name']for x in p['packages']]
    if len(set(names))!=len(names) or any(re.fullmatch('(?:[0-9A-F]{40}|[0-9A-F]{42})',n) is None for n in names):
        raise ValueError('invalid or duplicate DLC container name')
    if {x.name for x in source_root.iterdir()}!=set(names) or assets['container'] not in names:
        raise ValueError('source DLC package inventory mismatch')
    output_files={};reports=[]
    for spec in p['packages']:
        source=check_no_links(source_root/spec['name']);data=source.read_bytes()
        if sha(data)!=spec['input_sha256'] or len(data)!=spec['input_size']:
            raise ValueError('source DLC package identity mismatch')
        tracked[source]=spec['input_sha256'];package=StfsPackage(data);inv=package.inventory()
        if inv['title_id']!=p['title_id'] or inv['content_type']!=f'{p["content_type"]:08X}':
            raise ValueError('DLC title/content identity mismatch')
        spa=package.read_member('spa.bin')
        if sha(spa)!=spec['spa_sha256']:
            raise ValueError('SPA member source SHA256 mismatch')
        changed,spa_report=rebuild(spa,validate_strings(spa,strings));replacements={'spa.bin':changed};asset_reports=[]
        if assets['container']==spec['name']:
            members=set()
            for revision in assets['packages']:
                member=revision['member']
                if member in members or member=='spa.bin':
                    raise ValueError('duplicate or reserved asset member')
                members.add(member);raw=package.read_member(member)
                after,report=patch_package(raw,{k:v for k,v in revision.items()if k!='member'},decoder)
                replacements[member]=after;asset_reports.append(dict(member=member,**report))
        candidate,report=package.rebuild(replacements,expected_sha256=spec['input_sha256'],metadata_updates=spec['metadata'])
        checked=StfsPackage(candidate);after_inv=checked.inventory()
        for e in package.entries:
            if not e.directory and checked.read_member(e.path)!=replacements.get(e.path,package.read_member(e.path)):
                raise ValueError('final DLC independent member readback mismatch')
        relative=f'packages/{p["title_id"]}/{p["content_type"]:08X}/{spec["name"]}'
        output_files[relative]=candidate
        detail=dict(package=spec['name'],source=inv,candidate=after_inv,stfs=report,xdbf=spa_report,assets=asset_reports)
        output_files[f'reports/{spec["name"]}.json']=json_bytes(detail)
        reports.append(dict(name=spec['name'],path=relative,sha256=sha(candidate),size=len(candidate),
                            before_sha256=sha(data),changed_members=len(report['member_changes']),
                            strings=spa_report['changed_strings'],subtitle_fields=sum(len(r['edits'])for r in asset_reports)))
    if any(sha(path.read_bytes())!=expected for path,expected in tracked.items()):
        raise ValueError('DLC input changed during build')
    manifest=dict(schema_version=1,kind='localized-dlc-build',profile_sha256=tracked[profile_path],
                  strings_sha256=p['strings_sha256'],assets_sha256=p['assets_sha256'],packages=reports,
                  originals_unchanged=True,game_launched=False)
    output_files['manifest.json']=json_bytes(manifest)
    output.mkdir(parents=True,exist_ok=False)
    for relative,data in output_files.items():
        path=output/relative;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb')as f:f.write(data)
        if path.read_bytes()!=data:
            raise ValueError('DLC output reopening mismatch')
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True);p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lzx-library',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        result=build(a.source_root,a.profile,a.project_root,a.output,LzxDecoder(a.lzx_library))
        print(json.dumps(dict(packages=len(result['packages']),strings=sum(x['strings']for x in result['packages']),
                             subtitle_fields=sum(x['subtitle_fields']for x in result['packages']),originals_unchanged=True)))
        return 0
    except (OSError,ValueError,KeyError,TypeError)as e:
        print('ERROR: '+str(e));return 1


if __name__=='__main__':raise SystemExit(main())
