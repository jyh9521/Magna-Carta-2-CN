"""Bounded reference-helper code/name associations; no native execution."""
from __future__ import annotations
import re
import struct

try:
    from .ppc_native_bindings import d,x,mr,branch,conditional,integer,inside,checked_window
    from .ppc_class_tables import halves,registration_words
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError
except ImportError:
    from ppc_native_bindings import d,x,mr,branch,conditional,integer,inside,checked_window
    from ppc_class_tables import halves,registration_words
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError


def helper_words(s,c):
    rows=c['fallbacks']; tag=[halves(row['tag_address']) for row in rows]
    return [0x7d8802a6,branch(s+4,c['save_helper'],True),d(37,1,1,-0x80),d(14,11,0,0),mr(28,3),mr(30,4),
        d(36,11,3,0),mr(31,6),d(36,11,3,4),d(10,24,6,0),conditional(s+40,s+48,12),d(36,11,6,0),
        d(32,29,30,0),d(11,24,29,0),conditional(s+56,s+72,4),d(32,11,30,4),d(11,24,11,0),conditional(s+68,s+148,12),
        d(10,24,5,0),conditional(s+76,s+148,12),d(58,11,30,0),d(14,4,1,0x50),d(14,3,5,0xb0),d(62,11,1,0x50),
        branch(s+96,c['lookup_call'],True),d(10,24,3,0),conditional(s+104,s+148,12),d(32,11,30,4),d(10,24,31,0),
        d(36,29,28,0),mr(3,28),d(36,11,28,4),conditional(s+128,s+352,12),d(14,11,0,1),d(36,11,31,0),
        d(14,1,1,0x80),branch(s+144,c['restore_helper']),d(32,11,30,8),d(10,24,11,0),conditional(s+156,s+348,12),
        branch(s+160,rows[0]['registration_start'],True),d(32,11,30,8),d(10,24,11,0),conditional(s+172,s+196,12),
        x(31,24,11,3,32),conditional(s+180,s+280,12),d(32,11,11,0x3c),d(10,24,11,0),conditional(s+192,s+176,4),
        branch(s+196,rows[1]['registration_start'],True),d(32,11,30,8),d(10,24,11,0),conditional(s+208,s+232,12),
        x(31,24,11,3,32),conditional(s+216,s+292,12),d(32,11,11,0x3c),d(10,24,11,0),conditional(s+228,s+212,4),
        branch(s+232,rows[2]['registration_start'],True),d(32,11,30,8),d(10,24,11,0),conditional(s+244,s+348,12),
        x(31,24,11,3,32),conditional(s+252,s+304,12),d(32,11,11,0x3c),d(10,24,11,0),conditional(s+264,s+248,4),
        mr(3,28),d(14,1,1,0x80),branch(s+276,c['restore_helper']),
        d(15,11,0,tag[0][0]),d(14,4,11,tag[0][1]),branch(s+288,s+312),
        d(15,11,0,tag[1][0]),d(14,4,11,tag[1][1]),branch(s+300,s+312),
        d(15,11,0,tag[2][0]),d(14,4,11,tag[2][1]),d(14,7,0,1),d(14,6,0,1),d(14,5,0,0),d(14,3,1,0x50),
        branch(s+328,c['make_name_call'],True),d(32,10,1,0x50),d(32,9,1,0x54),d(36,10,28,0),d(36,9,28,4),
        mr(3,28),d(14,1,1,0x80),branch(s+356,c['restore_helper'])]


def literal(view,address,text,readonly,native=False):
    integer(address,1)
    pattern='U[A-Za-z_][A-Za-z0-9_]{0,127}' if native else '[A-Za-z_][A-Za-z0-9_]{0,127}'
    if not isinstance(text,str) or not re.fullmatch(pattern,text):
        raise FormatError('invalid helper name literal')
    encoded=(text+'\0').encode('utf-16-be')
    if (address%2 or not inside(address-2,len(encoded)+2,[readonly])
            or view.read(address-2,2)!=b'\0\0' or view.read(address,len(encoded))!=encoded):
        raise FormatError('helper literal boundary/content mismatch')


