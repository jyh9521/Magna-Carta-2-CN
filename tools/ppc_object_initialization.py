"""Static constructor-metadata/callback/clear-phase contracts, never a PPC VM.

Zero-fill geometry is integer interval algebra, not target execution. Opaque
allocation/wrapper regions are hash-locked but not semantically interpreted.
"""
from __future__ import annotations
import struct
try:
    from .ppc_native_bindings import d,mr,rotate,branch,conditional,integer,inside,checked_window
    from .ppc_class_tables import halves
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError,MAX_IMAGE,digest
except ImportError:
    from ppc_native_bindings import d,mr,rotate,branch,conditional,integer,inside,checked_window
    from ppc_class_tables import halves
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError,MAX_IMAGE,digest


def saved_register_words():
    return [d(62,r,1,-0x98+(r-14)*8) for r in range(14,32)]+[d(36,12,1,-8),0x4e800020]


def restored_register_words():
    return [d(58,r,1,-0x98+(r-14)*8) for r in range(14,32)]+[d(32,12,1,-8),0x7d8803a6,0x4e800020]


def metadata_base_words(s,c):
    fh,fl=halves(c['registry_flag_address']);ch,cl=halves(c['registry_head_address'])
    ih,il=halves(c['base_initial_table']);bh,bl=halves(c['base_final_table'])
    w=[d(62,31,1,-8),d(15,11,0,0x408),d(15,8,0,fh),d(24,11,9,0x4084),d(14,10,0,0x4000),d(15,7,0,ih),0x792a000e,
       d(32,9,8,fl),d(14,11,0,0),d(14,7,7,il),d(62,10,3,8),d(14,31,0,-1),d(36,11,3,0x10),d(14,8,0,-1),
       d(36,7,3,0),d(36,31,3,4),d(14,10,3,0x2c),d(36,11,3,0x18),d(11,24,9,0),d(36,11,3,0x1c),d(36,8,3,0x20),
       d(36,11,3,0x2c),d(36,11,3,0x30),d(36,5,3,0x2c),d(36,11,3,0x34),d(36,11,3,0x38),d(36,6,3,0x28),
       conditional(s+108,s+128,4),d(15,9,0,ch),d(32,10,9,cl),d(36,10,3,0x20),d(36,3,9,cl),d(15,10,0,bh),
       d(36,4,3,0x50),d(14,9,0,1),d(36,11,3,0x40),d(14,8,10,bl),d(36,11,3,0x44),d(36,11,3,0x48),d(36,8,3,0)]
    w += [d(36,11,3,n) for n in [0x4c,0x54,0x58,0x5c,0x60,0x64]]+[d(36,9,3,0x68)]
    return w+[d(36,11,3,n) for n in range(0x6c,0x8c,4)]+[d(58,31,1,-8),0x4e800020]


def metadata_constructor_words(s,c):
    th,tl=halves(c['metadata_table'])
    w=[0x7d8802a6,branch(s+4,c['save_start']+13*4,True),d(37,1,1,-0x80),mr(30,5),mr(5,6),mr(6,7),mr(31,3),mr(29,8),mr(28,9),mr(27,10),
       branch(s+40,c['metadata_base_start'],True),d(14,11,0,0),d(32,8,1,0xd4),d(15,9,0,th),d(14,10,0,8),d(62,11,3,0x8c),d(62,11,3,0x94),
       d(14,7,9,tl),d(36,11,3,0x9c),d(24,30,6,0x80),d(44,11,3,0xa0),d(14,5,0,1)]
    w += [d(36,11,3,n) for n in [0xa4,0xa8,0xac,0xb0]]+[d(36,10,3,0xb4),d(36,7,3,0),d(36,6,3,0xb8),d(36,11,3,0xbc),d(38,11,3,0xc0),d(36,11,3,0xc4)]
    w += [d(36,11,3,n) for n in range(0xd0,0x11c,4)]
    w += [d(36,28,3,0x11c),d(36,27,3,0x120),d(36,8,3,0x124)]+[d(36,11,3,n) for n in range(0x128,0x138,4)]
    w += [d(36,10,3,0x138)]+[d(36,10 if n==0x14c else 11,3,n) for n in range(0x13c,0x15c,4)]+[d(36,5,3,0x15c)]+[d(36,11,3,n) for n in range(0x160,0x178,4)]
    return w+[d(36,29,3,0xc8),d(14,1,1,0x80),branch(s+304,c['restore_start']+13*4)]


