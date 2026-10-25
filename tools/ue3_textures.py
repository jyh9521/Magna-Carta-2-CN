"""Read-only MC2 Texture2D bulk inspection and optional Xbox360 DXT5 preview.

Tiling address calculation adapted from UEViewer (MIT),
Copyright 2022 Konstantin Nosov. Full notice is retained below.
Upstream: https://github.com/gildor2/UEViewer
Revision: a0bfb468d42be831b126632fd8a0ae6b3614f981
Adapted function: Unreal/UnrealMaterial/UnTexture.cpp GetXbox360TiledOffset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

try:
    from .pure_bytes_cache import bounded_bytes_cache
except ImportError:
    from pure_bytes_cache import bounded_bytes_cache

try:
    from .ue3_package import Reader, FormatError, LzxDecoder, parse_summary, parse_tables
    from .ue3_fonts import read_properties, unique_properties, int_property
except ImportError:
    from ue3_package import Reader, FormatError, LzxDecoder, parse_summary, parse_tables
    from ue3_fonts import read_properties, unique_properties, int_property

UEVIEWER_LICENSE = """The MIT License (MIT)
Copyright 2022, Konstantin Nosov
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
MAX_BULK_SIZE = 64 * 1024 * 1024


def compressed_chunk(data, expected_size, decoder=None):
    """Validate one complete UE chunk and optionally decode its Xbox LZX blocks."""
    r = Reader(data)
    if r.u32() != 0x9E2A83C1:
        raise FormatError("invalid compressed bulk magic")
    block_size, compressed_size, uncompressed_size = r.u32(), r.u32(), r.u32()
    if not 0 < block_size <= 131072 or not 0 < uncompressed_size <= MAX_BULK_SIZE:
        raise FormatError("unsupported compressed bulk sizes")
    if uncompressed_size != expected_size:
        raise FormatError("bulk element count/decompressed size mismatch")
    count = (uncompressed_size + block_size - 1) // block_size
    blocks = [{"compressed_size": r.u32(), "uncompressed_size": r.u32()} for _ in range(count)]
    if sum(b["compressed_size"] for b in blocks) != compressed_size or sum(b["uncompressed_size"] for b in blocks) != uncompressed_size:
        raise FormatError("compressed bulk block totals mismatch")
    if r.pos + compressed_size != len(data):
        raise FormatError("compressed bulk physical size mismatch")
    output = bytearray()
    for index, block in enumerate(blocks):
        if block["uncompressed_size"] != min(block_size, uncompressed_size - index * block_size) or not block["compressed_size"]:
            raise FormatError("invalid compressed bulk block partition")
        block["offset"] = r.pos
        payload = r.read(block["compressed_size"])
        if decoder is not None:
            decoded = decoder(payload, block["uncompressed_size"])
            if len(decoded) != block["uncompressed_size"]:
                raise FormatError("decoder output size mismatch")
            output.extend(decoded)
    return {"block_size": block_size, "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size, "blocks": blocks}, bytes(output) if decoder is not None else None


def bulk_header(reader, serial_offset):
    offset = reader.pos
    flags, count, size, data_offset = [reader.u32() for _ in range(4)]
    if count > MAX_BULK_SIZE or size > MAX_BULK_SIZE:
        raise FormatError("bulk exceeds size limit")
    if data_offset != serial_offset + reader.pos:
        raise FormatError("bulk offset is not inline current position")
    return {"header_offset": offset, "flags": flags, "element_count": count,
            "size_on_disk": size, "data_offset": data_offset,
            "size_on_disk_field_offset": offset + 8, "data_offset_field_offset": offset + 12,
            "payload_offset": offset + 16}


def parse_texture_payload(data, names, serial_offset, decoder=None):
    r = Reader(data)
    net_index = r.i32()
    props = unique_properties(read_properties(r, names))
    width, height = int_property(props["SizeX"]), int_property(props["SizeY"])
    if not 0 < width <= 8192 or not 0 < height <= 8192:
        raise FormatError("invalid texture dimensions")
    fmt = props["Format"]
    if fmt["type"] != "ByteProperty" or fmt["raw"] != b"\x07":
        raise FormatError("only verified profile Format7 DXT5 supported")
    source = bulk_header(r, serial_offset)
    if any(source[k] for k in ("flags", "element_count", "size_on_disk")):
        raise FormatError("nonempty SourceArt is unsupported")
    mip_count = r.count(16)
    if not mip_count:
        raise FormatError("empty mip array")
    mips, pixels = [], []
    for index in range(mip_count):
        bulk = bulk_header(r, serial_offset)
        # MCARTA remaps bulk flag 0x40 to LZX; not the generic UE3 flag meaning.
        if bulk["flags"] != 0x40 or not bulk["element_count"] or not bulk["size_on_disk"]:
            raise FormatError("only inline MCARTA LZX bulk flag0x40 supported")
        chunk, decoded = compressed_chunk(r.read(bulk["size_on_disk"]), bulk["element_count"], decoder)
        dimensions_offset = r.pos
        mip_width, mip_height = r.u32(), r.u32()
        if (mip_width, mip_height) != (max(1, width >> index), max(1, height >> index)):
            raise FormatError("native/tagged mip dimensions mismatch")
        if mip_width < 32 or mip_height < 32 or mip_width % 4 or mip_height % 4:
            raise FormatError("packed lower mip or non-4-aligned dimensions unsupported")
        aligned_width, aligned_height = (mip_width + 127) & ~127, (mip_height + 127) & ~127
        if bulk["element_count"] != aligned_width * aligned_height:
            raise FormatError("DXT5 tiled alignment/storage size mismatch")
        mip = {"index": index, "width": mip_width, "height": mip_height,
               "aligned_width": aligned_width, "aligned_height": aligned_height,
               "bulk": bulk, "chunk": chunk, "dimensions_offset": dimensions_offset}
        if decoded is not None:
            mip["decoded_tiled_sha256"] = hashlib.sha256(decoded).hexdigest()
            linear = untile_dxt5(decoded, mip_width, mip_height)
            mip["linear_dxt5_sha256"] = hashlib.sha256(linear).hexdigest()
            pixels.append(decode_dxt5(linear, mip_width, mip_height))
        mips.append(mip)
    if r.pos != len(data):
        raise FormatError("Texture2D export trailing bytes")
    return {"net_index": net_index, "width": width, "height": height, "format_byte": 7,
            "format_interpretation": "PF_DXT5 / BC3", "source_art": source,
            "mips": mips, "properties_end": source["header_offset"],
            "decoded": decoder is not None}, pixels


def xbox_tiled_block_offset(x, y, width, log_bytes=4):
    """UEViewer MIT GetXbox360TiledOffset, block-address form (see notice)."""
    aligned_width = (width + 31) & ~31
    macro = ((x >> 5) + (y >> 5) * (aligned_width >> 5)) << (log_bytes + 7)
    micro = ((x & 7) + ((y & 14) << 2)) << log_bytes
    offset = macro + ((micro & ~15) << 1) + (micro & 15) + ((y & 1) << 4)
    return (((offset & ~511) << 3) + ((y & 16) << 7) + ((offset & 448) << 2)
            + (((((y & 8) >> 2) + (x >> 3)) & 3) << 6) + (offset & 63)) >> log_bytes


def untile_dxt5(data, width, height):
    if width < 32 or height < 32 or width % 4 or height % 4 or width > 8192 or height > 8192:
        raise FormatError("unsupported DXT5 untile dimensions")
    aligned_width, aligned_height = (width + 127) & ~127, (height + 127) & ~127
    if len(data) != aligned_width * aligned_height:
        raise FormatError("wrong tiled DXT5 buffer size")
    out = bytearray(width * height)
    for y in range(height // 4):
        for x in range(width // 4):
            source = xbox_tiled_block_offset(x, y, aligned_width // 4) * 16
            target = (y * (width // 4) + x) * 16
            if source + 16 > len(data):
                raise FormatError("tiled block outside buffer")
            block = data[source:source + 16]
            # Xbox BC3 is word-endian swapped, including endpoint/index words.
            out[target:target + 16:2] = block[1::2]
            out[target + 1:target + 16:2] = block[::2]
    return bytes(out)



def encode_white_bc3_block(alpha):
    """Encode 16 row-major alpha samples, constant white RGB, fixed 8-level alpha.

    Fixed endpoints (255,0) preserve fully transparent/opaque samples exactly.
    Intermediate alpha quantization error is at most 18 (out of 255).
    """
    if len(alpha) != 16 or any(not isinstance(a, int) or not 0 <= a <= 255 for a in alpha):
        raise FormatError("white BC3 block requires sixteen alpha bytes")
    palette = [255, 0] + [((7 - i) * 255) // 7 for i in range(1, 7)]
    indices = 0
    for index, value in enumerate(alpha):
        choice = min(range(8), key=lambda i: abs(palette[i] - value))
        indices |= choice << (index * 3)
    # BC3 uses four-color mode independent of the order of its RGB endpoints.
    return b"\xff\0" + indices.to_bytes(6, "little") + b"\xff\xff\xff\xff" + bytes(4)


def scatter_linear_dxt5_cell(tiled, width, height, x, y, cell_width, cell_height, linear):
    """Return a new tiled buffer replacing only a block-aligned cell.

    Untouched tile blocks and physical alignment padding retain their exact bytes.
    This is an in-memory primitive, not a package writer.
    """
    if (min(width, height) < 32 or max(width, height) > 8192
            or any(v % 4 for v in (width, height, x, y, cell_width, cell_height))
            or min(x, y) < 0 or min(cell_width, cell_height) <= 0
            or x + cell_width > width or y + cell_height > height):
        raise FormatError("invalid block-aligned DXT5 cell bounds")
    aligned_width, aligned_height = (width + 127) & ~127, (height + 127) & ~127
    if len(tiled) != aligned_width * aligned_height or len(linear) != cell_width * cell_height:
        raise FormatError("wrong tiled or cell DXT5 buffer size")
    out = bytearray(tiled)
    for by in range(cell_height // 4):
        for bx in range(cell_width // 4):
            source = (by * (cell_width // 4) + bx) * 16
            target = xbox_tiled_block_offset(x // 4 + bx, y // 4 + by, aligned_width // 4) * 16
            if target + 16 > len(out):
                raise FormatError("cell tile offset outside buffer")
            block = linear[source:source + 16]
            out[target:target + 16:2] = block[1::2]
            out[target + 1:target + 16:2] = block[::2]
    return bytes(out)


def supplement_white_dxt5_cell(tiled, width, height, x, y, cell_width, cell_height, alpha):
    """Encode row-major coverage samples and scatter only this rectangular cell."""
    if cell_width <= 0 or cell_height <= 0 or cell_width % 4 or cell_height % 4 or len(alpha) != cell_width * cell_height:
        raise FormatError("invalid white BC3 cell dimensions or alpha length")
    linear = bytearray()
    for by in range(cell_height // 4):
        for bx in range(cell_width // 4):
            samples = [alpha[(by * 4 + iy) * cell_width + bx * 4 + ix] for iy in range(4) for ix in range(4)]
            linear.extend(encode_white_bc3_block(samples))
    return scatter_linear_dxt5_cell(tiled, width, height, x, y, cell_width, cell_height, linear)


def _decode_dxt5_reference(data, width, height):
    """Decode standard linear little-endian BC3 blocks to RGBA, without dependencies."""
    if width <= 0 or height <= 0 or width % 4 or height % 4 or len(data) != width * height:
        raise FormatError("invalid linear DXT5 buffer or dimensions")
    out = bytearray(width * height * 4)
    for by in range(height // 4):
        for bx in range(width // 4):
            offset = (by * (width // 4) + bx) * 16
            block = data[offset:offset + 16]
            a, b = block[:2]
            alpha = [a, b]
            if a > b:
                alpha += [((7 - i) * a + i * b) // 7 for i in range(1, 7)]
            else:
                alpha += [((5 - i) * a + i * b) // 5 for i in range(1, 5)] + [0, 255]
            alpha_indices = int.from_bytes(block[2:8], "little")
            c0, c1 = struct.unpack("<HH", block[8:12])
            def rgb(value):
                r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
                return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))
            colors = [rgb(c0), rgb(c1)]
            colors += [tuple((2 * p + q) // 3 for p, q in zip(colors[0], colors[1])),
                       tuple((p + 2 * q) // 3 for p, q in zip(colors[0], colors[1]))]
            color_indices = int.from_bytes(block[12:16], "little")
            for pixel in range(16):
                color = colors[(color_indices >> (pixel * 2)) & 3]
                opacity = alpha[(alpha_indices >> (pixel * 3)) & 7]
                target = ((by * 4 + pixel // 4) * width + bx * 4 + pixel % 4) * 4
                out[target:target + 4] = bytes((*color, opacity))
    return bytes(out)


def _decode_dxt5_pillow(data, width, height):
    """Optional existing Pillow DDS codec; absence retains the Python oracle."""
    try:
        from PIL import Image
    except ImportError:
        return None
    import io
    header = bytearray(128)
    header[:4] = b'DDS '
    struct.pack_into('<7I', header, 4, 124, 0x81007, height, width, len(data), 0, 1)
    struct.pack_into('<II4s', header, 76, 32, 4, b'DXT5')
    struct.pack_into('<I', header, 108, 0x1000)
    with Image.open(io.BytesIO(bytes(header) + data), formats=['DDS']) as image:
        result = image.convert('RGBA').tobytes()
    if len(result) != width * height * 4:
        raise FormatError('accelerated BC3 decoded size mismatch')
    return result


@bounded_bytes_cache(64 * 1024 * 1024)
def decode_dxt5(data, width, height):
    """Bit-exact BC3 decoding with optional acceleration and bounded byte reuse."""
    if type(data) is not bytes or type(width) is not int or type(height) is not int:
        return _decode_dxt5_reference(data, width, height)
    if width <= 0 or height <= 0 or width % 4 or height % 4 or len(data) != width * height:
        raise FormatError('invalid linear DXT5 buffer or dimensions')
    result = _decode_dxt5_pillow(data, width, height)
    return _decode_dxt5_reference(data, width, height) if result is None else result


def png_rgba(pixels, width, height):
    if len(pixels) != width * height * 4:
        raise FormatError("wrong RGBA buffer size")
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))
    scan = b"".join(b"\0" + pixels[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scan)) + chunk(b"IEND", b""))


def inspect_package(data, decoder=None):
    summary = parse_summary(data, len(data))
    if summary["compression_flags"] or summary["byte_order"] != "big":
        raise FormatError("requires uncompressed big-endian package446/25")
    tables = parse_tables(data, summary)
    textures, previews = [], []
    for export in tables["exports"]:
        if export["class_path"] != "Engine.Texture2D":
            continue
        offset, size = export["serial_offset"], export["serial_size"]
        texture, decoded = parse_texture_payload(data[offset:offset + size], tables["names"], offset, decoder)
        texture.update({"path": export["path"], "serial_offset": offset, "serial_size": size})
        texture["previews"] = []
        for mip, pixels in zip(texture["mips"], decoded):
            filename = f"texture-{len(textures):03d}-mip-{mip['index']:02d}.png"
            preview = png_rgba(pixels, mip["width"], mip["height"])
            texture["previews"].append({"filename": filename, "sha256": hashlib.sha256(preview).hexdigest()})
            previews.append((filename, preview))
        textures.append(texture)
    return {"schema_version": 1, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "texture_count": len(textures), "textures": textures,
            "profile": "MC2-Xbox360-446/25-uncompressed-container-Format7-inlineLZX",
            "offset_convention": "bulk header/property/chunk block offsets relative to export or chunk; data_offset and serial_offset package-absolute",
            "runtime_rendering_verified": False}, previews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lzx-library", type=Path)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.output.exists() or args.package.resolve() == args.output.resolve():
            raise FormatError("output must be new and different from input")
        if bool(args.lzx_library) != bool(args.preview_dir):
            raise FormatError("preview-dir and lzx-library must be supplied together")
        if args.preview_dir and args.preview_dir.exists():
            raise FormatError("preview directory must be new")
        result, previews = inspect_package(args.package.read_bytes(), LzxDecoder(args.lzx_library) if args.lzx_library else None)
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True)
            for filename, data in previews:
                (args.preview_dir / filename).write_bytes(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
        print(json.dumps({"texture_count": result["texture_count"], "decoded_previews": len(previews), "sha256": result["sha256"]}))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
