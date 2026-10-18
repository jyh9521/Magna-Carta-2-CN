"""Read preinitialized name/code rows; never reinterpret cold descriptors."""
from __future__ import annotations
import re

try:
    from .font_binding_plan import parse_json_object
    from .ppc_native_bindings import integer,inside
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError,VirtualImage,digest,MAX_IMAGE
except ImportError:
    from font_binding_plan import parse_json_object
    from ppc_native_bindings import integer,inside
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError,VirtualImage,digest,MAX_IMAGE


def hash_field(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise FormatError('invalid initialized table SHA256 field')
    return value


def identity(record,table,source_sha):
    owner=record['owner']; cls=record['defining_class']; prefix=table['engine_class']+'.'
    if (owner['package']!='engine' or owner['source_sha256']!=source_sha or owner['class_path']!='Core.Function'
            or not isinstance(owner['path'],str) or not owner['path'].startswith(prefix)
            or cls['package']!='engine' or cls['source_sha256']!=source_sha or cls['class_path']!='Class'
            or cls['path']!=table['engine_class'] or cls['object_index']!=table['engine_class_index']):
        raise FormatError('initialized native declaration scope/source mismatch')
    integer(cls['object_index'],1); index=integer(owner['object_index'],1)
    name=owner['path'][len(prefix):]
    if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}',name):
        raise FormatError('invalid initialized native method identifier')
    flags=record['function_flags_hex']
    if not isinstance(flags,str) or not re.fullmatch('[0-9a-f]{8}',flags):
        raise FormatError('invalid initialized native function flags')
    native=bool(int(flags,16)&0x400)
    if record['declared_native'] is not native:
        raise FormatError('initialized native flag/declaration mismatch')
    token=integer(record['native_token'],0,65535)
    return name,index,native,token,flags


def declarations(raw,table,source_sha):
    if digest(raw)!=hash_field(table['metadata_sha256']):
        raise FormatError('initialized native metadata report SHA256 mismatch')
    metadata=parse_json_object(raw)
    if (type(metadata.get('schema_version')) is not int or metadata['schema_version']!=1
            or metadata.get('profile')!='446/25-big-retained-editor-fields-and-friendly-name'
            or metadata.get('source_sha256')!=source_sha or metadata.get('defining_class_scope')!=table['engine_class']
            or metadata.get('unparsed')!=[] or metadata.get('include_scripted') is not False):
        raise FormatError('initialized native metadata must be complete scoped native-only inventory')
    f=metadata.get('native_filter')
    if (not isinstance(f,dict) or set(f)!={'mode','class_function_count','omitted_non_native_count','inventory','omitted_scripts_decoded'}
            or f['mode']!='declared-native-only' or f['omitted_scripts_decoded'] is not False):
        raise FormatError('initialized native metadata requires explicit native-only filter')
    count=integer(f['class_function_count'],1,4096); omitted=integer(f['omitted_non_native_count'],0,count)
    if not isinstance(f['inventory'],list) or len(f['inventory'])!=count:
        raise FormatError('native-only header inventory count mismatch')
    inventory={}; ids=set(); non_native=[]
    for row in f['inventory']:
        name,index,native,token,flags=identity(row,table,source_sha)
        if name in inventory or index in ids:raise FormatError('duplicate native-only header identity')
        ids.add(index); inventory[name]=(index,native,token,flags)
        if not native:non_native.append(row['owner']['path'])
    if len(non_native)!=omitted:raise FormatError('native-only omitted count mismatch')
    expected={name:record for name,record in inventory.items() if record[1]}
    funcs=metadata.get('functions'); selected=metadata.get('selected_objects')
    if not isinstance(funcs,list) or len(funcs)!=len(expected) or not funcs:
        raise FormatError('native-only parsed declaration count mismatch')
    if (not isinstance(selected,list) or not all(isinstance(n,str) for n in selected)
            or len(set(selected))!=len(selected) or set(selected)!={table['engine_class']+'.'+n for n in expected}):
        raise FormatError('native-only selected object set mismatch')
    results={}
    for row in funcs:
        name,index,native,token,flags=identity(row,table,source_sha)
        if not native or row.get('script_kind')!='native-parameter-stub-only' or name in results:
            raise FormatError('initialized table requires unique exact native parameter stubs')
        if expected.get(name)!=(index,native,token,flags):
            raise FormatError('native-only header/parsed declaration mismatch')
        results[name]=row
    if set(results)!=set(expected):raise FormatError('native-only parsed method set mismatch')
    return results,dict(class_functions=count,declared_native=len(results),omitted_non_native=omitted,
                        omitted_paths=non_native,omitted_scripts_decoded=False)


