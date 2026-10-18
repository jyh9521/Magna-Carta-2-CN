"""Bounded XEX2 none/basic image reconstruction for offline inspection only.

Independent format implementation. Reference: xenia-project/xenia,
95a5c3ee250f80c3b9d139658649d9ffb6db3eec (BSD-3-Clause), xex2_info.h /
xex_module.cc. No emulator/runtime, RSA verification, patching or execution.
"""
from __future__ import annotations
import hashlib
import struct

MAX_IMAGE=256*1024*1024
PAGE_SIZE=65536
RETAIL_KEY=bytes.fromhex('20b185a59d28fdc340583fbb0896bf91')


class FormatError(ValueError):pass


def digest(data):return hashlib.sha256(data).hexdigest()


class VirtualImage:
    """Bounded reads of already reconstructed virtual bytes; never load/execute."""
    def __init__(self,data,base):
        if type(base) is not int or not 0<=base<=0xffffffff or len(data)>MAX_IMAGE or base+len(data)>0x100000000:
            raise FormatError('invalid virtual image base/size')
        self.data,self.base=data,base
    def read(self,address,size):
        if type(address) is not int or type(size) is not int:
            raise FormatError('virtual image address/size must be integers')
        offset=address-self.base
        if offset<0 or size<0 or offset+size>len(self.data):
            raise FormatError('virtual image read outside bounds')
        return self.data[offset:offset+size]
    def word(self,address):return struct.unpack('>I',self.read(address,4))[0]


def parse_xex(data,expected_sha256):
    if len(data)>MAX_IMAGE or digest(data)!=expected_sha256.lower():raise FormatError('XEX source size/hash mismatch')
    def span(offset,size):
        if offset<0 or size<0 or offset+size>len(data):raise FormatError('XEX range outside source')
        return data[offset:offset+size]
    def word(offset):return struct.unpack('>I',span(offset,4))[0]
    if span(0,4)!=b'XEX2' or word(4)!=1 or word(12):raise FormatError('unsupported XEX2 title profile')
    pe,sec,count=word(8),word(16),word(20)
    if not 1<=count<=4096 or 24+count*8>sec or sec+0x184>pe or pe>len(data) or pe%16:
        raise FormatError('invalid XEX header bounds')
    options={}
    for i in range(count):
        key,value=struct.unpack('>II',span(24+i*8,8))
        if key in options:raise FormatError('duplicate XEX optional header')
        options[key]=value
    if 0x3ff not in options:raise FormatError('missing XEX file-format header')
    f=options[0x3ff]
    if f<24+count*8 or f+8>pe:raise FormatError('file-format header outside XEX header area')
    size,enc,comp=struct.unpack('>IHH',span(f,8))
    if size<8 or f+size>pe or enc not in (0,1) or comp not in (0,1):raise FormatError('unsupported XEX encryption/compression profile')
    sec_size,image_size,load=word(sec),word(sec+4),word(sec+0x110)
    pages=word(sec+0x180)
    if not 0<image_size<=MAX_IMAGE or not 1<=pages<=MAX_IMAGE//PAGE_SIZE:
        raise FormatError('XEX image/page count outside bound')
    if sec_size<0x184+pages*24 or sec+sec_size>pe or not (f>=sec+sec_size or f+size<=sec):
        raise FormatError('XEX security/file-format ranges overlap or truncate')
    base=options.get(0x10201,load)
    if not base or base!=load or base+image_size>0x100000000:raise FormatError('unsupported XEX image base')
    ranges=[];cursor=0
    for i in range(pages):
        value=word(sec+0x184+i*24);kind,n=value&15,value>>4
        if kind not in (1,2,3) or not n or cursor+n*PAGE_SIZE>image_size:raise FormatError('invalid XEX page descriptor')
        if ranges and ranges[-1]['kind']==kind:ranges[-1]['size']+=n*PAGE_SIZE
        else:ranges.append(dict(offset=cursor,size=n*PAGE_SIZE,kind=kind))
        cursor+=n*PAGE_SIZE
    if cursor!=image_size:raise FormatError('XEX page extents do not cover image size')
    blocks=[]
    if comp==0:
        if size!=8:raise FormatError('uncompressed file-format trailing fields')
        blocks=[dict(data_size=image_size,zero_size=0)]
    else:
        if size<16 or (size-8)%8 or (size-8)//8>65536:raise FormatError('malformed/overlong basic block table')
        for offset in range(f+8,f+size,8):
            n,z=struct.unpack('>II',span(offset,8))
            if not n+z or n+z>MAX_IMAGE:raise FormatError('invalid basic block size')
            blocks.append(dict(data_size=n,zero_size=z))
    stored=sum(b['data_size'] for b in blocks);expanded=sum(b['data_size']+b['zero_size'] for b in blocks)
    if stored!=len(data)-pe or expanded!=image_size or (enc and (stored%16 or any(b['data_size']%16 for b in blocks))):
        raise FormatError('XEX stored/expanded/alignment totals mismatch')
    execution=None
    if 0x40006 in options:
        offset=options[0x40006]
        if offset<24+count*8 or offset+24>pe:raise FormatError('execution ID outside header area')
        if any(offset<end and offset+24>start for start,end in [(sec,sec+sec_size),(f,f+size)]):
            raise FormatError('execution ID overlaps another parsed header')
        media,version,base_ver,title,platform,kind,disc,total,save=struct.unpack('>4I4BI',span(offset,24))
        execution=dict(media_id=f'{media:08x}',title_id=f'{title:08x}',version_raw=f'{version:08x}',base_version_raw=f'{base_ver:08x}',
                       platform=platform,executable_type=kind,disc=disc,disc_count=total,savegame_id=f'{save:08x}')
    return dict(source_sha256=digest(data),source_size=len(data),pe_offset=pe,security_offset=sec,
                encryption=enc,compression=comp,image_size=image_size,image_base=base,entry_point=options.get(0x10100),
                blocks=blocks,page_descriptor_count=pages,page_ranges=ranges,execution_id=execution,
                stored_page_digests_verified=False,rsa_signature_verified=False)


