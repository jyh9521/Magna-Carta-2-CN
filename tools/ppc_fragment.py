"""Strict bounded PPC64 integer-fragment interpretation, not a game emulator.

Only the explicitly implemented instructions below are accepted. There are no
host calls, executable allocations, imported functions or instruction fallbacks.
Code is fetched from one read-only image window; synthetic memory is copied.
LFS records the loaded raw word only: no FP value, FPSCR or FP execution claim.

Integer operations follow PowerPC instruction definitions. In particular,
PPC64 RLWINM duplicates the low word before applying MASK(MB+32, ME+32), so a
wrapping mask can retain upper-word bits. Carry here is explicitly 64-bit.
Semantic cross-checks (independent implementation, no upstream code copied):
https://github.com/xenia-canary/xenia-canary/blob/96ce1ac47/src/xenia/cpu/ppc/ppc_emit_alu.cc#L987-L1035
https://www.ibm.com/docs/tr/aix/7.3?topic=set-subfe-sfe-subtract-from-extended-instruction
https://www.ibm.com/docs/en/aix/7.1.0?topic=set-lhzu-load-half-zero-update-instruction
https://www.nxp.com/docs/en/user-guide/821INSTSET.pdf (SRAWI opcode/carry)
"""
from __future__ import annotations

from collections.abc import Mapping,Sequence
from dataclasses import dataclass
import struct

MASK32=(1<<32)-1
MASK64=(1<<64)-1


class FragmentError(ValueError):
    """The fragment escaped its declared profile or consumed unknown state."""


@dataclass(frozen=True)
class MemorySegment:
    start:int
    data:bytes
    writable:bool=False


@dataclass(frozen=True)
class FragmentResult:
    stop_pc:int
    registers:dict[int,int]
    cr_bits:dict[int,bool]
    carry:bool|None
    fpr_bits:dict[int,int]
    segments:tuple[MemorySegment,...]
    trace:tuple[int,...]
    steps:int
    stores:tuple[tuple[int,int],...]


def _signed(value,bits):
    return value-(1<<bits) if value&(1<<(bits-1)) else value


def canonical_address(value):
    """Accept only zero-extended u32 or sign-extended negative s32 addresses."""
    if type(value) is not int or not 0<=value<=MASK64:
        raise FragmentError('invalid address value')
    upper=value>>32;lower=value&MASK32
    if upper==0 or (upper==MASK32 and lower&(1<<31)):
        return lower
    raise FragmentError('noncanonical virtual address')


def _mask64(begin,end):
    return sum(1<<(63-i) for i in range(64)
               if (begin<=i<=end if begin<=end else i>=begin or i<=end))


