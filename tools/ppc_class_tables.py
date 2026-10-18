"""Bounded class-name/callback/table associations and getter routing, statically.

No target instruction execution. A registered name operand and a callback word
do not establish runtime reachability, active vptrs or complete constructor state.
"""
from __future__ import annotations
import re
import struct
try:
    from .ppc_native_bindings import d,x,mr,rotate,branch,conditional,integer,inside,checked_window,sext
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError,inspect_pe,digest
except ImportError:
    from ppc_native_bindings import d,x,mr,rotate,branch,conditional,integer,inside,checked_window,sext
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError,inspect_pe,digest


def halves(address):return ((address+0x8000)>>16)&65535,sext(address&65535,16)


def registration_words(s,name,callback,size,c):
    ah,al=halves(c['common_name_address']);nh,nl=halves(c['shared_callback']);ch,cl=halves(callback);sh,sl=halves(name)
    return [d(15,11,0,ah),d(15,9,0,nh),d(15,10,0,sh),d(14,4,9,nl),d(14,7,11,al),d(15,6,0,nh),d(36,4,1,0x54),
            d(15,5,0,ch),d(14,11,10,sl),d(14,10,6,nl),d(14,9,5,cl),mr(8,7),d(14,6,11,2),d(14,5,0,0),d(14,4,0,size),branch(s+60,c['registration_helper'],True)]


def initializer_words(family,table,c):
    th,tl=halves(table);bh,bl=halves(c['base_secondary_table']);sh,sl=halves(c['secondary_table'])
    head=[d(10,24,3,0),0x4d9a0020]
    if family=='base':
        return head+[d(15,11,0,bh),d(15,10,0,th),d(15,9,0,sh),d(14,8,11,bl),d(14,7,10,tl),d(14,6,9,sl),
                     d(36,8,3,0x6c),d(14,10,0,0),d(36,7,3,0),d(14,11,0,3),d(36,6,3,0x6c),
                     d(36,10,3,0x70),d(36,10,3,0x74),d(14,10,3,0x8c),d(38,11,3,0xa0),d(38,11,3,0xa1),d(38,11,3,0xbc),d(38,11,3,0xbd),0x4e800020]
    if family=='derived':
        return head+[d(15,11,0,bh),d(14,10,0,0),d(14,9,11,bl),d(14,11,0,3),d(15,8,0,th),d(36,9,3,0x6c),d(15,7,0,sh),
                     d(36,10,3,0x70),d(36,10,3,0x74),d(14,6,8,tl),d(38,11,3,0xa0),d(14,5,7,sl),d(38,11,3,0xa1),
                     d(38,11,3,0xbc),d(38,11,3,0xbd),d(14,11,3,0x8c),d(36,6,3,0),d(36,5,3,0x6c),0x4e800020]
    raise FormatError('unknown class initializer family')


def getter_words(s,c):
    return [0x7d8802a6,branch(s+4,c['getter_prologue'],True),d(37,1,1,-0x80),d(32,31,3,0x28),mr(30,3),mr(29,4),mr(28,5),mr(27,6),
            d(10,24,4,0),conditional(s+36,s+96,4),d(32,11,31,0x8c),d(13,11,11,-1),conditional(s+48,s+96,12,0),
            d(32,10,31,0x88),rotate(9,11,2,0,29),x(31,10,9,10,266),d(32,9,10,0),d(10,24,9,0),conditional(s+72,s+92,4),
            d(13,11,11,-1),d(14,10,10,-4),conditional(s+84,s+64,4,0),branch(s+88,s+96),mr(29,9),
            d(32,11,30,0),mr(4,28),mr(3,30),d(32,10,11,0x124),0x7d4903a6,0x4e800421,d(32,9,31,0x270),d(11,24,3,0),
            rotate(11,9,27,31,31),conditional(s+132,s+164,12),d(14,31,30,0xe8),d(11,24,27,1),conditional(s+144,s+168,4),
            d(11,24,11,0),conditional(s+152,s+220,4),d(36,11,31,0x1c),branch(s+160,s+176),d(14,31,31,0x174),
            d(11,24,11,0),conditional(s+172,s+220,4),d(10,24,28,0),conditional(s+180,s+220,12),d(32,11,31,0x1c),
            d(10,24,11,0),conditional(s+192,s+208,12),d(32,11,11,0x28),0x7f0be040,conditional(s+204,s+220,12),
            mr(4,28),mr(3,31),branch(s+216,c['reference_helper'],True),mr(4,29),d(32,3,31,0x1c),
            branch(s+228,c['state_helper'],True),branch(s+232,c['cast_helper'],True),d(14,1,1,0x80),branch(s+240,c['getter_epilogue'])]