def inspect_pe(image,base,entry):
    def read(offset,fmt):
        size=struct.calcsize(fmt)
        if offset<0 or offset+size>len(image):raise FormatError('PE header range outside reconstructed image')
        return struct.unpack_from(fmt,image,offset)
    if image[:2]!=b'MZ':raise FormatError('decoded image has no MZ header (key/profile mismatch)')
    nt=read(0x3c,'<I')[0]
    if read(nt,'<4s')[0]!=b'PE\0\0':raise FormatError('decoded image has no PE signature')
    machine,count=read(nt+4,'<HH');opt_size=read(nt+20,'<H')[0];opt=nt+24
    if machine!=0x1f2 or not 1<=count<=96 or opt_size<96 or read(opt,'<H')[0]!=0x10b:
        raise FormatError('unsupported reconstructed PE machine/header profile')
    if read(opt+28,'<I')[0]!=base or (entry is not None and base+read(opt+16,'<I')[0]!=entry):
        raise FormatError('PE/XEX base or entry mismatch')
    sections=[]
    for i in range(count):
        offset=opt+opt_size+i*40;name=read(offset,'<8s')[0].rstrip(b'\0').decode('ascii')
        size,rva,raw_size,raw_pointer=read(offset+8,'<4I');flags=read(offset+36,'<I')[0]
        sections.append(dict(name=name,rva=rva,virtual_size=size,raw_size=raw_size,raw_pointer=raw_pointer,
                             flags=f'{flags:08x}',fully_present_in_xex_image=rva+size<=len(image)))
    return dict(machine='01f2',optional_magic='010b',header_offset=nt,declared_pe_image_size=read(opt+56,'<I')[0],
                sections=sections,pe_headers_for_annotation_only=True)


def decode_image(source,expected_sha256,key=None,cipher=None):
    meta=parse_xex(source,expected_sha256);payload=source[meta['pe_offset']:];session=None
    if meta['encryption']:
        if key is None or len(key)!=16 or cipher is None:raise FormatError('encrypted XEX requires an explicit 16-byte key and CBC backend')
        s=meta['security_offset'];session=cipher.decrypt(key,source[s+0x150:s+0x160])
        if len(session)!=16:raise FormatError('CBC backend returned invalid session-key size')
        plain=cipher.decrypt(session,payload)
        if len(plain)!=len(payload):raise FormatError('CBC backend changed payload size')
    else:
        if key is not None:raise FormatError('unencrypted XEX does not use a decryption key')
        plain=payload
    image=bytearray();cursor=0
    for block in meta['blocks']:
        n,z=block['data_size'],block['zero_size'];image.extend(plain[cursor:cursor+n]);image.extend(bytes(z));cursor+=n
    image=bytes(image);pe=inspect_pe(image,meta['image_base'],meta['entry_point'])
    # Independent inverse extent walk: omit only verified zero spans, then CBC
    # encrypt the concatenated stored stream, never resetting at basic blocks.
    pieces=[];offset=0
    for block in meta['blocks']:
        n,z=block['data_size'],block['zero_size'];pieces.append(image[offset:offset+n])
        if any(image[offset+n:offset+n+z]):raise FormatError('inverse extent walk found nonzero omitted bytes')
        offset+=n+z
    stored=b''.join(pieces);encoded=cipher.encrypt(session,stored) if meta['encryption'] else stored
    restored=source[:meta['pe_offset']]+encoded
    if restored!=source:raise FormatError('inverse source reconstruction mismatch')
    report=dict(schema_version=1,**meta,pe=pe,image_sha256=digest(image),roundtrip_source_sha256=digest(restored),
                roundtrip_verified=True,image_layout='XEX virtual-image bytes, not PE raw-file mapping',executed=False)
    return image,restored,report


def crypto_backend(name):
    """Optional crypto dependency, imported only after source/profile preflight."""
    if name=='pycryptodome':
        from Crypto.Cipher import AES
        class Backend:
            def decrypt(self,key,data):return AES.new(key,AES.MODE_CBC,bytes(16)).decrypt(data)
            def encrypt(self,key,data):return AES.new(key,AES.MODE_CBC,bytes(16)).encrypt(data)
        return Backend()
    if name=='cryptography':
        from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
        class Backend:
            def decrypt(self,key,data):
                c=Cipher(algorithms.AES(key),modes.CBC(bytes(16))).decryptor();return c.update(data)+c.finalize()
            def encrypt(self,key,data):
                c=Cipher(algorithms.AES(key),modes.CBC(bytes(16))).encryptor();return c.update(data)+c.finalize()
        return Backend()
    raise FormatError('unknown CBC backend')
