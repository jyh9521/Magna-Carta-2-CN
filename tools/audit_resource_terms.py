"""Read every INT/TXT disc resource and audit explicit forbidden terms."""
import argparse
import json
from pathlib import Path

from .coalesced import parse as parse_coalesced, extract_entries
from .disc_inventory import Disc
from .font_binding_plan import confined_path
from .reface_font import sha
from .subtitle_text import parse as parse_subtitle


def strings(data, path):
    if Path(path).name.lower() == 'coalesced.int':
        return [e['source'] for e in extract_entries(parse_coalesced(data), path)]
    if data.startswith(b'\xff\xfe'):
        if '/movies/' in path.lower():
            return [m[4] for m in parse_subtitle(data)[1]]
        return [data[2:].decode('utf-16-le')]
    return [data.decode('utf-8-sig')]


def audit(image, forbidden, replacement_manifest=None):
    if not forbidden or any(not t for t in forbidden):
        raise ValueError('explicit nonempty terms required')
    disc=Disc(image); replacements={}
    if replacement_manifest:
        spec=json.loads(Path(replacement_manifest).read_bytes())
        for row in spec['resources']:
            data=confined_path(Path(replacement_manifest).parent,row['file']).read_bytes()
            if len(data)!=row['size'] or sha(data)!=row['sha256']:
                raise ValueError('replacement identity mismatch')
            replacements[row['path']]=(row,data)
    files=[]
    for row in disc.inventory():
        if row['directory'] or Path(row['path']).suffix.lower() not in ('.int','.txt'):
            continue
        path=row['path']; before=disc.read(row['offset'],row['size']);after=before
        if path in replacements:
            spec,after=replacements[path]
            if sha(before)!=spec['before_sha256']:
                raise ValueError('disc replacement baseline mismatch')
        old=strings(before,path);new=strings(after,path)
        files.append(dict(path=path,before_sha256=sha(before),after_sha256=sha(after),
                          strings=len(new),before_occurrences=sum(s.count(t) for s in old for t in forbidden),
                          after_occurrences=sum(s.count(t) for s in new for t in forbidden)))
    count=sum(r['after_occurrences'] for r in files)
    return dict(status='PASS' if not count else 'FAIL',image=str(Path(image).resolve()),
                forbidden=forbidden,files=files,before_occurrences=sum(r['before_occurrences'] for r in files),
                after_occurrences=count,game_started=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',type=Path,required=True)
    p.add_argument('--forbidden',action='append',required=True)
    p.add_argument('--replacement-manifest',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('new report path required')
    result=audit(a.image,a.forbidden,a.replacement_manifest)
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
    a.output.write_bytes(raw)
    if a.output.read_bytes()!=raw:raise ValueError('audit reopening mismatch')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','image','forbidden')}|
                     dict(files=len(result['files']))))
    return int(result['status']!='PASS')


if __name__=='__main__':raise SystemExit(main())
