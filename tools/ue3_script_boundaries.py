"""Opt-in 446/25 function storage and source-byte boundary reader.

This is a syntax/serialization reader, not a VM, type checker or runtime call
trace.  The stricter UI wrapper decoder is deliberately left unchanged.  Unknown
tokens fail closed; no resynchronization or character-looking-byte scan occurs.
See docs/VM_STRING_BOUNDARIES.md for the dialect and independent source research.
"""
from __future__ import annotations

import struct
import hashlib
from collections import defaultdict

try:
    from .ue3_package import FormatError
    from .ue3_struct_defaults import payload, reference, property_chain
    from .ue3_function_metadata import function_owner_scope, native_parameter_stub
    from .ue3_ui_styles import read_name
except ImportError:
    from ue3_package import FormatError
    from ue3_struct_defaults import payload, reference, property_chain
    from ue3_function_metadata import function_owner_scope, native_parameter_stub
    from ue3_ui_styles import read_name


def function_storage(graph, node, *, max_script_size=65535):
    """Read an explicitly bounded function, including Net and FName instances.

    Byte spans are relative to the owning export.  The caller must bind package
    version/hash before constructing its graph (as other declaration readers do).
    """
    r, net = payload(graph, node, 'Function')
    e = graph.export(*node)
    package = node[0]
    spans = [dict(start=0, end=4, field='net_index'),
             dict(start=4, end=r.pos, field='empty_UObject_tags')]
    header = {}
    for field in ('super', 'next', 'script_text', 'children', 'cpp_text',
                  'line', 'text_pos', 'script_size'):
        start = r.pos
        header[field] = r.i32()
        spans.append(dict(start=start, end=r.pos, field=field))
    if header['super'] != e['super']:
        raise FormatError('native/table Function super mismatch')
    reference(graph, package, header['super'], {'Function'})
    reference(graph, package, header['next'])
    reference(graph, package, header['children'])
    if header['script_text'] or header['cpp_text'] or min(header['line'], header['text_pos']) < 0:
        raise FormatError('unsupported function editor header profile')
    if not 2 <= header['script_size'] <= max_script_size <= 65535:
        raise FormatError('function script size outside explicit storage profile')
    script_offset = r.pos
    script = r.read(header['script_size'])
    tail_offset = r.pos
    spans.append(dict(start=script_offset, end=tail_offset, field='script'))

    def scalar(field, size, fmt):
        start = r.pos
        value = struct.unpack(fmt, r.read(size))[0]
        spans.append(dict(start=start, end=r.pos, field=field))
        return value

    native = scalar('native_token', 2, '>H')
    precedence = scalar('precedence', 1, '>B')
    flags = scalar('flags', 4, '>I')
    rep_offset = scalar('replication_offset', 2, '>H') if flags & 0x40 else None
    friendly_offset = r.pos
    friendly = read_name(r, graph.packages[package]['tables']['names'])
    spans.extend([dict(start=friendly_offset, end=friendly_offset+4, field='friendly_name_index'),
                  dict(start=friendly_offset+4, end=r.pos, field='friendly_name_number')])
    canonical = friendly['name'] + (f"_{friendly['number']-1}" if friendly['number'] else '')
    if not friendly['name'] or (not flags & 0x1000 and canonical != e['path'].rsplit('.', 1)[-1]):
        raise FormatError('Function friendly name/export mismatch')
    if r.pos != len(r.data):
        raise FormatError('Function metadata trailing bytes')
    declaring_owner, outer = function_owner_scope(graph, node)
    return dict(net=net, export=e, header=header, script=script, script_offset=script_offset,
                tail_offset=tail_offset, native_token=native, precedence=precedence,
                flags=flags, replication_offset=rep_offset, friendly=friendly,
                friendly_canonical=canonical, outer=outer, declaring_owner=declaring_owner,
                storage_spans=spans)


