"""Independent LZX stored-block writer for local resource proofs of concept.

MIT project code. No Huffman compression, proprietary data, or native code.
The optional decoder remains separate; see docs/LZX_STORED_RESEARCH.md.
"""
from __future__ import annotations

import struct

FRAME_SIZE = 0x8000
UE3_BLOCK_SIZE = 0x20000
MAX_STREAM_SIZE = UE3_BLOCK_SIZE
MAX_CHUNK_SIZE = 128 * 1024 * 1024


def encode_framed(data: bytes) -> bytes:
    """Encode 1..128 KiB into one continuous LZX stream with Xbox frames.

    One type-3 stored block per <=32 KiB frame. Only the first block has the
    stream's zero Intel-transform header bit. Decoder state continues across
    frames, but each UE3 block is a separate stream.
    """
    if not isinstance(data, bytes):
        raise TypeError("LZX source must be bytes")
    if not 0 < len(data) <= MAX_STREAM_SIZE:
        raise ValueError("LZX stored stream requires 1..131072 input bytes")
    frames = []
    for offset in range(0, len(data), FRAME_SIZE):
        raw = data[offset:offset + FRAME_SIZE]
        # MSB-first fields inside little-endian 16-bit words. First block:
        # Intel=0, type=3 (3 bits), length (24 bits), alignment=0 (4 bits).
        # Subsequent blocks omit Intel and have 5 alignment zero bits.
        padding = 4 if offset == 0 else 5
        word = ((3 << 24) | len(raw)) << padding
        header = struct.pack("<HH", word >> 16, word & 0xffff)
        stored = header + struct.pack("<III", 1, 1, 1) + raw
        if len(raw) & 1:
            stored += b"\0"
        frames.append(b"\xff" + struct.pack(">HH", len(raw), len(stored)) + stored)
    return b"".join(frames)


def wrap_ue3_chunk(data: bytes) -> bytes:
    """Wrap bytes into big-endian UE3 chunk with independent 128 KiB streams.

    The returned physical chunk starts with magic/block-size/totals and the
    compressed-size/uncompressed-size table. It is not a full UE3 package and
    does not modify package summaries, export offsets, TOCs, or original files.
    """
    if not isinstance(data, bytes):
        raise TypeError("UE3 chunk source must be bytes")
    if not 0 < len(data) <= MAX_CHUNK_SIZE:
        raise ValueError("UE3 stored chunk requires 1..134217728 input bytes")
    blocks = [(encode_framed(data[start:start + UE3_BLOCK_SIZE]),
               len(data[start:start + UE3_BLOCK_SIZE]))
              for start in range(0, len(data), UE3_BLOCK_SIZE)]
    total = sum(len(encoded) for encoded, _ in blocks)
    summary = struct.pack(">IIII", 0x9e2a83c1, UE3_BLOCK_SIZE, total, len(data))
    table = b"".join(struct.pack(">II", len(encoded), size) for encoded, size in blocks)
    return summary + table + b"".join(encoded for encoded, _ in blocks)
