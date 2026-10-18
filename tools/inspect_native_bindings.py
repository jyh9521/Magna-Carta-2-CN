"""Hash-locked static native-table/initializer analysis; no target execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from .font_binding_plan import parse_json_object
    from .xex_image import MAX_IMAGE,FormatError,digest
    from .ppc_native_bindings import inspect_bindings
except ImportError:
    from font_binding_plan import parse_json_object
    from xex_image import MAX_IMAGE,FormatError,digest
    from ppc_native_bindings import inspect_bindings


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('--sha256',required=True)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--native-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv);created=False;encoded=None
    try:
        inputs=[a.image,a.plan,a.native_report]
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [x.resolve() for x in inputs]:raise FormatError('native binding report must be new and distinct from inputs')
        if a.image.stat().st_size>MAX_IMAGE or a.plan.stat().st_size>1024*1024 or a.native_report.stat().st_size>16*1024*1024:raise FormatError('native analysis input size outside bound')
        image,plan_raw,metadata_raw=[x.read_bytes() for x in inputs]
        if digest(image)!=a.sha256 or digest(plan_raw)!=a.plan_sha256:raise FormatError('image/plan SHA256 mismatch')
        plan=parse_json_object(plan_raw);metadata=parse_json_object(metadata_raw)
        report=inspect_bindings(image,plan,metadata_raw,metadata);report['plan_sha256']=digest(plan_raw)
        if any(path.read_bytes()!=raw for path,raw in zip(inputs,[image,plan_raw,metadata_raw])):raise FormatError('native analysis input changed')
        a.output.parent.mkdir(parents=True,exist_ok=True)
        encoded=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf8')
        with a.output.open('xb') as f:created=True;f.write(encoded)
        if a.output.read_bytes()!=encoded or parse_json_object(a.output.read_bytes())!=report:raise FormatError('native binding report reopening mismatch')
        if any(path.read_bytes()!=raw for path,raw in zip(inputs,[image,plan_raw,metadata_raw])):raise FormatError('native analysis input changed after writing')
        print(json.dumps(dict(bindings=len(report['bindings']),font_mask=report['font_field_instruction_chains']['set_mask'] if report['font_field_instruction_chains'] else None,executed=False),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if created:
            try:
                if not a.output.is_symlink() and a.output.read_bytes()==encoded:a.output.unlink()
            except OSError:pass
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
