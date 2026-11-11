"""Source-bound PPC replay of INI section/key *admission*, not a game emulator.

The negative result is strong only when the native loop reaches its terminal
branch without admitting any section. Positive controls can either stop at
section admission or explicitly inject a successful section-map witness and
continue to key admission. No allocator, TMap insertion, rendering, complete
FString implementation or macro substitution is simulated. Macro input fails
closed. The profile binds the actual image, instruction windows and constants.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.coalesced import parse, write_json_atomic
from tools.ppc_fragment import FragmentError, MemorySegment, run_fragment

MAX_UNITS = 4096
BUFFER = 0x70000000
STRING = 0x70010000
SECTION_WITNESS = 0x70020000
MAX_REPLAY_STEPS = MAX_UNITS * 100


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def address(value):
    if not isinstance(value, str) or not value.startswith('0x'):
        raise ValueError('profile addresses must be hexadecimal strings')
    result = int(value, 16)
    if not 0 <= result < 1 << 32:
        raise ValueError('profile address outside u32')
    return result


def validate_profile(image, profile):
    if profile.get('schema_version') != 1:
        raise ValueError('unsupported native profile schema')
    base = address(profile['image_base'])
    if sha256(image) != profile['image_sha256']:
        raise ValueError('native image SHA-256 mismatch')
    windows = profile['windows']
    if set(windows) != {'loader', 'array', 'fstring', 'macro_replace', 'parser', 'wcslen', 'wcsstr'}:
        raise ValueError('native profile window set mismatch')
    for name, window in windows.items():
        a, z = address(window['start']), address(window['end'])
        if a % 4 or z % 4 or not base <= a < z <= base + len(image):
            raise ValueError(f'invalid native window: {name}')
        if sha256(image[a-base:z-base]) != window['sha256']:
            raise ValueError(f'native window SHA-256 mismatch: {name}')
    for name, value in profile['labels'].items():
        a = address(value)
        if a % 4 or not any(address(w['start']) <= a < address(w['end']) for w in windows.values()):
            raise ValueError(f'native label outside code: {name}')
    for name, item in profile['constants'].items():
        a = address(item['address'])
        raw = (item['text'] + '\0').encode('utf-16-be')
        if not base <= a <= base + len(image) - len(raw) or image[a-base:a-base+len(raw)] != raw:
            raise ValueError(f'native constant mismatch: {name}')
    return base


class Replay:
    """Small orchestration layer; branch decisions come from native opcodes."""

    def __init__(self, image, profile):
        self.image = image
        self.profile = profile
        self.base = validate_profile(image, profile)
        self.labels = {k: address(v) for k, v in profile['labels'].items()}
        self.trace = []
        self.fragments = 0

    def run(self, window, entry, stops, regs, memory):
        w = self.profile['windows'][window]
        result = run_fragment(self.image, self.base, (address(w['start']), address(w['end'])),
                              entry, set(stops) - {entry}, regs, memory)
        self.trace.extend(result.trace)
        self.fragments += 1
        if len(self.trace) > MAX_REPLAY_STEPS:
            raise FragmentError('INI replay total instruction budget exhausted')
        return result

    def swap(self, raw):
        l = self.labels
        data = raw + b'\0\0'
        count = len(data) // 2
        memory = (MemorySegment(BUFFER, data, True),
                  MemorySegment(STRING, struct.pack('>III', BUFFER, count, count)))
        regs = {30: STRING}
        pc = l['swap_entry']
        stops = {l[k] for k in ('swap_loop', 'swap_compare', 'swap_done')}
        while pc != l['swap_done']:
            r = self.run('fstring', pc, stops, regs, memory)
            pc, regs, memory = r.stop_pc, r.registers, r.segments
        swapped = memory[0].data
        if swapped != (raw.decode('utf-16-le') + '\0').encode('utf-16-be'):
            raise FragmentError('native FString byte swap differs from expected code units')
        return (memory[0],)

    def length(self, regs, memory):
        l = self.labels
        pc = l['length_entry']
        stops = {l[k] for k in ('length_loop', 'length_compare', 'length_return_pc')}
        while pc != l['length_return_pc']:
            r = self.run('wcslen', pc, stops, regs, memory)
            pc, regs, memory = r.stop_pc, r.registers, r.segments
        return regs, memory

    def find(self, regs, memory):
        l = self.labels
        pc = l['find_entry']
        stops = {l[k] for k in ('find_empty_return', 'find_outer', 'find_reset', 'find_inner',
                                'find_check', 'find_match_return', 'find_advance', 'find_return_pc')}
        while pc != l['find_return_pc']:
            r = self.run('wcsstr', pc, stops, regs, memory)
            pc, regs, memory = r.stop_pc, r.registers, r.segments
            if pc in (l['find_empty_return'], l['find_match_return']):
                # Handle only the verified BEQLR leaf return. Its CR was produced
                # by native code in this fragment; no condition is reconstructed.
                if struct.unpack_from('>I', self.image, pc-self.base)[0] != 0x4d820020:
                    raise FragmentError('conditional leaf return opcode mismatch')
                self.trace.append(pc)
                if r.cr_bits[2]:
                    break
                pc += 4
        return regs, memory


def replay_document(image, profile, raw_utf16le, *, assume_section_map_success=False):
    """Read-only native admission replay; a positive source stops by default."""
    if not isinstance(raw_utf16le, bytes) or len(raw_utf16le) % 2:
        raise ValueError('expected even-sized UTF-16LE payload without terminator')
    if len(raw_utf16le) // 2 > MAX_UNITS:
        raise ValueError('document exceeds bounded replay size')
    text = raw_utf16le.decode('utf-16-le', errors='strict')
    if '\0' in text:
        raise ValueError('embedded NUL is outside replay profile')
    macro = profile['constants']['macro']['text']
    if not macro or macro in text:
        raise ValueError('macro-bearing input requires a separate native replacement profile')
    engine = Replay(image, profile)
    l = engine.labels
    memory = engine.swap(raw_utf16le)
    regs = {26: BUFFER}
    pc = l['parser_init']
    stops = {l[k] for k in ('skip_newline', 'line_start', 'scan', 'scan_update', 'split_line',
                            'length_call', 'section_admitted', 'section_gate', 'find_call',
                            'key_admitted', 'line_end', 'parser_done')}
    lines = []
    section_admissions = 0
    key_admissions = 0
    assumptions = []
    line = None
    while pc != l['parser_done']:
        r = engine.run('parser', pc, stops, regs, memory)
        pc, regs, memory = r.stop_pc, r.registers, r.segments
        if pc == l['line_start']:
            line = {'number': len(lines)+1, 'start_unit': (regs[26]-BUFFER)//2}
        elif pc == l['split_line']:
            if line is None:
                raise FragmentError('line boundary without native line start')
            a = line['start_unit']*2
            z = regs[26]-BUFFER
            raw_line = memory[0].data[a:z]
            line.update(code_units=len(raw_line)//2, sha256_utf16be=sha256(raw_line),
                        first_codeunit=int.from_bytes(raw_line[:2], 'big') if raw_line else None,
                        last_codeunit=int.from_bytes(raw_line[-2:], 'big') if raw_line else None,
                        prefix_utf16be_hex=raw_line[:32].hex(),
                        delimiter_codeunit=int.from_bytes(memory[0].data[z:z+2], 'big'),
                        decision='not-yet-decided')
        elif pc == l['length_call']:
            regs, memory = engine.length(regs, memory)
            pc = l['length_return']
        elif pc == l['section_admitted']:
            section_admissions += 1
            line['decision'] = 'native-section-admission'
            if not assume_section_map_success:
                lines.append(line)
                break
            assumptions.append({'line': line['number'], 'kind': 'section-map-success-witness',
                                'native_stop': hex(pc), 'resume': hex(l['line_end'])})
            regs[27] = SECTION_WITNESS
            pc = l['line_end']
        elif pc == l['section_gate']:
            line['decision'] = 'no-section-skip' if regs[27] == 0 else 'section-key-check'
        elif pc == l['find_call']:
            regs, memory = engine.find(regs, memory)
            pc = l['find_return']
        elif pc == l['key_admitted']:
            key_admissions += 1
            line['decision'] = 'native-key-admission-not-insertion'
            line['equals_unit'] = (regs[3]-BUFFER)//2
            assumptions.append({'line': line['number'], 'kind': 'skip-key-insertion',
                                'native_stop': hex(pc), 'resume': hex(l['line_end'])})
            pc = l['line_end']
        if pc == l['line_end']:
            lines.append(line)
            line = None
    terminal = pc == l['parser_done']
    if terminal and (regs[19] != 1 or regs[26] != BUFFER + len(raw_utf16le) + 2):
        raise FragmentError('native exit did not consume exactly the final NUL')
    return dict(schema_version=1, evidence_type='bounded-native-instruction-replay',
                document_sha256=sha256(raw_utf16le), code_units=len(raw_utf16le)//2,
                terminal=terminal, stop_pc=hex(pc), final_cursor_unit=(regs[26]-BUFFER)//2,
                final_current_section=hex(regs[27]), section_admissions=section_admissions,
                key_admissions=key_admissions, map_insertions_executed=0,
                macro_absent=True, assumptions=assumptions, lines=lines,
                instruction_count=len(engine.trace), fragment_count=engine.fragments,
                executed_pcs=[hex(x) for x in sorted(set(engine.trace))],
                trace_sha256=sha256(b''.join(struct.pack('>I',x) for x in engine.trace)),
                conclusion='verified-no-section-no-key-registration-route'
                    if terminal and not section_admissions and not assumptions
                    else 'native-admission-only-not-completed-registration')


def run_controls(image, profile):
    cases = {
        'no_section': ('K=example', False, (True, 0, 0)),
        'bad_section_tail': ('[S]junk\nK=example', False, (True, 0, 0)),
        'valid_section_stop': ('[S]\nK=example', False, (False, 1, 0)),
        'valid_section_key_witness': ('[S]\nK=example', True, (True, 1, 1)),
        'later_valid_section_witness': ('[S]junk\nK=old\n[T]\nK=example', True, (True, 1, 1)),
        'crlf_and_empty_lines_witness': ('\r\n[S]\r\n\r\nK=example\r\n', True, (True, 1, 1)),
        'valid_section_no_equals_witness': ('[S]\nK', True, (True, 1, 0)),
        'empty': ('', False, (True, 0, 0)),
    }
    outputs = {}
    for name, (text, witness, expected) in cases.items():
        result = replay_document(image, profile, text.encode('utf-16-le'), assume_section_map_success=witness)
        actual = result['terminal'], result['section_admissions'], result['key_admissions']
        if actual != expected:
            raise FragmentError(f'synthetic control failed: {name}: {actual} != {expected}')
        outputs[name] = {'input': text, 'expected': list(expected), 'result': result}
    try:
        replay_document(image, profile, '[%GAME%]\nK=x'.encode('utf-16-le'))
    except ValueError as e:
        if 'macro-bearing' not in str(e):
            raise
        outputs['macro_rejected'] = {'input': '[%GAME%]\nK=x', 'error': str(e), 'expected': 'rejected'}
    else:
        raise FragmentError('macro control did not fail closed')
    return outputs


def select_document(data, embedded_path, expected_sha256):
    matches = [f for f in parse(data) if f.path.text == embedded_path]
    if len(matches) != 1 or matches[0].content.encoding != 'utf-16-le':
        raise ValueError('expected one exact UTF-16LE embedded document')
    content = matches[0].content
    units = struct.unpack_from('>i', data, content.offset)[0]
    raw = data[content.offset+4:content.offset+4+(-units-1)*2]
    if raw != content.text.encode('utf-16-le') or sha256(raw) != expected_sha256:
        raise ValueError('embedded document SHA-256 or serialized byte mismatch')
    return raw, content.offset


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image', type=Path, required=True)
    ap.add_argument('--profile', type=Path, required=True)
    ap.add_argument('--coalesced', type=Path, required=True)
    ap.add_argument('--coalesced-sha256', required=True)
    ap.add_argument('--embedded-path', required=True)
    ap.add_argument('--embedded-sha256', required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--controls', action='store_true')
    ap.add_argument('--expect-inactive', action='store_true')
    args = ap.parse_args(argv)
    inputs = (args.image, args.profile, args.coalesced)
    if any(args.output.resolve() == p.resolve() or
           (args.output.exists() and p.exists() and args.output.samefile(p)) for p in inputs):
        raise ValueError('report output aliases a read-only input')
    image, profile_raw, data = (p.read_bytes() for p in inputs)
    if sha256(data) != args.coalesced_sha256:
        raise ValueError('Coalesced SHA-256 mismatch')
    profile = json.loads(profile_raw)
    raw, offset = select_document(data, args.embedded_path, args.embedded_sha256)
    result = replay_document(image, profile, raw)
    report = dict(schema_version=1, image_sha256=sha256(image), profile_sha256=sha256(profile_raw),
                  coalesced_sha256=sha256(data), embedded_path=args.embedded_path,
                  serialized_length_offset=offset, payload_offset=offset+4, payload_bytes=len(raw),
                  source=result, boundary=profile['boundary'])
    if args.controls:
        report['controls'] = run_controls(image, profile)
    if any(p.read_bytes() != b for p,b in zip(inputs,(image,profile_raw,data))):
        raise ValueError('read-only input changed during replay')
    write_json_atomic(args.output, report)
    if json.loads(args.output.read_text(encoding='utf-8')) != report:
        raise ValueError('report reopen verification failed')
    print(f"source_gate: terminal={str(result['terminal']).lower()} section_admissions={result['section_admissions']} key_admissions={result['key_admissions']} lines={len(result['lines'])}")
    print(f"native_exit: {result['stop_pc']} cursor={result['final_cursor_unit']} code_units={result['code_units']} assumptions={len(result['assumptions'])}")
    if args.controls:
        print(f"controls: PASS {len(report['controls'])}")
    print('inputs: unchanged; report: reopened')
    if args.expect_inactive and result['conclusion'] != 'verified-no-section-no-key-registration-route':
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