def decode_boundaries(script, names, resolve_reference, native_bindings, *,
                      max_depth=128, max_tokens=65536, max_arguments=256):
    """Return complete nonoverlapping atoms and a nested expression forest.

    ``resolve_reference(i32)`` validates source-table bounds and returns an
    explanatory JSON record. ``native_bindings`` binds numeric opcodes to source
    declarations; this does not establish executable native registrations.
    The supported serialized profile is big-endian v446/licensee25 only.
    """
    pos = 0
    atoms, tokens, stack = [], [], []

    def read(size, field):
        nonlocal pos
        if size < 0 or pos + size > len(script):
            raise FormatError(f'truncated {field} at {pos:#x}')
        start = pos
        raw = script[pos:pos+size]
        pos += size
        atoms.append(dict(start=start, end=pos, field=field,
                          token_at=stack[-1] if stack else start, hex=raw.hex()))
        return raw

    def u8(field): return read(1, field)[0]
    def u16(field): return struct.unpack('>H', read(2, field))[0]
    def i32(field): return struct.unpack('>i', read(4, field))[0]

    def ref(field, kinds=None, nullable=False):
        value = i32(field)
        binding = resolve_reference(value)
        if kinds is not None and (binding is None and not nullable or
                                  binding is not None and binding.get('class_name') not in kinds):
            raise FormatError(f'wrong declaration class for {field} at {pos-4:#x}: {value}, {binding}')
        return dict(index=value, binding=binding)

    def fname(field):
        index, number = i32(field+'.index'), i32(field+'.number')
        if not 0 <= index < len(names) or number < 0:
            raise FormatError('invalid script FName reference')
        return dict(index=index, number=number, name=names[index],
                    canonical=names[index]+(f'_{number-1}' if number else ''))

    def marker(value, name):
        if u8(name) != value:
            raise FormatError(f'missing {name} at {pos-1:#x}')

    def arguments():
        result = []
        while pos < len(script) and script[pos] != 0x16:
            if len(result) >= max_arguments:
                raise FormatError('argument count exceeds bound')
            result.append(expr())
        marker(0x16, 'EndFunctionParms')
        return result

    def string(wide):
        start = pos
        size = 2 if wide else 1
        while True:
            if pos + size > len(script):
                raise FormatError('unterminated string literal')
            end = script[pos:pos+size] == bytes(size)
            read(size, 'wide_string_terminator' if end and wide else
                 'string_terminator' if end else 'wide_string_unit' if wide else 'string_byte')
            if end:
                break
        raw = script[start:pos-size]
        try:
            return raw.decode('utf-16-be' if wide else 'latin1')
        except UnicodeDecodeError as exc:
            raise FormatError('invalid Unicode literal') from exc

    def expr():
        if len(stack) >= max_depth or len(tokens) >= max_tokens:
            raise FormatError('script nesting/token count exceeds bound')
        start = pos
        stack.append(start)
        opcode = u8('opcode')
        x = dict(at=start, opcode=opcode, parents=stack[:-1].copy())
        tokens.append(x)
        if opcode in (0, 1, 2, 0x29, 0x48):
            x.update(op={0:'Local', 1:'Instance', 2:'Default', 0x29:'NativeParm', 0x48:'OutLocal'}[opcode],
                     reference=ref('property_reference', {'BoolProperty', 'IntProperty', 'FloatProperty',
                         'ByteProperty', 'StrProperty', 'NameProperty', 'ObjectProperty', 'ClassProperty',
                         'ArrayProperty', 'MapProperty', 'InterfaceProperty', 'StructProperty',
                         'DelegateProperty', 'ComponentProperty'}))
        elif opcode in (4, 0x2d, 0x36, 0x51):
            x.update(op={4:'Return', 0x2d:'Bool', 0x36:'Length', 0x51:'InterfaceContext'}[opcode], value=expr())
        elif opcode in (0x0f, 0x14, 0x44):
            x.update(op={0x0f:'Let', 0x14:'LetBool', 0x44:'LetDelegate'}[opcode], left=expr(), right=expr())
        elif opcode in (0x10, 0x1a):
            x.update(op='DynamicArrayElement' if opcode == 0x10 else 'ArrayElement', index=expr(), array=expr())
        elif opcode in (0x12, 0x19):
            x.update(op='ClassContext' if opcode == 0x12 else 'Context', object=expr(),
                     skip=u16('context_skip'), property_type=u8('context_property_type'), value=expr())
        elif opcode in (0x13, 0x2e, 0x52):
            x.update(op={0x13:'MetaCast', 0x2e:'DynamicCast', 0x52:'InterfaceCast'}[opcode],
                     reference=ref('cast_class_reference', {'Class'}), value=expr())
        elif opcode in (0x1b, 0x37):
            x.update(op='VirtualFunction' if opcode == 0x1b else 'GlobalFunction',
                     name=fname('function_name'), args=arguments())
        elif opcode == 0x1c:
            x.update(op='FinalFunction', reference=ref('function_reference', {'Function'}), args=arguments())
        elif opcode == 0x1d:
            x.update(op='Int', value=i32('int_literal'))
        elif opcode == 0x1e:
            # Hex retains NaN/Infinity without making JSON emit nonstandard numbers.
            x.update(op='Float', value_hex=read(4, 'float_literal').hex())
        elif opcode in (0x1f, 0x34):
            x.update(op='String' if opcode == 0x1f else 'UnicodeString', value=string(opcode == 0x34))
        elif opcode == 0x20:
            x.update(op='Object', reference=ref('object_reference'))
        elif opcode == 0x21:
            x.update(op='Name', name=fname('name_literal'))
        elif opcode in (0x22, 0x23):
            x.update(op='Rotation' if opcode == 0x22 else 'Vector', value_hex=read(12, 'triple_literal').hex())
        elif opcode in (0x24, 0x2c):
            x.update(op='Byte' if opcode == 0x24 else 'IntByte', value=u8('byte_literal'))
        elif opcode in (0x25, 0x26, 0x27, 0x28, 0x0b, 0x17, 0x2a, 0x30, 0x31, 0x3f, 0x4a):
            x.update(op={0x25:'Zero', 0x26:'One', 0x27:'True', 0x28:'False', 0xb:'Nothing',
                         0x17:'Self', 0x2a:'NoObject', 0x30:'IteratorPop', 0x31:'IteratorNext',
                         0x3f:'EmptyDelegate', 0x4a:'Omitted'}[opcode])
        elif opcode in (6, 7):
            x.update(op='Jump' if opcode == 6 else 'JumpIfNot', target=u16('jump_target'))
            if opcode == 7:
                x['condition'] = expr()
        elif opcode == 0x18:
            x.update(op='Skip', size=u16('skip_size'), value=expr())
        elif opcode == 0x35:
            x.update(op='StructMember', member=ref('struct_member_reference'), structure=ref('struct_reference'),
                     copy=u8('struct_copy'), modify=u8('struct_modify'), value=expr())
        elif opcode == 0x38:
            x.update(op='Cast', cast=u8('cast_kind'), value=expr())
        elif opcode in (0x0e, 0x3a):
            x.update(op='EatReturnValue' if opcode == 0x0e else 'ReturnNothing', reference=ref('return_property_reference'))
        elif opcode in (0x39, 0x40):
            x.update(op='ArrayInsert' if opcode == 0x39 else 'ArrayRemove', array=expr(), index=expr(), count=expr())
        elif opcode == 0x11:
            x.update(op='New', outer=expr(), name=expr(), flags=expr(), cls=expr(), template=expr())
        elif opcode == 0x49:
            x.update(op='DefaultParam', size=u16('default_size'), value=expr())
            marker(0x15, 'EndParmValue')
        elif opcode == 0x53:
            if len(stack) != 1 or pos != len(script):
                raise FormatError('EndOfScript must be the final top-level byte')
            x.update(op='EndOfScript')
        elif opcode == 5:
            x.update(op='Switch', kind=u8('switch_property_type'), value=expr())
        elif opcode == 0x0a:
            x.update(op='Case', target=u16('case_target'))
            if x['target'] != 0xffff:
                x['value'] = expr()
        elif opcode == 0x2f:
            x.update(op='Iterator', value=expr(), target=u16('iterator_target'))
        elif opcode in (0x32, 0x33):
            x.update(op='StructEqual' if opcode == 0x32 else 'StructNotEqual',
                     structure=ref('comparison_struct_reference'), left=expr(), right=expr())
        elif opcode in (0x3b, 0x3c, 0x3d, 0x3e):
            x.update(op='DelegateComparison', kind=opcode, left=expr(), right=expr())
            marker(0x16, 'EndFunctionParms')
        elif opcode == 0x4b:
            x.update(op='InstanceDelegate', name=fname('delegate_name'))
        elif opcode == 0x45:
            x.update(op='Conditional', condition=expr(), true_skip=u16('conditional_true_skip'),
                     when_true=expr(), false_skip=u16('conditional_false_skip'), when_false=expr())
        elif opcode >= 0x60:
            native = (opcode-0x60)*256 + u8('extended_native') if opcode < 0x70 else opcode
            if native not in native_bindings:
                raise FormatError(f'unbound native token {native:#x} at {start:#x}')
            x.update(op='Native', native=native, callee=native_bindings[native], args=arguments())
        else:
            raise FormatError(f'unsupported opcode {opcode:#x} at {start:#x}')
        x['end'] = pos
        stack.pop()
        return x

    statements = []
    while pos < len(script):
        statements.append(expr())
    if not statements or statements[-1]['op'] != 'EndOfScript':
        raise FormatError('script lacks final EndOfScript')
    if any(a['end'] != b['start'] for a, b in zip(atoms, atoms[1:])):
        raise FormatError('internal atom coverage gap')
    return dict(statements=statements, tokens=tokens, atoms=atoms,
                full_script_consumed=True, runtime_execution_observed=False,
                native_implementation_verified=False)


