"""Hash-locked preinitialized native tables; no loader, emulator or native call."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .font_binding_plan import parse_json_object
    from .xex_image import FormatError,MAX_IMAGE,digest
    from .initialized_native_tables import inspect_tables
except ImportError:
    from font_binding_plan import parse_json_object
    from xex_image import FormatError,MAX_IMAGE,digest
    from initialized_native_tables import inspect_tables


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('--sha256',required=True)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--native-report',nargs=2,action='append',required=True,metavar=('LABEL','PATH'))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv);created=False;encoded=None
    try:
        if not 1<=len(a.native_report)<=32:raise FormatError('initialized native report count outside bound')
        inputs=[a.image,a.plan]+[Path(path) for _,path in a.native_report]
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [v.resolve() for v in inputs]:
            raise FormatError('initialized native report must be new and distinct from inputs')
        if a.image.stat().st_size>MAX_IMAGE or a.plan.stat().st_size>1024*1024 or any(v.stat().st_size>16*1024*1024 for v in inputs[2:]):
            raise FormatError('initialized native input size outside bound')
        raws=[v.read_bytes() for v in inputs];image,plan_raw=raws[:2]
        if digest(image)!=a.sha256 or digest(plan_raw)!=a.plan_sha256:raise FormatError('initialized native CLI image/plan SHA256 mismatch')
        metadata={}
        for (label,_),raw in zip(a.native_report,raws[2:]):
            if label in metadata:raise FormatError('duplicate initialized native report label')
            metadata[label]=raw
        report=inspect_tables(image,parse_json_object(plan_raw),metadata);report['plan_sha256']=digest(plan_raw)
        if any(v.read_bytes()!=raw for v,raw in zip(inputs,raws)):raise FormatError('initialized native input changed')
        a.output.parent.mkdir(parents=True,exist_ok=True)
        encoded=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
        with a.output.open('xb') as f:created=True;f.write(encoded)
        if a.output.read_bytes()!=encoded or parse_json_object(a.output.read_bytes())!=report:raise FormatError('initialized native report reopening mismatch')
        if any(v.read_bytes()!=raw for v,raw in zip(inputs,raws)):raise FormatError('initialized native input changed after writing')
        print(json.dumps(dict(tables=len(report['tables']),bindings=sum(t['table_count'] for t in report['tables']),executed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if created:
            try:
                if not a.output.is_symlink() and a.output.read_bytes()==encoded:a.output.unlink()
            except OSError:pass
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
