"""Bounded 446/25 UI-wrapper syntax/reference analysis, never a VM/evaluator.

Only the explicitly handled grammar is admitted. Source references, argument
types, statement jumps and short-circuit spans are checked; Context's raw skip
word is retained but its VM meaning is deliberately not inferred.
"""
from __future__ import annotations
import struct
try:
    from .ue3_package import Reader, FormatError
    from .ue3_struct_defaults import property_declaration
    from .ue3_function_metadata import function_header, function_signature, parse_function_metadata, function_owner_scope
except ImportError:
    from ue3_package import Reader, FormatError
    from ue3_struct_defaults import property_declaration
    from ue3_function_metadata import function_header, function_signature, parse_function_metadata, function_owner_scope


def ancestry(graph,node,kind):
    result=[]
    while node:
        if node in result or len(result)>=256:raise FormatError('cyclic/overlong script type ancestry')
        e=graph.export(*node)
        if e['class_path']!=kind:raise FormatError('script type ancestry class mismatch')
        result.append(node);node=graph.reference(node[0],e['super'])
    return result


def native_operator(graph,index):
    """Bind numeric tokens only to unique serialized Core.Object declarations."""
    if not hasattr(graph,'_script_native_headers'):
        if 'core' not in graph.packages:raise FormatError('script native operators require the Core reference package')
        owners=graph.paths['core'].get('object',[])
        if len(owners)!=1 or graph.export('core',owners[0])['class_path']!='Class':raise FormatError('missing/ambiguous Core.Object operator scope')
        headers={}
        for i,e in enumerate(graph.packages['core']['tables']['exports'],1):
            if e['outer']==owners[0] and e['class_path']=='Core.Function':
                h=function_header(graph,('core',i))
                if h['flags']&0x400 and h['native_token']:
                    headers.setdefault(h['native_token'],[]).append(('core',i))
        graph._script_native_headers=headers
    nodes=graph._script_native_headers.get(index,[])
    if len(nodes)!=1:raise FormatError('missing/ambiguous scoped native operator token')
    result=parse_function_metadata(graph,nodes[0])
    if not int(result['function_flags_hex'],16)&0x1000:raise FormatError('native token is not a declared operator')
    return result


