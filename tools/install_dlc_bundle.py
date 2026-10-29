"""Incremental DLC-only install and guarded rollback, without launching games."""
import argparse
import json
from pathlib import Path
import sys

from .build_dlc_localization import json_bytes,read_json
from .content_bundle import check_no_links,read_bundle,_validate_manifest
from .prepare_oneclick_probe import launcher
from .refresh_oneclick_probe import atomic_write
from .xdbf_strings import sha


def state(path):
    path=check_no_links(path)
    if not path.exists():return None
    if not path.is_file():raise ValueError('DLC transaction target is not a regular file')
    return sha(path.read_bytes())


def install(bundle,manifest_sha256,content_root,test_root,backup,prepared_sha256,project,exe,config):
    bundle,content_root,test_root,backup,project,exe,config=map(check_no_links,(bundle,content_root,test_root,backup,project,exe,config))
    if (backup.exists() or not content_root.is_dir() or not test_root.is_dir()
            or content_root.is_relative_to(test_root) or test_root.is_relative_to(content_root)
            or any(backup.is_relative_to(r)or r.is_relative_to(backup) for r in (content_root,test_root,bundle))):
        raise ValueError('new disjoint DLC backup and existing target roots required')
    manifest,payloads=read_bundle(bundle,manifest_sha256)
    prepared=test_root/'PREPARED.json'
    if state(prepared)!=prepared_sha256:raise ValueError('prepared identity mismatch')
    old=read_json(prepared)
    if old.get('kind')!='prepared-oneclick-warning-probe' or 'runtime_patch'in old or 'content_bundle'in old:
        raise ValueError('unsupported prepared entry or DLC already bound')
    if state(config)!=old['config_sha256']:raise ValueError('configuration changed; retain and review current configuration')
    args=[Path(sys.executable).resolve(),project,Path(old['packet_root']),old['packet_manifest_sha256'],exe,config,old['config_sha256'],'candidate']
    cmd=test_root/'开始中文测试.cmd'
    if cmd.read_bytes()!=launcher(*args):raise ValueError('existing launcher differs from prepared template')
    target_bundle=test_root/'dlc-content'
    if target_bundle.exists():raise ValueError('DLC bundle target already exists')
    binding=dict(bundle=str(target_bundle),manifest_sha256=manifest_sha256)
    updated=dict(old,content_bundle=binding)
    changes=[('test','PREPARED.json',json_bytes(updated)),('test','开始中文测试.cmd',launcher(*args,
             content_bundle=target_bundle,content_manifest_sha256=manifest_sha256))]
    changes.append(('test','dlc-content/manifest.json',(bundle/'manifest.json').read_bytes()))
    for relative,data in payloads.items():
        if (content_root/relative).exists():raise ValueError('shared DLC target already exists')
        changes.extend([('content',relative,data),('test','dlc-content/files/'+relative,data)])
    roots=dict(content=content_root,test=test_root);rows=[];saved={};dirs=set()
    for index,(role,name,data)in enumerate(changes):
        path=check_no_links(roots[role]/name);before=path.read_bytes()if path.exists()else None
        saved[index]=before
        rows.append(dict(role=role,path=name,before=sha(before)if before is not None else None,after=sha(data),backup=str(index)+'.bin'))
        parent=path.parent
        while not parent.exists():dirs.add((role,parent.relative_to(roots[role]).as_posix()));parent=parent.parent
    if state(prepared)!=prepared_sha256:raise ValueError('prepared changed during preflight')
    backup.mkdir(parents=True,exist_ok=False)
    for index,data in saved.items():
        if data is not None:
            path=backup/(str(index)+'.bin');path.write_bytes(data)
            if path.read_bytes()!=data:raise ValueError('DLC backup reopening mismatch')
    journal=dict(schema_version=1,kind='incremental-dlc-install',roots={k:str(v)for k,v in roots.items()},
                 manifest=manifest,files=rows,created_dirs=[dict(role=r,path=p)for r,p in sorted(dirs)],game_launched=False)
    jp=backup/'INSTALL.json';jp.write_bytes(json_bytes(journal))
    if read_json(jp)!=journal:raise ValueError('journal reopening mismatch')
    written=[]
    try:
        for index,(role,name,data)in enumerate(changes):
            path=roots[role]/name
            if state(path)!=rows[index]['before']:raise ValueError('DLC target changed during install')
            path.parent.mkdir(parents=True,exist_ok=True);atomic_write(path,data);written.append(index)
        read_bundle(target_bundle,manifest_sha256)
        if any(state(roots[r['role']]/r['path'])!=r['after']for r in rows):raise ValueError('DLC install readback mismatch')
        if state(config)!=old['config_sha256']:raise ValueError('configuration changed during install')
    except Exception:
        rollback(backup,sha(jp.read_bytes()))
        raise
    return dict(files=len(rows),journal_sha256=sha(jp.read_bytes()),game_launched=False)


