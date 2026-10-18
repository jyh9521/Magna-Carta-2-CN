"""Exact static getter/overlay templates; no native-code execution or simulation."""
from __future__ import annotations
import struct
try:
    from .ppc_native_bindings import d,mr,rotate,branch,conditional,integer,checked_window,inside,mask32
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError
except ImportError:
    from ppc_native_bindings import d,mr,rotate,branch,conditional,integer,checked_window,inside,mask32
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError


def overlay_words(s):
    # Each flag test has a bounded forward bypass. No incoming native state is read.
    w=[d(32,11,3,0xe4),rotate(10,11,0,0,0),d(10,24,10,0),conditional(s+12,s+48,12)]
    for reg,offset in [(11,0),(10,4),(9,8),(8,12)]:w += [d(32,reg,3,0xc4+offset),d(36,reg,4,offset)]
    w += [d(32,11,3,0xe4),rotate(10,11,0,1,1),d(10,24,10,0),conditional(s+60,s+80,12),
          d(48,0,3,0xd4),d(48,13,4,12),0xed800372,d(52,12,4,12),
          d(32,11,3,0xe4),rotate(10,11,0,2,2),d(10,24,10,0),conditional(s+92,s+112,12),
          d(32,11,3,0xd8),d(10,24,11,0),conditional(s+104,s+112,12),d(36,11,4,0x20),
          d(32,11,3,0xe4),rotate(10,11,0,3,3),d(10,24,10,0),conditional(s+124,s+136,12),d(32,11,3,0xdc),d(36,11,4,0x38),
          d(32,11,3,0xe4),rotate(10,11,0,4,4),d(10,24,10,0),conditional(s+148,s+160,12),d(34,11,3,0xe0),d(38,11,4,0x3c),
          d(32,11,3,0xe4),rotate(10,11,0,4,4),d(10,24,10,0),0x4d9a0020,d(34,11,3,0xe1),d(38,11,4,0x3d),0x4e800020]
    return w


def final_words(s,c):
    return [0x7d8802a6,branch(s+4,c['prologue_helper'],True),d(37,1,1,-0xe0),d(32,11,3,0),mr(30,4),
            d(14,6,0,0),d(14,5,0,0),d(14,4,0,0),mr(31,3),d(32,10,11,0x128),d(14,29,0,0),0x7d4903a6,0x4e800421,
            mr(4,3),d(10,24,3,0),conditional(s+60,s+116,12),d(14,5,0,1),d(14,3,1,0x50),branch(s+72,c['producer_helper'],True),
            d(14,4,1,0x50),d(14,5,0,0x64),mr(3,30),branch(s+88,c['copy_call_target'],True),mr(4,30),mr(3,31),
            branch(s+100,c['overlay_start'],True),d(14,3,0,1),d(14,1,1,0xe0),branch(s+112,c['epilogue_helper']),
            mr(3,29),d(14,1,1,0xe0),branch(s+124,c['epilogue_helper'])]


def applied_tail_words(s,epilogue):
    return [d(32,11,29,0),d(14,6,0,0),d(14,5,0,0),d(32,4,1,0x50),mr(3,29),d(32,10,11,0x128),
            0x7d4903a6,0x4e800421,d(36,3,28,0),d(14,1,1,0x80),branch(s+40,epilogue)]


def verify_style_selection(view,rows,c,code_ranges):
    if c.get('profile')!='ppc-style-overlay-v1':raise FormatError('unsupported style selection profile')
    for key in ('overlay_start','final_start','prologue_helper','producer_helper','copy_call_target','epilogue_helper','applied_epilogue','final_wrapper_epilogue'):
        integer(c[key],1)
        if c[key]%4 or not inside(c[key],4,code_ranges):raise FormatError('style helper outside aligned code range')
    for key in ('final_wrapper_tail_offset','applied_wrapper_tail_offset'):integer(c[key],0,4096)
    by_name={r['method']:r['code_address'] for r in rows}
    fs=c['final_start'];ov=c['overlay_start'];ft=by_name[c['final_method']]+c['final_wrapper_tail_offset'];at=by_name[c['applied_method']]+c['applied_wrapper_tail_offset']
    windows=[('overlay',ov,overlay_words(ov)),('final',fs,final_words(fs,c)),
             ('final_wrapper_tail',ft,[mr(4,30),mr(3,28),branch(ft+8,fs,True),d(36,3,27,0),d(14,1,1,0xf0),branch(ft+20,c['final_wrapper_epilogue'])]),
             ('applied_wrapper_tail',at,applied_tail_words(at,c['applied_epilogue']))]
    evidence=[]
    for name,start,words in windows:
        raw=checked_window(view,start,start+len(words)*4,c[name+'_sha256'],code_ranges)
        if list(struct.unpack('>'+str(len(words))+'I',raw))!=words:raise FormatError('style '+name+' structural template mismatch')
        evidence.append(dict(name=name,start=start,end=start+len(raw),sha256=c[name+'_sha256'],instruction_count=len(words)))
    pdata=read_pdata(view.data,view.base,code_ranges);selected={};native_extents={}
    for row in rows:
        r=exact_record(pdata,row['code_address'])
        if r is None:raise FormatError('bound native method has no exact pdata record')
        native_extents[row['method']]=r
    for name,address in [('final',fs),('final_wrapper',by_name[c['final_method']]),('applied_wrapper',by_name[c['applied_method']])]:
        r=exact_record(pdata,address)
        if r is None:raise FormatError('required style pdata entry absent')
        selected[name]=r
    if selected['final']['end']!=fs+128 or selected['final_wrapper']['end']!=ft+24 or selected['applied_wrapper']['end']!=at+44:
        raise FormatError('style templates do not match declared pdata end')
    if any(r['start']<ov+188 and ov<r['end'] for r in pdata['records']):raise FormatError('overlay leaf unexpectedly covered by pdata')
    # All stores in the exact leaf template are r4-relative, non-updating and disjoint
    # except intentional alpha overlap. In particular only +0x20 can write the font.
    return dict(profile=c['profile'],windows=evidence,virtual_slot_byte_offset=0x128,
                final_virtual_result_zero_bypasses_producer_copy_overlay=True,
                producer_call_target=c['producer_helper'],copy_call_target=c['copy_call_target'],copy_call_size_operand=0x64,
                font_overlay=dict(flag_word_offset=0xe4,flag_mask=f'{mask32(2,2):08x}',pointer_word_offset=0xd8,
                                  output_word_offset=0x20,store_instruction=ov+108,
                                  required_conditions=['flag bit nonzero','pointer word nonzero'],
                                  guard_edges=[dict(address=ov+92,condition='flag bit zero',taken=ov+112,fallthrough=ov+96),
                                               dict(address=ov+104,condition='pointer word zero',taken=ov+112,fallthrough=ov+108)],
                                  bypass_preserves_output_word=True,source_pointer_dereferenced=False,
                                  semantic_field_names='high-confidence deduction; not a complete struct layout'),
                declared_function_records=selected,declared_native_extents=native_extents,
                overlay_pdata_record=None,overlay_window_end=ov+188,
                pdata_summary={k:v for k,v in pdata.items() if k!='records'},
                callee_register_preservation_verified=False,producer_semantics_verified=False,copy_semantics_verified=False,
                virtual_target_verified=False,constructor_values_verified=False,active_font_verified=False,
                complete_native_struct_layout_verified=False,image_modified=False,executed=False)
