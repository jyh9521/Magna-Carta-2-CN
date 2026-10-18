"""Exact metric-path instruction patterns; no execution or runtime font model."""
from __future__ import annotations
import struct
try:
    from .ppc_native_bindings import d,x,mr,rotate,branch,conditional,integer,inside,checked_window
    from .ppc_class_tables import halves
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError
except ImportError:
    from ppc_native_bindings import d,x,mr,rotate,branch,conditional,integer,inside,checked_window
    from ppc_class_tables import halves
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError


def fp(dst,src,xo):return 63<<26|dst<<21|src<<11|xo<<1
def fa(op,dst,a,b,c,xo):return op<<26|dst<<21|a<<16|b<<11|c<<6|xo<<1
def ext(dst,src):return x(31,src,dst,0,986)


def caller_tail_words(s,c):
    mh,ml=halves(c['null_message_address']);eh,el=halves(c['empty_string_address'])
    return [d(32,3,24,0x3c),d(10,24,3,0),conditional(s+8,s+36,4),d(15,11,0,mh),mr(3,30),d(14,4,11,ml),
        branch(s+24,c['null_call'],True),d(14,3,31,0x88),branch(s+32,s+136),d(32,11,31,0x8c),d(11,24,11,0),
        conditional(s+44,s+56,12),d(32,6,31,0x88),branch(s+52,s+64),d(15,11,0,eh),d(14,6,11,el),
        d(14,5,31,0x78),d(14,4,31,0x80),branch(s+72,c['helper_start'],True),d(32,11,31,0x78),d(32,10,31,0x80),
        ext(9,11),ext(8,10),d(62,9,31,0x80),d(50,0,31,0x80),d(62,8,31,0x80),d(50,13,31,0x80),
        fp(11,0,846),fp(12,13,846),fp(9,11,12),fp(10,12,12),d(52,10,23,0),d(52,9,28,0),d(14,3,31,0x88),
        branch(s+136,c['string_cleanup'],True),d(14,1,31,0xf0),d(50,31,1,-0x58),branch(s+148,c['caller_restore'])]


def helper_words(s,c):
    zh,zl=halves(c['zero_float_address']);uh,ul=halves(c['unit_float_address'])
    return [0x7d8802a6,d(36,12,1,-8),d(62,30,1,-0x18),d(62,31,1,-0x10),d(37,1,1,-0xa0),
        d(14,11,0,0),mr(31,4),d(36,11,4,0),mr(30,5),d(10,24,3,0),d(36,11,5,0),conditional(s+44,s+164,12),
        d(15,10,0,zh),d(36,3,1,0x68),d(15,9,0,uh),d(14,11,0,3),mr(4,6),d(38,11,1,0x6c),d(14,3,1,0x50),
        d(48,0,10,zl),d(38,11,1,0x6d),d(48,13,9,ul),d(52,0,1,0x50),d(52,0,1,0x54),d(52,0,1,0x58),d(52,0,1,0x5c),
        d(52,13,1,0x60),d(52,13,1,0x64),d(52,0,1,0x70),d(52,0,1,0x74),d(52,0,1,0x78),d(52,0,1,0x7c),d(52,0,1,0x80),d(52,0,1,0x84),
        branch(s+136,c['leaf_start'],True),d(48,0,1,0x58),d(48,13,1,0x5c),fp(12,0,15),x(31,12,0,31,983),fp(11,13,15),x(31,11,0,30,983),
        d(14,1,1,0xa0),d(32,12,1,-8),0x7d8803a6,d(58,30,1,-0x18),d(58,31,1,-0x10),0x4e800020]


