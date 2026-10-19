"""Hash-guarded refresh of a prepared local test copy; preserve runs, saves and raw controls."""
from pathlib import Path
import argparse,json,os,sys,tempfile
from .prepare_oneclick_probe import launcher,digest
from .verify_resource_phase import inspect,confined,stable,file_state,sha,unique

def atomic_write(path,data):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
            temporary=Path(f.name);f.write(data)
        if temporary.read_bytes()!=data:raise ValueError('refresh staging mismatch')
        os.replace(temporary,path);temporary=None
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)

def refresh(root,prepared_sha256,packet,manifest_sha256,exe,config,backup,project=None):
    root,packet,backup=map(lambda p:Path(p).resolve(),(root,packet,backup))
    exe,config=Path(exe).resolve(),Path(config).resolve()
    project=Path(project or Path(__file__).resolve().parents[1]).resolve()
    if (backup.exists() or backup.is_relative_to(root) or root.is_relative_to(backup)
            or backup.is_relative_to(packet) or packet.is_relative_to(backup)
            or root.is_relative_to(packet) or packet.is_relative_to(root)):
        raise ValueError('refresh backup must be new and disjoint from test copy and packet')
    prepared=confined(root,'PREPARED.json');old_raw=prepared.read_bytes()
    if sha(old_raw)!=prepared_sha256:raise ValueError('prepared report hash mismatch')
    old=json.loads(old_raw,object_pairs_hook=unique)
    if (old.get('kind')!='prepared-oneclick-warning-probe' or old.get('full_independent_copies') is not True
            or 'runtime_patch' in old or root.is_relative_to(Path(old['source_root']).resolve())):
        raise ValueError('unsupported refresh source or original game target')
    snapshots=[(prepared,file_state(prepared))];new_candidate=None
    for phase in ('candidate','raw-controls'):
        before,s=inspect(old['packet_root'],old['packet_manifest_sha256'],root/phase,phase)
        expected,s2=inspect(packet,manifest_sha256,packet/phase,phase)
        if not before['all_resources_match'] or not expected['all_resources_match']:raise ValueError('refresh preflight resource mismatch')
        if {r['path'] for r in before['resources']}!={r['path'] for r in expected['resources']}:raise ValueError('refresh resource sets differ')
        snapshots.extend(s+s2)
        if phase=='raw-controls':
            unchanged,s3=inspect(packet,manifest_sha256,root/phase,phase)
            if not unchanged['all_resources_match']:raise ValueError('refresh would change raw controls')
            snapshots.extend(s3)
        else:new_candidate=expected
        if digest(root/phase/'default.xex')!=old['game_sha256']:raise ValueError('refresh game identity mismatch')
    for p in (exe,config):
        if not p.is_file():raise ValueError('missing launcher dependency')
        snapshots.append((p,file_state(p)))
    config_sha=digest(config);updates={}
    for row in new_candidate['resources']:
        p=confined(root/'candidate',row['path']);data=confined(packet/'candidate',row['path']).read_bytes()
        if p.read_bytes()!=data:updates[p]=data
    for name,phase in [('开始中文测试.cmd','candidate'),('开始原文对照.cmd','raw-controls')]:
        updates[confined(root,name)]=launcher(Path(sys.executable).resolve(),project,packet,manifest_sha256,exe,config,config_sha,phase)
    report=dict(old,packet_root=str(packet),packet_manifest_sha256=manifest_sha256,config_sha256=config_sha,
                previous_packet_manifest_sha256=old['packet_manifest_sha256'],runs_and_saves_preserved=True,
                game_started=False,game_rendering_verified=False)
    updates[prepared]=(json.dumps(report,ensure_ascii=True,indent=2)+'\n').encode()
    saved={p:p.read_bytes() for p in updates}
    stable(snapshots)
    backup.mkdir(parents=True,exist_ok=False)
    for p,data in saved.items():
        q=confined(backup,p.relative_to(root).as_posix());q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
        if q.read_bytes()!=data:raise ValueError('refresh backup reopening mismatch')
    written=[]
    try:
        for p,data in updates.items():
            if p.read_bytes()!=saved[p]:raise ValueError('test resource changed during refresh')
            atomic_write(p,data);written.append(p)
        for phase in ('candidate','raw-controls'):
            r,_=inspect(packet,manifest_sha256,root/phase,phase)
            if not r['all_resources_match']:raise ValueError('post-refresh verification mismatch')
        if config_sha!=digest(config):raise ValueError('user configuration changed during refresh')
    except Exception:
        for p in reversed(written):
            if p.read_bytes()!=updates[p]:raise ValueError('concurrent modification during rollback')
            atomic_write(p,saved[p])
        raise
    evidence=dict(kind='hash-guarded-test-copy-refresh',root=str(root),changed_files=len(updates),raw_controls_unchanged=True,
                  runs_and_saves_preserved=True,game_started=False,
                  files=[dict(path=p.relative_to(root).as_posix(),before=sha(saved[p]),after=sha(data)) for p,data in updates.items()])
    (backup/'REFRESH.json').write_bytes((json.dumps(evidence,indent=2)+'\n').encode())
    return evidence

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','packet','exe','config','backup'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--prepared-sha256',required=True);p.add_argument('--manifest-sha256',required=True);a=p.parse_args()
    try:
        result=refresh(a.root,a.prepared_sha256,a.packet,a.manifest_sha256,a.exe,a.config,a.backup)
        print(json.dumps(dict(changed_files=result['changed_files'],raw_controls_unchanged=True,runs_and_saves_preserved=True,game_started=False)));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:print('ERROR: '+str(e));return 2

if __name__=='__main__':raise SystemExit(main())
