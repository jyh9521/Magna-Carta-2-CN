"""Read verified 446/25 declarations and opt-in bounded UI-wrapper scripts.

This is not a general bytecode decompiler or VM. Native implementations, registration,
call order and runtime font selection are not established by these records.
"""
from __future__ import annotations
import struct

try:
    from .ue3_package import FormatError, Reader
    from .ue3_ui_styles import read_name
    from .ue3_struct_defaults import payload, reference, property_chain
except ImportError:
    from ue3_package import FormatError, Reader
    from ue3_ui_styles import read_name
    from ue3_struct_defaults import payload, reference, property_chain


def native_parameter_stub(raw, expected):
    """Recognize (NativeParm + local i32 reference)*, Nothing, EndOfScript only."""
    r=Reader(raw);records=[]
    for ref in expected:
        offset=r.pos
        if r.read(1)!=b'\x29' or r.i32()!=ref:
            raise FormatError('native parameter stub/declaration order mismatch')
        records.append(dict(opcode='NativeParm',reference=ref,script_offset=offset))
    if r.read(2)!=b'\x0b\x53' or r.pos!=len(raw):
        raise FormatError('unsupported native function script; not an exact parameter stub')
    records.extend([dict(opcode='Nothing',script_offset=r.pos-2),
                    dict(opcode='EndOfScript',script_offset=r.pos-1)])
    return records


def function_owner_scope(graph, node):
    """Resolve a Class or one local State's Class; no State bytecode is inferred."""
    package = node[0]
    owner = graph.reference(package, graph.export(*node)['outer'])
    if owner is None:
        raise FormatError('Function has no declaring owner')
    declaration = graph.export(*owner)
    if declaration['class_path'] == 'Class':
        return owner, owner
    if declaration['class_path'] != 'Core.State' or owner[0] != package:
        raise FormatError('supported Function owner must be a Class or local Core.State')
    if declaration['outer'] <= 0:
        raise FormatError('State Function requires a local defining Class')
    defining = graph.reference(package, declaration['outer'])
    if defining is None or graph.export(*defining)['class_path'] != 'Class':
        raise FormatError('State Function owner must directly belong to a Class')
    return owner, defining


def function_header(graph,node):
    r,net=payload(graph,node,'Function');e=graph.export(*node);package=node[0]
    header={name:r.i32() for name in ('super','next','script_text','children','cpp_text','line','text_pos','script_size')}
    if header['super']!=e['super']:
        raise FormatError('native/table Function super mismatch')
    reference(graph,package,header['super'],{'Function'})
    reference(graph,package,header['next'])
    if header['script_text'] or header['cpp_text'] or min(header['line'],header['text_pos'])<0:
        raise FormatError('unsupported function editor header profile')
    # This bounded profile must later pass exact stub or opt-in script decoding.
    if not 2<=header['script_size']<=10242:
        raise FormatError('function script size outside bounded function profile')
    script_offset=r.pos;script=r.read(header['script_size']);tail_offset=r.pos
    native_token=struct.unpack('>H',r.read(2))[0];precedence=r.read(1)[0];flags=r.u32()
    if flags & 0x40:
        raise FormatError('networked Function metadata unsupported')
    # This game retains the FName and nonzero Line/TextPos despite Xenon cooking.
    friendly=read_name(r,graph.packages[package]['tables']['names'])
    if (not flags & 0x1000 and friendly['name']!=e['path'].rsplit('.',1)[-1]) or not friendly['name'] or friendly['number']:
        raise FormatError('Function friendly name/export mismatch')
    if r.pos!=len(r.data):
        raise FormatError('Function metadata trailing bytes')
    declaring_owner,outer=function_owner_scope(graph,node)
    return dict(reader=r,net=net,export=e,header=header,script=script,script_offset=script_offset,tail_offset=tail_offset,
                native_token=native_token,precedence=precedence,flags=flags,friendly=friendly,outer=outer,declaring_owner=declaring_owner)


def function_signature(graph,node):
    h=function_header(graph,node);members=property_chain(graph,node,h['header']['children']);params=[];returns=[];locals_=[]
    for member in members:
        bits=int(member['flags_hex'],16)
        if not bits & 0x80:
            if bits & 0xf10:raise FormatError('local declaration has parameter-only flags')
            locals_.append(member);continue
        record=dict(member,parameter_flags=dict(optional=bool(bits&0x10),out=bool(bits&0x100),returns=bool(bits&0x400)))
        (returns if bits&0x400 else params).append(record)
    if len(returns)>1:
        raise FormatError('multiple Function return declarations')
    return h,params,returns,locals_


def parse_function_metadata(graph,node,include_scripted=False):
    h,params,returns,locals_=function_signature(graph,node)
    e=h['export'];native=bool(h['flags']&0x400)
    if not native and not include_scripted:
        raise FormatError('only declared-native Function metadata supported')
    if native:
        if locals_:raise FormatError('native function contains a non-parameter declaration')
        tokens=native_parameter_stub(h['script'],[p['owner']['object_index'] for p in params]);program=None
    else:
        if h['native_token']:raise FormatError('scripted function has nonzero native token')
        try:from .ue3_scripted_ui import decode_script
        except ImportError:from ue3_scripted_ui import decode_script
        program=decode_script(graph,node,h['script'],params,returns,locals_);tokens=program['tokens']
    for token in tokens:
        token['logical_package_offset']=e['serial_offset']+h['script_offset']+token['script_offset']
    return dict(owner=graph.describe(node),defining_class=graph.describe(h['outer']),
                declaring_owner=graph.describe(h['declaring_owner']),net_index=h['net'],
                header=h['header'],native_token=h['native_token'],operator_precedence=h['precedence'],
                function_flags_hex=f"{h['flags']:08x}",declared_native=native,friendly_name=h['friendly'],
                parameters=params,return_declaration=returns[0] if returns else None,local_declarations=locals_,
                complete_property_chain=True,script_kind='native-parameter-stub-only' if native else 'bounded-scripted-ui',script_tokens=tokens,script_program=program,
                logical_script_offset=e['serial_offset']+h['script_offset'],
                logical_metadata_tail_offset=e['serial_offset']+h['tail_offset'],
                native_implementation_verified=False,runtime_effective_values_resolved=False)
