"""Hash-guarded static localized-template/lis-addi-call inspection; no execution."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
try:
    from .xex_image import VirtualImage, FormatError
except ImportError:
    from xex_image import VirtualImage, FormatError

def digest(data):return hashlib.sha256(data).hexdigest()
def signed16(value):return value-65536 if value&32768 else value

def inspect_templates(data,plan):
    if plan.get('schema_version')!=1 or plan.get('profile')!='ppc-localized-wide-template-v1':raise FormatError('unsupported localized template profile')
    if len(data)!=plan['image_size'] or digest(data)!=plan['image_sha256']:raise FormatError('image size/hash mismatch')
    view=VirtualImage(data,plan['image_base']);rows=plan['templates']
    if not isinstance(rows,list) or not 1<=len(rows)<=256:raise FormatError('invalid template count')
    seen=set();result=[]
    for row in rows:
        pointer=row['address'];site=row['call_setup'];prefix=row['prefix'];suffix=row['suffix']
        if any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*',x) for x in [prefix,suffix]):raise FormatError('invalid localization lookup')
        if (prefix,suffix) in seen:raise FormatError('duplicate template')
        seen.add((prefix,suffix))
        # The finite expected sequence is the selected profile, not a printf evaluator.
        expected=f'<Strings:{prefix}>%s<Strings:{suffix}>\n%s'
        raw=expected.encode('utf-16-be')+b'\0\0'
        if pointer%2 or len(raw)>2048 or view.read(pointer,len(raw))!=raw:raise FormatError('wide template mismatch')
        code=view.read(site,16)
        if site%4 or digest(code)!=row['code_sha256']:raise FormatError('code window mismatch')
        a,b,c,d=struct.unpack('>4I',code)
        if a>>26!=15 or (a>>16)&31 or b>>26!=14 or (b>>21)&31!=3 or (b>>16)&31!=31:raise FormatError('unsupported lis/result-address setup')
        reg=(a>>21)&31
        if c>>26!=14 or (c>>21)&31!=4 or (c>>16)&31!=reg:raise FormatError('template argument register mismatch')
        resolved=((signed16(a&65535)<<16)+signed16(c&65535))&0xffffffff
        if resolved!=pointer:raise FormatError('template pointer mismatch')
        if d>>26!=18 or d&3!=1:raise FormatError('expected relative linked branch')
        disp=d&0x3fffffc
        if disp&0x2000000:disp-=0x4000000
        target=(site+12+disp)&0xffffffff
        if target!=plan['format_call_target']:raise FormatError('format call target mismatch')
        result.append(dict(prefix=prefix,suffix=suffix,address=pointer,call_setup=site,code_sha256=digest(code),template_sha256=digest(raw),format_call_target=target,sequence=['localized-prefix','string-argument-1','localized-suffix','LF','string-argument-2'],argument_slots=2))
    return dict(schema_version=1,profile=plan['profile'],image_sha256=digest(data),templates=result,static_template_order_verified=True,formatter_implementation_verified=False,executed=False,game_rendering_verified=False)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:
        inputs=[a.image.resolve(),a.plan.resolve()]
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in inputs:raise FormatError('report must be new and distinct')
        raw=a.image.read_bytes();pr=a.plan.read_bytes()
        if digest(raw)!=a.sha256 or digest(pr)!=a.plan_sha256:raise FormatError('input SHA256 mismatch')
        plan=json.loads(pr);report=inspect_templates(raw,plan);report['plan_sha256']=digest(pr)
        if a.image.read_bytes()!=raw or a.plan.read_bytes()!=pr:raise FormatError('input changed during inspection')
        out=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode();a.output.write_bytes(out)
        if a.output.read_bytes()!=out:raise FormatError('report reopening mismatch')
        print('PASS static localized templates='+str(len(report['templates']))+';inputs unchanged;executed=false');return 0
    except (OSError,ValueError,KeyError,TypeError,struct.error) as exc:
        print('ERROR '+str(exc));return 2
if __name__=='__main__':raise SystemExit(main())
