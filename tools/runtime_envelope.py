"""Cheap final-delivery gate for the verified Xenon 446/25 raw-package profile.

Hash equality is not this check. It does not decompress, render, or run a game.
Unmodified original compressed packages do not need this generated-output gate.
"""
import struct

try:
    from .ue3_package import parse_summary,parse_tables
    from .lzx_stored import wrap_ue3_chunk,UE3_BLOCK_SIZE,FRAME_SIZE
except ImportError:
    from ue3_package import parse_summary,parse_tables
    from lzx_stored import wrap_ue3_chunk,UE3_BLOCK_SIZE,FRAME_SIZE

MAGICS = (b'\x9e\x2a\x83\xc1', b'\xc1\x83\x2a\x9e')
PROFILE = 'xenon-446-25-raw32k-v1'
ALIGNMENT = 32768


def generated_stored_chunk(data):
    """Recognize only byte-exact output of our writer, without an LZX decoder."""
    try:
        if len(data)<24:return False
        magic,block,packed,size=struct.unpack_from('>IIII',data)
        if magic!=0x9e2a83c1 or block!=UE3_BLOCK_SIZE or not 0<size<=128*1024*1024:return False
        count=(size+block-1)//block;cursor=16+count*8
        if cursor+packed!=len(data):return False
        decoded=bytearray()
        for index in range(count):
            packed_size,raw_size=struct.unpack_from('>II',data,16+index*8)
            if raw_size!=min(block,size-index*block):return False
            end=cursor+packed_size;part=bytearray()
            while cursor<end:
                if data[cursor]!=255:return False
                length,stored=struct.unpack_from('>HH',data,cursor+1)
                expected=min(FRAME_SIZE,raw_size-len(part))
                if length!=expected or not length or stored!=16+length+(length&1):return False
                at=cursor+5
                word=((3<<24)|length)<<(4 if not part else 5)
                if data[at:at+16]!=struct.pack('<HHIII',word>>16,word&65535,1,1,1):return False
                part.extend(data[at+16:at+16+length]);cursor=at+stored
            if cursor!=end or len(part)!=raw_size:return False
            decoded.extend(part)
        return len(decoded)==size and cursor==len(data) and wrap_ue3_chunk(bytes(decoded))==data
    except (ValueError,IndexError,struct.error):
        return False


def require_raw_envelope(data):
    if not isinstance(data, bytes) or not 0 < len(data) <= 512*1024*1024:
        raise ValueError('runtime package size/type outside bounded profile')
    summary = parse_summary(data, len(data))
    if summary['byte_order'] != 'big':
        raise ValueError('runtime envelope requires big-endian 446/25')
    if (summary['compression_flags'] or summary['compressed_chunks']
            or summary['package_flags'] & 0x02000000):
        raise ValueError('modified runtime package still has a compressed outer envelope')
    if len(data) % ALIGNMENT:
        raise ValueError('modified runtime package is not 32768-byte aligned')
    tables=parse_tables(data,summary,len(data))
    for export in tables['exports']:
        if export['class_path'] not in ('Engine.Texture2D','Texture2D'):continue
        start=export['serial_offset'];end=start+export['serial_size'];cursor=start;scanned=0
        while True:
            at=data.find(MAGICS[0],cursor,end)
            if at<0:break
            cursor=at+4;scanned+=1
            if scanned>4096:raise ValueError('texture chunk scan exceeds bound')
            if at+16>end:continue
            _,block,packed,size=struct.unpack_from('>IIII',data,at)
            if block!=UE3_BLOCK_SIZE or not 0<size<=128*1024*1024:continue
            length=16+8*((size+block-1)//block)+packed
            if at+length<=end and generated_stored_chunk(data[at:at+length]):
                raise ValueError('modified runtime texture still has a generated stored-LZX bulk: '+export['path'])
    return dict(profile=PROFILE, size=len(data), outer_compression=0,
                alignment=ALIGNMENT, game_started=False)
