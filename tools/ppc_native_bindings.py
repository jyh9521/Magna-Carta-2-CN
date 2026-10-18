"""Narrow static PPC constant-store/lookup proofs. Not a VM or game evaluator."""
from __future__ import annotations
import re
import struct
try:
    from .xex_image import FormatError,VirtualImage,digest
except ImportError:
    from xex_image import FormatError,VirtualImage,digest

MASK64=(1<<64)-1


def integer(v,lo=0,hi=0xffffffff):
    if type(v) is not int or not lo<=v<=hi:raise FormatError('invalid bounded integer in native plan')
    return v


def sext(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
def d(op,rt,ra,imm):return op<<26|rt<<21|ra<<16|(imm&65535)
def x(op,rt,ra,rb,xo):return op<<26|rt<<21|ra<<16|rb<<11|xo<<1
def mr(dst,src):return x(31,src,dst,src,444)
def rotate(dst,src,sh,mb,me):return 21<<26|src<<21|dst<<16|sh<<11|mb<<6|me<<1
def branch(pc,target,link=False):
    delta=target-pc
    if delta%4 or not -(1<<25)<=delta<(1<<25):raise FormatError('branch target outside profile')
    return 18<<26|(delta&0x3fffffc)|int(link)
def conditional(pc,target,bo,bi=26):
    delta=target-pc
    if delta%4 or not -(1<<15)<=delta<(1<<15):raise FormatError('conditional branch outside profile')
    return 16<<26|bo<<21|bi<<16|(delta&0xfffc)


def mask32(mb,me):
    integer(mb,0,31);integer(me,0,31)
    return sum(1<<(31-i) for i in range(32) if (mb<=i<=me if mb<=me else i>=mb or i<=me))


def inside(address,size,ranges):return any(a<=address and address+size<=b for a,b in ranges)


def checked_window(view,start,end,expected,ranges):
    integer(start);integer(end)
    if start%4 or end%4 or not 0<end-start<=65536 or not inside(start,end-start,ranges):raise FormatError('native code window outside range/alignment/bound')
    raw=view.read(start,end-start)
    if digest(raw)!=expected:raise FormatError('native code window hash mismatch')
    return raw


def table_rows(view,plan):
    start=integer(plan['table_address']);count=integer(plan['table_count'],1,4096);prefix=plan['symbol_prefix']
    if not isinstance(prefix,str) or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',prefix):raise FormatError('invalid native symbol prefix')
    if start%4 or not inside(start,(count+1)*12,[plan['data_range']]):raise FormatError('native table outside data range')
    rows=[];seen=set();lo,hi=plan['string_range']
    for i in range(count):
        at=start+i*12;ptr=view.word(at)
        if ptr%2 or not lo<=ptr<hi:raise FormatError('native name outside aligned string range')
        end=ptr
        while end+2<=hi and end-ptr<1024 and view.read(end,2)!=b'\0\0':end+=2
        if end+2>hi or end-ptr>=1024:raise FormatError('unterminated/overlong native name')
        name=view.read(ptr,end-ptr).decode('utf-16-be')
        method=name[len(prefix):] if name.startswith(prefix) else ''
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',method) or method in seen:raise FormatError('wrong/duplicate full native symbol')
        if view.read(at+4,8)!=bytes(8):raise FormatError('only cold zero native descriptors supported')
        seen.add(method);rows.append(dict(index=i,symbol=name,method=method,name_address=ptr,row_address=at,descriptor_address=at+4))
    if view.read(start+count*12,12)!=bytes(12):raise FormatError('native table lacks full zero sentinel')
    return rows


def recover_stores(view,raw,start,slots,tail):
    """Abstract constants + symbolic stack bytes only; never mutate image memory."""
    if not raw or len(raw)%4 or len(raw)>65536 or start%4:raise FormatError('invalid initializer window length/alignment')
    regs={1:('stack',0,[])};stack={};writes={};instructions=[]
    def reg(n):
        if n not in regs:raise FormatError('unknown register in native initializer')
        return regs[n]
    def pointer(value):
        if value<=0xffffffff:return value
        if value>>32==0xffffffff and value&0x80000000:return value&0xffffffff
        raise FormatError('non-canonical32-bit native address')
    for i in range(0,len(raw),4):
        pc=start+i;w=struct.unpack_from('>I',raw,i)[0];op=w>>26;rt=(w>>21)&31;ra=(w>>16)&31;imm=sext(w&65535,16)
        record=dict(address=pc,word=f'{w:08x}')
        if op in (14,15):
            if rt==1:raise FormatError('initializer changes symbolic stack base')
            if op==15:
                if ra:raise FormatError('only lis form supported in initializer')
                value=('const',(sext(w&65535,16)<<16)&MASK64,[pc]);record['opcode']='lis'
            elif ra==0:value=('const',imm&MASK64,[pc]);record['opcode']='li'
            else:
                kind,v,trace=reg(ra);value=(kind,(v+imm)&MASK64 if kind=='const' else v+imm,trace+[pc]);record['opcode']='addi'
            regs[rt]=value
        elif op==36:
            if not ra:raise FormatError('zero-base stw is outside initializer profile')
            kind,address,base_trace=reg(ra);sk,value,trace=reg(rt)
            if kind!='stack' or sk!='const':raise FormatError('only constant symbolic-stack stw supported')
            address+=imm;integer(address,-65536,65536)
            for j,b in enumerate((value&0xffffffff).to_bytes(4,'big')):stack[address+j]=(b,trace+base_trace+[pc])
            record.update(opcode='stw-stack',stack_offset=address)
        elif op in (58,62):
            if not ra:raise FormatError('zero-base DS form is outside initializer profile')
            if w&3:raise FormatError('updating/unknown DS-form initializer instruction')
            disp=sext(w&0xfffc,16);kind,address,base_trace=reg(ra);address+=disp
            if op==58:
                if rt==1 or kind!='stack' or any(address+j not in stack for j in range(8)):raise FormatError('unknown/non-stack ld source')
                values=[stack[address+j] for j in range(8)];trace=list(dict.fromkeys([p for _,t in values for p in t]+base_trace+[pc]))
                regs[rt]=('const',int.from_bytes(bytes(b for b,_ in values),'big'),trace);record.update(opcode='ld-stack',stack_offset=address)
            else:
                sk,value,trace=reg(rt)
                if kind!='const' or sk!='const':raise FormatError('nonconstant native descriptor store')
                address=pointer(address&MASK64)
                if address not in slots or address in writes:raise FormatError('unexpected/duplicate native descriptor store')
                writes[address]=dict(address=address,word64=f'{value:016x}',words=[value>>32,value&0xffffffff],store_instruction=pc,
                                     evidence_instructions=list(dict.fromkeys(trace+base_trace+[pc])))
                record.update(opcode='std-descriptor',destination=address)
        elif op==18 and not w&3 and i+4==len(raw):
            target=(pc+sext(w&0x3fffffc,26))&0xffffffff
            if target!=tail:raise FormatError('initializer terminal branch mismatch')
            record.update(opcode='terminal-branch',target=target)
        else:raise FormatError('unsupported initializer opcode/control flow at '+hex(pc))
        instructions.append(record)
    if not instructions or instructions[-1]['opcode']!='terminal-branch' or set(writes)!=set(slots):raise FormatError('incomplete native descriptor initializer')
    return writes,instructions


def lookup_words(start,table,prologue,comparator,epilogue):
    """Verified narrow lookup shape: comparator-zero selects row+4, stride12."""
    hi=((table+0x8000)>>16)&65535;lo=sext(table&65535,16)
    return [0x7d8802a6,branch(start+4,prologue,True),d(37,1,1,-128),d(15,11,0,hi),mr(28,3),d(14,30,11,lo),d(14,31,0,0),d(32,11,11,lo),
            d(10,24,11,0),conditional(start+36,start+100,12),mr(11,30),d(14,29,0,0),mr(3,28),d(32,4,11,0),branch(start+56,comparator,True),d(11,24,3,0),
            conditional(start+64,start+112,12),d(14,31,31,1),rotate(11,31,1,0,30),x(31,11,31,11,266),rotate(29,11,2,0,29),x(31,11,29,30,266),
            x(31,10,29,30,23),d(10,24,10,0),conditional(start+96,start+48,4),d(14,3,0,0),d(14,1,1,128),branch(start+108,epilogue),d(14,11,30,4),x(31,3,29,11,266),d(14,1,1,128),branch(start+124,epilogue)]


def verify_lookup(view,plan):
    start=plan['lookup_start'];raw=checked_window(view,start,start+128,plan['lookup_sha256'],plan['code_ranges'])
    expected=lookup_words(start,plan['table_address'],plan['lookup_prologue'],plan['lookup_comparator'],plan['lookup_epilogue'])
    if list(struct.unpack('>32I',raw))!=expected:raise FormatError('native lookup structural template mismatch')
    return dict(start=start,stride=12,descriptor_offset=4,comparator_target=plan['lookup_comparator'],zero_result_selects_descriptor=True,
                comparator_semantics_verified=False,prologue_epilogue_semantics_verified=False,executed=False)


def verify_font_fields(view,rows,config,code_ranges):
    for key in ('setter_alias_offset','setter_window_offset','disable_alias_offset','disable_window_offset','disable_skip_offset'):integer(config[key],0,4096)
    integer(config['conditional_helper'])
    if not inside(config['conditional_helper'],4,code_ranges):raise FormatError('font helper outside code range')
    methods={r['method']:r['code_address'] for r in rows};setter=methods[config['setter_method']];disable=methods[config['disable_method']]
    for address,size in [(setter+config['setter_alias_offset'],4),(disable+config['disable_alias_offset'],4),
                         (setter+config['setter_window_offset'],44),(disable+config['disable_window_offset'],36)]:
        if address%4 or not inside(address,size,code_ranges):raise FormatError('font instruction chain outside aligned code range')
    if view.word(setter+config['setter_alias_offset'])!=mr(30,3) or view.word(disable+config['disable_alias_offset'])!=mr(31,3):raise FormatError('native font entry-r3 alias mismatch')
    sw=setter+config['setter_window_offset'];dw=disable+config['disable_window_offset']
    a=[d(32,9,30,0xe4),d(14,11,30,0xc4),d(32,10,1,0x50),d(32,8,30,0xd8),x(31,9,7,9,124),d(25,9,6,0x2000),
       x(31,5,8,10,40),rotate(4,7,3,31,31),d(36,6,30,0xe4),d(12,3,5,-1),d(36,10,30,0xd8)]
    b=[d(32,10,31,0xe4),d(14,11,31,0xc4),rotate(9,10,3,31,31),rotate(8,10,0,3,1),d(11,24,9,0),d(36,8,31,0xe4),
       conditional(dw+24,disable+config['disable_skip_offset'],12),mr(3,31),branch(dw+32,config['conditional_helper'],True)]
    if list(struct.unpack('>11I',view.read(sw,44)))!=a or list(struct.unpack('>9I',view.read(dw,36)))!=b:raise FormatError('native font field chain mismatch')
    keep=mask32(3,1);set_mask=0x2000<<16
    if keep^0xffffffff!=set_mask:raise FormatError('font set/clear masks are not complementary')
    return dict(setter=setter,disable=disable,setter_window=sw,disable_window=dw,object_pointer_word_offset=0xd8,
                object_flag_word_offset=0xe4,struct_base_addend=0xc4,set_mask=f'{set_mask:08x}',clear_keep_mask=f'{keep:08x}',
                old_flag_extract=dict(rotate_left=3,mask_begin=31,mask_end=31),conditional_helper=config['conditional_helper'],
                parameter_stack_word_offset=0x50,entry_r3_alias_instructions_verified=True,
                callee_register_preservation_verified=False,semantic_field_names='high-confidence deduction from paired scoped native methods',
                complete_native_struct_layout_verified=False,function_extents_verified=False,
                constructor_values_verified=False,runtime_values_verified=False)


def inspect_bindings(image,plan,metadata_raw,metadata):
    if plan.get('schema_version')!=1 or type(plan['schema_version']) is not int or plan.get('profile')!='ppc-native-row12-cold-init-v1':raise FormatError('unsupported native binding plan')
    if digest(image)!=plan['image_sha256'] or digest(metadata_raw)!=plan['native_report_sha256']:raise FormatError('native image/metadata report hash mismatch')
    base=integer(plan['image_base']);view=VirtualImage(image,base)
    for key in ('initializer_start','initializer_end','initializer_tail','lookup_start','lookup_prologue','lookup_comparator','lookup_epilogue','engine_class_index'):integer(plan[key],1)
    for ranges in [plan['code_ranges'],[plan['data_range']],[plan['string_range']]]:
        if not 1<=len(ranges)<=32:raise FormatError('native range count outside bound')
        for a,b in ranges:
            integer(a);integer(b)
            if b<=a:raise FormatError('empty/reversed native range')
            view.read(a,b-a)
    for region in [plan['data_range'],plan['string_range']]:
        if any(a<region[1] and b>region[0] for a,b in plan['code_ranges']):raise FormatError('native data/string and code ranges overlap')
    if plan['data_range'][0]<plan['string_range'][1] and plan['data_range'][1]>plan['string_range'][0]:raise FormatError('native data and string ranges overlap')
    for key in ('initializer_tail','lookup_prologue','lookup_comparator','lookup_epilogue'):
        if plan[key]%4 or not inside(plan[key],4,plan['code_ranges']):raise FormatError('native helper outside aligned code range')
    if metadata.get('source_sha256')!=plan['engine_source_sha256'] or metadata.get('defining_class_scope')!=plan['engine_class']:raise FormatError('Engine declaration source/scope mismatch')
    if not isinstance(metadata.get('functions'),list) or not 1<=len(metadata['functions'])<=4096:raise FormatError('invalid native declarations list')
    declarations={};ids=set()
    for f in metadata['functions']:
        if not isinstance(f,dict):raise FormatError('native declaration must be an object')
        if not isinstance(f.get('function_flags_hex'),str) or not re.fullmatch('[0-9a-fA-F]{8}',f['function_flags_hex']):raise FormatError('invalid native function flags field')
        if f.get('declared_native') is not True or f.get('script_kind')!='native-parameter-stub-only' or not int(f['function_flags_hex'],16)&0x400:raise FormatError('metadata record is not a native declaration')
        owner=f['owner'];defining=f['defining_class']
        integer(defining['object_index'],1)
        if (type(f.get('native_token')) is not int or f['native_token']!=0 or defining['object_index']!=plan['engine_class_index']
            or defining['path']!=plan['engine_class'] or defining['class_path']!='Class' or defining['package']!='engine'
            or defining['source_sha256']!=plan['engine_source_sha256'] or owner['package']!='engine'
            or owner['source_sha256']!=plan['engine_source_sha256'] or owner['class_path']!='Core.Function'):
            raise FormatError('native declaration identity mismatch')
        index=integer(owner['object_index'],1)
        if index in ids:raise FormatError('duplicate native export identity')
        ids.add(index)
        name=f['owner']['path'];prefix=plan['engine_class']+'.'
        if not name.startswith(prefix) or name[len(prefix):] in declarations:raise FormatError('duplicate/cross-owner native method')
        declarations[name[len(prefix):]]=f['owner']
    rows=table_rows(view,plan)
    if set(declarations)!={r['method'] for r in rows}:raise FormatError('native table/declaration method sets differ')
    raw=checked_window(view,plan['initializer_start'],plan['initializer_end'],plan['initializer_sha256'],plan['code_ranges'])
    slots=[r['descriptor_address'] for r in rows]+[plan['table_address']+len(rows)*12+4]
    writes,instructions=recover_stores(view,raw,plan['initializer_start'],slots,plan['initializer_tail'])
    if writes[slots[-1]]['words']!=[0,0]:raise FormatError('native sentinel initialized nonzero')
    for row in rows:
        evidence=writes[row['descriptor_address']];code,adjustment=evidence['words']
        if code%4 or not inside(code,4,plan['code_ranges']) or adjustment:raise FormatError('unsupported native code/adjustor descriptor')
        row.update(code_address=code,adjustment_word=adjustment,initializer_evidence=evidence,engine_declaration=declarations[row['method']])
    lookup=verify_lookup(view,plan)
    fields=verify_font_fields(view,rows,plan['font_fields'],plan['code_ranges']) if plan.get('font_fields') else None
    if fields:
        by_name={f['owner']['path'].rsplit('.',1)[-1]:f for f in metadata['functions']}
        setter=by_name[plan['font_fields']['setter_method']];disable=by_name[plan['font_fields']['disable_method']]
        params=setter['parameters']
        if len(params)!=1 or params[0]['kind']!='ObjectProperty' or params[0]['target']['path']!='engine.font' or disable['parameters'] or setter['return_declaration'] is not None or disable['return_declaration'] is not None:
            raise FormatError('scoped font method parameter declarations mismatch')
        fields.update(font_parameter_declaration_verified=True,parameter_stack_producer_verified=False)
    report=dict(schema_version=1,image_sha256=digest(image),metadata_report_sha256=digest(metadata_raw),bindings=rows,lookup=lookup,
                initializer_instructions=instructions,font_field_instruction_chains=fields,
                engine_package_reread=False,metadata_identity_anchor_verified=True,image_modified=False,
                initializer_reached_at_runtime_verified=False,active_font_verified=False,executed=False)
    if 'style_selection' in plan:
        try:
            from .ppc_style_selection import verify_style_selection
        except ImportError:
            from ppc_style_selection import verify_style_selection
        report['style_selection']=verify_style_selection(view,rows,plan['style_selection'],plan['code_ranges'])
    if 'class_tables' in plan:
        if 'style_selection' not in report:raise FormatError('class table analysis requires explicit style selection plan')
        try:
            from .ppc_class_tables import verify_class_tables
        except ImportError:
            from ppc_class_tables import verify_class_tables
        report['class_tables']=verify_class_tables(view,plan['class_tables'],plan['engine_class'],plan['code_ranges'],
                                                  report['style_selection']['virtual_slot_byte_offset'])
    if 'style_predicate' in plan:
        if 'class_tables' not in report:raise FormatError('style predicate requires explicit class table plan')
        try:
            from .ppc_style_predicate import verify_style_predicate
        except ImportError:
            from ppc_style_predicate import verify_style_predicate
        report['style_predicate']=verify_style_predicate(view,plan['style_predicate'],report['class_tables'],plan['code_ranges'])
    if 'style_reference_helper' in plan:
        if 'style_predicate' not in report:raise FormatError('style reference helper requires explicit style predicate plan')
        try:
            from .ppc_style_reference_helper import verify_style_reference_helper
        except ImportError:
            from ppc_style_reference_helper import verify_style_reference_helper
        report['style_reference_helper']=verify_style_reference_helper(view,plan['style_reference_helper'],report['style_predicate'],
            plan['class_tables'],report['class_tables'],plan['code_ranges'])
    if 'object_initialization' in plan:
        if 'class_tables' not in report:raise FormatError('object initialization requires explicit class table plan')
        try:
            from .ppc_object_initialization import verify_object_initialization
        except ImportError:
            from ppc_object_initialization import verify_object_initialization
        report['object_initialization']=verify_object_initialization(view,plan['object_initialization'],report['class_tables'],
                                                                     plan['code_ranges'],plan['data_range'])
    return report
