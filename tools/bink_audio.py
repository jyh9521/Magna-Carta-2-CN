"""Bounded BIKi packet transport preserving compressed audio without decoding.

The frame-prefix layout is independently documented by FFmpeg's Bink demuxer.
No FFmpeg implementation is copied here. Only revision i, non-alpha clips with
at most eight tracks and 6144 frames are supported. Replacements are silent BIKi
clips of identical dimensions, frame count and rate.
"""
from __future__ import annotations

import hashlib
import struct


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect(data):
    if not isinstance(data, (bytes, bytearray)) or len(data) < 48 or data[:4] != b'BIKi':
        raise ValueError('Expected bounded BIKi container')
    size, count, largest, repeated, width, height, num, den, flags, tracks = struct.unpack_from('<10I', data, 4)
    if (size + 8 != len(data) or count != repeated or not 1 <= count <= 6144
            or not 1 <= width <= 1920 or not 1 <= height <= 1080
            or not num or not den or flags or not 0 <= tracks <= 8):
        raise ValueError('Unsupported BIKi dimensions, audio, flags or frame count')
    table_offset = 44 + 12 * tracks
    table_end = table_offset + 4 * (count + 1)
    if table_end > len(data):
        raise ValueError('Truncated BIKi audio metadata/frame table')
    metadata = bytes(data[44:table_offset])
    if tracks:
        maximum = struct.unpack_from('<' + 'I' * tracks, metadata)
        rates_flags = struct.unpack_from('<' + 'HH' * tracks, metadata, 4 * tracks)
        identities = struct.unpack_from('<' + 'I' * tracks, metadata, 8 * tracks)
        if (any(not 0 < n <= 16 * 1024 * 1024 for n in maximum)
                or any(not 8000 <= rates_flags[2*i] <= 192000 or rates_flags[2*i+1] & ~0x7000 for i in range(tracks))
                or len(set(identities)) != tracks):
            raise ValueError('Unsupported BIKi audio metadata')
    indexed = struct.unpack_from('<' + 'I' * (count + 1), data, table_offset)
    offsets = [n & ~1 for n in indexed]
    if (offsets[0] < table_end or offsets[-1] != len(data)
            or any(a >= b for a, b in zip(offsets, offsets[1:]))
            or max(b-a for a, b in zip(offsets, offsets[1:])) != largest):
        raise ValueError('Invalid BIKi frame offsets/largest frame')
    frames = []
    for index, (start, end) in enumerate(zip(offsets, offsets[1:])):
        cursor = start
        audio = []
        for _ in range(tracks):
            if cursor + 4 > end:
                raise ValueError('Truncated BIKi audio length')
            length = struct.unpack_from('<I', data, cursor)[0]
            if length > end - cursor - 4:
                raise ValueError('BIKi audio packet leaves its frame')
            audio.append(bytes(data[cursor:cursor+4+length]))
            cursor += 4 + length
        video = bytes(data[cursor:end])
        if not video or len(video) % 2:
            raise ValueError('BIKi video packet must be nonempty and even-sized')
        frames.append(dict(audio=audio, video=video, keyframe=bool(indexed[index] & 1)))
    return dict(header=dict(width=width, height=height, frames=count, numerator=num,
                            denominator=den, magic='BIKi', audio_tracks=tracks),
                audio_metadata=metadata, frames=frames,
                padding=bytes(data[table_end:offsets[0]]))


def _assemble(template, frames, metadata, tracks, padding=b''):
    header = template['header']
    count = header['frames']
    if len(frames) != count or len(metadata) != 12 * tracks or len(padding) % 2:
        raise ValueError('BIKi assembly shape mismatch')
    payloads = [b''.join(frame['audio']) + frame['video'] for frame in frames]
    if any(not payload or len(payload) % 2 for payload in payloads):
        raise ValueError('BIKi frame parity mismatch')
    offsets = [44 + len(metadata) + 4 * (count + 1) + len(padding)]
    for payload in payloads:
        offsets.append(offsets[-1] + len(payload))
    indexed = [offset | int(frames[i]['keyframe']) if i < count else offset
               for i, offset in enumerate(offsets)]
    result = b'BIKi' + struct.pack('<10I', offsets[-1]-8, count, max(map(len, payloads)), count,
        header['width'], header['height'], header['numerator'], header['denominator'], 0, tracks)
    result += metadata + struct.pack('<' + 'I' * (count + 1), *indexed) + padding + b''.join(payloads)
    inspect(result)
    return result