def native_declarations(graph):
    """Inventory source declarations; duplicate tokens intentionally stay unbound."""
    rows, unparsed = defaultdict(list), []
    for package, context in graph.packages.items():
        for index, export in enumerate(context['tables']['exports'], 1):
            if export['class_path'] != 'Core.Function':
                continue
            try:
                h = function_storage(graph, (package, index))
            except ValueError as exc:
                unparsed.append(dict(package=package, export=index, reason=str(exc)))
                continue
            if h['native_token']:
                if not h['flags'] & 0x400:
                    unparsed.append(dict(package=package, export=index,
                                         reason='non-native declaration has a native token'))
                    continue
                rows[h['native_token']].append(dict(package=package, export=index, path=export['path']))
    return dict(bindings={k:v[0] for k, v in rows.items() if len(v) == 1},
                ambiguous={k:v for k, v in rows.items() if len(v) > 1}, unparsed_headers=unparsed)


def function_boundary_report(graph, node, bindings):
    """Produce an export/hash-bound JSON record without executing its script."""
    h = function_storage(graph, node)
    e = h['export']
    p = graph.packages[node[0]]
    declarations = None
    if h['flags'] & 0x400:
        declarations = property_chain(graph, node, h['header']['children'])
        parameters = [d['owner']['object_index'] for d in declarations
                      if int(d['flags_hex'], 16) & 0x80 and not int(d['flags_hex'], 16) & 0x400]
        if any(not int(d['flags_hex'], 16) & 0x80 for d in declarations):
            raise FormatError('declared-native function contains local variables')
        native_parameter_stub(h['script'], parameters)
    elif h['native_token']:
        raise FormatError('scripted function has nonzero native token')
    result = decode_boundaries(h['script'], p['tables']['names'],
                              lambda n: reference(graph, node[0], n), bindings)
    data = p['logical'][e['serial_offset']:e['serial_offset']+e['serial_size']]
    return dict(package=node[0], export=node[1], path=e['path'],
                package_sha256=p['sha256'], payload_sha256=hashlib.sha256(data).hexdigest(),
                script_sha256=hashlib.sha256(h['script']).hexdigest(), script_size=len(h['script']),
                export_logical_offset=e['serial_offset'], logical_script_offset=e['serial_offset']+h['script_offset'],
                metadata={k:list(v) if isinstance(v, tuple) else v
                          for k, v in h.items() if k not in ('script', 'export')},
                native_stub_declarations=declarations,
                scripted_declaration_types_fully_validated=False, **result)


def classify_export_offset(report, relative_offset):
    """Classify one source byte; a 0x34 match alone is not a Unicode token."""
    spans = report['metadata']['storage_spans']
    field = next((x for x in spans if x['start'] <= relative_offset < x['end']), None)
    if field is None:
        raise FormatError('candidate outside complete Function payload')
    if field['field'] != 'script':
        return dict(status='not_bytecode_metadata', atom=field)
    at = relative_offset - report['metadata']['script_offset']
    atom = next(x for x in report['atoms'] if x['start'] <= at < x['end'])
    token = next(x for x in report['tokens'] if x['at'] == atom['token_at'])
    return dict(status='real_unicode_token' if atom['field'] == 'opcode' and token['opcode'] == 0x34
                else 'not_unicode_opcode', script_offset=at, atom=atom,
                token=dict(at=token['at'], opcode=token['opcode'], op=token['op'], end=token['end']))
