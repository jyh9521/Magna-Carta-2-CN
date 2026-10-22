"""Bounded serialized integer-to-digit-tag loop inspection; never execute UE3 code."""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from pathlib import Path
try:
    from .ue3_package import FormatError,LzxDecoder
    from .inspect_font_references import _tables
    from .ue3_ui_styles import StyleGraph
    from .ue3_function_metadata import function_header,function_signature,parse_function_metadata
except ImportError:
    from ue3_package import FormatError,LzxDecoder
    from inspect_font_references import _tables
    from ue3_ui_styles import StyleGraph
    from ue3_function_metadata import function_header,function_signature,parse_function_metadata
H=lambda b:hashlib.sha256(b).hexdigest()

def script_shape(refs,prefix):
    if len(refs)!=7 or len(set(refs.values()))!=7 or any(type(x) is not int or not 1<=x<=0x7fffffff for x in refs.values()):raise FormatError('invalid or duplicate property bindings')
    if not isinstance(prefix,str) or not re.fullmatch(r'<Strings:[A-Za-z_][A-Za-z0-9_.]*',prefix):raise FormatError('invalid digit tag prefix')
    loc=lambda role:b'\x00'+struct.pack('>I',refs[role])
    string=lambda value:b'\x1f'+value.encode('ascii')+b'\0'
    let=lambda role,value:b'\x0f'+loc(role)+value
    native=lambda token,*args:bytes([token])+b''.join(args)+b'\x16'
    code=let('text',b'\x38\x53'+loc('input'))+let('length',native(125,loc('text')))+let('markup',string(''))+let('index',b'\x25')
    loop=len(code);condition=native(150,loc('index'),loc('length'))
    body=let('char',native(127,loc('text'),loc('index'),b'\x26'))
    body+=let('markup',native(112,native(112,native(112,loc('markup'),string(prefix)),loc('char')),string('>')))
    body+=native(165,loc('index'))+b'\x06'+struct.pack('>H',loop)
    end=len(code)+3+len(condition)+len(body)
    code+=b'\x07'+struct.pack('>H',end)+condition+body+b'\x04'+loc('markup')+b'\x04\x3a'+struct.pack('>I',refs['result'])+b'\x53'
    return code,dict(loop_condition=loop,condition_false=end,back_edge_target=loop)

def verify_script(script,refs,prefix):
    expected,edges=script_shape(refs,prefix)
    if script!=expected:raise FormatError('digit loop bytecode shape mismatch')
    return dict(script_sha256=H(script),script_size=len(script),control_flow=edges,conversion_token='PrimitiveCast:0x53',digit_tag_prefix=prefix,source_shape_verified=True,executed=False)

def model_positive_digits(value,prefix):
    """Explicit finite-domain offline model, not the game's VM or tag renderer."""
    if type(value) is not int or not 0<=value<=2147483647:raise FormatError('offline model requires nonnegative signed32 integer')
    if not isinstance(prefix,str) or not re.fullmatch(r'<Strings:[A-Za-z_][A-Za-z0-9_.]*',prefix):raise FormatError('invalid digit tag prefix')
    return ''.join(prefix+digit+'>' for digit in str(value))

def inspect_graph(graph,label,plan):
    matches=graph.paths[label].get(plan['function'].casefold(),[])
    if len(matches)!=1:raise FormatError('missing or ambiguous digit function')
    h,params,returns,locals_=function_signature(graph,(label,matches[0]))
    if h['flags']&0x400 or len(params)!=1 or len(returns)!=1:raise FormatError('unexpected digit function signature')
    rows={e['name']:e for e in params+returns+locals_};expected_types={'input':'IntProperty','result':'StrProperty','text':'StrProperty','char':'StrProperty','markup':'StrProperty','length':'IntProperty','index':'IntProperty'};refs={}
    if set(rows)!=set(plan['binding_names'].values()):raise FormatError('unexpected local/property set')
    for role,kind in expected_types.items():
        e=rows[plan['binding_names'][role]]
        if e['kind']!=kind:raise FormatError('digit binding type mismatch')
        refs[role]=e['owner']['object_index']
    if params[0]['name']!=plan['binding_names']['input'] or returns[0]['name']!=plan['binding_names']['result']:raise FormatError('digit input/return binding mismatch')
    if H(h['script'])!=plan['script_sha256']:raise FormatError('script SHA256 mismatch')
    result=verify_script(h['script'],refs,plan['digit_tag_prefix']);operators=[]
    wanted={112:('Object.Concat_StrStr',['StrProperty','StrProperty'],'StrProperty'),125:('Object.Len',['StrProperty'],'IntProperty'),127:('Object.Mid',['StrProperty','IntProperty','IntProperty'],'StrProperty'),150:('Object.Less_IntInt',['IntProperty','IntProperty'],'BoolProperty'),165:('Object.AddAdd_Int',['IntProperty'],'IntProperty')}
    for token,(path,kinds,ret) in wanted.items():
        owners=graph.paths['core'].get(path.casefold(),[])
        if len(owners)!=1:raise FormatError('missing or ambiguous Core declaration')
        d=parse_function_metadata(graph,('core',owners[0]))
        if not d['declared_native'] or d['native_token']!=token or [p['kind'] for p in d['parameters']]!=kinds or d['return_declaration']['kind']!=ret:raise FormatError('Core digit operator signature mismatch')
        operators.append(dict(token=token,path=path,parameter_types=kinds,return_type=ret))
    result.update(function=plan['function'],property_bindings=refs,operators=operators,script_runtime_verified=False,game_rendering_verified=False)
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--core',type=Path,required=True);p.add_argument('--core-sha256',required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True);p.add_argument('--lzx-library',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:
        inputs=[a.package,a.core,a.plan]+([a.lzx_library] if a.lzx_library else [])
        if a.output.exists() or a.output.is_symlink() or a.output.resolve() in [x.resolve() for x in inputs]:raise FormatError('report must be new and distinct')
        raw=a.package.read_bytes();core=a.core.read_bytes();pr=a.plan.read_bytes()
        if H(raw)!=a.sha256 or H(core)!=a.core_sha256 or H(pr)!=a.plan_sha256:raise FormatError('input SHA256 mismatch')
        plan=json.loads(pr)
        if plan.get('schema_version')!=1 or plan.get('profile')!='int-to-digit-markup-loop-v1':raise FormatError('unsupported digit loop profile')
        dec=LzxDecoder(a.lzx_library) if a.lzx_library else None;packages={}
        for label,value,sha in [('target',raw,a.sha256),('core',core,a.core_sha256)]:
            logical,tables=_tables(value,sha,dec);packages[label]=dict(logical=logical,tables=tables,sha256=sha)
        report=inspect_graph(StyleGraph(packages),'target',plan);report.update(schema_version=1,package_sha256=a.sha256,core_sha256=a.core_sha256,plan_sha256=a.plan_sha256)
        if a.package.read_bytes()!=raw or a.core.read_bytes()!=core or a.plan.read_bytes()!=pr:raise FormatError('source changed during inspection')
        out=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode();a.output.write_bytes(out)
        if a.output.read_bytes()!=out:raise FormatError('report reopening mismatch')
        print('PASS digit-tag script shape;7 typed bindings;5 Core declarations;executed=false');return 0
    except (OSError,ValueError,KeyError,TypeError,struct.error) as exc:print('ERROR '+str(exc));return 2
if __name__=='__main__':raise SystemExit(main())