def decode_script(graph,node,raw,parameters,returns,locals_):
    r=Reader(raw);tokens=[];statements=[];jumps=[];defaults=[]
    package=node[0];_,class_node=function_owner_scope(graph,node)
    classes=ancestry(graph,class_node,'Class')
    members={m['owner']['object_index']:m for m in parameters+returns+locals_}
    optional=[p for p in parameters if p['parameter_flags']['optional']]

    def error(message):raise FormatError(message+' at script offset '+str(r.pos))
    def byte():return r.read(1)[0]
    def u16():return struct.unpack('>H',r.read(2))[0]
    def typ(d):
        return dict(kind=d['kind'],array_dim=d['array_dim'],package=d['owner']['package'],
                    target_reference=d['target']['reference'] if d['target'] else 0)
    def scalar(kind):return dict(kind=kind,array_dim=1,package=package,target_reference=0)
    def same(a,b):
        return (a['kind']==b['kind'] and a['array_dim']==b['array_dim'] and
                (a['kind'] not in ('StructProperty','ByteProperty') or target(a)==target(b)))
    def target(t):return graph.reference(t['package'],t['target_reference'])
    def assignable(x):
        return x['opcode'] in ('LocalVariable','InstanceVariable','StructMember','ArrayElement') or (x['opcode']=='BoolVariable' and assignable(x['value']))
    def prop(ref):
        n=graph.reference(package,ref)
        if n is None:error('null script property reference')
        return n,property_declaration(graph,n)
    def args(depth):
        values=[]
        while r.pos<len(raw) and raw[r.pos]!=0x16:
            if len(values)>=256:error('script argument limit exceeded')
            values.append(expr(depth+1))
        start=r.pos
        if byte()!=0x16:error('missing EndFunctionParms')
        tokens.append(dict(opcode='EndFunctionParms',script_offset=start,script_end=r.pos))
        return values
    def check_args(values,params):
        if len(values)>len(params):error('too many call arguments')
        for i,p in enumerate(params):
            if i>=len(values) or values[i]['opcode']=='EmptyParmValue':
                if not p['parameter_flags']['optional']:error('missing required call argument')
                continue
            value=values[i]
            if not same(value['value_type'],typ(p)):error('call argument/declaration type mismatch')
            if p['parameter_flags']['out'] and not assignable(value):error('out argument is not assignable')
            if bool(int(p['flags_hex'],16)&0x200)!=(value['opcode']=='Skip'):
                error('Skip argument/declaration flag mismatch')

    def expr(depth=0):
        if depth>64 or len(tokens)>=8192:error('script depth/token limit exceeded')
        start=r.pos;op=byte();x=dict(script_offset=start);tokens.append(x)
        if depth and op in (4,7,0x0f,0x14,0x49):error('statement opcode in expression position')
        if op in (0,1):
            ref=r.i32();n,d=prop(ref);owner=graph.reference(n[0],graph.export(*n)['outer'])
            if op==0 and (n[0]!=package or n[1] not in members or owner!=node):error('LocalVariable crosses function scope')
            if op==1 and owner not in classes:error('InstanceVariable crosses class ancestry')
            x.update(opcode='LocalVariable' if op==0 else 'InstanceVariable',reference=ref,declaration=d['owner'],value_type=typ(d))
        elif op in (0x25,0x26,0x27,0x28,0x0b,0x4a):
            name,kind,value={0x25:('IntZero','IntProperty',0),0x26:('IntOne','IntProperty',1),
                0x27:('True','BoolProperty',True),0x28:('False','BoolProperty',False),
                0x0b:('Nothing','Void',None),0x4a:('EmptyParmValue','Empty',None)}[op]
            x.update(opcode=name,value=value,value_type=scalar(kind))
        elif op in (0x04,0x2d,0x38):
            if op==0x38 and byte()!=0x3a:error('unsupported primitive cast')
            v=expr(depth+1);x.update(opcode={4:'Return',0x2d:'BoolVariable',0x38:'ByteToInt'}[op],value=v,value_type=v['value_type'])
            if op==0x2d and v['value_type']['kind']!='BoolProperty':error('BoolVariable type mismatch')
            if op==0x38:
                if v['value_type']['kind']!='ByteProperty':error('ByteToInt source type mismatch')
                x['value_type']=scalar('IntProperty')
            if op==4:
                expected=typ(returns[0]) if returns else scalar('Void')
                if not same(v['value_type'],expected):error('return/declaration type mismatch')
        elif op in (0x0f,0x14):
            left,right=expr(depth+1),expr(depth+1)
            if not assignable(left) or not same(left['value_type'],right['value_type']):error('assignment target/type mismatch')
            if op==0x14 and left['value_type']['kind']!='BoolProperty':error('LetBool target is not bool')
            x.update(opcode='LetBool' if op==0x14 else 'Let',target=left,value=right,value_type=scalar('Void'))
        elif op==0x1a:
            index,array=expr(depth+1),expr(depth+1);t=array['value_type']
            if index['value_type']['kind']!='IntProperty' or t['array_dim']<=1:error('static array/index declaration mismatch')
            x.update(opcode='ArrayElement',index=index,array=array,value_type=dict(t,array_dim=1),
                     runtime_index_bounds_verified=index['opcode'] in ('IntZero','IntOne'))
        elif op==0x35:
            ref=r.i32();n,d=prop(ref);struct_ref=r.i32();struct_node=graph.reference(package,struct_ref)
            owner=graph.reference(n[0],graph.export(*n)['outer']);copy_,mod=byte(),byte()
            if owner not in ancestry(graph,struct_node,'Core.ScriptStruct') or copy_ not in (0,1) or mod not in (0,1):error('StructMember owner/flags mismatch')
            value=expr(depth+1)
            if value['value_type']['kind']!='StructProperty' or target(value['value_type'])!=struct_node:error('StructMember context type mismatch')
            x.update(opcode='StructMember',reference=ref,declaration=d['owner'],struct=graph.describe(struct_node),
                     is_copy=copy_,is_modification=mod,value=value,value_type=typ(d))
        elif op==0x18:
            size=u16();begin=r.pos;value=expr(depth+1)
            if begin+size!=r.pos+1 or r.pos>=len(raw) or raw[r.pos]!=0x16:error('short-circuit Skip span mismatch')
            x.update(opcode='Skip',skip_size=size,skip_target=begin+size,value=value,value_type=value['value_type'])
        elif op==0x07:
            dest=u16();condition=expr(depth+1)
            if condition['value_type']['kind']!='BoolProperty':error('JumpIfNot condition is not bool')
            x.update(opcode='JumpIfNot',jump_target=dest,condition=condition,value_type=scalar('Void'));jumps.append(x)
        elif op==0x49:
            size=u16();begin=r.pos;value=expr(depth+1)
            if byte()!=0x15 or r.pos-begin!=size:error('DefaultParmValue span/terminator mismatch')
            if len(defaults)>=len(optional) or not same(value['value_type'],typ(optional[len(defaults)])):error('default parameter declaration mismatch')
            p=optional[len(defaults)];defaults.append(p)
            tokens.append(dict(opcode='EndParmValue',script_offset=r.pos-1,script_end=r.pos))
            x.update(opcode='DefaultParmValue',skip_size=size,parameter=p['owner'],value=value,value_type=scalar('Void'))
        elif op==0x3a:
            ref=r.i32();n,d=prop(ref)
            if not returns or n!=(package,returns[0]['owner']['object_index']):error('ReturnNothing does not name return declaration')
            x.update(opcode='ReturnNothing',reference=ref,declaration=d['owner'],value_type=typ(d))
        elif op==0x19:
            obj=expr(depth+1);skip=u16();property_type=byte();value=expr(depth+1)
            if obj['value_type']['kind'] not in ('ObjectProperty','ClassProperty') or property_type!=0 or not 0<skip<=r.pos-start:error('unsupported Context profile')
            x.update(opcode='Context',object=obj,raw_skip_size=skip,property_type=property_type,
                     skip_vm_meaning_verified=False,value=value,value_type=value['value_type'])
        elif op==0x1c or op>=0x70:
            if op==0x1c:
                ref=r.i32();callee=graph.reference(package,ref)
                if callee is None:error('null FinalFunction reference')
                h,params,ret,_=function_signature(graph,callee)
                call=dict(opcode='FinalFunction',reference=ref,callee=graph.describe(callee),callee_body_verified=False)
            else:
                decl=native_operator(graph,op);params=decl['parameters'];ret=[decl['return_declaration']] if decl['return_declaration'] else []
                call=dict(opcode='NativeOperator',native_token=op,callee=decl['owner'],friendly_name=decl['friendly_name'],native_implementation_verified=False)
            values=args(depth);check_args(values,params)
            bindings=[dict(parameter=p['owner'],kind=p['kind'],flags_hex=p['flags_hex'],argument_index=i,
                           omitted=i>=len(values) or values[i]['opcode']=='EmptyParmValue') for i,p in enumerate(params)]
            x.update(call,arguments=values,argument_bindings=bindings,value_type=typ(ret[0]) if ret else scalar('Void'))
        else:error('unsupported opcode 0x%02x'%op)
        x['script_end']=r.pos
        return x

    while r.pos<len(raw) and raw[r.pos]!=0x53:
        x=expr();statements.append(x)
        if x['opcode'] not in ('Let','LetBool','Return','JumpIfNot','Context','DefaultParmValue'):error('unsupported top-level statement')
    end=r.pos
    if r.read(1)!=b'\x53' or r.pos!=len(raw):error('missing/extra EndOfScript')
    tokens.append(dict(opcode='EndOfScript',script_offset=end,script_end=r.pos))
    starts={s['script_offset'] for s in statements}|{end}
    if any(j['jump_target'] not in starts or j['jump_target']<=j['script_end'] for j in jumps):error('jump is not a forward statement boundary')
    if len(defaults)!=len(optional):error('missing optional parameter defaults')
    if not statements or statements[-1]['opcode']!='Return':error('wrapper does not end with a Return statement')
    if any(s['opcode']=='DefaultParmValue' for s in statements[len(defaults):]):error('parameter defaults must precede the body')
    if len(tokens)>8192:error('script token limit exceeded')
    def placement(x,parent=None):
        if x['opcode'] in ('ReturnNothing','Nothing') and parent!='Return':error('return marker outside Return')
        if x['opcode']=='EmptyParmValue' and parent not in ('FinalFunction','NativeOperator'):error('omitted argument outside call')
        for value in x.values():
            values=value if isinstance(value,list) else [value]
            for v in values:
                if isinstance(v,dict) and 'opcode' in v:placement(v,x['opcode'])
    for s in statements:placement(s)
    edges=[]
    for i,s in enumerate(statements):
        following=statements[i+1]['script_offset'] if i+1<len(statements) else end
        if s['opcode']!='Return':edges.append(dict(source=s['script_offset'],target=following,kind='condition-true' if s['opcode']=='JumpIfNot' else 'fallthrough'))
        if s['opcode']=='JumpIfNot':edges.append(dict(source=s['script_offset'],target=s['jump_target'],kind='condition-false'))
    reachable={statements[0]['script_offset']}
    while True:
        expanded=reachable|{e['target'] for e in edges if e['source'] in reachable}
        if expanded==reachable:break
        reachable=expanded
    return dict(statements=statements,tokens=tokens,full_script_consumed=True,
                source_references_verified=True,jump_statement_boundaries_verified=True,
                source_like_statements=[f"{s['script_offset']:04x}: "+source_like(s) for s in statements],
                control_flow_edges=edges,syntactically_reachable_offsets=sorted(reachable),
                context_skip_vm_meaning_verified=False,executed=False)


