"""Bounded ScriptStruct declarations/defaults for the verified UE3 446/25 profile.

The supported profile retains zero-valued editor header fields and no bytecode.
This reads serialized defaults, never C++ initialization or effective runtime state.
"""
from __future__ import annotations
import struct

try:
    from .ue3_package import FormatError, Reader
    from .ue3_fonts import read_properties
    from .ue3_ui_styles import TAGGED_STRUCTS, object_flags, read_name
except ImportError:
    from ue3_package import FormatError, Reader
    from ue3_fonts import read_properties
    from ue3_ui_styles import TAGGED_STRUCTS, object_flags, read_name


KINDS = {'BoolProperty','IntProperty','FloatProperty','NameProperty','StrProperty',
         'ByteProperty','ObjectProperty','ClassProperty','StructProperty','InterfaceProperty'}


def reference(graph,package,ref,kinds=None):
    if not ref: return None
    ctx = graph.packages[package]
    if not -len(ctx['tables']['imports']) <= ref <= len(ctx['tables']['exports']):
        raise FormatError('declaration reference outside tables')
    kind = (graph.export(package,ref)['class_path'].rsplit('.',1)[-1] if ref>0
            else ctx['tables']['imports'][-ref-1]['class_name']['name'])
    if kinds is not None and kind not in kinds:
        raise FormatError('declaration reference has wrong class')
    return dict(reference=ref,path=graph.symbolic_reference(package,ref),class_name=kind)


def payload(graph,node,kind):
    e = graph.export(*node);ctx = graph.packages[node[0]]
    if e['class_path'] != 'Core.'+kind:
        raise FormatError('expected exact Core.'+kind+' definition')
    lo,ho = object_flags(e)
    if lo & 0x02000000 or ho & 0x200:
        raise FormatError('stack/CDO metadata prefix is unsupported')
    start,size = e['serial_offset'],e['serial_size']
    if start<0 or size<12 or start+size>len(ctx['logical']):
        raise FormatError('declaration payload outside logical package')
    r = Reader(ctx['logical'][start:start+size]);net = r.i32()
    if read_properties(r,ctx['tables']['names']):
        raise FormatError('nonempty metadata UObject tags unsupported')
    return r,net


def property_declaration(graph,node):
    e = graph.export(*node);kind = e['class_path'].rsplit('.',1)[-1]
    if kind not in KINDS: raise FormatError('unsupported declaration property type')
    r,net = payload(graph,node,kind);package = node[0]
    parent,next_field = r.i32(),r.i32()
    if parent or e['super']:
        raise FormatError('inherited property declaration unsupported')
    reference(graph,package,next_field)
    dimensions = r.u32()
    if not 1<=dimensions<=2048:
        raise FormatError('packed/invalid property array dimension unsupported')
    flags = struct.unpack('>Q',r.read(8))[0]
    if flags & 0x20: raise FormatError('networked property declaration unsupported')
    category = read_name(r,graph.packages[package]['tables']['names'])
    array_enum = reference(graph,package,r.i32(),{'Enum'})
    target,meta_class = None,None
    if kind in ('ObjectProperty','ClassProperty','InterfaceProperty'):
        target = reference(graph,package,r.i32(),{'Class'})
        if target is None: raise FormatError('null object property class declaration')
        if kind=='ClassProperty': meta_class = reference(graph,package,r.i32(),{'Class'})
    elif kind=='StructProperty':
        target = reference(graph,package,r.i32(),{'ScriptStruct'})
        if target is None: raise FormatError('null struct property type declaration')
    elif kind=='ByteProperty': target = reference(graph,package,r.i32(),{'Enum'})
    if r.pos!=len(r.data): raise FormatError('property declaration trailing bytes')
    return dict(owner=graph.describe(node),name=e['path'].rsplit('.',1)[-1],kind=kind,
                net_index=net,next_reference=next_field,array_dim=dimensions,flags_hex=f'{flags:016x}',
                category=category,array_enum=array_enum,target=target,meta_class=meta_class,
                enum_catalog=enum_catalog(graph,package,target) if kind=='ByteProperty' and target else None,
                array_enum_catalog=enum_catalog(graph,package,array_enum) if array_enum else None)