def run_fragment(image:bytes,base:int,window:tuple[int,int],entry:int,
                 stops:set[int],registers:Mapping[int,int],
                 memory:Sequence[MemorySegment]=(),max_steps:int=256)->FragmentResult:
    """Interpret a declared fragment until a listed PC, with at most 256 steps.

    Stops are checked before fetch and may deliberately be outside the window.
    Every other fetch must lie within the window and original image. All GPRs,
    consumed CR bits and carry inputs must have been explicitly initialized or
    produced by supported instructions. SO is not modeled, so its CR bit stays
    unknown. Results contain independent memory snapshots, not caller buffers.
    """
    if not isinstance(image,(bytes,bytearray)) or not image:
        raise FragmentError('image must contain bytes')
    image=bytes(image)
    if type(base) is not int or base%4 or not 0<=base<1<<32 or base+len(image)>1<<32:
        raise FragmentError('invalid image range')
    if (not isinstance(window,(tuple,list)) or len(window)!=2
            or any(type(a) is not int or a%4 for a in window)):
        raise FragmentError('invalid fetch window')
    start,end=window
    if not base<=start<end<=base+len(image):
        raise FragmentError('fetch window outside image')
    if type(entry) is not int or entry%4 or not start<=entry<end:
        raise FragmentError('entry outside fetch window')
    try:stop_set=set(stops)
    except TypeError as e:raise FragmentError('invalid stop PCs') from e
    if not stop_set or any(type(a) is not int or a%4 or not 0<=a<1<<32 for a in stop_set):
        raise FragmentError('invalid stop PCs')
    if type(max_steps) is not int or not 1<=max_steps<=256:
        raise FragmentError('step budget must be between 1 and 256')
    if not isinstance(registers,Mapping):raise FragmentError('invalid initial registers')
    regs={}
    for r,v in registers.items():
        if type(r) is not int or not 0<=r<32 or type(v) is not int or not -(1<<63)<=v<=MASK64:
            raise FragmentError('invalid initial register')
        regs[r]=v&MASK64
    if not isinstance(memory,Sequence):raise FragmentError('invalid memory segments')
    segments=[]
    for s in memory:
        if (not isinstance(s,MemorySegment) or not isinstance(s.data,(bytes,bytearray))
                or not s.data or type(s.writable) is not bool):
            raise FragmentError('invalid synthetic memory segment')
        a=canonical_address(s.start);z=a+len(s.data)
        if z>1<<32 or (a<base+len(image) and base<z):
            raise FragmentError('synthetic memory overlaps image or address limit')
        if any(a<old+len(data) and old<z for old,data,_ in segments):
            raise FragmentError('overlapping synthetic memory segments')
        segments.append((a,bytearray(s.data),s.writable))
    cr={};carry=None;fpr={};trace=[];stores=[];pc=entry

    def reg(r):
        if r not in regs:raise FragmentError(f'unknown register r{r}')
        return regs[r]

    def read_integer(raw_address,width):
        a=canonical_address(raw_address)
        name='word' if width==4 else 'halfword'
        if a%width:raise FragmentError(f'unaligned {name} read')
        fmt='>I' if width==4 else '>H'
        if base<=a<=base+len(image)-width:
            return struct.unpack_from(fmt,image,a-base)[0]
        for start,data,_ in segments:
            if start<=a<=start+len(data)-width:
                return struct.unpack_from(fmt,data,a-start)[0]
        raise FragmentError(f'unknown memory read at 0x{a:08X}')

    def write_integer(raw_address,value,width):
        a=canonical_address(raw_address)
        name='word' if width==4 else 'halfword'
        if a%width:raise FragmentError(f'unaligned {name} write')
        if a<base+len(image) and base<a+width:raise FragmentError('image is read-only')
        for start,data,writable in segments:
            if start<=a<=start+len(data)-width:
                if not writable:raise FragmentError('synthetic memory is read-only')
                value&=(1<<(width*8))-1
                struct.pack_into('>I' if width==4 else '>H',data,a-start,value)
                stores.append((a,value));return
        raise FragmentError(f'unknown memory write at 0x{a:08X}')

    def compare(field,left,right):
        cr[field*4]=left<right;cr[field*4+1]=left>right;cr[field*4+2]=left==right
        cr.pop(field*4+3,None)  # XER.SO is deliberately unknown.

    def record(value):compare(0,_signed(value&MASK64,64),0)

    while True:
        if pc in stop_set:
            return FragmentResult(pc,dict(regs),dict(cr),carry,dict(fpr),
                tuple(MemorySegment(a,bytes(data),writable) for a,data,writable in segments),
                tuple(trace),len(trace),tuple(stores))
        if type(pc) is not int or pc%4 or not start<=pc<=end-4:
            raise FragmentError(f'instruction fetch escaped window at 0x{pc:X}')
        if len(trace)>=max_steps:raise FragmentError('fragment step budget exhausted')
        word=struct.unpack_from('>I',image,pc-base)[0]
        trace.append(pc);next_pc=pc+4
        op=word>>26;rt=(word>>21)&31;ra=(word>>16)&31;rb=(word>>11)&31
        imm=word&0xffff;simm=_signed(imm,16)
        if op in (14,15):  # ADDI / ADDIS (RA=0 means literal zero).
            source=reg(ra) if ra else 0
            regs[rt]=(source+(simm if op==14 else simm<<16))&MASK64
        elif op==12:  # ADDIC: carry is the unsigned 64-bit carry-out.
            total=reg(ra)+(simm&MASK64)
            regs[rt]=total&MASK64;carry=total>MASK64
        elif op in (32,36,37,48):
            if op==37 and not ra:raise FragmentError('STWU requires a nonzero base register')
            address=((reg(ra) if ra else 0)+simm)&MASK64
            if op==32:regs[rt]=read_integer(address,4)
            elif op==48:fpr[rt]=read_integer(address,4)
            else:
                value=reg(rt);write_integer(address,value,4)
                if op==37:regs[ra]=address
        elif op in (40,41,44):  # LHZ / LHZU / STH, big-endian halfwords.
            if op==41 and (not ra or ra==rt):
                raise FragmentError('LHZU requires nonzero base distinct from target')
            address=((reg(ra) if ra else 0)+simm)&MASK64
            if op==44:write_integer(address,reg(rt),2)
            else:
                regs[rt]=read_integer(address,2)
                if op==41:regs[ra]=address
        elif op in (10,11):  # CMPLWI / CMPWI; reject 64-bit/reserved forms.
            if word&(3<<21):raise FragmentError('unsupported compare length/reserved bits')
            field=(word>>23)&7;left=reg(ra)&MASK32
            compare(field,left if op==10 else _signed(left,32),imm if op==10 else simm)
        elif op==18:
            if word&3:raise FragmentError('absolute/link branch is unsupported')
            next_pc=pc+_signed(word&0x03fffffc,26)
        elif op==16:
            bo=(word>>21)&31;bi=(word>>16)&31
            if word&3 or bo not in (4,12):raise FragmentError('unsupported conditional branch form')
            if bi not in cr:raise FragmentError(f'unknown CR bit {bi}')
            if cr[bi]==(bo==12):next_pc=pc+_signed(word&0xfffc,16)
        elif op==21:
            sh=(word>>11)&31;mb=(word>>6)&31;me=(word>>1)&31
            low=reg(rt)&MASK32;rotated=((low<<32)|low)
            if sh:rotated=((rotated<<sh)|(rotated>>(64-sh)))&MASK64
            regs[ra]=rotated&_mask64(mb+32,me+32)
            if word&1:record(regs[ra])
        elif op==24:regs[ra]=reg(rt)|imm
        elif op==31:
            xo=(word>>1)&1023;rc=word&1
            if xo in (444,28):
                regs[ra]=reg(rt)|reg(rb) if xo==444 else reg(rt)&reg(rb)
                if rc:record(regs[ra])
            elif xo==136:
                if carry is None:raise FragmentError('unknown carry input')
                total=(~reg(ra)&MASK64)+reg(rb)+int(carry)
                regs[rt]=total&MASK64;carry=total>MASK64
                if rc:record(regs[rt])
            elif xo==40:  # SUBF; OE forms remain unsupported.
                regs[rt]=(reg(rb)-reg(ra))&MASK64
                if rc:record(regs[rt])
            elif xo==824:  # SRAWI sign-extends the low-word result in PPC64.
                source=reg(rt)&MASK32;shift=rb
                signed=_signed(source,32)
                regs[ra]=(signed>>shift)&MASK64
                carry=signed<0 and bool(source&((1<<shift)-1))
                if rc:record(regs[ra])
            elif xo in (0,32):
                if rc or word&(3<<21):raise FragmentError('unsupported compare length/reserved bits')
                left=reg(ra)&MASK32;right=reg(rb)&MASK32
                if xo==0:left=_signed(left,32);right=_signed(right,32)
                compare((word>>23)&7,left,right)
            elif xo in (23,279):  # LWZX / LHZX.
                if rc:raise FragmentError('unsupported indexed load record bit')
                address=((reg(ra) if ra else 0)+reg(rb))&MASK64
                regs[rt]=read_integer(address,4 if xo==23 else 2)
            elif xo==266:
                if rc:raise FragmentError('unsupported ADD record bit')
                regs[rt]=(reg(ra)+reg(rb))&MASK64
            else:raise FragmentError(f'unsupported PPC XO {xo} at 0x{pc:08X}')
        else:raise FragmentError(f'unsupported PPC opcode {op} at 0x{pc:08X}')
        pc=next_pc
