"""Read CE/PPC packed function records from a reconstructed virtual PE image.

Format research: hedge-dev/XenonRecomp ddd128bcca99fe8bfbb99bea583c972351fa6ace,
XenonUtils/xbox.h and XenonRecomp/recompiler.cpp (MIT). Independent reader;
no unwinding, loading, disassembly or execution. Flags remain raw metadata.
"""
from __future__ import annotations
import struct
try:
    from .xex_image import FormatError,VirtualImage,inspect_pe,digest
except ImportError:
    from xex_image import FormatError,VirtualImage,inspect_pe,digest


def read_pdata(image,base,code_ranges):
    view=VirtualImage(image,base);pe=inspect_pe(image,base,None)
    opt=pe['header_offset']+24
    u16=lambda offset:struct.unpack('<H',view.read(base+offset,2))[0]
    u32=lambda offset:struct.unpack('<I',view.read(base+offset,4))[0]
    count=u32(opt+92);opt_size=u16(pe['header_offset']+20)
    if not 4<=count<=16 or opt_size<96+count*8:
        raise FormatError('exception directory absent/truncated/unsupported')
    rva,size=u32(opt+120),u32(opt+124)
    sections=[s for s in pe['sections'] if s['name']=='.pdata']
    if (len(sections)!=1 or rva!=sections[0]['rva'] or size!=sections[0]['virtual_size']
        or rva%4 or not 0<size<=8*131072 or size%8):
        raise FormatError('exception directory does not match bounded .pdata section')
    if not 1<=len(code_ranges)<=32:raise FormatError('invalid pdata code range count')
    for a,b in code_ranges:
        if type(a) is not int or type(b) is not int or a%4 or b%4 or b<=a:
            raise FormatError('invalid pdata code range')
        view.read(a,b-a)
        if a<base+rva+size and base+rva<b:raise FormatError('pdata overlaps code range')
    raw=view.read(base+rva,size);records=[];previous_end=-1;flags={}
    for index,(start,packed) in enumerate(struct.iter_unpack('>II',raw)):
        length=(packed>>8)&0x3fffff;prologue=packed&255;end=start+length*4
        if (not length or prologue>length or start%4 or start<previous_end
            or not any(a<=start and end<=b for a,b in code_ranges)):
            raise FormatError('invalid/overlapping/out-of-code pdata function record')
        flags[str(packed>>30)]=flags.get(str(packed>>30),0)+1
        records.append(dict(index=index,start=start,end=end,length_words=length,
                            prologue_words=prologue,prologue_end=start+prologue*4,
                            packed_word=f'{packed:08x}',thirty_two_bit=(packed>>30)&1,
                            exception_flag=(packed>>31)&1))
        previous_end=end
    return dict(directory_rva=rva,directory_size=size,record_count=len(records),
                directory_sha256=digest(raw),flag_pair_counts=flags,records=records,
                coordinate_system='virtual-image RVA; not PE raw pointer',
                declared_extents_only=True,complete_code_coverage_verified=False,
                flag_semantics_verified=False,unwinding_performed=False,executed=False)


def exact_record(table,start):
    """Absent leaf functions are explicit None, never inferred to the next start."""
    if type(start) is not int:raise FormatError('pdata lookup address must be an integer')
    return next((r for r in table['records'] if r['start']==start),None)