def zero_fill_words(s):
    # Branch prediction bits are retained; they do not replace count/condition tests.
    return [d(14,0,5,1),0x7c0903a6,d(24,3,6,0),branch(s+12,s+28),d(14,5,5,-1),d(38,4,6,0),d(14,6,6,1),d(28,6,0,3),conditional(s+32,s+16,0,2),
            0x5084442e,rotate(0,5,28,4,31)|1,0x5084801e,conditional(s+48,s+80,15,2),0x7c0903a6,
            d(36,4,6,0),d(36,4,6,4),d(36,4,6,8),d(36,4,6,12),d(14,6,6,16),conditional(s+76,s+56,25,0),
            rotate(0,5,30,30,31)|1,conditional(s+84,s+124,14,2),0x7c0903a6,d(36,4,6,0),d(14,6,6,4),conditional(s+100,s+124,26,0),
            d(36,4,6,0),d(14,6,6,4),conditional(s+112,s+124,26,0),d(36,4,6,0),d(14,6,6,4),d(28,5,0,3),0x7c0903a6,0x4de20020,
            d(38,4,6,0),0x4f400020,d(38,4,6,1),0x4f400020,d(38,4,6,2),0x4e800020]


def zero_fill_partition(address,size):
    """Closed-form disjoint intervals; no image/memory access or instruction loop."""
    integer(address);integer(size,0,MAX_IMAGE)
    if address+size>0x100000000:raise FormatError('zero-fill geometry wraps address space')
    prefix=min(size,(-address)&3);remaining=size-prefix;blocks=remaining//16;words=(remaining%16)//4;tail=remaining%4
    ends=[address,address+prefix,address+prefix+blocks*16,address+prefix+blocks*16+words*4,address+size]
    if ends[3]+tail!=ends[4]:raise FormatError('zero-fill interval partition mismatch')
    return dict(start=address,end=address+size,size=size,prefix_bytes=prefix,blocks16=blocks,words4=words,tail_bytes=tail,
                intervals=[dict(kind=k,start=a,end=b) for k,a,b in zip(['prefix','blocks16','words4','tail'],ends,ends[1:])],
                arithmetic_only=True,target_executed=False)


def wrapper_windows(s,c):
    entry=[0x7d8802a6,branch(s+4,c['save_start']+7*4,True),d(37,1,1,-0xc0)]+[mr(a,b) for a,b in [(23,3),(30,4),(29,5),(25,6),(28,7),(27,8),(26,9),(21,10),(24,10)]]+[d(14,31,0,0),d(14,22,0,1)]
    a=s+0xbc
    alloc=[mr(10,26),d(36,24,1,0x54),d(14,9,0,0),mr(8,27),mr(7,28),mr(6,25),mr(5,29),mr(4,30),mr(3,23),branch(a+36,c['allocation_start'],True),mr(30,3),d(10,24,3,0),conditional(a+48,s+0x228,12)]
    q=s+0x110
    dispatch=[mr(11,23),d(10,24,23,0),conditional(q+8,q+40,12),d(58,10,11,8),rotate(9,10,0,18,18),d(10,25,9,0),conditional(q+24,q+52,4),
              d(32,11,11,0x3c),d(10,24,11,0),conditional(q+36,q+12,4),d(32,11,23,0x11c),0x7d6903a6,branch(q+48,q+68),
              branch(q+52,c['fallback_class_helper'],True),d(32,10,3,0x11c),mr(11,3),0x7d4903a6,mr(3,30),0x4e800421]
    z=s+0x190
    post=[d(14,7,0,0),d(14,6,0,0),d(14,5,0,0),d(14,4,0,0),mr(3,30),branch(z+20,c['post_callback_helpers'][0],True),d(14,5,0,0),d(14,4,0,0),mr(3,30),branch(z+36,c['post_callback_helpers'][1],True)]
    z=s+0x228
    tail=[d(10,24,21,0),conditional(z+4,z+32,4),d(10,24,24,0),conditional(z+12,z+32,12),mr(3,24),branch(z+20,c['wrapper_cleanup_helpers'][0],True),
          mr(3,24),branch(z+28,c['wrapper_cleanup_helpers'][1],True),mr(3,30),d(14,1,1,0xc0),branch(z+40,c['restore_start']+7*4)]
    return [('wrapper_entry',s,entry),('allocation_result',a,alloc),('callback_dispatch',q,dispatch),('post_callback',s+0x190,post),('wrapper_exit',z,tail)]