def strip_audio(source):
    parsed = inspect(source)
    frames = [dict(audio=[], video=f['video'], keyframe=f['keyframe']) for f in parsed['frames']]
    return _assemble(parsed, frames, b'', 0, parsed['padding'])


def replace_video(source, silent):
    original, replacement = inspect(source), inspect(silent)
    if replacement['header']['audio_tracks']:
        raise ValueError('Replacement video must be silent')
    fields = ('width', 'height', 'frames', 'numerator', 'denominator', 'magic')
    if any(original['header'][k] != replacement['header'][k] for k in fields):
        raise ValueError('Replacement video changed geometry/frame count/timing')
    frames = [dict(audio=a['audio'], video=b['video'], keyframe=b['keyframe'])
              for a, b in zip(original['frames'], replacement['frames'], strict=True)]
    result = _assemble(original, frames, original['audio_metadata'], original['header']['audio_tracks'], original['padding'])
    check = inspect(result)
    if audio_fingerprint(check) != audio_fingerprint(original):
        raise ValueError('Original compressed audio changed during transport')
    return result


def replace_video_tail(source, silent_tail, first_frame):
    """Preserve original prefix packets and restart an encoded tail at a keyframe.

    The original header, frame count/rate and every compressed audio packet are
    retained. The tail must be a complete independent silent BIKi clip, not a
    predicted-frame fragment. Decoded replay remains the caller's required gate.
    """
    original, tail = inspect(source), inspect(silent_tail)
    old, new = original['header'], tail['header']
    if (type(first_frame) is not int or not 0 <= first_frame < old['frames']
            or new['audio_tracks'] or new['frames'] != old['frames'] - first_frame
            or any(old[k] != new[k] for k in ('width', 'height', 'magic'))
            or not original['frames'][0]['keyframe'] or not tail['frames'][0]['keyframe']):
        raise ValueError('Independent silent keyframe tail geometry/count mismatch')
    old_rate, new_rate = old['numerator'] / old['denominator'], new['numerator'] / new['denominator']
    if abs(old_rate - new_rate) / old_rate > .0001:
        raise ValueError('Encoded tail changed frame rate')
    frames = list(original['frames'][:first_frame])
    frames += [dict(audio=a['audio'], video=b['video'], keyframe=b['keyframe'])
               for a, b in zip(original['frames'][first_frame:], tail['frames'], strict=True)]
    result = _assemble(original, frames, original['audio_metadata'], old['audio_tracks'], original['padding'])
    check = inspect(result)
    if (check['header'] != old or check['frames'][:first_frame] != original['frames'][:first_frame]
            or audio_fingerprint(check) != audio_fingerprint(original)):
        raise ValueError('Original prefix/audio changed during tail transport')
    return result


def trim_silent_guard_frames(encoded, expected_frames, maximum_guard_frames):
    """Remove only explicitly declared trailing encoder guard packets.

    Some AVI readers floor clip durations and lose the last intended frame.
    The producer can append duplicate raw guard frames; no missing frame is
    invented here, and no audio-bearing or unexpectedly long clip is trimmed.
    """
    if (type(expected_frames) is not int or not 1 <= expected_frames <= 6144
            or type(maximum_guard_frames) is not int or not 0 <= maximum_guard_frames <= 2):
        raise ValueError('Explicit encoder guard-frame bound')
    parsed = inspect(encoded)
    count = parsed['header']['frames']
    if (parsed['header']['audio_tracks'] or not expected_frames <= count <= expected_frames + maximum_guard_frames
            or not parsed['frames'][0]['keyframe']):
        raise ValueError('Encoder lost intended frames or exceeded declared silent guards')
    if count == expected_frames:
        return bytes(encoded)
    template = {**parsed, 'header': {**parsed['header'], 'frames': expected_frames}}
    return _assemble(template, parsed['frames'][:expected_frames], b'', 0, parsed['padding'])


def audio_fingerprint(parsed):
    tracks = parsed['header']['audio_tracks']
    return dict(tracks=tracks, metadata_sha256=digest(parsed['audio_metadata']),
                frame_packets=[[digest(packet) for packet in frame['audio']] for frame in parsed['frames']],
                track_payload_sha256=[digest(b''.join(frame['audio'][i] for frame in parsed['frames'])) for i in range(tracks)])
