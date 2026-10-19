"""Prepare full independent drag/drop game copies and user-click launchers.

Preparation never launches a game or installs into the original game directory.
No hardlinks/junctions; launcher --launch appears only in the generated CMD text.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
try:
    from .verify_resource_phase import inspect,stable,confined,hash_value,file_state
except ImportError:
    from verify_resource_phase import inspect,stable,confined,hash_value,file_state


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def quote(value):
    value=str(value)
    if any(c in value for c in '%"\r\n'):raise ValueError('CMD input path contains unsupported expansion/quote characters')
    return '"'+value+'"'


def launcher(python,project,packet,manifest_sha,exe,config,config_sha,phase):
    """Only produce text. This function does not execute the launcher."""
    check=' '.join(map(quote,[python,project/'tools/verify_resource_phase.py','--packet-root',packet,'--manifest-sha256',manifest_sha]))
    run=' '.join(map(quote,[python,project/'tools/launch_xenia.py','--exe',exe,'--config',config,'--config-sha256',config_sha]))
    lines=['@echo off','chcp 65001 >nul','setlocal DisableDelayedExpansion','cd /d "%~dp0"',
        'set "MC2_RUN_ID='+phase+'-%RANDOM%-%RANDOM%"',
        check+' --resource-root "%~dp0'+phase+'" --phase '+phase+' --output "%~dp0runs\\%MC2_RUN_ID%-check.json"',
        'if errorlevel 1 goto failed',run+' --game "%~dp0'+phase+'\\default.xex" --run-dir "%~dp0runs\\%MC2_RUN_ID%" --launch',
        'if errorlevel 1 goto failed','exit /b 0',':failed','echo Resource or launcher verification failed. No automatic fallback was used.','pause','exit /b 1']
    return ('\r\n'.join(lines)+'\r\n').encode('utf8')


def prepare(source_root,packet_root,manifest_sha256,game_sha256,exe,config,output_root,project_root=None,python=None):
    source=Path(source_root).resolve();packet=Path(packet_root).resolve();out=Path(output_root).resolve()
    project=Path(project_root or Path(__file__).resolve().parents[1]).resolve();python=Path(python or sys.executable).resolve()
    exe,config=Path(exe).resolve(),Path(config).resolve()
    if out.exists() or Path(output_root).is_symlink() or out.is_relative_to(source) or source.is_relative_to(out) or out.is_relative_to(packet) or packet.is_relative_to(out):
        raise ValueError('one-click output must be new and disjoint from source and packet')
    for path in [source,packet]:
        if not path.is_dir():raise ValueError('source and packet roots must exist')
    for path in [exe,config,python,project/'tools/launch_xenia.py',project/'tools/verify_resource_phase.py']:
        if not path.is_file():raise ValueError('missing local launcher dependency: '+str(path))
        quote(path)
    quote(packet);hash_value(game_sha256)
    game=confined(source,'default.xex')
    if digest(game)!=game_sha256:raise ValueError('original default.xex SHA256 mismatch')
    original,snap=inspect(packet,manifest_sha256,source,'controls')
    if not original['all_resources_match']:raise ValueError('original game resource bytes differ from packet controls')
    phases=('candidate','raw-controls');phase_snapshots=[];phase_bytes=0
    for phase in phases:
        r,s=inspect(packet,manifest_sha256,packet/phase,phase)
        if not r['all_resources_match']:raise ValueError('packet phase did not match')
        phase_snapshots.extend(s)
        phase_bytes+=sum(row['expected']['size'] for row in r['resources'])
    # Snapshot every source file and reject links before creating output.
    files=[];directories=[]
    for path in sorted(source.rglob('*')):
        if path.is_symlink() or path.is_junction():raise ValueError('linked source members are not supported')
        if path.is_dir():directories.append(path.relative_to(source).as_posix());continue
        if not path.is_file():raise ValueError('non-regular source member')
        relative=path.relative_to(source).as_posix();files.append((relative,path,path.stat().st_size,digest(path)))
    if not files:raise ValueError('empty game source')
    need=sum(size for _,_,size,_ in files)*2+phase_bytes+64*1024*1024
    parent=out.parent
    while not parent.exists():parent=parent.parent
    if shutil.disk_usage(parent).free<need:raise ValueError('insufficient free space for two independent full game copies')
    config_sha=digest(config);extra=[(config,file_state(config)),(exe,file_state(exe)),(python,file_state(python))]
    out.mkdir(parents=True,exist_ok=False);results=[]
    for phase in phases:
        target=out/phase;target.mkdir()
        for name in directories:confined(target,name).mkdir(parents=True,exist_ok=True)
        selected={row['path']:row['expected'] for row in inspect(packet,manifest_sha256,packet/phase,phase)[0]['resources']}
        for relative,old,size,h in files:
            new=confined(target,relative);new.parent.mkdir(parents=True,exist_ok=True)
            origin=confined(packet,phase+'/'+relative) if relative in selected else old
            shutil.copyfile(origin,new)
            expected=selected[relative]['sha256'] if relative in selected else h
            if digest(new)!=expected:raise ValueError('copied game member hash mismatch: '+relative)
            if digest(old)!=h or old.stat().st_size!=size:raise ValueError('source changed during preparation')
        r,s=inspect(packet,manifest_sha256,target,phase)
        if not r['all_resources_match'] or digest(target/'default.xex')!=game_sha256:raise ValueError('prepared game phase failed final check')
        results.append(dict(phase=phase,game=str(target/'default.xex'),resource_count=r['resource_count'],files=len(files),resource_bytes_match=True))
        phase_snapshots.extend(s)
    stable(snap+phase_snapshots+extra)
    for relative,old,size,h in files:
        if digest(old)!=h or old.stat().st_size!=size:raise ValueError('original game changed before publication')
    current={p.relative_to(source).as_posix() for p in source.rglob('*')}
    if current!={name for name,_,_,_ in files}|set(directories):raise ValueError('source member inventory changed before publication')
    # Publish clickable files last, after both complete trees have validated.
    for name,phase in [('开始中文测试.cmd','candidate'),('开始原文对照.cmd','raw-controls')]:
        raw=launcher(python,project,packet,manifest_sha256,exe,config,config_sha,phase);path=out/name;path.write_bytes(raw)
        if path.read_bytes()!=raw:raise ValueError('launcher reopening mismatch')
    report=dict(schema_version=1,kind='prepared-oneclick-warning-probe',source_root=str(source),packet_root=str(packet),
        packet_manifest_sha256=manifest_sha256,game_sha256=game_sha256,config_sha256=config_sha,
        phases=results,full_independent_copies=True,links_created=False,originals_unchanged=True,
        game_started=False,game_rendering_verified=False,deployment_to_original_performed=False)
    raw=(json.dumps(report,ensure_ascii=True,indent=2)+'\n').encode();(out/'PREPARED.json').write_bytes(raw)
    if (out/'PREPARED.json').read_bytes()!=raw:raise ValueError('prepared report reopening mismatch')
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ['source-root','packet-root','exe','config','output-root']:p.add_argument('--'+flag,type=Path,required=True)
    p.add_argument('--manifest-sha256',required=True);p.add_argument('--game-sha256',required=True);a=p.parse_args(argv)
    try:
        r=prepare(a.source_root,a.packet_root,a.manifest_sha256,a.game_sha256,a.exe,a.config,a.output_root)
        print(json.dumps(dict(phases=len(r['phases']),game_started=False,originals_unchanged=True,output=str(a.output_root.resolve())),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
