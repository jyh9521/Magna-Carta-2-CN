"""Hash-guarded refresh of a prepared local test copy; preserve runs, saves and raw controls."""
from pathlib import Path
import argparse,json,os,sys,tempfile
from .prepare_oneclick_probe import launcher,digest
from .verify_resource_phase import inspect,confined,stable,file_state,sha,unique,hash_value,relative,MAX_PACKET_RESOURCES


def audit_refresh_journal(root,backup,journal_sha256):
    from .restore_probe_refresh import audit
    return audit(root,backup,journal_sha256)[0]


def restore_refresh_journal(root,backup,journal_sha256,receipt):
    from .restore_probe_refresh import restore
    return restore(root,backup,journal_sha256,receipt)


def enroll_inventory(plan_path,plan_sha256,root,prepared_sha256,old,new_hash,packet,before,expected):
    """Authorize only an exact additive inventory, backed by original bytes.

    The old default same-set guard is not relaxed. New raw resources must be
    original bytes in both live phases; existing raw controls are checked later.
    """
    p=Path(plan_path).resolve();state=file_state(p)
    if state is None or state['size']>4*1024*1024 or state['sha256']!=hash_value(plan_sha256):
        raise ValueError('enrollment plan SHA256 mismatch or size bound')
    plan=json.loads(p.read_bytes(),object_pairs_hook=unique,
                    parse_constant=lambda _:(_ for _ in ()).throw(ValueError('non-finite enrollment JSON')))
    if (not isinstance(plan,dict) or type(plan.get('schema_version')) is not int or plan['schema_version']!=1
            or plan.get('kind')!='explicit-resource-enrollment' or plan.get('game_rendering_verified') is not False
            or plan.get('prepared_sha256')!=prepared_sha256
            or plan.get('old_packet_manifest_sha256')!=old['packet_manifest_sha256']
            or plan.get('new_packet_manifest_sha256')!=new_hash):raise ValueError('enrollment identity mismatch')
    mpath=confined(packet,'manifest.json');raw=mpath.read_bytes()
    if sha(raw)!=new_hash:raise ValueError('enrollment packet identity mismatch')
    m=json.loads(raw,object_pairs_hook=unique)
    if (m.get('kind')!='offline-disc-locale-raw-comparison' or type(plan.get('disc')) is not int
            or plan['disc']!=m['disc']):raise ValueError('enrollment requires matching disc comparison packet')
    oldset={r['path'] for r in before['resources']};newset={r['path'] for r in expected['resources']}
    additions=newset-oldset;entries=plan.get('additions')
    if not oldset<newset or not isinstance(entries,list) or not 1<=len(entries)<=MAX_PACKET_RESOURCES:
        raise ValueError('enrollment must be bounded and strictly additive')
    names=[relative(r['path']) for r in entries]
    if len(set(n.casefold() for n in names))!=len(names) or set(names)!=additions:
        raise ValueError('enrollment additions do not exactly match new resources')
    snapshots=[(p,state),(mpath,dict(size=len(raw),sha256=new_hash))]
    controls,s=inspect(packet,new_hash,packet/'controls','controls')
    if not controls['all_resources_match']:raise ValueError('enrollment original controls mismatch')
    snapshots.extend(s);originals={r['path']:r['expected'] for r in controls['resources']}
    for row in entries:
        name=row['path'];identity=dict(size=row['original_size'],sha256=hash_value(row['original_sha256']))
        if type(row['original_size']) is not int or identity!=originals[name]:raise ValueError('enrollment original identity mismatch')
        raw_path=confined(packet,'raw-controls/'+name);raw_state=file_state(raw_path)
        if raw_state!=identity:raise ValueError('enrollment new raw control is not original bytes')
        snapshots.append((raw_path,raw_state))
        for phase in ('candidate','raw-controls'):
            target=confined(root/phase,name);current=file_state(target)
            if current!=identity:raise ValueError('enrollment live addition is not original bytes')
            snapshots.append((target,current))
    stable(snapshots);return snapshots,plan

