"""Reconstruct a new hash-locked XEX2 none/basic image for offline analysis."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
try:
    from .xex_image import MAX_IMAGE,RETAIL_KEY,FormatError,digest,parse_xex,decode_image,crypto_backend
except ImportError:
    from xex_image import MAX_IMAGE,RETAIL_KEY,FormatError,digest,parse_xex,decode_image,crypto_backend


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--sha256',required=True)
    p.add_argument('--key',choices=['none','retail','devkit'],default='none')
    p.add_argument('--backend',choices=['pycryptodome','cryptography'],default='pycryptodome')
    p.add_argument('--image-sha256');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--roundtrip-output',type=Path)
    a=p.parse_args(argv);created=[]
    try:
        outputs=[a.output,a.report]+([a.roundtrip_output] if a.roundtrip_output else [])
        if len({x.resolve() for x in outputs+[a.source]})!=len(outputs)+1 or any(x.exists() or x.is_symlink() for x in outputs):
            raise FormatError('outputs must be new and distinct from source and each other')
        if a.source.stat().st_size>MAX_IMAGE:raise FormatError('source exceeds supported size bound')
        source=a.source.read_bytes();meta=parse_xex(source,a.sha256)
        if meta['encryption'] and a.key=='none':raise FormatError('encrypted XEX requires an explicit key selection')
        if not meta['encryption'] and a.key!='none':raise FormatError('unencrypted XEX does not use a key selection')
        key=None if a.key=='none' else RETAIL_KEY if a.key=='retail' else bytes(16)
        cipher=crypto_backend(a.backend) if meta['encryption'] else None
        image,restored,report=decode_image(source,a.sha256,key,cipher)
        if a.image_sha256 and digest(image)!=a.image_sha256.lower():raise FormatError('reconstructed image SHA256 mismatch')
        version=None
        if cipher:
            try:version=importlib.metadata.version(a.backend)
            except importlib.metadata.PackageNotFoundError:pass
        report.update(key_profile=a.key,crypto_backend=a.backend if cipher else None,crypto_backend_version=version)
        if a.source.read_bytes()!=source:raise FormatError('source changed during reconstruction')
        encoded=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
        artifacts=[(a.output,image),(a.report,encoded)]+([(a.roundtrip_output,restored)] if a.roundtrip_output else [])
        for path,data in artifacts:
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:
                created.append((path,digest(data)));f.write(data);f.flush();os.fsync(f.fileno())
            if path.read_bytes()!=data:raise FormatError('artifact reopening mismatch')
        if json.loads(a.report.read_text(encoding='utf8'))!=report:raise FormatError('report reopening mismatch')
        if a.source.read_bytes()!=source:raise FormatError('source changed after artifact writing')
        print(json.dumps(dict(image_sha256=digest(image),image_size=len(image),roundtrip_verified=True,executed=False),sort_keys=True))
        return 0
    except (OSError,ValueError,ImportError) as exc:
        for path,expected in created:
            try:
                if not path.is_symlink() and path.is_file() and digest(path.read_bytes())==expected:path.unlink()
            except OSError:pass
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
