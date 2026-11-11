"""Replay a source-bound positive-length FString byte-widen loop, read-only.

The allocator, archive read, free and callers are outside this bounded proof.
Only actual instructions between the declared entry and stop are interpreted;
the supplied byte buffer models a completed archive read including its NUL.
No code-page choice, replacement decoder, or game-rendering claim is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from .ppc_fragment import MemorySegment, run_fragment
from .replay_ini_registration import address
from .verify_resource_phase import unique

MAX_BYTES = 65535
BUFFER, OUTPUT, STRING = 0x70000000, 0x70020000, 0x70050000


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_profile(image, profile):
    if (not isinstance(profile, dict) or type(profile.get('schema_version')) is not int
            or profile['schema_version'] != 1
            or profile.get('kind') != 'positive-fstring-byte-widen-profile'):
        raise ValueError('unsupported byte-widen profile')
    base = address(profile['image_base'])
    if base % 4 or digest(image) != profile['image_sha256']:
        raise ValueError('native image SHA256/base mismatch')
    window = profile['window']
    a, z = address(window['start']), address(window['end'])
    if a % 4 or z % 4 or not base <= a < z <= base + len(image):
        raise ValueError('native window outside image')
    if digest(image[a-base:z-base]) != window['sha256']:
        raise ValueError('native window SHA256 mismatch')
    labels = {k: address(v) for k, v in profile['labels'].items()}
    if (set(labels) != {'entry', 'loop', 'compare', 'done'}
            or len(set(labels.values())) != 4
            or any(v % 4 or not a <= v < z for v in labels.values())
            or not labels['entry'] < labels['loop'] < labels['compare'] < labels['done']):
        raise ValueError('invalid byte-widen labels')
    return base, (a, z), labels


def replay(image, profile, payload):
    if (not isinstance(image, bytes) or not isinstance(payload, bytes)
            or len(payload) > MAX_BYTES or b'\0' in payload):
        raise ValueError('expected bounded bytes without terminator/embedded NUL')
    base, window, labels = validate_profile(image, profile)
    source = payload + b'\0'
    count = len(source)
    memory = (MemorySegment(BUFFER, source),
              MemorySegment(OUTPUT, b'\xcc' * (2 * count), True),
              MemorySegment(STRING, struct.pack('>III', OUTPUT, count, count)))
    registers = {29: BUFFER, 30: STRING}
    pc = labels['entry']; trace = []; fragments = 0; stores = 0
    while pc != labels['done']:
        r = run_fragment(image, base, window, pc,
                         {labels[k] for k in ('loop', 'compare', 'done')} - {pc},
                         registers, memory)
        pc, registers, memory = r.stop_pc, r.registers, r.segments
        trace.extend(r.trace); fragments += 1; stores += len(r.stores)
        if len(trace) > (count + 1) * 32 or fragments > (count + 1) * 4:
            raise ValueError('byte-widen replay budget exhausted')
    expected = b''.join(bytes((0, c)) for c in source)
    if memory[0].data != source or memory[2].data != struct.pack('>III', OUTPUT, count, count):
        raise ValueError('read-only source/descriptor changed')
    if memory[1].data != expected or stores != count or registers[11] != count:
        raise ValueError('native loop did not widen every input byte exactly once')
    text = expected[:-2].decode('utf-16-be')
    return dict(schema_version=1, kind='positive-fstring-byte-widen-replay',
                decoder='unsigned-byte-to-u16', image_sha256=digest(image),
                profile_id=profile.get('profile_id'), payload_sha256=digest(payload),
                payload_size=len(payload), decoded_utf8_sha256=digest(text.encode('utf8')),
                non_ascii=[dict(offset=i, byte=b, codepoint=f'U+{b:04X}')
                           for i, b in enumerate(payload) if b >= 128],
                terminal=True, stop_pc=hex(pc), units_including_terminator=count,
                stores=stores, instruction_count=len(trace), fragment_count=fragments,
                executed_pcs=[hex(v) for v in sorted(set(trace))],
                trace_sha256=digest(b''.join(struct.pack('>I', v) for v in trace)),
                source_unchanged=True, allocation_and_archive_read_executed=False,
                ini_registration_executed=False, game_rendering_verified=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('image', 'profile', 'payload', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    for key in ('profile', 'payload'):
        p.add_argument('--' + key + '-sha256', required=True)
    args = p.parse_args(argv)
    try:
        if args.output.exists() or args.output.resolve() in {args.image.resolve(), args.profile.resolve(), args.payload.resolve()}:
            raise ValueError('new disjoint output required')
        pr = args.profile.read_bytes(); raw = args.payload.read_bytes()
        if len(pr) > 65536 or digest(pr) != args.profile_sha256 or digest(raw) != args.payload_sha256:
            raise ValueError('profile/payload SHA256 mismatch')
        image = args.image.read_bytes()
        result = replay(image, json.loads(pr, object_pairs_hook=unique), raw)
        result['profile_sha256'] = digest(pr)
        if args.payload.read_bytes() != raw or args.profile.read_bytes() != pr or digest(args.image.read_bytes()) != digest(image):
            raise ValueError('source changed during replay')
        output = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as stream:
            stream.write(output)
        if args.output.read_bytes() != output:
            raise ValueError('report reopening mismatch')
        print(f'BYTES={len(raw)} WIDENED_UNITS={result["stores"]} HIGH_BYTES={len(result["non_ascii"])} SOURCE_UNCHANGED=YES RESULT=PASS')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