def atomic_write(path,data):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
            temporary=Path(f.name);f.write(data)
        if temporary.read_bytes()!=data:raise ValueError('refresh staging mismatch')
        os.replace(temporary,path);temporary=None
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)

def refresh(root,prepared_sha256,packet,manifest_sha256,exe,config,backup,project=None,
            enrollment=None,enrollment_sha256=None):
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
    if (enrollment is None)!=(enrollment_sha256 is None):raise ValueError('enrollment requires plan and trusted SHA256')
    snapshots=[(prepared,file_state(prepared))];new_candidate=None;enrolled=None
    for phase in ('candidate','raw-controls'):
        before,s=inspect(old['packet_root'],old['packet_manifest_sha256'],root/phase,phase)
        expected,s2=inspect(packet,manifest_sha256,packet/phase,phase)
        if not before['all_resources_match'] or not expected['all_resources_match']:raise ValueError('refresh preflight resource mismatch')
        if {r['path'] for r in before['resources']}!={r['path'] for r in expected['resources']}:
            if enrollment is None:raise ValueError('refresh resource sets differ')
            s4,enrolled=enroll_inventory(enrollment,enrollment_sha256,root,prepared_sha256,old,
                                       manifest_sha256,packet,before,expected)
            snapshots.extend(s4)
        snapshots.extend(s+s2)
        if phase=='raw-controls':
            unchanged,s3=inspect(packet,manifest_sha256,root/phase,phase)
            if not unchanged['all_resources_match']:raise ValueError('refresh would change raw controls')
            snapshots.extend(s3)
        else:new_candidate=expected
        game=root/phase/'default.xex'
        if digest(game)!=old['game_sha256']:raise ValueError('refresh game identity mismatch')
        snapshots.append((game,file_state(game)))
    if enrollment is not None and enrolled is None:raise ValueError('enrollment supplied without resource additions')
    for p in (exe,config):
        if not p.is_file():raise ValueError('missing launcher dependency')
        snapshots.append((p,file_state(p)))
    config_sha=digest(config);updates={}
    content=old.get('content_bundle')
    if content is not None:
        from .content_bundle import read_bundle
        if not isinstance(content,dict) or set(content)!={'bundle','manifest_sha256'}:
            raise ValueError('invalid retained content bundle record')
        read_bundle(content['bundle'],content['manifest_sha256'])
        content_root=Path(content['bundle']).resolve()
        snapshots.extend((p,file_state(p))for p in content_root.rglob('*')if p.is_file())
    checked,checked_states=inspect(packet,manifest_sha256,packet/'candidate','candidate',runtime_envelope=True)
    if not checked['all_runtime_envelopes_match']:raise ValueError('candidate runtime envelopes require normalization')
    snapshots.extend(checked_states)
    for row in new_candidate['resources']:
        p=confined(root/'candidate',row['path']);data=confined(packet/'candidate',row['path']).read_bytes()
        if p.read_bytes()!=data:updates[p]=data
    for name,phase in [('开始中文测试.cmd','candidate'),('开始原文对照.cmd','raw-controls')]:
        kwargs=({'content_bundle':content['bundle'],'content_manifest_sha256':content['manifest_sha256']}
                if content is not None and phase=='candidate' else {})
        updates[confined(root,name)]=launcher(Path(sys.executable).resolve(),project,packet,manifest_sha256,exe,config,config_sha,phase,**kwargs)
    report=dict(old,packet_root=str(packet),packet_manifest_sha256=manifest_sha256,config_sha256=config_sha,
                previous_packet_manifest_sha256=old['packet_manifest_sha256'],runs_and_saves_preserved=True,
                game_started=False,game_rendering_verified=False)
    if enrolled is not None:
        report['enrollment_plan_sha256']=enrollment_sha256
        report['enrolled_resources']=[r['path'] for r in enrolled['additions']]
        report['phases']=[dict(p,resource_count=len(new_candidate['resources'])) for p in old['phases']]
    updates[prepared]=(json.dumps(report,ensure_ascii=True,indent=2)+'\n').encode()
    if enrolled is not None:
        # Refuse file/directory links or hardlinks before touching a player copy.
        requested=[root/n for n in ('PREPARED.json','开始中文测试.cmd','开始原文对照.cmd')]
        requested.extend(root/phase/r['path'] for phase in ('candidate','raw-controls') for r in new_candidate['resources'])
        for p in requested:
            cursor=p
            while cursor!=root:
                if cursor.is_symlink() or getattr(cursor,'is_junction',lambda:False)():raise ValueError('linked refresh target')
                cursor=cursor.parent
        for p in updates:
            if p.is_symlink() or p.stat().st_nlink!=1:raise ValueError('linked refresh target')
            if p.is_relative_to(root/'raw-controls'):raise ValueError('raw control write forbidden')
    saved={p:p.read_bytes() for p in updates}
    stable(snapshots)
    backup.mkdir(parents=True,exist_ok=False)
    for p,data in saved.items():
        q=confined(backup,p.relative_to(root).as_posix());q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
        if q.read_bytes()!=data:raise ValueError('refresh backup reopening mismatch')
    evidence=dict(kind='hash-guarded-test-copy-refresh',root=str(root),changed_files=len(updates),raw_controls_unchanged=True,
                  runs_and_saves_preserved=True,game_started=False,status='prepared',
                  files=[dict(path=p.relative_to(root).as_posix(),before=sha(saved[p]),after=sha(data)) for p,data in updates.items()])
    if enrolled is not None:evidence.update(enrollment_plan_sha256=enrollment_sha256,enrolled_resource_count=len(enrolled['additions']))
    journal=backup/'REFRESH.json';journal.write_bytes((json.dumps(evidence,indent=2)+'\n').encode())
    if json.loads(journal.read_bytes())!=evidence:raise ValueError('refresh journal reopening mismatch')
    written=[]
    try:
        for p,data in updates.items():
            if p.read_bytes()!=saved[p]:raise ValueError('test resource changed during refresh')
            written.append(p);atomic_write(p,data)
        for phase in ('candidate','raw-controls'):
            r,_=inspect(packet,manifest_sha256,root/phase,phase)
            if not r['all_resources_match']:raise ValueError('post-refresh verification mismatch')
        if config_sha!=digest(config):raise ValueError('user configuration changed during refresh')
        # Snapshots outside the explicit write set must remain unchanged.
        stable([(p,s) for p,s in snapshots if p not in updates])
        evidence['status']='committed'
        atomic_write(journal,(json.dumps(evidence,indent=2)+'\n').encode())
        if json.loads(journal.read_bytes())!=evidence:raise ValueError('refresh committed journal mismatch')
    except Exception:
        for p in reversed(written):
            if p.read_bytes()==saved[p]:continue
            if p.read_bytes()!=updates[p]:raise ValueError('concurrent modification during rollback')
            atomic_write(p,saved[p])
        evidence['status']='rolled-back'
        atomic_write(journal,(json.dumps(evidence,indent=2)+'\n').encode())
        raise
    return evidence

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','packet','exe','config','backup'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--prepared-sha256',required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--enrollment',type=Path);p.add_argument('--enrollment-sha256');a=p.parse_args()
    try:
        result=refresh(a.root,a.prepared_sha256,a.packet,a.manifest_sha256,a.exe,a.config,a.backup,
                       enrollment=a.enrollment,enrollment_sha256=a.enrollment_sha256)
        print(json.dumps(dict(changed_files=result['changed_files'],raw_controls_unchanged=True,runs_and_saves_preserved=True,game_started=False)));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:print('ERROR: '+str(e));return 2

if __name__=='__main__':raise SystemExit(main())
