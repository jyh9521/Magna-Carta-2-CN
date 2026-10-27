"""Normalize generated stored-LZX resource copies without reencoding artwork.

This is an offline format transformation, not a successful-boot assertion. Only
byte-exact matches to this project's stored writer identify generated streams;
original compressed streams and unsupported original texture layouts stay put.
The supported inner profile is the existing inline single-mip BC1/BC3 profile.
"""
from __future__ import annotations

import hashlib
import re
import struct

from .decompress_package import decompress_copy
from .lzx_stored import wrap_ue3_chunk
from .supplement_font import decode_logical
from .texture_layout import read_texture
from .ue3_package import FormatError, Reader, parse_summary, parse_tables
from .ue3_fonts import read_properties
from .ue3_textures import compressed_chunk

MAX_PACKAGE_BYTES = 512 * 1024 * 1024
MAX_CHUNK_BYTES = 128 * 1024 * 1024
MAGIC = b'\x9e\x2a\x83\xc1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def generated_chunk_offsets(payload, decoder):
    """Find only complete, bounded, exactly reproducible stored chunks.

    Used as a fail-closed guard on unsupported texture layouts. A matching magic
    word alone is not enough to identify a chunk or authorize an edit.
    """
    found = []
    position = 0
    count = 0
    while True:
        position = payload.find(MAGIC, position)
        if position < 0:
            return found
        count += 1
        if count > 4096:
            raise FormatError('texture chunk candidate count exceeds bound')
        start = position
        position += 4
        if start + 16 > len(payload):
            continue
        _, block_size, packed, unpacked = struct.unpack_from('>IIII', payload, start)
        if not 0 < block_size <= 16 * 1024 * 1024 or not 0 < unpacked <= MAX_CHUNK_BYTES:
            continue
        blocks = (unpacked + block_size - 1) // block_size
        if blocks > 4096:
            continue
        size = 16 + blocks * 8 + packed
        if size > len(payload) - start:
            continue
        candidate = payload[start:start + size]
        # Validate framing/totals before involving the native decoder. Invalid
        # magic collisions are data, not a damaged compressed-stream assertion.
        try:
            compressed_chunk(candidate, unpacked, None)
        except FormatError:
            continue
        raw = compressed_chunk(candidate, unpacked, decoder)[1]
        if raw is None:
            raise FormatError('generated-stream audit requires LZX decoder')
        if candidate == wrap_ue3_chunk(raw):
            found.append(start)


def _already_raw_single_mip(payload, names, serial_offset):
    """Recognize an untouched raw bulk header without allocating tile maps.

    No artwork interpretation is needed for a byte-identical retained export.
    The complete conversion parser still checks all selected compressed exports.
    """
    try:
        reader = Reader(payload)
        reader.i32()
        read_properties(reader, names)
        source = reader.pos
        if [reader.u32() for _ in range(4)] != [0, 0, 0, serial_offset + source + 16]:
            return False
        if reader.u32() != 1:
            return False
        flags, count, size, at = [reader.u32() for _ in range(4)]
        return (flags == 0 and 0 < count == size
                and at == serial_offset + reader.pos and reader.pos + size + 8 == len(payload))
    except FormatError:
        return False