def enum_catalog(graph,package,ref):
    node=graph.reference(package,ref['reference'])
    if node is None:raise FormatError('null enum catalog')
    r,net=payload(graph,node,'Enum');parent,next_field=r.i32(),r.i32()
    if parent or graph.export(*node)['super']:raise FormatError('enum inheritance unsupported')
    reference(graph,node[0],next_field)
    values=[read_name(r,graph.packages[node[0]]['tables']['names']) for _ in range(r.count(4096))]
    if r.pos!=len(r.data):raise FormatError('enum catalog trailing bytes')
    return dict(owner=graph.describe(node),net_index=net,stored_names=values)


def annotate_enum_slots(fields,declarations,prefix=0):
    declared={d['name']:d for d in declarations}
    for record in fields:
        if len(record['property_path'])!=prefix+1:continue
        p=record['property_path'][-1];d=declared.get(p['name'])
        if d is None:continue
        if d['enum_catalog'] and isinstance(record.get('value'),int):
            values=d['enum_catalog']['stored_names'];value=record['value']
            record['enum_slot_name']=values[value] if 0<=value<len(values) else None
        if d['array_enum_catalog']:
            values=d['array_enum_catalog']['stored_names'];i=p['array_index']
            record['array_index_name']=values[i] if i<len(values) else None


def local_schema(graph,node):
    r,net = payload(graph,node,'ScriptStruct');e = graph.export(*node);package = node[0]
    header = {name:r.i32() for name in ('super','next','script_text','children','cpp_text','line','text_pos','script_size')}
    if header['super']!=e['super']:
        raise FormatError('native/table ScriptStruct super mismatch')
    reference(graph,package,header['super'],{'ScriptStruct'})
    if any(header[k] for k in ('script_text','cpp_text','line','text_pos','script_size')):
        raise FormatError('only verified zero-editor-header/data-only struct profile supported')
    reference(graph,package,header['next'])
    flags = r.u32();default_start = r.pos
    defaults = read_properties(r,graph.packages[package]['tables']['names'])
    if r.pos!=len(r.data): raise FormatError('ScriptStruct defaults trailing bytes')
    members,seen,current = [],set(),header['children']
    while current:
        if current<0 or current in seen or len(seen)>=2048:
            raise FormatError('imported/cyclic/overlong struct property chain')
        seen.add(current);child = graph.export(package,current)
        if child['outer']!=node[1]: raise FormatError('struct property chain crosses owner')
        declaration = property_declaration(graph,(package,current));members.append(declaration)
        current = declaration['next_reference']
    local = {i for i,c in enumerate(graph.packages[package]['tables']['exports'],1)
             if c['outer']==node[1] and c['class_path'].endswith('Property')}
    if seen!=local: raise FormatError('struct property chain omits local declarations')
    if len({d['name'] for d in members})!=len(members): raise FormatError('duplicate struct property names')
    return dict(owner=graph.describe(node),net_index=net,header=header,struct_flags=flags,
                default_start=default_start,defaults=defaults,declarations=members)


def schema(graph,node,cache=None,stack=()):
    cache={} if cache is None else cache
    if node in stack or len(stack)>=64:raise FormatError('cyclic/overlong ScriptStruct super chain')
    if node in cache:return cache[node]
    s=local_schema(graph,node);own=s['declarations'];s['own_declarations']=own;s['super_chain']=[]
    if s['header']['super']:
        parent=graph.reference(node[0],s['header']['super'])
        p=schema(graph,parent,cache,stack+(node,))
        if {d['name'] for d in own} & {d['name'] for d in p['declarations']}:
            raise FormatError('shadowed inherited struct property unsupported')
        s['declarations']=p['declarations']+own;s['super_chain']=[parent]+p['super_chain']
    cache[node]=s
    return s


