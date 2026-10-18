"""Static Font callback/serialization templates, not a PPC interpreter.

Archive virtual-call semantics and actual loaded font selection remain unknown.
All offsets refer to entry aliases, not a reconstructed universal object layout.
"""
from __future__ import annotations
import struct
try:
    from .ppc_native_bindings import d,x,mr,rotate,branch,conditional,integer,inside,checked_window
    from .ppc_class_tables import registration_words,font_initializer_words
    from .ppc_pdata import read_pdata,exact_record
    from .xex_image import FormatError,VirtualImage,digest,inspect_pe
except ImportError:
    from ppc_native_bindings import d,x,mr,rotate,branch,conditional,integer,inside,checked_window
    from ppc_class_tables import registration_words,font_initializer_words
    from ppc_pdata import read_pdata,exact_record
    from xex_image import FormatError,VirtualImage,digest,inspect_pe


def mtctr(reg):return 0x7c0903a6|reg<<21
def slwi(dst,src,n):return rotate(dst,src,n,0,31-n)
def add(dst,a,b):return x(31,dst,a,b,266)
def cmp(a,b):return x(31,24,a,b,0)


def record_words(kind):
    head=[0x7d8802a6,d(36,12,1,-8),d(62,30,1,-24),d(62,31,1,-16),d(37,1,1,-0x70),d(32,11,3,0)]
    tail=[mr(3,30),d(14,1,1,0x70),d(32,12,1,-8),0x7d8803a6,d(58,30,1,-24),d(58,31,1,-16),0x4e800020]
    if kind=='glyph_record':
        out=head+[d(14,5,0,4),mr(30,3),mr(31,4),d(32,10,11,4),mtctr(10),0x4e800421]
        for vtable,callee,offset,size in [(9,8,4,4),(7,6,8,4),(11,10,12,4),(9,8,16,1)]:
            out += [d(32,vtable,30,0),mr(3,30),d(14,5,0,size),d(14,4,31,offset),d(32,callee,vtable,4),mtctr(callee),0x4e800421]
        return out+tail
    if kind=='map_record':
        return head+[mr(31,4),d(14,5,0,2),d(14,4,4,4),mr(30,3),d(32,10,11,4),mtctr(10),0x4e800421,
            d(32,9,30,0),mr(3,30),d(14,5,0,2),d(14,4,31,6),d(32,8,9,4),mtctr(8),0x4e800421]+tail
    raise FormatError('unsupported font record template')


def font_words(s,c):
    return [0x7d8802a6,branch(s+4,c['save29'],True),d(37,1,1,-0x70),mr(30,3),mr(29,4),branch(s+20,c['parent'],True),
        d(14,4,30,0x3c),mr(3,29),d(14,31,30,0x48),branch(s+36,c['glyph_array'],True),mr(4,31),branch(s+44,c['texture_array'],True),
        d(32,11,3,0),d(14,5,0,4),d(14,4,30,0x6c),d(32,10,11,4),mtctr(10),0x4e800421,
        d(14,31,30,0x54),mr(3,29),mr(4,31),branch(s+84,c['map_array'],True),d(32,9,29,0x10),d(11,24,9,0),
        conditional(s+96,s+196,12),d(32,11,31,0x10),d(32,10,31,4),d(14,11,11,4),slwi(9,11,1),cmp(9,10),
        conditional(s+120,s+160,4,24),d(32,11,31,0x10),slwi(9,11,1),slwi(11,9,0),d(36,9,31,0x10),d(32,8,31,4),
        d(14,7,11,4),slwi(6,7,1),cmp(6,8),conditional(s+156,s+124,12,24),d(11,24,10,0),conditional(s+164,s+180,12),
        mr(3,31),branch(s+172,c['rehash'],True),branch(s+176,s+196),d(32,3,31,12),branch(s+184,c['free'],True),d(14,11,0,0),
        d(36,11,31,12),d(32,11,29,0),d(14,5,0,4),d(14,4,30,0x68),mr(3,29),d(32,10,11,4),mtctr(10),0x4e800421,
        d(14,1,1,0x70),branch(s+228,c['restore29'])]


def multifont_words(s,c):
    return [0x7d8802a6,d(36,12,1,-8),d(62,30,1,-24),d(62,31,1,-16),d(37,1,1,-0x70),mr(31,3),mr(30,4),
        branch(s+28,c['font'],True),d(14,4,31,0x70),mr(3,30),branch(s+40,c['float_array'],True),d(14,1,1,0x70),
        d(32,12,1,-8),0x7d8803a6,d(58,30,1,-24),d(58,31,1,-16),0x4e800020]


