"""Read-only header inventory of exact/prefix texture names on original discs.

The caller supplies names, discs and an LZX decoder. No locale or game resource
identifier is built in. Every package is hashed; cross-disc identical packages
reuse parsed headers but retain separate disc provenance. Missing or unsupported
headers are reported as failures, never silently counted as empty matches.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .disc_inventory import Disc
from .ue3_package import parse_summary,parse_tables,package_header,LzxDecoder


def inspect(data,decoder,names,prefixes):
    summary=parse_summary(data,len(data))
    size=max([len(data)]+[c['uncompressed_offset']+c['uncompressed_size'] for c in summary['compressed_chunks']])
    header=package_header(data,summary,decoder)[:summary['header_size']]
    tables=parse_tables(header,summary,size)
    result=[]
    for row in tables['exports']:
        short=row['path'].rsplit('.',1)[-1]
        if row['class_path'].rsplit('.',1)[-1]=='Texture2D' and (short in names or any(short.startswith(p) for p in prefixes)):
            result.append(dict(object=row['path'],class_path=row['class_path'],serial_offset=row['serial_offset'],serial_size=row['serial_size']))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',action='append',required=True,type=Path)
    p.add_argument('--name',action='append',default=[])
    p.add_argument('--prefix',action='append',default=[])
    p.add_argument('--lzx-library',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if not 1<=len(a.image)<=8 or not a.name+a.prefix or any(not x or len(x)>128 for x in a.name+a.prefix):
        raise ValueError('Explicit bounded texture query required')
    decoder=LzxDecoder(a.lzx_library);cache={};discs=[]
    for image in a.image:
        disc=Disc(image);rows=[]
        for record in disc.inventory():
            if record['directory'] or Path(record['path']).suffix.casefold()!='.xxx':continue
            raw=disc.read(record['offset'],record['size']);sha=hashlib.sha256(raw).hexdigest()
            if sha not in cache:
                try:cache[sha]=dict(status='PASS',matches=inspect(raw,decoder,set(a.name),a.prefix))
                except (ValueError,KeyError,TypeError) as exc:cache[sha]=dict(status='FAIL',error=str(exc),matches=[])
            rows.append(dict(path=record['path'],sha256=sha,size=record['size'],**cache[sha]))
        discs.append(dict(image=image.name,image_size=disc.size,partition_base=disc.base,packages=rows))
        print('scanned',image.name,'packages',len(rows),flush=True)
    failures=sum(r['status']!='PASS' for d in discs for r in d['packages'])
    out=dict(schema_version=1,kind='texture-export-disc-inventory',names=a.name,prefixes=a.prefix,discs=discs,
             packages=sum(len(d['packages']) for d in discs),unique_packages=len(cache),failures=failures,
             matches=sum(len(r['matches']) for d in discs for r in d['packages']),game_rendering_verified=False)
    data=(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode();a.output.write_bytes(data)
    if a.output.read_bytes()!=data:raise ValueError('Inventory reopening mismatch')
    print(('PASS' if not failures else 'FAIL')+' packages=%d unique=%d matches=%d failures=%d'%(out['packages'],len(cache),out['matches'],failures))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