def rollback(backup,journal_sha256,content_root=None,test_root=None):
    backup=check_no_links(backup);jp=backup/'INSTALL.json'
    if state(jp)!=journal_sha256:raise ValueError('DLC journal SHA256 mismatch')
    j=read_json(jp)
    if j.get('kind')!='incremental-dlc-install' or type(j.get('schema_version'))is not int or j['schema_version']!=1:
        raise ValueError('unsupported DLC journal')
    manifest=j['manifest'];_validate_manifest(manifest)
    allowed={('content',r['path'])for r in manifest['files']}|{('test','dlc-content/files/'+r['path'])for r in manifest['files']}
    allowed|={('test',n)for n in ('PREPARED.json','开始中文测试.cmd','dlc-content/manifest.json')}
    rows=j['files'];keys=[(r['role'],r['path'])for r in rows]
    if len(set(keys))!=len(keys) or set(keys)!=allowed:raise ValueError('unexpected DLC journal target inventory')
    roots=dict(content=check_no_links(content_root or Path(j['roots']['content'])),test=check_no_links(test_root or Path(j['roots']['test'])))
    operations=[];valid_dirs=set()
    for i,row in enumerate(rows):
        path=check_no_links(roots[row['role']]/row['path'])
        if row['backup']!=str(i)+'.bin':raise ValueError('invalid DLC backup member')
        data=check_no_links(backup/row['backup']).read_bytes()if row['before']is not None else None
        if data is not None and sha(data)!=row['before']:raise ValueError('DLC backup SHA256 mismatch')
        current=state(path)
        if current not in (row['before'],row['after']):raise ValueError('DLC rollback target modified by another writer')
        operations.append((path,current,row,data))
        parent=Path(row['path']).parent
        while parent!=Path('.'):
            valid_dirs.add((row['role'],parent.as_posix()));parent=parent.parent
    directories=[(d['role'],d['path'])for d in j['created_dirs']]
    if len(set(directories))!=len(directories) or not set(directories)<=valid_dirs:raise ValueError('invalid created-directory journal')
    for role,name in directories:check_no_links(roots[role]/name)
    for path,current,row,data in reversed(operations):
        if current==row['before']:continue
        if state(path)!=current:raise ValueError('DLC rollback concurrent modification')
        if data is None:path.unlink()
        else:atomic_write(path,data)
    for role,name in sorted(directories,key=lambda r:len(r[1]),reverse=True):
        path=roots[role]/name
        if path.is_dir() and not any(path.iterdir()):path.rmdir()
    if any(state(path)!=row['before']for path,_,row,_ in operations):raise ValueError('DLC rollback readback mismatch')
    return dict(restored_files=len(rows),restored_pre_dlc_status=True,game_launched=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='mode',required=True)
    a=s.add_parser('install')
    for key in ('bundle','content-root','test-root','backup','project','exe','config'):a.add_argument('--'+key,type=Path,required=True)
    for key in ('manifest-sha256','prepared-sha256'):a.add_argument('--'+key,required=True)
    b=s.add_parser('rollback');b.add_argument('--backup',type=Path,required=True);b.add_argument('--journal-sha256',required=True)
    b.add_argument('--content-root',type=Path);b.add_argument('--test-root',type=Path)
    args=vars(p.parse_args());mode=args.pop('mode')
    try:print(json.dumps((install if mode=='install'else rollback)(**args)));return 0
    except (ValueError,OSError,KeyError,TypeError)as e:print('ERROR: '+str(e));return 1

if __name__=='__main__':raise SystemExit(main())