def inspect_tables(image,plan,metadata_raw):
    fields={'schema_version','profile','image_sha256','image_base','code_ranges','string_range','data_range','engine_source_sha256','tables'}
    if (not isinstance(plan,dict) or set(plan)-fields not in (set(),{'measurement_path'}) or not fields<=set(plan) or type(plan.get('schema_version')) is not int
            or plan['schema_version']!=1 or plan.get('profile')!='ppc-initialized-native-row8-v1'):
        raise FormatError('unsupported initialized native table plan')
    if len(image)>MAX_IMAGE or digest(image)!=hash_field(plan['image_sha256']):
        raise FormatError('initialized native image SHA256/size mismatch')
    source_sha=hash_field(plan['engine_source_sha256']);base=integer(plan['image_base']);view=VirtualImage(image,base)
    code=plan['code_ranges']; regions=[plan['string_range'],plan['data_range']]
    if not isinstance(code,list) or not 1<=len(code)<=32:raise FormatError('invalid initialized native code range count')
    for region in code+regions:
        if not isinstance(region,list) or len(region)!=2:raise FormatError('invalid initialized native range')
        a,b=region;integer(a);integer(b)
        if b<=a or a%4 or b%4:raise FormatError('reversed/unaligned initialized native range')
        view.read(a,b-a)
    all_ranges=code+regions
    if any(a<d and c<b for i,(a,b) in enumerate(all_ranges) for c,d in all_ranges[i+1:]):
        raise FormatError('overlapping initialized native ranges')
    tables=plan['tables'];labels=set();out=[]
    if not isinstance(tables,list) or not 1<=len(tables)<=32:raise FormatError('initialized native table count outside bound')
    for table in tables:
        if not isinstance(table,dict) or set(table)!={'label','table_address','table_count','table_sha256','symbol_prefix','engine_class','engine_class_index','metadata_sha256'}:
            raise FormatError('invalid initialized native table fields')
        for key in ['label','engine_class','symbol_prefix']:
            if not isinstance(table[key],str) or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}',table[key]):
                raise FormatError('invalid initialized native label/class/prefix')
        if not re.fullmatch('int[UA]'+re.escape(table['engine_class'])+'exec',table['symbol_prefix']):
            raise FormatError('initialized native class/symbol prefix mismatch')
        if table['label'].casefold() in labels:raise FormatError('duplicate initialized native table label')
        labels.add(table['label'].casefold());integer(table['engine_class_index'],1)
    if not isinstance(metadata_raw,dict) or set(metadata_raw)!={t['label'] for t in tables}:
        raise FormatError('initialized native metadata labels must match all planned tables')
    pdata=read_pdata(image,base,code)
    for table in tables:
        declared,coverage=declarations(metadata_raw[table['label']],table,source_sha)
        at=integer(table['table_address'],1);count=integer(table['table_count'],1,4096);size=(count+1)*8
        if count!=len(declared):raise FormatError('initialized native table/declaration count mismatch')
        if at%4 or not inside(at,size,[plan['data_range']]):raise FormatError('initialized native table outside aligned data range')
        if any(at<t['table_address']+(t['table_count']+1)*8 and t['table_address']<at+size for t in out):
            raise FormatError('initialized native table windows overlap')
        raw=view.read(at,size)
        if digest(raw)!=hash_field(table['table_sha256']):raise FormatError('initialized native table window SHA256 mismatch')
        if raw[-8:]!=bytes(8):raise FormatError('initialized native table lacks full zero sentinel')
        bindings=[];seen=set();lo,hi=plan['string_range']
        for i in range(count):
            row=at+i*8;ptr=view.word(row);target=view.word(row+4)
            if ptr%2 or not lo+2<=ptr<hi or view.read(ptr-2,2)!=b'\0\0':
                raise FormatError('initialized native symbol boundary/range mismatch')
            end=ptr
            while end+2<=hi and end-ptr<1024 and view.read(end,2)!=b'\0\0':end+=2
            if end+2>hi or end-ptr>=1024:raise FormatError('initialized native symbol unterminated/overlong')
            symbol=view.read(ptr,end-ptr).decode('utf-16-be');prefix=table['symbol_prefix']
            method=symbol[len(prefix):] if symbol.startswith(prefix) else ''
            if method not in declared or method in seen:raise FormatError('initialized native symbol/declaration method set mismatch')
            seen.add(method)
            if target%4 or not inside(target,4,code):raise FormatError('initialized native code word outside aligned code range')
            rec=exact_record(pdata,target)
            if rec is None:raise FormatError('initialized native code word has no exact pdata entry')
            f=declared[method]
            bindings.append(dict(index=i,symbol=symbol,method=method,row_address=row,name_address=ptr,code_address=target,
                native_token=f['native_token'],function_flags_hex=f['function_flags_hex'],engine_declaration=f['owner'],
                declared_function_record=rec,function_semantics_verified=False,runtime_binding_verified=False))
        if seen!=set(declared):raise FormatError('initialized native table omits scoped declarations')
        out.append(dict(label=table['label'],engine_class=table['engine_class'],engine_class_index=table['engine_class_index'],
            metadata_sha256=table['metadata_sha256'],table_address=at,table_count=count,row_size=8,
            table_window_sha256=table['table_sha256'],sentinel_address=at+count*8,metadata_coverage=coverage,bindings=bindings))
    report=dict(schema_version=1,profile=plan['profile'],image_sha256=digest(image),engine_source_sha256=source_sha,tables=out,
        coordinate_system='reconstructed virtual-image addresses; not raw PE pointers',
        storage='preinitialized name/code words; no descriptor initializer or adjustor word inferred',
        static_name_code_association_verified=True,native_tokens_preserved=True,native_token_dispatch_semantics_verified=False,
        engine_package_reread=False,metadata_identity_anchor_verified=True,code_body_semantics_verified=False,
        runtime_registration_verified=False,active_font_verified=False,image_modified=False,executed=False)
    if 'measurement_path' in plan:
        try:from .ppc_text_measurement import verify_measurement
        except ImportError:from ppc_text_measurement import verify_measurement
        report['measurement_path']=verify_measurement(view,plan['measurement_path'],out,code,plan['string_range'],plan['data_range'])
    return report
