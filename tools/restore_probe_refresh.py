"""Audit or explicitly restore a hash-pinned local refresh journal.

Only journaled candidate resource bytes and the three legacy entry metadata
files are eligible. Raw controls, configuration, executables, runs and saves
are never restored. No game launch, new game tree or automatic forward replay.
"""
from pathlib import Path
import argparse,json
from .verify_resource_phase import sha,hash_value,relative,confined,file_state,stable,unique
from .refresh_oneclick_probe import atomic_write

METADATA={'PREPARED.json','开始中文测试.cmd','开始原文对照.cmd'}
PROTECTED={'runs','storage','saves','save','config','configuration'}
SUFFIXES={'.xex','.exe','.dll','.sav','.save','.toml','.ini','.cmd','.bat','.ps1','.sh'}


def unlinked(path,root):
    cursor=path
    while True:
        if cursor.is_symlink() or getattr(cursor,'is_junction',lambda:False)():raise ValueError('linked journal path')
        if cursor==root:break
        if not cursor.is_relative_to(root):raise ValueError('journal path outside root')
        cursor=cursor.parent
    if path.is_file() and path.stat().st_nlink!=1:raise ValueError('hardlinked journal file')


def eligible(name):
    relative(name)
    if name in METADATA:return
    p=Path(name)
    if (not name.startswith('candidate/') or len(p.parts)<3 or p.suffix.lower() in SUFFIXES
            or any(part.casefold() in PROTECTED for part in p.parts)
            or p.name.casefold()=='default.xex'):raise ValueError('journal contains protected or non-resource target')


def audit(root,backup,journal_sha256):
    for p in (Path(root),Path(backup)):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('linked journal root')
    root,backup=Path(root).resolve(),Path(backup).resolve()
    if not root.is_dir() or not backup.is_dir() or root.is_relative_to(backup) or backup.is_relative_to(root):
        raise ValueError('journal roots must exist and be disjoint')
    journal=confined(backup,'REFRESH.json');unlinked(journal,backup);state=file_state(journal)
    if state is None or state['size']>4*1024*1024 or state['sha256']!=hash_value(journal_sha256):
        raise ValueError('refresh journal SHA256 mismatch or size bound')
    m=json.loads(journal.read_bytes(),object_pairs_hook=unique,
                 parse_constant=lambda _:(_ for _ in ()).throw(ValueError('non-finite journal JSON')))
    if (not isinstance(m,dict) or m.get('kind')!='hash-guarded-test-copy-refresh'
            or not isinstance(m.get('root'),str) or not Path(m['root']).is_absolute() or Path(m['root']).resolve()!=root
            or m.get('status') not in ('prepared','committed','rolled-back')
            or m.get('raw_controls_unchanged') is not True or m.get('runs_and_saves_preserved') is not True
            or m.get('game_started') is not False):raise ValueError('unsupported refresh journal identity or state')
    rows=m.get('files')
    if (not isinstance(rows,list) or not 3<=len(rows)<=35 or type(m.get('changed_files')) is not int
            or m['changed_files']!=len(rows)):raise ValueError('journal file inventory outside bound')
    seen=set();snapshots=[(journal,state)];operations=[];results=[]
    for r in rows:
        name=r['path'];eligible(name)
        if name.casefold() in seen:raise ValueError('duplicate journal target')
        seen.add(name.casefold());before=hash_value(r['before']);after=hash_value(r['after'])
        # Check unresolved paths, then confine resolved ones to the same roots.
        unlinked(root/name,root);unlinked(backup/name,backup)
        target=confined(root,name);saved=confined(backup,name);current=file_state(target);original=file_state(saved)
        if original is None or original['sha256']!=before:raise ValueError('journal backup before-hash mismatch')
        kind='conflict' if current is None else ('before' if current['sha256']==before else 'after' if current['sha256']==after else 'conflict')
        snapshots.extend([(saved,original),(target,current)])
        results.append(dict(path=name,state=kind,before_sha256=before,after_sha256=after,current=current))
        operations.append((target,saved,before,after,current))
    if not {s.casefold() for s in METADATA}<=seen:raise ValueError('journal missing required entry metadata')
    old_path=confined(backup,'PREPARED.json');old=json.loads(old_path.read_bytes(),object_pairs_hook=unique)
    if (old.get('kind')!='prepared-oneclick-warning-probe' or old.get('full_independent_copies') is not True
            or 'runtime_patch' in old or not isinstance(old.get('source_root'),str)):
        raise ValueError('unsupported original prepared metadata')
    source=Path(old['source_root']).resolve()
    if root.is_relative_to(source) or source.is_relative_to(root):raise ValueError('journal target overlaps original source')
    stable(snapshots);conflicts=sum(r['state']=='conflict' for r in results)
    report=dict(schema_version=1,kind='read-only-refresh-journal-audit',root=str(root),backup=str(backup),journal_sha256=journal_sha256,
                journal_status=m['status'],files=results,before_count=sum(r['state']=='before' for r in results),
                after_count=sum(r['state']=='after' for r in results),conflict_count=conflicts,restorable=not conflicts,
                game_started=False,resource_writes_performed=False,game_rendering_verified=False)
    return report,operations,snapshots


