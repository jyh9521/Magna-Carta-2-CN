"""Inventory Font namespace candidates in hash-locked discs, decoding headers only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .disc_inventory import Disc
    from .ue3_package import FormatError,LzxDecoder,parse_summary,parse_tables,package_header,write_report
    from .ue3_ui_styles import StyleGraph,object_flags
except ImportError:
    from disc_inventory import Disc
    from ue3_package import FormatError,LzxDecoder,parse_summary,parse_tables,package_header,write_report
    from ue3_ui_styles import StyleGraph,object_flags


def header_fonts(data,expected,label,decoder=None):
    if hashlib.sha256(data).hexdigest()!=expected:
        raise FormatError('package SHA256 mismatch')
    summary=parse_summary(data,len(data))
    if summary['byte_order']!='big':
        raise FormatError('requires supported big-endian profile')
    logical_size=max([len(data)]+[c['uncompressed_offset']+c['uncompressed_size'] for c in summary['compressed_chunks']])
    header=package_header(data,summary,decoder)[:summary['header_size']]
    tables=parse_tables(header,summary,logical_size)
    key=label.casefold()
    graph=StyleGraph({key:dict(logical=header,tables=tables,sha256=expected,package_guid=summary['guid'])})
    fonts=[]
    for index,e in enumerate(tables['exports'],1):
        if e['class_path'].rsplit('.',1)[-1] not in ('Font','MultiFont'):
            continue
        row=dict(owner=graph.describe((key,index)),class_default=bool(object_flags(e)[1]&0x200))
        try:row['identity']=graph.canonical_identity((key,index))
        except ValueError as exc:row['identity_error']=str(exc)
        fonts.append(row)
    return dict(status='tables-validated',exports=len(tables['exports']),font_candidates=fonts,
                logical_header_size=len(header),font_payloads_validated=False)


def scan_disc(image,manifest,decoder=None,cache=None,progress=None):
    if not isinstance(manifest,dict):
        raise FormatError('hashed inventory must be an object')
    disc=Disc(image)
    for field,current in [('image_size',disc.size),('partition_base',disc.base),('root_sector',disc.root_sector),
                          ('root_size',disc.root_size),('timestamp_raw',disc.timestamp_raw)]:
        if manifest.get(field)!=current:
            raise FormatError('disc descriptor/inventory mismatch: '+field)
    actual=disc.inventory();expected=manifest.get('entries')
    fields=('path','directory','sector','offset','size','attributes')
    if (not isinstance(expected,list) or len(expected)!=len(actual)
            or any(not isinstance(e,dict) for e in expected)):
        raise FormatError('disc directory inventory mismatch')
    for a,b in zip(actual,expected):
        if any(a.get(k)!=b.get(k) for k in fields):
            raise FormatError('disc entry mismatch: '+a['path'])
    cache={} if cache is None else cache
    rows=[];cache_hits=0
    for entry in expected:
        if entry['directory'] or Path(entry['path']).suffix.casefold()!='.xxx':
            continue
        expected_hash=entry.get('sha256')
        if not isinstance(expected_hash,str) or len(expected_hash)!=64:
            raise FormatError('missing resource SHA256: '+entry['path'])
        data=disc.read(entry['offset'],entry['size'])
        if hashlib.sha256(data).hexdigest()!=expected_hash:
            raise FormatError('resource SHA256 mismatch: '+entry['path'])
        label=Path(entry['path']).stem.casefold();key=expected_hash,label
        if key in cache:
            result=cache[key];cache_hits+=1
        else:
            try:result=header_fonts(data,expected_hash,label,decoder)
            except (ValueError,KeyError) as exc:result=dict(status='unparsed',reason=str(exc),font_candidates=[])
            cache[key]=result
        rows.append(dict(path=entry['path'],sha256=expected_hash,size=entry['size'],
                         resource_hash_verified=True,**result))
        if progress and len(rows)%250==0:progress(len(rows))
    return dict(image=str(Path(image).resolve()),image_sha256_expected=manifest.get('sha256'),
                whole_image_hash_reverified=False,packages=rows,cache_hits=cache_hits,
                font_payloads_validated=False,game_rendering_verified=False)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--disc',nargs=2,action='append',required=True,metavar=('IMAGE','HASHED_INVENTORY'))
    p.add_argument('--lzx-library',type=Path);p.add_argument('--canonical-path',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:
        if a.output.exists() or a.output.is_symlink():raise FormatError('output must be new')
        reports=[];cache={};decoder=LzxDecoder(a.lzx_library) if a.lzx_library else None
        for image,path in a.disc:
            manifest=json.loads(Path(path).read_text(encoding='utf-8'))
            reports.append(scan_disc(image,manifest,decoder,cache,
                lambda count: print(json.dumps(dict(image=Path(image).name,packages_hashed=count)),flush=True)))
        matches=[]
        for disc in reports:
            for package in disc['packages']:
                for font in package['font_candidates']:
                    if font.get('identity',{}).get('canonical_path')==a.canonical_path.casefold():
                        matches.append(dict(image=disc['image'],path=package['path'],sha256=package['sha256'],**font))
        result=dict(schema_version=1,canonical_path=a.canonical_path.casefold(),discs=reports,matches=matches,
                    interpretation='class/namespace inventory only; no Font payload or runtime validation')
        write_report(a.output,result)
        if json.loads(a.output.read_text(encoding='utf-8'))!=result:raise FormatError('report reopening mismatch')
        print(json.dumps(dict(packages=sum(len(d['packages']) for d in reports),matches=len(matches),
            unparsed=sum(p['status']=='unparsed' for d in reports for p in d['packages']),
            font_payloads_validated=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