def source_like(x):
    """Display syntax only; preserve branch/Skip/omitted/ReturnNothing markers."""
    op=x['opcode'];render=source_like
    if op in ('LocalVariable','InstanceVariable'):
        return ('self.' if op=='InstanceVariable' else '')+x['declaration']['path'].rsplit('.',1)[-1]
    if op=='StructMember':return render(x['value'])+'.'+x['declaration']['path'].rsplit('.',1)[-1]
    if op=='ArrayElement':return render(x['array'])+'['+render(x['index'])+']'
    if op=='BoolVariable':return render(x['value'])
    if op=='ByteToInt':return 'int('+render(x['value'])+')'
    if op in ('IntZero','IntOne'):return str(x['value'])
    if op in ('True','False'):return op.lower()
    if op=='Nothing':return '<Nothing>'
    if op=='EmptyParmValue':return '<omitted>'
    if op=='ReturnNothing':return '<ReturnNothing:'+x['declaration']['path'].rsplit('.',1)[-1]+'>'
    if op=='Skip':return f"SkipTo({x['skip_target']:04x}, {render(x['value'])})"
    if op=='NativeOperator':return x['callee']['path']+'('+', '.join(render(a) for a in x['arguments'])+')'
    if op=='FinalFunction':return x['callee']['path']+'('+', '.join(render(a) for a in x['arguments'])+')'
    if op=='Context':return 'Context('+render(x['object'])+', '+render(x['value'])+')'
    if op in ('Let','LetBool'):return render(x['target'])+' = '+render(x['value'])
    if op=='Return':return 'return '+render(x['value'])
    if op=='DefaultParmValue':return 'default '+x['parameter']['path'].rsplit('.',1)[-1]+' = '+render(x['value'])
    if op=='JumpIfNot':return f"if not {render(x['condition'])}: goto {x['jump_target']:04x}"
    raise FormatError('unsupported source-like display opcode')