def verify_style_reference_helper(view,c,predicate,registration_config,class_tables,code_ranges):
    fields={'profile','start','sha256','save_helper','restore_helper','lookup_call','make_name_call','fallbacks'}
    if not isinstance(c,dict) or set(c)!=fields or c.get('profile')!='ppc-style-reference-helper-v1':
        raise FormatError('unsupported style reference helper profile/fields')
    s=integer(c['start'],1); rows=c['fallbacks']; readonly=class_tables['readonly_table_range']
    if s!=predicate['helper_call']['target']:
        raise FormatError('reference helper does not match verified predicate call')
    if not isinstance(rows,list) or len(rows)!=3:
        raise FormatError('reference helper requires three ordered fallback associations')
    for key in ['save_helper','restore_helper','lookup_call','make_name_call']:
        address=integer(c[key],1)
        if address%4 or not inside(address,4,code_ranges) or s<=address<s+360:
            raise FormatError('reference helper external target outside aligned separate code range')
    pdata=read_pdata(view.data,view.base,code_ranges);record=exact_record(pdata,s)
    if record is None or record['end']!=s+360 or record['prologue_end']!=s+12:
        raise FormatError('reference helper declared extent/prologue mismatch')
    associations=[]; seen=set()
    row_fields={'native_name','name_address','registration_start','registration_sha256','callback_word','size_operand','tag_name','tag_address'}
    for index,row in enumerate(rows):
        if not isinstance(row,dict) or set(row)!=row_fields:
            raise FormatError('invalid reference helper fallback fields')
        literal(view,row['name_address'],row['native_name'],readonly,True)
        literal(view,row['tag_address'],row['tag_name'],readonly)
        reg=integer(row['registration_start'],1); callback=integer(row['callback_word'],1)
        size=integer(row['size_operand'],1,32767); window=reg+52
        identity=row['native_name'],row['tag_name'],reg
        if any(a==identity[0] or b==identity[1] or d==identity[2] for a,b,d in seen):
            raise FormatError('duplicate reference helper fallback association')
        seen.add(identity)
        if (reg%4 or callback%4 or not inside(callback,4,code_ranges) or s<=reg<s+360 or s<=callback<s+360):
            raise FormatError('reference helper class target outside aligned separate code range')
        rec=exact_record(pdata,reg)
        if rec is None or not rec['start']<=window<window+64<=rec['end']:
            raise FormatError('reference helper registration lacks covering declared entry')
        raw=checked_window(view,window,window+64,row['registration_sha256'],code_ranges)
        if list(struct.unpack('>16I',raw))!=registration_words(window,row['name_address'],callback,size,registration_config):
            raise FormatError('reference helper registration argument template mismatch')
        associations.append(dict(native_name=row['native_name'],name_address=row['name_address'],tag_name=row['tag_name'],
            tag_address=row['tag_address'],registration_start=reg,registration_window=window,registration_sha256=row['registration_sha256'],
            declared_registration_record=rec,callback_operand=callback,size_operand=size,
            helper_call_instruction=s+[160,196,232][index],tag_operand_instruction=s+[280,292,304][index],
            runtime_class_identity_verified=False,callback_semantics_verified=False))
    raw=checked_window(view,s,s+360,c['sha256'],code_ranges)
    if list(struct.unpack('>90I',raw))!=helper_words(s,c):
        raise FormatError('reference helper structural template mismatch')
    return dict(profile=c['profile'],start=s,end=s+360,sha256=c['sha256'],instruction_count=90,declared_record=record,
        predicate_call_association_verified=True,class_name_tag_operand_associations=associations,
        pre_call_register_aliases={'r28':'post-prologue-save r3/output-like','r30':'post-prologue-save r4/reference-like',
                                  'r31':'post-prologue-save r6/optional-flag-like'},
        direct_output_zero_stores=[s+24,s+32],direct_optional_flag_stores=[dict(address=s+44,value=0),dict(address=s+136,value=1)],
        reference_input_word_offsets=[0,4,8],context_addend_before_lookup=0xb0,
        lookup_call=dict(address=s+96,target=c['lookup_call'],semantics_verified=False),
        class_chain_loops=[dict(comparison=s+offset,parent_load=s+offset+8,backedge=s+offset+16,parent_word_offset=0x3c)
                           for offset in [176,212,248]],
        fallback_name_call=dict(address=s+328,target=c['make_name_call'],operand_constants={'r5':0,'r6':1,'r7':1},semantics_verified=False),
        final_stack_to_output_stores=[s+340,s+344],return_pointer_alias='r28; preservation across external calls unverified',
        loop_termination_verified=False,external_call_semantics_verified=False,callee_register_preservation_verified=False,
        serialized_native_layout_verified=False,native_owner_pointer_identity_verified=False,runtime_dispatch_verified=False,
        effective_style_verified=False,active_font_verified=False,image_modified=False,executed=False)
