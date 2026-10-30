"""Compose current dual-disc release candidates without copying complete games.

Replays existing hash-bound Disc-2 resource journals, then explicitly adopts
the latest shared Disc-1 resources only when original path AND digest match.
Disc-specific resources remain independent. TOCs are rebuilt from each original.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .disc_inventory import Disc
from .installer_core import sha_file, safe_relative
from .installer_delta import digest
from .runtime_package import normalize_package
from .runtime_envelope import require_raw_envelope
from .ue3_package import LzxDecoder
from .update_resource_sizes import update_sizes_reversible


def locked(path, expected):
    path=Path(path).resolve()
    if sha_file(path)!=expected:raise ValueError('source lock mismatch: '+str(path))
    return json.loads(path.read_text(encoding='utf-8'))


def prepare(spec_path, expected, output):
    spec=locked(spec_path,expected);root=Path(spec['project_root']).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError('preparation output must be new')
    output.mkdir(parents=True)
    decoder=LzxDecoder(root/spec['lzx']['file'])
    if sha_file(root/spec['lzx']['file'])!=spec['lzx']['sha256']:raise ValueError('LZX identity mismatch')
    maps=[];originals=[];provenance=[]
    for n in (1,2):
        item=spec[f'disc{n}'];packet=root/item['packet'];manifest=locked(packet/'manifest.json',item['manifest_sha256'])
        provenance.append(dict(kind='packet',disc=n,sha256=item['manifest_sha256']))
        maps.append({e['path']:dict(path=e['path'],file=str(packet/'candidate'/e['path']),sha256=e['candidate_sha256']) for e in manifest['resources']})
        inv=locked(root/item['inventory'],item['inventory_sha256'])
        originals.append({e['path']:e for e in inv['entries'] if not e['directory']})
    # The final file inventory closes the journal chain; no ISO is regenerated.
    journal_path=root/spec['disc2']['journal'];journal=locked(journal_path,spec['disc2']['journal_sha256'])
    expected_inventory={e['path']:e for e in journal['file_inventory']}
    expected_inventory.update({e['path']:e for e in journal['changes']})
    chain=[];seen=set()
    while journal.get('kind')=='incremental-runtime-image-repair':
        if str(journal_path) in seen:raise ValueError('cyclic journal chain')
        seen.add(str(journal_path));chain.append((journal_path,journal));ref=journal['previous_report']
        journal_path=Path(ref['path']);journal=locked(journal_path,ref['sha256'])
    if journal['packet']['manifest_sha256']!=spec['disc2']['manifest_sha256']:raise ValueError('journal base packet mismatch')
    for path,plan in reversed(chain):
        provenance.append(dict(kind='resource-journal',disc=2,sha256=sha_file(path)))
        for entry in plan['changes']:
            name=safe_relative(entry['path'])
            maps[1][name]=dict(path=name,file=str(path.parent/entry['file']),sha256=entry['sha256'])
    for name,entry in maps[1].items():
        if entry['sha256']!=expected_inventory[name]['sha256']:raise ValueError('final Disc 2 journal inventory mismatch: '+name)
    shared=[]
    toc='MC2Game/Xbox360TOC.txt'
    for name,entry in maps[0].items():
        if name==toc or name not in originals[1]:continue
        if originals[0][name]['sha256']==originals[1][name]['sha256']:
            maps[1][name]=dict(entry);shared.append(name)
    recipe=dict(version=spec['version'],title_id=spec['title_id'],output_name=spec['output_name'],
                tools={k:{**v,'file':str(root/v['file'])} for k,v in spec['tools'].items()},
                usage=str(root/spec['usage']),discs=[],dlc=[],provenance=provenance)
    cache={}
    for n,candidates in enumerate(maps,1):
        normalized=[]
        for i,(name,entry) in enumerate(sorted(candidates.items())):
            if name==toc:continue
            path=Path(entry['file']);data=path.read_bytes()
            if digest(data)!=entry['sha256']:raise ValueError('candidate changed: '+str(path))
            if entry['sha256']==originals[n-1][name]['sha256']:continue
            if name.lower().endswith('.xxx'):
                if entry['sha256'] in cache:entry=cache[entry['sha256']] | {'path':name}
                else:
                    old_hash=entry['sha256']
                    try:require_raw_envelope(data)
                    except ValueError:
                        result,_=normalize_package(data,old_hash,decoder)
                        result+=bytes((-len(result))%32768)
                        require_raw_envelope(result)
                        target=output/f'Disc{n}'/name;target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(result);entry=dict(path=name,file=str(target),sha256=digest(result));data=result
                    cache[old_hash]=entry
            normalized.append(entry)
            if i%75==0:print(f'PREPARE {n} {i+1}/{len(candidates)}',flush=True)
        iso=root/spec[f'disc{n}']['iso'];disc=Disc(iso);record=next(e for e in disc.inventory() if e['path']==toc)
        source=disc.read(record['offset'],record['size'])
        changes=[]
        for entry in normalized:
            size=Path(entry['file']).stat().st_size;old=originals[n-1][entry['path']]['size']
            if old!=size:changes.append(dict(path=entry['path'],expected_size=old,new_size=size))
        result,proof=update_sizes_reversible(source,digest(source),changes)
        target=output/f'Disc{n}'/toc;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
        normalized.append(dict(path=toc,file=str(target),sha256=digest(result)))
        recipe['discs'].append(dict(iso=str(iso),sha256=spec[f'disc{n}']['iso_sha256'],resources=normalized))
    for item in spec['dlc']:
        recipe['dlc'].append({**item,'source':str(root/item['source']),'candidate':str(root/item['candidate'])})
    (output/'shared-provenance.json').write_text(json.dumps(dict(shared_count=len(shared),paths=shared),indent=2)+'\n')
    raw=(json.dumps(recipe,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode()
    (output/'recipe.json').write_bytes(raw)
    print(json.dumps(dict(recipe=str(output/'recipe.json'),sha256=digest(raw),resources=[len(d['resources']) for d in recipe['discs']])),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prepare(a.spec,a.sha256,a.output)


if __name__=='__main__':main()
