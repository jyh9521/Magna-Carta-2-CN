"""Exact slot124 predicate words/edges, not a native evaluator or runtime probe."""
from __future__ import annotations
import struct

try:
    from .ppc_native_bindings import d, x, mr, branch, conditional, integer, inside, checked_window
    from .ppc_pdata import read_pdata, exact_record
    from .xex_image import FormatError
except ImportError:
    from ppc_native_bindings import d, x, mr, branch, conditional, integer, inside, checked_window
    from ppc_pdata import read_pdata, exact_record
    from xex_image import FormatError


def predicate_words(start, helper):
    return [0x7d8802a6, d(36,12,1,-8), d(37,1,1,-0x60), d(32,10,3,0x104), mr(11,3), mr(5,4),
        d(12,9,10,-1), x(31,3,9,10,136)|1, conditional(start+32,start+128,4,2),
        d(10,24,4,0), conditional(start+40,start+128,12),
        d(32,10,11,0x100), d(32,9,11,0xfc), d(32,8,11,0xf8), x(31,10,7,9,444),
        d(32,6,11,0xf4), x(31,7,4,8,444), x(31,4,3,6,444), d(10,24,3,0),
        conditional(start+76,start+124,4), d(14,6,0,0), d(14,4,11,0xe8), d(14,3,1,0x50),
        branch(start+92,helper,True), d(32,11,3,0), d(11,24,11,0), conditional(start+104,start+124,4),
        d(32,11,3,4), d(14,3,0,0), d(11,24,11,0), conditional(start+120,start+128,12),
        d(14,3,0,1), d(14,1,1,0x60), d(32,12,1,-8), 0x7d8803a6, 0x4e800020]


def verify_style_predicate(view, config, class_tables, code_ranges):
    if (not isinstance(config,dict) or set(config) != {'profile','start','sha256','reference_helper'}
            or config.get('profile') != 'ppc-style-predicate-v1'):
        raise FormatError('unsupported style predicate profile/fields')
    start = integer(config['start'],1); helper = integer(config['reference_helper'],1)
    if helper%4 or not inside(helper,4,code_ranges) or start<=helper<start+144:
        raise FormatError('style predicate helper outside aligned separate code range')
    raw = checked_window(view,start,start+144,config['sha256'],code_ranges)
    if list(struct.unpack('>36I',raw)) != predicate_words(start,helper):
        raise FormatError('style predicate structural template mismatch')
    classes = class_tables['classes']; getter = class_tables['getter']
    if not classes or any(row['slot124'] != start for row in classes):
        raise FormatError('style predicate does not match every supplied class slot124')
    if (getter['selection_virtual_slot'] != 0x124 or getter['nonzero_result_base']['addend'] != 0xe8
            or getter['zero_result_base']['addend'] != 0x174):
        raise FormatError('style predicate getter association mismatch')
    pdata = read_pdata(view.data,view.base,code_ranges); record = exact_record(pdata,start)
    if record is None or record['end'] != start+144 or record['prologue_end'] != start+12:
        raise FormatError('style predicate declared extent/prologue mismatch')
    return dict(profile=config['profile'],start=start,end=start+144,sha256=config['sha256'],
        instruction_count=36,declared_record=record,
        class_table_associations=[dict(native_name=row['native_name'],table_address=row['table_address'],
                                      slot=0x124,target=row['slot124']) for row in classes],
        static_class_slot_target_verified=True,
        entry_word_gate=dict(word_offset=0x104,load_instruction=start+12,
            normalization_words=[f'{w:08x}' for w in predicate_words(start,helper)[6:8]],
            normalization_interpretation='high-confidence nonzero boolean idiom; not runtime evaluation'),
        input_argument_alias=dict(entry_register='r4',helper_argument_register='r5'),
        four_word_gate=dict(offsets=[0x100,0xfc,0xf8,0xf4],operation='bitwise OR then zero comparison'),
        conditional_edges=[
            dict(address=start+32,condition='normalization CR0 not equal',taken=start+128,fallthrough=start+36),
            dict(address=start+40,condition='entry r4 equals zero',taken=start+128,fallthrough=start+44),
            dict(address=start+76,condition='four-word OR nonzero',taken=start+124,fallthrough=start+80),
            dict(address=start+104,condition='helper-return pointer word0 nonzero',taken=start+124,fallthrough=start+108),
            dict(address=start+120,condition='helper-return pointer word4 zero',taken=start+128,fallthrough=start+124)],
        helper_call=dict(address=start+92,target=helper,declared_record=exact_record(pdata,helper),
            argument_operands={'r3':'stack+0x50','r4':'entry r3+0xe8','r5':'entry r4','r6':0},
            returned_pointer_read_offsets=[0,4],semantics_verified=False,effects_verified=False),
        literal_return_assignments=[dict(address=start+112,register='r3',value=0),
                                    dict(address=start+124,register='r3',value=1)],
        direct_entry_object_stores_present=False,helper_effects_verified=False,
        serialized_field_names_verified=False,native_owner_pointer_identity_verified=False,
        callee_register_preservation_verified=False,runtime_dispatch_verified=False,
        active_font_verified=False,image_modified=False,executed=False)
