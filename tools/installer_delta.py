"""Bounded, source-dependent XOR deltas; no executable or complete game files.

MCD1: magic, BE source/target lengths, source/target SHA256, then independently
zlib-compressed 1-MiB XOR blocks (BE packed length). The source is zero-extended
only to the target length. Every block, EOF and both identities are checked.
"""
from __future__ import annotations

import hashlib
import io
import struct
import zlib

BLOCK = 1024 * 1024
MAX_RESOURCE = 512 * BLOCK
HEADER = struct.Struct('>4sQQ32s32s')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def xor_bytes(left, right):
    return (int.from_bytes(left, 'little') ^ int.from_bytes(right, 'little')).to_bytes(len(left), 'little')


def create_delta(source, target):
    if max(len(source), len(target)) > MAX_RESOURCE:
        raise ValueError('delta resource exceeds 512 MiB')
    out = io.BytesIO()
    out.write(HEADER.pack(b'MCD1', len(source), len(target),
                          hashlib.sha256(source).digest(), hashlib.sha256(target).digest()))
    for at in range(0, len(target), BLOCK):
        part = target[at:at + BLOCK]
        mask = xor_bytes(part, source[at:at + len(part)].ljust(len(part), b'\0'))
        packed = zlib.compress(mask, 9)
        out.write(struct.pack('>I', len(packed)))
        out.write(packed)
    return out.getvalue()


def apply_delta(source, patch, check_cancel=lambda: None):
    if len(patch) < HEADER.size or len(patch) > MAX_RESOURCE + BLOCK:
        raise ValueError('invalid delta size')
    magic, source_size, size, before, after = HEADER.unpack_from(patch)
    if magic != b'MCD1' or max(source_size, size) > MAX_RESOURCE:
        raise ValueError('unsupported delta header')
    if len(source) != source_size or hashlib.sha256(source).digest() != before:
        raise ValueError('delta source identity mismatch')
    out, cursor = bytearray(), HEADER.size
    while len(out) < size:
        check_cancel()
        if cursor + 4 > len(patch):
            raise ValueError('truncated delta block')
        length = struct.unpack_from('>I', patch, cursor)[0]
        cursor += 4
        if not 1 <= length <= BLOCK + 4096 or cursor + length > len(patch):
            raise ValueError('delta compressed extent outside bounds')
        count = min(BLOCK, size - len(out))
        decoder = zlib.decompressobj()
        mask = decoder.decompress(patch[cursor:cursor + length], count + 1)
        if len(mask) != count or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('delta decoded length/EOF mismatch')
        cursor += length
        at = len(out)
        out.extend(xor_bytes(mask, source[at:at + count].ljust(count, b'\0')))
    if cursor != len(patch) or hashlib.sha256(out).digest() != after:
        raise ValueError('delta result identity/trailing bytes mismatch')
    return bytes(out)