def verify_class_tables(view,c,engine_class,code_ranges,slot_offset):
    if c.get('profile')!='ppc-class-name-table-v1':raise FormatError('unsupported class table profile')
    if type(slot_offset) is not int or slot_offset!=0x128:raise FormatError('class table requires verified slot128 style profile')
    for key in ['shared_callback','registration_helper','getter_start','getter_prologue','getter_epilogue','reference_helper','state_helper','cast_helper']:
        integer(c[key],1)
        if c[key]%4 or not inside(c[key],4,code_ranges):raise FormatError('class helper outside aligned code range')
    pe=inspect_pe(view.data,view.base,None);sections=[s for s in pe['sections'] if s['name']=='.rdata']
    if len(sections)!=1:raise FormatError('class tables require one .rdata section')
    sec=sections[0];readonly=[view.base+sec['rva'],view.base+sec['rva']+sec['virtual_size']]
    if int(sec['flags'],16)&0xa0000000 or not int(sec['flags'],16)&0x40000000:
        raise FormatError('class table section must be readable non-writable non-executable')
    view.read(readonly[0],readonly[1]-readonly[0])
    if any(a<readonly[1] and readonly[0]<b for a,b in code_ranges):raise FormatError('.rdata overlaps code range')
    for key in ['common_name_address','base_secondary_table','secondary_table']:
        integer(c[key],1)
        if c[key]%2 or not inside(c[key],4,[readonly]):raise FormatError('class auxiliary address outside .rdata')
    rows=c['classes']
    if not isinstance(rows,list) or not 1<=len(rows)<=64:raise FormatError('class count outside bound')
    pdata=read_pdata(view.data,view.base,code_ranges);out=[];seen=set();getter=c['getter_start']
    pdstart=view.base+pdata['directory_rva']
    if pdstart<readonly[1] and readonly[0]<pdstart+pdata['directory_size']:raise FormatError('.rdata overlaps .pdata')
    expected=getter_words(getter,c);raw=checked_window(view,getter,getter+244,c['getter_sha256'],code_ranges)
    if list(struct.unpack('>61I',raw))!=expected:raise FormatError('class style getter structural template mismatch')
    rec=exact_record(pdata,getter)
    if rec is None or rec['end']!=getter+244:raise FormatError('class style getter pdata extent mismatch')
    for row in rows:
        name=row['native_name'];address=integer(row['name_address'],1);table=integer(row['table_address'],1)
        callback=integer(row['callback_start'],1);reg_start=integer(row['registration_start'],1);window=reg_start+52
        size=integer(row['size_operand'],1,32767)
        if not isinstance(name,str) or not re.fullmatch('U[A-Za-z_][A-Za-z0-9_]{0,127}',name) or name in seen:raise FormatError('duplicate/invalid full native class name')
        seen.add(name);encoded=(name+'\0').encode('utf-16-be')
        if (address%2 or not inside(address-2,len(encoded)+2,[readonly]) or view.read(address-2,2)!=b'\0\0'
            or view.read(address,len(encoded))!=encoded):raise FormatError('native class name boundary/content mismatch')
        expected=registration_words(window,address,callback,size,c)
        raw=checked_window(view,window,window+64,row['registration_sha256'],code_ranges)
        if list(struct.unpack('>16I',raw))!=expected:raise FormatError('class registration argument chain mismatch')
        r=exact_record(pdata,reg_start)
        if r is None or not r['start']<=window<window+64<=r['end']:raise FormatError('class registration lacks covering declared entry')
        expected=initializer_words(row['initializer_family'],table,c)
        raw=checked_window(view,callback,callback+84,row['initializer_sha256'],code_ranges)
        if list(struct.unpack('>21I',raw))!=expected:raise FormatError('class callback initializer template mismatch')
        if any(r['start']<callback+84 and callback<r['end'] for r in pdata['records']):raise FormatError('class callback unexpectedly covered by pdata')
        if table%4 or not inside(table,81*4,[readonly]):raise FormatError('class table window outside .rdata')
        raw=view.read(table,81*4)
        if digest(raw)!=row['table_sha256']:raise FormatError('class table window hash mismatch')
        words=list(struct.unpack('>81I',raw))
        if any(v%4 or not inside(v,4,code_ranges) for v in words):raise FormatError('class table contains non-code/unaligned word')
        if words[74]!=getter:raise FormatError('class table slot128 does not point to verified getter')
        stores=[dict(offset=0x6c,value=c['base_secondary_table'],width=4),dict(offset=0,value=table,width=4),dict(offset=0x6c,value=c['secondary_table'],width=4),
                dict(offset=0x70,value=0,width=4),dict(offset=0x74,value=0,width=4)]+[dict(offset=n,value=3,width=1) for n in [0xa0,0xa1,0xbc,0xbd]]
        if row['initializer_family']=='derived':stores=stores[:1]+stores[3:]+stores[1:3]
        out.append(dict(native_name=name,registration_name=name[1:],name_argument_address=address+2,size_operand=size,
                        registration_start=reg_start,registration_window=window,registration_call_instruction=window+60,
                        callback_argument_word=callback,callback_pdata_record=None,initializer_window_end=callback+84,
                        initializer_guard='entry r3 nonzero; zero path returns without stores',
                        ordered_explicit_stores=stores,table_address=table,table_window_words=81,table_end_verified=False,
                        slot124=words[73],slot128=words[74],slot12c=words[75],font_pointer_flag_written_by_leaf=False,
                        full_constructor_state_verified=False,active_instance_verified=False))
    if engine_class not in [r['registration_name'] for r in out]:raise FormatError('class table names do not include scoped Engine class')
    return dict(profile=c['profile'],classes=out,readonly_table_range=readonly,registration_helper=c['registration_helper'],
                registration_helper_semantics_verified=False,callback_type_semantics='high-confidence constructor helper association, not runtime invocation',
                getter=dict(start=getter,declared_record=rec,entry_object_alias='r30',related_object_word_offset=0x28,
                            selection_virtual_slot=0x124,nonzero_result_base=dict(register='r30',pre_call_alias='entry r3',addend=0xe8),
                            zero_result_base=dict(register='r31',pre_call_alias='word loaded at entry+0x28',addend=0x174),selected_pointer_word_offset=0x1c,
                            selection_virtual_target_verified=False,helper_semantics_verified=False,callee_register_preservation_verified=False,
                            semantic_field_names='unverified native layout; operands and branch shape only'),
                static_slot_target_association_verified=True,runtime_dispatch_verified=False,complete_native_layout_verified=False,
                active_font_verified=False,constructor_values_verified=False,image_modified=False,executed=False)