def leaf_words(s,c):
    zh,zl=halves(c['zero_float_address']);gh,gl=halves(c['global_pointer_slot'])
    return [d(15,11,0,zh),d(32,7,3,0x18),d(10,24,7,0),d(48,10,11,zl),d(52,10,3,8),d(52,10,3,12),0x4d9a0020,
        d(32,11,7,0x6c),mr(6,4),d(40,8,4,0),ext(10,11),d(10,24,8,0),d(62,10,1,-0x10),d(50,0,1,-0x10),fp(13,0,846),fp(9,13,12),0x4d9a0020,
        d(15,11,0,gh),d(48,12,3,0x10),d(48,11,3,0x14),d(32,5,11,gl),d(32,11,7,0x68),fp(13,10,72),fp(0,10,72),d(11,24,11,0),conditional(s+100,s+232,12),
        d(32,9,7,0x60),d(10,24,9,0),conditional(s+112,s+216,12),d(32,11,7,0x58),d(11,24,11,0),conditional(s+124,s+216,4,25),
        d(32,11,7,0x64),rotate(10,8,0,16,31),d(14,11,11,-1),x(31,11,8,10,28),rotate(4,8,2,0,29),x(31,11,4,9,23),d(11,24,11,-1),conditional(s+156,s+216,12),
        d(32,9,7,0x54),rotate(11,11,3,0,28),x(31,11,11,9,266),d(40,8,11,4),x(31,24,8,10,32),conditional(s+180,s+204,12),
        d(32,11,11,0),d(11,24,11,-1),conditional(s+192,s+164,4),d(14,11,0,0x7f),branch(s+200,s+296),d(14,11,11,6),d(10,24,11,0),conditional(s+212,s+224,4),
        d(14,11,0,0x7f),branch(s+220,s+296),d(40,11,11,0),branch(s+228,s+296),d(32,10,7,0x40),rotate(11,8,0,16,31),x(31,24,11,10,0),conditional(s+244,s+256,12,24),
        d(14,11,0,0x7f),branch(s+252,s+296),rotate(10,11,2,0,29),d(32,9,7,0x3c),x(31,11,11,10,266),rotate(11,11,2,0,29),x(31,10,11,9,266),
        d(14,11,0,0x7f),d(32,9,10,0xc),d(11,24,9,0),conditional(s+288,s+296,12),mr(11,8),d(32,10,7,0x40),rotate(11,11,0,16,31),x(31,24,11,10,0),conditional(s+308,s+416,4,24),
        rotate(9,11,2,0,29),d(32,10,7,0x3c),d(32,8,7,0x4c),x(31,4,11,9,266),rotate(11,4,2,0,29),x(31,10,11,10,266),d(34,11,10,0x10),x(31,24,11,8,0),conditional(s+344,s+416,4,24),
        d(32,9,7,0x48),rotate(8,11,2,0,29),x(31,4,8,9,23),d(10,24,4,0),conditional(s+364,s+416,12),d(32,11,10,0xc),d(32,10,10,8),ext(9,11),ext(8,10),
        d(62,9,1,-0x10),d(50,0,1,-0x10),d(62,8,1,-8),d(50,13,1,-8),fp(7,0,846),fp(8,13,846),fp(13,7,12),fp(0,8,12),
        d(41,11,6,2),d(48,8,5,0x430),fa(59,0,0,8,0,20),d(10,24,11,0),conditional(s+432,s+440,12),fa(59,0,0,9,0,21),fa(59,13,11,0,13,25),
        d(48,8,3,0xc),d(48,7,3,8),fa(59,6,12,7,0,29),d(52,6,3,8),fa(59,5,8,13,0,20),fa(63,4,5,13,8,23),d(52,4,3,0xc),d(40,8,6,0),d(10,24,8,0),conditional(s+480,s+84,4),0x4e800020]


