"""Preflight small sparse-artifact output names for portable PNG publication."""
from .font_binding_plan import confined_path, _relative


def validate_patch_paths(cases,output):
    names=[]
    for case in cases:
        if (not isinstance(case,dict) or not isinstance(case.get('patch'),dict)
                or set(case['patch'])!={'path','sha256'}):
            raise ValueError('explicit sparse patch path/SHA256 required')
        name=_relative(case['patch']['path']);parts=name.split('/')
        if (parts[0].casefold()=='manifest.json' or not name.casefold().endswith('.png')
                or len(name)>1024
                or any(len(p)>240 or any(ord(c)<32 or c in '<>"|?*' for c in p)
                       or p.endswith(('.', ' ')) or p.split('.')[0].casefold() in
                       {'con','prn','aux','nul',*(f'com{i}'for i in range(1,10)),*(f'lpt{i}'for i in range(1,10))}
                       for p in parts)):
            raise ValueError('reserved or nonportable sparse patch output path')
        confined_path(output,name)
        names.append(name)
    folded=sorted(n.casefold() for n in names)
    if len(set(folded))!=len(folded):
        raise ValueError('case-insensitive duplicate sparse patch output path')
    files=set(folded)
    for name in folded:
        parts=name.split('/')
        if any('/'.join(parts[:i]) in files for i in range(1,len(parts))):
            raise ValueError('sparse patch output file/ancestor conflict')
    return names