def output_path(path,root,backup):
    p=Path(path)
    if p.exists() or p.is_symlink():raise ValueError('audit/restore output must be new')
    p=p.resolve()
    if p.is_relative_to(root) or p.is_relative_to(backup):raise ValueError('audit/restore output must be outside both roots')
    return p


def emit_new(path,report):
    data=(json.dumps(report,ensure_ascii=True,indent=2,sort_keys=True)+'\n').encode()
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data)
    if path.read_bytes()!=data:raise ValueError('audit/restore output reopening mismatch')


def restore(root,backup,journal_sha256,receipt):
    report,ops,snapshots=audit(root,backup,journal_sha256)
    root,backup=Path(root).resolve(),Path(backup).resolve();receipt=output_path(receipt,root,backup)
    if not report['restorable']:raise ValueError('journal target conflict; no restoration written')
    updates={p:s.read_bytes() for p,s,b,a,c in ops if c['sha256']!=b}
    observed={p:p.read_bytes() for p in updates}
    for p,s,b,a,c in ops:
        if sha(s.read_bytes())!=b or (p in observed and sha(observed[p])!=c['sha256']):raise ValueError('restore input changed')
    stable(snapshots);written=[]
    try:
        for p,data in updates.items():
            if p.read_bytes()!=observed[p]:raise ValueError('target changed before restore')
            written.append(p);atomic_write(p,data)
        stable([(p,s) for p,s in snapshots if p not in updates])
        for p,s,b,a,c in ops:
            if sha(p.read_bytes())!=b:raise ValueError('restored target before-hash mismatch')
        result=dict(schema_version=1,kind='hash-guarded-refresh-restore-receipt',root=str(root),backup=str(backup),
                    journal_sha256=journal_sha256,restored_files=len(updates),already_before=report['before_count'],
                    all_journal_targets_before=True,raw_controls_written=False,game_started=False,game_rendering_verified=False)
        emit_new(receipt,result)
    except Exception:
        for p in reversed(written):
            current=p.read_bytes()
            if current==observed[p]:continue
            if current!=updates[p]:raise ValueError('concurrent modification during restore reversal')
            atomic_write(p,observed[p])
        raise
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('audit','restore'),required=True)
    for key in ('root','backup','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--journal-sha256',required=True);a=p.parse_args(argv)
    try:
        if a.mode=='restore':result=restore(a.root,a.backup,a.journal_sha256,a.output);code=0
        else:
            out=output_path(a.output,a.root.resolve(),a.backup.resolve());result,_,snapshots=audit(a.root,a.backup,a.journal_sha256)
            stable(snapshots);emit_new(out,result);stable(snapshots);code=0 if result['restorable'] else 1
        print(json.dumps(dict(mode=a.mode,restorable=result.get('restorable',True),restored_files=result.get('restored_files',0),
                             game_started=False),sort_keys=True));return code
    except (OSError,ValueError,KeyError,TypeError) as e:print('ERROR: '+str(e));return 2


if __name__=='__main__':raise SystemExit(main())
