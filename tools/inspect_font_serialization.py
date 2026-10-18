"""Read-only hash-locked Font class/serialization audit; no target execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .font_binding_plan import parse_json_object
    from .xex_image import FormatError,MAX_IMAGE,digest
    from .ppc_font_serialization import inspect_serialization
except ImportError:
    from font_binding_plan import parse_json_object
    from xex_image import FormatError,MAX_IMAGE,digest
    from ppc_font_serialization import inspect_serialization


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('--sha256',required=True)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv);created=False;encoded=None
    try:
        inputs=[a.image,a.plan]
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise FormatError('font serialization report must be new and distinct from inputs')
        if a.image.stat().st_size>MAX_IMAGE or a.plan.stat().st_size>1024*1024:raise FormatError('font serialization input size outside bound')
        raws=[v.read_bytes() for v in inputs];image,plan_raw=raws
        if digest(image)!=a.sha256 or digest(plan_raw)!=a.plan_sha256:raise FormatError('font serialization CLI image/plan SHA256 mismatch')
        report=inspect_serialization(image,parse_json_object(plan_raw));report['plan_sha256']=digest(plan_raw)
        if any(v.read_bytes()!=raw for v,raw in zip(inputs,raws)):raise FormatError('font serialization input changed')
        a.output.parent.mkdir(parents=True,exist_ok=True)
        encoded=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
        with a.output.open('xb') as f:created=True;f.write(encoded)
        if a.output.read_bytes()!=encoded or parse_json_object(a.output.read_bytes())!=report:raise FormatError('font serialization report reopening mismatch')
        if any(v.read_bytes()!=raw for v,raw in zip(inputs,raws)):raise FormatError('font serialization input changed after writing')
        print(json.dumps(dict(classes=len(report['classes']),windows=len(report['windows']),executed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if created:
            try:
                if not a.output.is_symlink() and a.output.read_bytes()==encoded:a.output.unlink()
            except OSError:pass
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