def array_words(s,c,glyph):
    # Explicit two variants: 20-byte glyph arithmetic is not an 8-byte map.
    out=[0x7d8802a6,branch(s+4,c['save27'],True),d(37,1,1,-0x90),d(32,7 if glyph else 11,3,0),mr(30,4),
        d(32,10,4,8),d(14,27,4,4),d(32,11 if glyph else 9,4,4),mr(31,3)]
    if glyph:out += [slwi(9,10,2),slwi(8,11,2),d(32,6,7,20),add(5,10,9),add(4,11,8),slwi(5,5,2),slwi(4,4,2),mtctr(6)]
    else:out += [slwi(5,10,3),slwi(4,9,3),d(32,8,11,20),mtctr(8)]
    out += [0x4e800421,d(32,11,31,0),d(14,5,0,4),d(32,3 if glyph else 7,31,16)]
    if glyph:out += [d(11,24,3,0),mr(3,31)]
    else:out += [mr(3,31),d(11,24,7,0)]
    # Internal labels differ because the glyph stride computation takes more words.
    save=248 if glyph else 224;done=312 if glyph else 288;loop=172 if glyph else 156;save_loop=276 if glyph else 252
    out += [d(32,10,11,4),mtctr(10),conditional(s+len(out)*4+8,s+save,12),d(14,4,1,80),0x4e800421,
        d(32,11,1,80),d(32,8,30,8),d(14,9,0,0),d(36,9,27,0),cmp(8,11)]
    pc=s+len(out)*4
    out += [conditional(pc,pc+28,12),d(36,11,30,8),d(14,5,0,8),d(14,4,0,20 if glyph else 8),mr(3,30),branch(pc+20,c['resize'],True),d(32,11,1,80),
        d(14,29,0,0),d(11,24,11,0),conditional(pc+36,s+done,4,25),d(14,5,0,20 if glyph else 8),d(14,4,0,1),mr(3,30),branch(pc+52,c['append'],True),
        mr(11,3),d(32,10,30,0),mr(3,31)]
    out += [slwi(9,11,2),add(11,11,9),slwi(11,11,2)] if glyph else [slwi(11,11,3)]
    out += [add(4,11,10)];pc=s+len(out)*4;record=c['glyph_record' if glyph else 'map_record']
    out += [branch(pc,record,True),d(32,10,1,80),d(14,29,29,1),cmp(29,10),conditional(pc+16,s+loop,12,24),mr(3,31),d(14,1,1,0x90),branch(pc+28,c['restore27']),
        mr(4,27),0x4e800421,d(32,9,27,0),d(14,29,0,0),d(11,24,9,0),conditional(pc+52,s+done,4,25),d(14,28,0,0),
        d(32,11,30,0),mr(3,31),add(4,28,11),branch(pc+72,record,True),d(32,11,27,0),d(14,29,29,1),d(14,28,28,20 if glyph else 8),
        cmp(29,11),conditional(pc+92,s+save_loop,12,24),mr(3,31),d(14,1,1,0x90),branch(pc+104,c['restore27'])]
    return out


def templates(c):
    return dict(font=font_words(c['font'],c),multifont=multifont_words(c['multifont'],c),
        glyph_array=array_words(c['glyph_array'],c,True),map_array=array_words(c['map_array'],c,False),
        glyph_record=record_words('glyph_record'),map_record=record_words('map_record'))