def verify_object_initialization(view,c,class_report,code_ranges,data_range):
    if c.get('profile')!='ppc-object-initialization-v1':raise FormatError('unsupported object initialization profile')
    keys=['metadata_base_start','metadata_constructor_start','save_start','restore_start','zero_fill_start','size_getter_start','wrapper_start','allocation_start','fallback_class_helper']
    for key in keys:
        integer(c[key],1)
        if c[key]%4 or not inside(c[key],4,code_ranges):raise FormatError('object initialization helper outside aligned code range')
    if c['metadata_constructor_start']!=class_report['registration_helper']:raise FormatError('object metadata helper does not match class registration chain')
    readonly=class_report['readonly_table_range']
    for key in ['metadata_table','base_initial_table','base_final_table']:
        integer(c[key],1)
        if c[key]%4 or not inside(c[key],4,[readonly]):raise FormatError('metadata table address outside aligned .rdata')
    for key in ['registry_flag_address','registry_head_address']:
        integer(c[key],1)
        if c[key]%4 or not inside(c[key],4,[data_range]):raise FormatError('metadata global outside aligned data range')
    for key,n in [('post_callback_helpers',2),('post_allocation_helpers',3),('wrapper_cleanup_helpers',2)]:
        if not isinstance(c[key],list) or len(c[key])!=n:raise FormatError('initialization phase helper count mismatch')
        for value in c[key]:
            integer(value,1)
            if value%4 or not inside(value,4,code_ranges):raise FormatError('initialization phase helper outside code range')
    pdata=read_pdata(view.data,view.base,code_ranges);evidence=[]
    def checked(name,start,words):
        raw=checked_window(view,start,start+len(words)*4,c[name+'_sha256'],code_ranges)
        if list(struct.unpack('>'+str(len(words))+'I',raw))!=words:raise FormatError('object '+name+' structural template mismatch')
        evidence.append(dict(name=name,start=start,end=start+len(raw),instruction_words=len(words),sha256=digest(raw)))
    for name,key,words in [('save_helpers','save_start',saved_register_words()),('restore_helpers','restore_start',restored_register_words()),
                           ('metadata_base','metadata_base_start',metadata_base_words(c['metadata_base_start'],c)),
                           ('metadata_constructor','metadata_constructor_start',metadata_constructor_words(c['metadata_constructor_start'],c)),
                           ('zero_fill','zero_fill_start',zero_fill_words(c['zero_fill_start'])),('size_getter','size_getter_start',[d(32,3,3,0x50),0x4e800020])]:checked(name,c[key],words)
    declared={}
    for name,key,length in [('metadata_base','metadata_base_start',57),('metadata_constructor','metadata_constructor_start',77),('wrapper','wrapper_start',149),('allocation','allocation_start',739)]:
        start=c[key];record=exact_record(pdata,start)
        if record is None or record['end']!=start+length*4:raise FormatError('object initialization declared extent mismatch')
        raw=checked_window(view,start,record['end'],c[name+'_function_sha256'],code_ranges);declared[name]=dict(record=record,sha256=digest(raw),all_words_structurally_checked=name in ['metadata_base','metadata_constructor'])
    for name,start,words in wrapper_windows(c['wrapper_start'],c):checked(name,start,words)
    a=c['allocation_start']+0x97c
    checked('allocation_clear',a,[d(32,11,24,0),mr(3,24),d(32,10,11,0x120),0x7d4903a6,0x4e800421,mr(5,3),d(14,4,0,0),mr(3,30),branch(a+32,c['zero_fill_start'],True)])
    for index,offset in enumerate([0xaf0,0xb00,0xb0c]):checked('post_allocation_'+str(index),c['allocation_start']+offset,[branch(c['allocation_start']+offset,c['post_allocation_helpers'][index],True)])
    table=c['metadata_table'];raw=view.read(table,73*4)
    if not inside(table,len(raw),[readonly]) or digest(raw)!=c['metadata_table_sha256']:raise FormatError('metadata table window outside .rdata/hash mismatch')
    words=list(struct.unpack('>73I',raw))
    if any(v%4 or not inside(v,4,code_ranges) for v in words) or words[72]!=c['size_getter_start']:raise FormatError('metadata size slot120 mismatch/non-code table word')
    cases=[]
    for row in class_report['classes']:
        size=row['size_operand'];cases.append(dict(name=row['registration_name'],constructed_metadata_size_operand=size,
            pointer_range_within_size=0xd8+4<=size,flag_range_within_size=0xe4+4<=size,
            synthetic_alignment_geometries=[zero_fill_partition(0x1000+i,size) for i in range(4)]))
    return dict(profile=c['profile'],windows=evidence,declared_functions=declared,
                metadata_chain=dict(size_word_offset=0x50,callback_word_offset=0x11c,metadata_table=table,size_virtual_slot=0x120,
                                    callback_argument='entry r9 -> r28 -> result+0x11c',size_argument='entry r4 -> base result+0x50',
                                    argument_preservation_inside_checked_helpers_verified=True,metadata_constructor_returns_entry_r3=True,
                                    full_class_registration_semantics_verified=False),
                callback_dispatch=dict(wrapper_start=c['wrapper_start'],pre_call_class_alias='entry r3 -> r23',allocation_result_alias='returned r3 -> r30',
                                       callback_field_word_offset=0x11c,fallback_class_helper=c['fallback_class_helper'],call_instruction=c['wrapper_start']+0x158,
                                       allocation_zero_result_skips_selected_callback_site=True,allocation_zero_branch_target=c['wrapper_start']+0x228,
                                       class_pointer_null_handling_verified=False,
                                       allocation_callee_register_preservation_verified=False,runtime_reachability_verified=False),
                clear_phase=dict(call_instruction=a+32,destination_register='r30',fill_value_operand=0,size_source='virtual slot120 result on r24',
                                 zero_helper_start=c['zero_fill_start'],geometry_domain='32-bit nonwrapping address; 0<=size<=MAX_IMAGE; writable destination; zero fill',
                                 store_sites=dict(prefix=[c['zero_fill_start']+20],blocks16=[c['zero_fill_start']+n for n in [56,60,64,68]],
                                                  words4=[c['zero_fill_start']+n for n in [92,104,116]],tail=[c['zero_fill_start']+n for n in [136,144,152]]),
                                 prefix_count_rule='min(size, (-address) & 3); CTR starts size+1',
                                 bulk_count_rule='remaining >> 4',word_count_rule='(remaining >> 2) & 3',tail_count_rule='remaining & 3',
                                 zero_after_clear_if_preconditions_hold=True,zero_at_callback_entry_verified=False,zero_at_rendering_verified=False,
                                 post_allocation_call_targets=c['post_allocation_helpers'],post_callback_call_targets=c['post_callback_helpers'],
                                 intervening_helper_semantics_verified=False,complete_allocation_control_flow_verified=False,
                                 runtime_memory_writability_verified=False,address_translation_verified=False),
                class_size_geometry_cases=cases,active_font_verified=False,constructor_effective_values_verified=False,image_modified=False,executed=False)
