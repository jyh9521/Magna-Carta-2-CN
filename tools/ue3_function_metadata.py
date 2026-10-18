"""Read only the verified 446/25 native-function declaration/stub profile.

This is not a general bytecode decompiler. Native implementations, registration,
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


def parse_function_metadata(graph,node):
    r,net=payload(graph,node,'Function');e=graph.export(*node);package=node[0]
    header={name:r.i32() for name in ('super','next','script_text','children','cpp_text','line','text_pos','script_size')}
    if header['super']!=e['super']:
        raise FormatError('native/table Function super mismatch')
    reference(graph,package,header['super'],{'Function'})
    reference(graph,package,header['next'])
    if header['script_text'] or header['cpp_text'] or min(header['line'],header['text_pos'])<0:
        raise FormatError('unsupported function editor header profile')
    # No blind v446 bytecode skipping: only a bounded exact stub is accepted below.
    if not 2<=header['script_size']<=10242:
        raise FormatError('function script size outside bounded native stub profile')
    script_offset=r.pos;script=r.read(header['script_size']);tail_offset=r.pos
    native_token=struct.unpack('>H',r.read(2))[0];precedence=r.read(1)[0];flags=r.u32()
    if flags & 0x40:
        raise FormatError('networked Function metadata unsupported')
    if not flags & 0x400:
        raise FormatError('only declared-native Function metadata supported')
    # This game retains the FName and nonzero Line/TextPos despite Xenon cooking.
    friendly=read_name(r,graph.packages[package]['tables']['names'])
    if friendly['name']!=e['path'].rsplit('.',1)[-1] or friendly['number']:
        raise FormatError('Function friendly name/export mismatch')
    if r.pos!=len(r.data):
        raise FormatError('Function metadata trailing bytes')
    outer=graph.reference(package,e['outer'])
    if outer is None or graph.export(*outer)['class_path']!='Class':
        raise FormatError('supported Function owner must be a Class')
    members=property_chain(graph,node,header['children']);params=[];returns=[]
    for member in members:
        bits=int(member['flags_hex'],16)
        if not bits & 0x80:
            raise FormatError('native function contains a non-parameter declaration')
        record=dict(member,parameter_flags=dict(optional=bool(bits&0x10),out=bool(bits&0x100),returns=bool(bits&0x400)))
        (returns if bits&0x400 else params).append(record)
    if len(returns)>1:
        raise FormatError('multiple Function return declarations')
    tokens=native_parameter_stub(script,[p['owner']['object_index'] for p in params])
    for token in tokens:
        token['logical_package_offset']=e['serial_offset']+script_offset+token['script_offset']
    return dict(owner=graph.describe(node),defining_class=graph.describe(outer),net_index=net,
                header=header,native_token=native_token,operator_precedence=precedence,
                function_flags_hex=f'{flags:08x}',declared_native=True,friendly_name=friendly,
                parameters=params,return_declaration=returns[0] if returns else None,
                complete_property_chain=True,script_kind='native-parameter-stub-only',script_tokens=tokens,
                logical_script_offset=e['serial_offset']+script_offset,
                logical_metadata_tail_offset=e['serial_offset']+tail_offset,
                native_implementation_verified=False,runtime_effective_values_resolved=False)
