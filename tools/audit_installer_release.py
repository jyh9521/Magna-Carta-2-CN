"""Compare an actual one-file installer with a hash-locked current recipe.

This is an offline payload/version audit, not game or full-install acceptance.
PyInstaller and pefile are loaded only for the native EXE audit, not source tests.
"""
import argparse
import hashlib
import json
from pathlib import Path


def compare_manifest(manifest, recipe):
    failures = []; checked = 0
    for key in ('version', 'title_id', 'output_name'):
        if manifest.get(key) != recipe.get(key):failures.append(key)
    if len(manifest.get('discs', [])) != 2 or len(recipe['discs']) != 2:
        raise ValueError('two ordered discs required')
    for n,(actual,want) in enumerate(zip(manifest['discs'],recipe['discs']),1):
        if actual['sha256'] != want['sha256']:failures.append(f'disc{n}:original identity')
        files = {r['path']:r for r in actual['files']}
        if len(files) != len(actual['files']):raise ValueError('duplicate release member')
        seen = set()
        for r in want['resources']:
            if r['path'] in seen:raise ValueError('duplicate recipe resource')
            seen.add(r['path']);checked += 1;a=files.get(r['path'])
            if a is None or a.get('output_sha256',a['sha256']) != r['sha256']:
                failures.append(f'disc{n}:'+r['path'])
    actual={r['name']:r for r in manifest['dlc']};wanted={r['name']:r for r in recipe['dlc']}
    if len(actual)!=len(manifest['dlc']) or len(wanted)!=len(recipe['dlc']):raise ValueError('duplicate DLC')
    if actual.keys()!=wanted.keys():failures.append('DLC inventory')
    for name,r in wanted.items():
        a=actual.get(name)
        if a is None or any(a.get(k)!=r[k] for k in ('sha256','output_sha256')):
            failures.append('DLC:'+name)
    return dict(resources=checked,dlc=len(wanted),failures=failures,passed=not failures)


def pe_version(data):
    import pefile
    pe=pefile.PE(data=data,fast_load=True)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        info=pe.VS_FIXEDFILEINFO[0]
        def quad(a,b):return [a>>16,a&65535,b>>16,b&65535]
        strings=[]
        for group in pe.FileInfo:
            for block in group:
                for table in getattr(block,'StringTable',[]):
                    strings.append({k.decode('utf8'):v.decode('utf8')for k,v in table.entries.items()
                                    if k in (b'FileVersion',b'ProductVersion')})
        return dict(file_numeric=quad(info.FileVersionMS,info.FileVersionLS),
                    product_numeric=quad(info.ProductVersionMS,info.ProductVersionLS),strings=strings)
    finally:pe.close()


def audit(installer, recipe):
    from PyInstaller.archive.readers import CArchiveReader
    from .installer_singlefile import sha_file
    installer=Path(installer);archive=CArchiveReader(str(installer))
    def member(relative):return archive.extract('payload\\'+relative.replace('/','\\'))
    raw=member('patch/manifest.json');manifest=json.loads(raw);inventory=json.loads(member('release-files.json'))
    result=compare_manifest(manifest,recipe);issues=list(result['failures'])
    if hashlib.sha256(raw).hexdigest()!=inventory['manifest_sha256']:issues.append('embedded manifest identity')
    expected_members={'payload/'+n for n in inventory['files']}|{'payload/release-files.json'}
    actual_members={n.replace('\\','/')for n in archive.toc if n.replace('\\','/').startswith('payload/')}
    if actual_members!=expected_members:issues.append('embedded payload inventory')
    if inventory.get('version')!=recipe['version']:issues.append('payload version')
    for name,identity in inventory['files'].items():
        data=member(name)
        if len(data)!=identity['size'] or hashlib.sha256(data).hexdigest()!=identity['sha256']:
            issues.append('embedded member:'+name)
    versions=dict(bootstrap=pe_version(installer.read_bytes()),gui=pe_version(member('MC2Installer.exe')))
    for name,v in versions.items():
        if (v['file_numeric']!=[1,0,0,0] or v['product_numeric']!=[1,0,0,0]
                or not v['strings'] or any(s.get(k)!='v1.0' for s in v['strings'] for k in ('FileVersion','ProductVersion'))):
            issues.append(name+':version')
    result.update(passed=not issues,failures=issues,versions=versions,files=len(inventory['files']),
                  installer=str(installer.resolve()),installer_sha256=sha_file(installer),
                  manifest_sha256=hashlib.sha256(raw).hexdigest(),game_started=False)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('installer','recipe','report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--recipe-sha256',required=True);a=p.parse_args();raw=a.recipe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.recipe_sha256:raise ValueError('recipe SHA256 mismatch')
    result=audit(a.installer,json.loads(raw))
    with a.report.open('x',encoding='utf8')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(f'RESOURCES={result["resources"]} DLC={result["dlc"]} FAILURES={len(result["failures"])} RESULT={"PASS" if result["passed"] else "FAIL"}')
    return int(not result['passed'])


if __name__=='__main__':raise SystemExit(main())