def inspect_serialization(image,plan):
    if plan.get('schema_version')!=1 or plan.get('profile')!='ppc-font-serialization-v1':raise FormatError('unsupported font serialization profile')
    if set(plan)!={'schema_version','profile','image_sha256','image_base','code_ranges','readonly_range','calls','registration','windows','classes'}:
        raise FormatError('font serialization plan fields mismatch')
    if digest(image)!=plan['image_sha256']:raise FormatError('font serialization image SHA256 mismatch')
    base=integer(plan['image_base']);view=VirtualImage(image,base);pe=inspect_pe(image,base,None)
    code=plan['code_ranges'];readonly=plan['readonly_range']
    if not isinstance(readonly,list) or len(readonly)!=2 or any(type(v) is not int for v in readonly) or readonly[1]<=readonly[0]:
        raise FormatError('font serialization readonly range malformed')
    view.read(readonly[0],readonly[1]-readonly[0])
    sections=[s for s in pe['sections'] if s['name']=='.rdata']
    if len(sections)!=1:raise FormatError('font serialization requires one .rdata')
    section=sections[0]
    if readonly!=[base+section['rva'],base+section['rva']+section['virtual_size']] or int(section['flags'],16)&0xa0000000 or not int(section['flags'],16)&0x40000000:
        raise FormatError('font serialization readonly range mismatch')
    if any(a<readonly[1] and readonly[0]<b for a,b in code):raise FormatError('font serialization code/data overlap')
    pd=read_pdata(image,base,code);c=plan['calls'];windows=[]
    pdstart=base+pd['directory_rva']
    if pdstart<readonly[1] and readonly[0]<pdstart+pd['directory_size']:raise FormatError('font serialization pdata/readonly overlap')
    keys={'font','multifont','glyph_array','map_array','glyph_record','map_record','save29','restore29','parent',
          'texture_array','rehash','free','float_array','save27','restore27','resize','append'}
    if not isinstance(c,dict) or set(c)!=keys:raise FormatError('font serialization call fields mismatch')
    for address in c.values():
        integer(address,1)
        if address%4 or not inside(address,4,code):raise FormatError('font serialization helper outside aligned code')
    if set(plan['windows'])!={'font','multifont','glyph_array','map_array','glyph_record','map_record'}:
        raise FormatError('font serialization window fields mismatch')
    for key in ('shared_callback','registration_helper'):
        address=integer(plan['registration'][key],1)
        if address%4 or not inside(address,4,code):raise FormatError('font registration helper outside aligned code')
    address=integer(plan['registration']['common_name_address'],1)
    if address%2 or not inside(address,2,[readonly]):raise FormatError('font registration common name outside readonly')
    for name,words in templates(c).items():
        start=integer(c[name],1);row=plan['windows'][name]
        raw=checked_window(view,start,start+len(words)*4,row['sha256'],code)
        if list(struct.unpack('>'+str(len(words))+'I',raw))!=words:raise FormatError('font serialization '+name+' structural mismatch')
        rec=exact_record(pd,start)
        if rec is None or rec['end']!=start+len(raw) or rec['prologue_words']!=row['prologue_words']:raise FormatError('font serialization pdata extent/prologue mismatch')
        windows.append(dict(label=name,start=start,end=start+len(raw),instruction_count=len(words),sha256=digest(raw),declared_record=rec))
    classes=plan['classes']
    if not isinstance(classes,list) or [r['name'] for r in classes]!=['UFont','UMultiFont']:raise FormatError('font class scope/order mismatch')
    out=[]
    for row,family in zip(classes,['Font','MultiFont']):
        name=integer(row['name_address'],1);encoded=(row['name']+'\0').encode('utf-16-be')
        if name%2 or not inside(name,len(encoded),[readonly]) or view.read(name,len(encoded))!=encoded:raise FormatError('font operand-anchored class literal mismatch')
        start=integer(row['registration_start'],1);callback=integer(row['callback'],1);table=integer(row['table'],1)
        reg=registration_words(start+52,name,callback,0x70 if family=='Font' else 0x7c,plan['registration'])
        raw=checked_window(view,start+52,start+116,row['registration_sha256'],code)
        if list(struct.unpack('>16I',raw))!=reg:raise FormatError('font class registration structural mismatch')
        rec=exact_record(pd,start)
        if rec is None or rec['end']!=start+280 or rec['prologue_words']!=5:raise FormatError('font class registration pdata mismatch')
        words=font_initializer_words(family,table);raw=checked_window(view,callback,callback+52,row['callback_sha256'],code)
        if list(struct.unpack('>13I',raw))!=words:raise FormatError('font class callback structural mismatch')
        count=70 if family=='Font' else 71
        if table%4 or not inside(table,count*4,[readonly]):raise FormatError('font table outside readonly range')
        raw=view.read(table,count*4)
        if digest(raw)!=row['table_sha256'] or view.word(table+0x34)!=c['font' if family=='Font' else 'multifont']:raise FormatError('font table hash/slot34 mismatch')
        out.append(dict(native_name=row['name'],literal_address=name,passed_name_address=name+2,literal_preceding_nul_required=False,
            registration_start=start,callback=callback,table=table,table_window_words=count,complete_table_extent_verified=False,slot34_target=view.word(table+0x34),
            callback_map_zero_offsets=[0x54,0x58,0x5c,0x60],callback_bucket_count_offset=0x64,callback_bucket_count=8,callback_initializes_mode_or_spacing=False))
    return dict(schema_version=1,profile=plan['profile'],image_sha256=digest(image),classes=out,windows=windows,
        native_entry_offsets=dict(glyph_array=0x3c,texture_array=0x48,map_array=0x54,spacing_word=0x6c,mode_word=0x68,multifont_extra_array=0x70),
        transfer_order=['glyph_array','texture_array','spacing_word','map_array','mode_word'],archive_vtable_transfer_slot=4,
        glyph_record=dict(native_stride=20,transferred_offsets=[0,4,8,12,16],transfer_sizes=[4,4,4,4,1],serialized_bytes=17),
        map_record=dict(native_stride=8,transferred_offsets=[4,6],transfer_sizes=[2,2],serialized_bytes=4,next_link_serialized=False),
        static_template_verified=True,archive_virtual_call_semantics_verified=False,callee_register_preservation_verified=False,
        serialized_field_identity_verified=False,runtime_font_selection_verified=False,game_rendering_verified=False,executed=False,image_modified=False)
