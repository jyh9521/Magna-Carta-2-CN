"""Bounded read-only Xbox 2D texture inspection, separate from patch profiles.

PF_A8R8G8B8 (2), DXT1 (5), DXT5 (7); raw/LZX inline bulks, explicitly
resolved external LZX, and the packed-tail 0x21 empty-mip sentinel. This does
not enable writing these formats in the production overlay builder.

Packed coordinates adapted from Xenia GetPackedMipOffset, Copyright 2022
Ben Vanik, BSD-3-Clause. Existing tiled addressing is UEViewer-derived MIT
code. See NOTICE.md, references/texture-layout-research.lock.json and
licenses/Xenia-BSD-3-Clause.txt. Format2 channel/endian interpretation is
from the pinned UEViewer EPixelFormat/Xbox decoder in that same lock.
"""
import io
import struct

from .ue3_package import Reader, FormatError
from .ue3_fonts import read_properties, unique_properties, int_property
from .ue3_textures import compressed_chunk, xbox_tiled_block_offset, decode_dxt5

MAX_BYTES = 64 * 1024 * 1024
MAX_UNITS = 1024 * 1024


def unit_layout(width, height, fmt, mip=0):
    """Return checked unit addresses, including packed-tail physical owner."""
    if (type(fmt) is not int or fmt not in (2, 5, 7)
            or any(type(v) is not int or not 1 <= v <= 8192 or v & (v - 1)
                   for v in (width, height))
            or type(mip) is not int or not 0 <= mip < max(width, height).bit_length()):
        raise FormatError('inspection geometry/format/mip bound')
    block, size = (1, 4) if fmt == 2 else (4, 8 if fmt == 5 else 16)
    lw, lh = width.bit_length() - 1, height.bit_length() - 1
    tail = max(0, min(lw, lh) - 4)
    owner = min(mip, tail)
    ow, oh = max(1, width >> owner), max(1, height >> owner)
    alignment = block * 32
    sw = (ow + alignment - 1) // alignment * alignment
    sh = (oh + alignment - 1) // alignment * alignment
    storage = sw * sh * size // (block * block)
    w, h = max(1, width >> mip), max(1, height >> mip)
    bw, bh = (w + block - 1) // block, (h + block - 1) // block
    if storage > MAX_BYTES or bw * bh > MAX_UNITS:
        raise FormatError('inspection allocation/unit bound')
    ox = oy = 0
    if mip >= tail:
        p = mip - tail
        if p < 3:
            ox, oy = (0, 16 >> p) if lw > lh else (16 >> p, 0)
        elif lw > lh:
            ox = (1 << (lw - tail)) >> (p - 2)
        else:
            oy = (1 << (lh - tail)) >> (p - 2)
    ox, oy = ox // block, oy // block
    offsets = [xbox_tiled_block_offset(x + ox, y + oy, sw // block, size.bit_length() - 1) * size
               for y in range(bh) for x in range(bw)]
    if len(set(offsets)) != len(offsets) or any(o < 0 or o + size > storage for o in offsets):
        raise FormatError('inspection addressed units overlap/outside allocation')
    return dict(width=w, height=h, owner_mip=owner, tail_base=tail,
                storage_dimensions=[sw, sh], storage_bytes=storage,
                unit_bytes=size, block_texels=block, origin_units=[ox, oy], offsets=offsets)


def read_texture(payload, names, serial_offset, decoder, external_resolver=None):
    """Parse complete native data. Resolver must supply independently locked bytes.

    external_resolver(mip) receives metadata only and returns encoded LZX bytes.
    It must verify the external package/export identity before supplying bytes;
    this module additionally checks encoded length, LZX metadata and raw count.
    It never follows a path or assumes a resource based on a texture leaf name.
    """
    r = Reader(payload)
    r.i32()
    props = unique_properties(read_properties(r, names))
    if not {'SizeX', 'SizeY', 'Format'} <= set(props):
        raise FormatError('inspection texture properties missing')
    width, height = int_property(props['SizeX']), int_property(props['SizeY'])
    prop = props['Format']
    if prop['type'] != 'ByteProperty' or len(prop['raw']) != 1:
        raise FormatError('inspection format property')
    fmt = prop['raw'][0]
    first_layout = unit_layout(width, height, fmt)
    source = r.pos
    if [r.u32() for _ in range(4)] != [0, 0, 0, serial_offset + source + 16]:
        raise FormatError('inspection requires empty inline SourceArt')
    count = r.count(16)
    if not 1 <= count <= max(width, height).bit_length():
        raise FormatError('inspection native mip count bound')
    if count > 1 and 'MipTailBaseIdx' in props:
        if int_property(props['MipTailBaseIdx']) != first_layout['tail_base']:
            raise FormatError('inspection MipTailBaseIdx mismatch')
    mips, physical, used = [], {}, {}
    for index in range(count):
        header = r.pos
        flags, n, size, offset = [r.u32() for _ in range(4)]
        layout = unit_layout(width, height, fmt, index)
        mip = dict(index=index, header_offset=header, flags=flags,
                   count=n, stored_size=size, data_offset=offset,
                   layout=layout)
        if index > layout['owner_mip']:
            if (flags, n, size, offset) != (0x21, 0, 0xffffffff, 0xffffffff):
                raise FormatError('inspection packed-tail sentinel mismatch')
        else:
            if (flags not in (0, 0x40, 0x41) or n != layout['storage_bytes']
                    or not 0 < size <= MAX_BYTES):
                raise FormatError('inspection bulk allocation/profile mismatch')
            if flags == 0x41:
                if external_resolver is None:
                    raise FormatError('inspection external bulk requires explicit resolver')
                encoded = external_resolver(mip)
            else:
                if offset != serial_offset + r.pos:
                    raise FormatError('inspection inline bulk pointer mismatch')
                encoded = r.read(size)
            if not isinstance(encoded, bytes) or len(encoded) != size:
                raise FormatError('inspection encoded bulk size mismatch')
            if flags in (0x40, 0x41):
                tiles = compressed_chunk(encoded, n, decoder)[1]
            else:
                tiles = encoded
            if not isinstance(tiles, bytes) or len(tiles) != n:
                raise FormatError('inspection decoded bulk size mismatch')
            physical[index] = tiles
        minimum = 1 if fmt == 2 else 4
        native = [r.u32(), r.u32()]
        if native != [max(minimum, width >> index), max(minimum, height >> index)]:
            raise FormatError('inspection native mip dimensions mismatch')
        mip['native_dimensions'] = native
        owner = layout['owner_mip']
        if owner not in physical:
            raise FormatError('inspection packed mip owner missing')
        prior = used.setdefault(owner, set())
        if prior.intersection(layout['offsets']):
            raise FormatError('inspection shared mip units overlap')
        prior.update(layout['offsets'])
        mips.append(mip)
    if r.pos != len(payload):
        raise FormatError('inspection native export termination mismatch')
    return dict(width=width, height=height, format=fmt, source_offset=source,
                mips=mips, physical=physical, parsed_bytes=r.pos)


def extract_units(raw, layout, fmt):
    if not isinstance(raw, bytes) or len(raw) != layout['storage_bytes']:
        raise FormatError('inspection tiled allocation size mismatch')
    step = 4 if fmt == 2 else 2
    size = layout['unit_bytes']
    return b''.join(raw[offset + i:offset + i + step][::-1]
                    for offset in layout['offsets'] for i in range(0, size, step))


def decode_units(raw, layout, fmt):
    from PIL import Image
    linear = extract_units(raw, layout, fmt)
    w, h, block = layout['width'], layout['height'], layout['block_texels']
    aw, ah = (w + block - 1) // block * block, (h + block - 1) // block * block
    if fmt == 2:
        image = Image.frombytes('RGBA', (aw, ah), linear, 'raw', 'BGRA')
    elif fmt == 7:
        image = Image.frombytes('RGBA', (aw, ah), decode_dxt5(linear, aw, ah))
    else:
        header = bytearray(128)
        header[:4] = b'DDS '
        struct.pack_into('<7I', header, 4, 124, 0x81007, ah, aw, len(linear), 0, 1)
        struct.pack_into('<II4s', header, 76, 32, 4, b'DXT1')
        struct.pack_into('<I', header, 108, 0x1000)
        with Image.open(io.BytesIO(bytes(header) + linear)) as dds:
            image = dds.convert('RGBA')
    return image.crop((0, 0, w, h))


def decode_mip(texture, index=0):
    if type(index) is not int or not 0 <= index < len(texture['mips']):
        raise FormatError('inspection mip index bound')
    layout = texture['mips'][index]['layout']
    return decode_units(texture['physical'][layout['owner_mip']], layout, texture['format'])