def validate_values(graph,package,props,declarations,cache,depth=0):
    if depth>8: raise FormatError('typed struct defaults nesting exceeds limit')
    declared = {d['name']:d for d in declarations};seen=set()
    for p in props:
        key=p['name'],p['array_index'];d=declared.get(p['name'])
        if d is None or key in seen or not 0<=p['array_index']<d['array_dim']:
            raise FormatError('unknown/duplicate/out-of-range default property slot')
        seen.add(key);expected='ObjectProperty' if d['kind']=='ClassProperty' else d['kind']
        if p['type']!=expected: raise FormatError('default tag/declaration type mismatch')
        if p['type']=='StructProperty':
            if p['struct'].casefold()!=d['target']['path'].rsplit('.',1)[-1]:
                raise FormatError('default struct tag/type target mismatch')
            if p['struct'] in TAGGED_STRUCTS:
                target=graph.reference(d['owner']['package'],d['target']['reference'])
                if target is None: raise FormatError('null tagged default struct definition')
                if target not in cache: schema(graph,target,cache)
                r=Reader(p['raw']);children=read_properties(r,graph.packages[package]['tables']['names'])
                if r.pos!=len(r.data): raise FormatError('tagged default struct trailing bytes')
                # Property value FNames are always local to the serializing package.
                validate_values(graph,package,children,cache[target]['declarations'],cache,depth+1)
    return [dict(name=d['name'],array_index=i) for d in declarations for i in range(d['array_dim'])
            if (d['name'],i) not in seen]


def parse_struct_defaults(graph,node):
    cache={};s=schema(graph,node,cache)
    checked={}
    while set(cache)-set(checked):
        current=next(n for n in cache if n not in checked);item=cache[current]
        checked[current]=validate_values(graph,current[0],item['defaults'],item['declarations'],cache)
    missing=checked[node]
    flat,opaque=graph.flatten_properties(node[0],s['defaults'],s['owner']['logical_serial_offset'])
    annotate_enum_slots(flat,s['declarations'])
    return dict(owner=s['owner'],net_index=s['net_index'],header=s['header'],struct_flags=s['struct_flags'],
                profile='446/25-big-data-only-with-editor-fields',
                default_tagged_offset=s['default_start'],declarations=s['declarations'],fields=flat,opaque=opaque,
                own_declaration_count=len(s['own_declarations']),super_chain=[graph.describe(n) for n in s['super_chain']],
                super_defaults=[dict(owner=graph.describe(n),missing_default_slots=checked[n],
                                fields=graph.flatten_properties(n[0],cache[n]['defaults'],
                                graph.export(*n)['serial_offset'])[0]) for n in s['super_chain']],
                missing_default_slots=missing,complete_property_chain=True,
                missing_values_assumed_zero=False,native_initialization_verified=False,runtime_effective_values_resolved=False)


def audit_struct_property(graph,node,name):
    """Bind a field by defining Class + export outer, not a struct-name guess."""
    current=graph.reference(node[0],graph.export(*node)['class']);seen=set();search=[]
    while current:
        if current in seen or len(seen)>=256: raise FormatError('cyclic/overlong defining class chain')
        seen.add(current);package,index=current;e=graph.export(*current)
        if e['class_path']!='Class': raise FormatError('property owner must resolve to Class')
        search.append(graph.describe(current))
        matches=[i for i,c in enumerate(graph.packages[package]['tables']['exports'],1)
                 if c['outer']==index and c['path'].rsplit('.',1)[-1]==name]
        if len(matches)>1: raise FormatError('ambiguous scoped property declaration')
        if matches:
            d=property_declaration(graph,(package,matches[0]))
            if d['kind']!='StructProperty' or d['array_dim']!=1: raise FormatError('expected scalar StructProperty declaration')
            target=graph.reference(package,d['target']['reference'])
            if target is None: raise FormatError('null property ScriptStruct type')
            defaults=parse_struct_defaults(graph,target)
            explicit=[dict(p) for p in graph.parse(node)['flattened'] if p['property_path'][0]['name']==name]
            annotate_enum_slots(explicit,defaults['declarations'],1)
            return dict(field=name,class_search=search,declaration=d,struct_defaults=defaults,instance_fields=explicit,
                        binding='serialized-Class/outer/property/type-reference',runtime_effective_values_resolved=False)
        current=graph.reference(package,e['super'])
    raise FormatError('scoped struct property declaration not found')