def normalize_package(data, expected_sha256, decoder):
    """Return a new byte string and proof; never edit an input or launch a game."""
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_PACKAGE_BYTES:
        raise FormatError('bounded immutable package bytes required')
    if (not isinstance(expected_sha256, str)
            or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None
            or sha(data) != expected_sha256):
        raise FormatError('package SHA256 mismatch')
    summary = parse_summary(data, len(data))
    if summary['byte_order'] != 'big' or summary['compression_flags'] not in (0, 4):
        raise FormatError('only big-endian raw/LZX 446/25 package profile supported')
    if bool(summary['compression_flags']) != bool(summary['package_flags'] & 0x02000000):
        raise FormatError('inconsistent compressed package flag')
    logical = decode_logical(data, summary, decoder)
    tables = parse_tables(logical, summary, len(logical))
    generated_outer = []
    for index, chunk in enumerate(summary['compressed_chunks']):
        start, size = chunk['uncompressed_offset'], chunk['uncompressed_size']
        packed_start, packed_size = chunk['compressed_offset'], chunk['compressed_size']
        if data[packed_start:packed_start + packed_size] == wrap_ue3_chunk(logical[start:start + size]):
            generated_outer.append(index)

    selected = []
    retained_unsupported = []
    supported_textures = 0
    original_lzx_textures = 0
    raw_textures_preserved = 0
    for index, export in enumerate(tables['exports']):
        if export['class_path'] != 'Engine.Texture2D':
            continue
        offset, size = export['serial_offset'], export['serial_size']
        payload = logical[offset:offset + size]
        if _already_raw_single_mip(payload, tables['names'], offset):
            raw_textures_preserved += 1
            continue
        texture = None
        errors = []
        for fmt in (5, 7):
            try:
                texture = read_texture(payload, tables['names'], offset,
                                       {'kind': 'xbox-inline-bc-v1', 'format': fmt}, decoder)
                break
            except FormatError as exc:
                errors.append(str(exc))
        if texture is None:
            if generated_chunk_offsets(payload, decoder):
                raise FormatError('generated stored-LZX in unsupported texture layout: ' + export['path'])
            retained_unsupported.append({'object': export['path'], 'payload_sha256': sha(payload),
                                         'reasons': errors})
            continue
        supported_textures += 1
        if texture['flags'] != 64:
            continue
        at = texture['payload_offset']
        packed = payload[at:at + texture['stored_size']]
        if packed == wrap_ue3_chunk(texture['tiles']):
            selected.append((index, export, payload, texture))
        else:
            original_lzx_textures += 1

    outer_decompressed = bool(summary['compression_flags'] and (generated_outer or selected))
    if outer_decompressed:
        raw, outer_proof = decompress_copy(data, expected_sha256, decoder, alignment=1)
    else:
        raw, outer_proof = data, None
    output = bytearray(raw)
    changed_fields = []
    texture_proofs = []
    for index, export, payload, texture in selected:
        target = (len(output) + 3) & ~3
        at, old_size = texture['payload_offset'], texture['stored_size']
        native = texture['tiles']
        patched = bytearray(payload[:at] + native + payload[at + old_size:])
        struct.pack_into('>I', patched, texture['source_offset'] + 12,
                         target + texture['source_offset'] + 16)
        struct.pack_into('>IIII', patched, texture['bulk_offset'],
                         0, len(native), len(native), target + at)
        check = read_texture(bytes(patched), tables['names'], target,
                             {'kind': 'xbox-inline-bc-v1', 'format': texture['format']}, decoder)
        if check['tiles'] != native or check['flags'] != 0:
            raise FormatError('raw texture native tile roundtrip mismatch')
        output.extend(bytes(target - len(output)) + patched)
        field = export['table_offset'] + 32
        struct.pack_into('>II', output, field, len(patched), target)
        changed_fields.append((field, field + 8))
        texture_proofs.append(dict(object=export['path'], export_index=index + 1,
                                   old_serial_offset=export['serial_offset'], new_serial_offset=target,
                                   old_serial_size=export['serial_size'], new_serial_size=len(patched),
                                   before_flags=64, after_flags=0,
                                   before_tiles_sha256=sha(native), after_tiles_sha256=sha(check['tiles']),
                                   before_payload_sha256=sha(payload), after_payload_sha256=sha(patched),
                                   native_tiles_preserved=True))
    changed = outer_decompressed or bool(selected)
    if changed:
        # Compare whole spans in native byte operations rather than iterating
        # every byte in Python for hundreds of multi-megabyte resources.
        cursor = 0
        for start, end in sorted(changed_fields):
            if raw[cursor:start] != output[cursor:start]:
                raise FormatError('raw logical prefix changed outside selected export fields')
            cursor = end
        if raw[cursor:] != output[cursor:len(raw)]:
            raise FormatError('raw logical prefix changed outside selected export fields')
        output.extend(bytes((-len(output)) % 32768))
    result = bytes(output)
    after_summary = parse_summary(result, len(result))
    after_logical = decode_logical(result, after_summary, decoder)
    after_tables = parse_tables(after_logical, after_summary, len(after_logical))
    if tables['names'] != after_tables['names'] or tables['imports'] != after_tables['imports']:
        raise FormatError('name/import tables changed')
    selected_indexes = {index for index, _, _, _ in selected}
    for index, (before, after) in enumerate(zip(tables['exports'], after_tables['exports'])):
        off, size = before['serial_offset'], before['serial_size']
        if index not in selected_indexes:
            if before != after or logical[off:off + size] != after_logical[off:off + size]:
                raise FormatError('nonselected export changed')
        elif {k: v for k, v in before.items() if k not in ('serial_offset', 'serial_size')} != {
                k: v for k, v in after.items() if k not in ('serial_offset', 'serial_size')}:
            raise FormatError('selected export metadata changed outside size/offset')
    if changed and (after_summary['compression_flags'] or after_summary['package_flags'] & 0x02000000):
        raise FormatError('normalized package retained outer compression')
    proof = dict(schema_version=1, kind='offline-generated-lzx-normalization',
                 input_sha256=expected_sha256, input_size=len(data), output_sha256=sha(result),
                 output_size=len(result), changed=changed, generated_outer_chunks=len(generated_outer),
                 generated_outer_chunk_indexes=generated_outer, outer_decompressed=outer_decompressed,
                 outer_proof=outer_proof, converted_bulk_count=len(selected), textures=texture_proofs,
                 supported_texture_exports=supported_textures,
                 raw_texture_exports_preserved=raw_textures_preserved,
                 original_lzx_texture_exports_preserved=original_lzx_textures,
                 unsupported_texture_exports_preserved=retained_unsupported,
                 nonselected_exports_preserved=len(tables['exports']) - len(selected),
                 native_tiles_preserved=True, name_import_tables_preserved=True,
                 game_started=False, game_rendering_verified=False)
    return result, proof