def verify_measurement(view,c,tables,code_ranges,string_range,data_range):
    expected={'profile','canvas_label','textsize_method','caller_tail_offset','caller_tail_sha256','null_message_address','null_call',
        'empty_string_address','string_cleanup','caller_restore','helper_start','helper_sha256','leaf_start','leaf_sha256',
        'zero_float_address','unit_float_address','global_pointer_slot'}
    if not isinstance(c,dict) or set(c)!=expected or c.get('profile')!='ppc-canvas-measurement-v1':
        raise FormatError('unsupported measurement path profile/fields')
    matches=[t for t in tables if t['label']==c['canvas_label'] and t['engine_class']=='Canvas']
    if len(matches)!=1 or c['textsize_method']!='TextSize':raise FormatError('measurement path requires exact Canvas.TextSize scope')
    rows=[b for b in matches[0]['bindings'] if b['method']==c['textsize_method']]
    if len(rows)!=1:raise FormatError('measurement path method missing/ambiguous')
    binding=rows[0];offset=integer(c['caller_tail_offset'],0,65536);caller=binding['code_address']+offset
    if caller%4 or binding['declared_function_record']['end']!=caller+152:
        raise FormatError('measurement caller tail does not match declared extent')
    for key in ['helper_start','leaf_start','null_call','string_cleanup','caller_restore']:
        a=integer(c[key],1)
        if a%4 or not inside(a,4,code_ranges):raise FormatError('measurement target outside aligned code range')
    for key,bits in [('zero_float_address',bytes(4)),('unit_float_address',bytes.fromhex('3f800000'))]:
        a=integer(c[key],1)
        if a%4 or not inside(a,4,[string_range]) or view.read(a,4)!=bits:raise FormatError('measurement float constant mismatch')
    for key in ['null_message_address','empty_string_address']:
        a=integer(c[key],1)
        if a%2 or not inside(a,2,[string_range]):raise FormatError('measurement string operand outside range')
    if view.read(c['empty_string_address'],2)!=bytes(2):raise FormatError('measurement empty-string operand is not zero')
    slot=integer(c['global_pointer_slot'],1)
    if slot%4 or not inside(slot,4,[data_range]):raise FormatError('measurement global pointer slot outside data range')
    windows=[('caller_tail',caller,caller_tail_words(caller,c)),('helper',c['helper_start'],helper_words(c['helper_start'],c)),
             ('leaf',c['leaf_start'],leaf_words(c['leaf_start'],c))]
    spans=[];evidence=[]
    for name,start,words in windows:
        end=start+len(words)*4
        if any(start<b and a<end for a,b in spans):raise FormatError('measurement code windows overlap')
        spans.append((start,end));raw=checked_window(view,start,end,c[name+'_sha256'],code_ranges)
        if list(struct.unpack('>'+str(len(words))+'I',raw))!=words:raise FormatError('measurement '+name+' structural template mismatch')
        evidence.append(dict(name=name,start=start,end=end,sha256=c[name+'_sha256'],instruction_count=len(words)))
    if any(a<=c[key]<b for key in ['null_call','string_cleanup','caller_restore'] for a,b in spans):
        raise FormatError('measurement external target overlaps checked body')
    pdata=read_pdata(view.data,view.base,code_ranges);helper=exact_record(pdata,c['helper_start']);leaf=c['leaf_start']
    if helper is None or helper['end']!=c['helper_start']+188 or helper['prologue_end']!=c['helper_start']+20:
        raise FormatError('measurement helper declared extent/prologue mismatch')
    if any(r['start']<leaf+488 and leaf<r['end'] for r in pdata['records']):
        raise FormatError('measurement leaf unexpectedly covered by pdata')
    return dict(profile=c['profile'],source_binding=binding,windows=evidence,helper_declared_record=helper,leaf_declared_record=None,
        leaf_extent_kind='bounded call-free selected window ending BLR, not pdata-proven extent',
        caller_font_like_load=dict(register='r24',word_offset=0x3c,helper_call=caller+72,null_branch_bypasses_helper=True),
        helper_parameter_block=dict(stack_base=0x50,font_like_word_offset=0x18,scale_offsets=[0x10,0x14],unit_scale_bits='3f800000'),
        leaf_parameter_block=dict(font_like_word_offset=0x18,output_float_offsets=[8,12],string_code_unit_bytes=2),
        native_observed_offsets=dict(mode_word=0x68,glyph_array=0x3c,glyph_count=0x40,glyph_stride=20,
            glyph_width=8,glyph_height=12,glyph_texture_byte=16,texture_array=0x48,texture_count=0x4c,spacing_word=0x6c),
        zero_mode_path=dict(code_unit_mask=65535,in_range_height_nonzero_keeps_code_unit=True,out_of_range_or_zero_height_fallback=127),
        nonzero_mode_path=dict(element_array=0x54,element_count=0x58,bucket_array=0x60,bucket_mask_source=0x64,
            entry_stride=8,next_offset=0,key_u16_offset=4,value_u16_offset=6,chain_end_word=-1,missing_fallback=127),
        global_float_adjustment=dict(pointer_slot=slot,float_word_offset=0x430,runtime_pointer_value_verified=False),
        caller_entry_object_alias_verified=False,callee_register_preservation_verified=False,serialized_native_layout_verified=False,
        source_font_mode_bridge_verified=False,runtime_font_selection_verified=False,loop_termination_verified=False,
        native_rendering_path_equivalence_verified=False,game_rendering_verified=False,image_modified=False,executed=False)
