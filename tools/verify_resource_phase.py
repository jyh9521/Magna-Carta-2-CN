"""Standalone, read-only resource phase checks. Never install, launch or test a game.

A caller supplies a trusted packet-manifest hash, an exact phase and an explicit
resource root. Only allowlisted resource bytes are read; unrelated files and
configuration are neither enumerated nor touched. Python standard library only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_PACKET_RESOURCES=512
MAX_FILE=512*1024*1024
PHASES=('controls','raw-controls','candidate')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def hash_value(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('expected lowercase SHA256')
    return value


def unique(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('duplicate manifest JSON key')
        out[key]=value
    return out


def relative(value):
    if (not isinstance(value,str) or not value or '\\' in value or ':' in value or value.startswith('/')
            or any(p in ('','.','..') or p.endswith(('.', ' ')) for p in value.split('/'))):
        raise ValueError('invalid relative resource path')
    return value


def confined(root,name):
    target=(root/relative(name)).resolve()
    if not target.is_relative_to(root):raise ValueError('resource path escapes explicit root')
    return target


def file_state(path):
    """None is missing, never a positive result; reject directories and huge files."""
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size>MAX_FILE:raise ValueError('resource must be a bounded regular file')
    size=0;h=hashlib.sha256()
    with path.open('rb') as stream:
        for raw in iter(lambda:stream.read(1024*1024),b''):
            size+=len(raw)
            if size>MAX_FILE:raise ValueError('resource grew beyond size bound')
            h.update(raw)
    return dict(size=size,sha256=h.hexdigest())


def stable(snapshots):
    for path,expected in snapshots:
        if file_state(path)!=expected:raise ValueError('resource or packet changed during check')


def inspect(packet_root,manifest_sha256,resource_root,phase):
    if phase not in PHASES:raise ValueError('unsupported resource phase')
    packet=Path(packet_root).resolve();game=Path(resource_root).resolve()
    if not packet.is_dir() or not game.is_dir():raise ValueError('packet and resource roots must exist')
    manifest_path=confined(packet,'manifest.json')
    if manifest_path.stat().st_size>4*1024*1024:raise ValueError('manifest exceeds size bound')
    raw=manifest_path.read_bytes()
    if sha(raw)!=hash_value(manifest_sha256):raise ValueError('packet manifest SHA256 mismatch')
    m=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('non-finite manifest JSON')))
    if (not isinstance(m,dict) or type(m.get('schema_version')) is not int or m['schema_version']!=1
            or m.get('kind') not in ('offline-font-route-probe','offline-disc-locale-raw-comparison') or m.get('deployment_performed') is not False
            or m.get('game_rendering_verified') is not False):raise ValueError('unsupported packet manifest')
    comparison=m['kind']=='offline-disc-locale-raw-comparison'
    if comparison:
        if (type(m.get('disc')) is not int or m['disc'] not in (1,2) or m.get('raw_package_outputs') is not True
                or m.get('raw_control_method')!='source-derived-uncompressed-fonts-original-text-disc-toc'
                or m.get('unknown_control_syntax_resolved') is not False):
            raise ValueError('invalid disc comparison contract')
        hash_value(m.get('composition_manifest_sha256'));hash_value(m.get('comparison_plan_canonical_sha256'))
    resources=m.get('resources');members=m.get('member_sha256')
    if not isinstance(resources,list) or not 1<=len(resources)<=MAX_PACKET_RESOURCES or not isinstance(members,dict):raise ValueError('invalid packet resource inventory')
    if phase=='raw-controls' and m.get('raw_package_outputs') is not True:raise ValueError('packet has no declared raw control phase')
    snapshots=[(manifest_path,dict(size=len(raw),sha256=sha(raw)))];seen=set();rows=[];aliases=set()
    for row in resources:
        name=relative(row['path']);fold=name.casefold()
        if fold in seen:raise ValueError('duplicate case-insensitive resource path')
        seen.add(fold);member=phase+'/'+name;expected_hash=hash_value(members[member]);source=confined(packet,member)
        expected=file_state(source)
        if expected is None or expected['sha256']!=expected_hash:raise ValueError('packet phase member SHA256 mismatch')
        if phase in ('candidate','controls') or comparison:
            key={'candidate':'candidate','controls':'original','raw-controls':'raw'}[phase]
            if hash_value(row[key+'_sha256'])!=expected_hash or type(row[key+'_size']) is not int or row[key+'_size']!=expected['size']:
                raise ValueError('packet resource row/member contract mismatch')
        target=confined(game,name)
        if target in aliases:raise ValueError('multiple resource paths alias one file')
        aliases.add(target);actual=file_state(target)
        status='missing' if actual is None else ('matched' if actual==expected else 'mismatch')
        snapshots.extend([(source,expected),(target,actual)])
        rows.append(dict(path=name,status=status,expected=expected,actual=actual))
    stable(snapshots)
    matched=sum(r['status']=='matched' for r in rows)
    result=dict(schema_version=1,kind='read-only-resource-phase-check',packet_manifest_sha256=sha(raw),phase=phase,
        packet_root=str(packet),resource_root=str(game),
        resource_count=len(rows),matched_count=matched,all_resources_match=matched==len(rows),resources=rows,
        scope='only the declared packet resource bytes; not execution, rendering or runtime behavior',
        game_rendering_verified=False,game_started=False,resource_writes_performed=False,deployment_performed=False)
    return result,snapshots


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet-root',type=Path,required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--resource-root',type=Path,required=True);p.add_argument('--phase',choices=PHASES,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv);created=False;data=None
    try:
        output=a.output.resolve();roots=[a.packet_root.resolve(),a.resource_root.resolve()]
        if a.output.exists() or a.output.is_symlink() or any(output.is_relative_to(root) for root in roots):
            raise ValueError('phase report must be new and outside packet/resource roots')
        result,snapshots=inspect(a.packet_root,a.manifest_sha256,a.resource_root,a.phase)
        data=(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf8')
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open('xb') as stream:created=True;stream.write(data)
        if output.read_bytes()!=data:raise ValueError('phase report reopening mismatch')
        stable(snapshots)
        code=0 if result['all_resources_match'] else 1
        print(json.dumps(dict(phase=result['phase'],matched=result['matched_count'],resources=result['resource_count'],
            result='resource-bytes-match' if code==0 else 'resource-bytes-mismatch',game_started=False),sort_keys=True));return code
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if created:
            try:
                if not a.output.is_symlink() and a.output.read_bytes()==data:a.output.unlink()
            except OSError:pass
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
