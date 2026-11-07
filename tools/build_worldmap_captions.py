"""Build bounded video captions while retaining every original Bink audio packet.

The renderer and independent image replay are shared with build_video_captions.
Only the audio transport is new: video-only BIKi inputs/outputs are temporary
derived resources, and original compressed tracks are remuxed without decoding.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from . import bink_audio
from . import build_video_captions as captions
from .video_caption import decoded_frames
from .verify_resource_phase import unique


def write_locked(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Existing derived resource identity mismatch: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(raw)
    if path.read_bytes() != raw:
        raise ValueError('Derived resource reopening mismatch')


def run(args):
    root = args.project_root.resolve()
    source_root = args.source_root.resolve()
    output = args.output_dir.resolve()
    if output == root or not output.is_relative_to(root):
        raise ValueError('Output must stay inside project')
    if output.is_relative_to(source_root) or source_root.is_relative_to(output):
        raise ValueError('Source and output trees must be disjoint')
    plan_raw = captions.locked_file(args.plan, args.plan_sha256, 8 * 1024 * 1024)
    plan = json.loads(plan_raw, object_pairs_hook=unique)
    if (plan.get('schema_version') != 1 or plan.get('kind') != 'bink-audio-caption-plan'
            or not isinstance(plan.get('entries'), list) or not 1 <= len(plan['entries']) <= 64):
        raise ValueError('Expected bounded audio-caption plan')
    # Validate every output identity before deriving even the first file. The
    # shared renderer's later validation is not an output confinement boundary.
    ids = []
    files = []
    for entry in plan['entries']:
        identity = entry['id']
        if (not isinstance(identity, str) or not 1 <= len(identity) <= 64
                or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in identity)):
            raise ValueError('Movie identifier must be a bounded leaf name')
        ids.append(identity)
        files.append(captions.canonical_relative(entry['source']['file']).casefold())
        captions.canonical_relative(entry['source']['member'])
        captions.encoded_size_limit(entry)
        captions.frame_count_limit(entry)
        captions.encoder_time_limit(entry)
    if len(set(ids)) != len(ids) or len(set(files)) != len(files):
        raise ValueError('Duplicate movie identity or source member')
    if args.entry is not None and args.entry not in ids:
        raise ValueError('Unknown movie identifier')
    source_data = {}
    derived = json.loads(plan_raw)
    derived['kind'] = 'bink-caption-plan'
    for original, entry in zip(plan['entries'], derived['entries'], strict=True):
        ref = original['source']
        source = captions.member(source_root, ref['file'])
        raw = captions.locked_file(source, ref['sha256'])
        if len(raw) != ref['size']:
            raise ValueError('Original sound movie size mismatch')
        parsed = bink_audio.inspect(raw)
        if parsed['header']['frames'] > captions.frame_count_limit(original):
            raise ValueError('Original sound movie exceeds its explicit frame limit')
        if parsed['header'] != original['expected_header']:
            raise ValueError('Original sound movie metadata mismatch')
        silent = bink_audio.strip_audio(raw)
        # An independent exact identity round trip validates packet boundaries
        # before any lossy video encoding or artwork operation.
        if bink_audio.replace_video(raw, silent) != raw:
            raise ValueError('Original Bink packet identity round trip failed')
        name = original['id'] + '.silent.bik'
        write_locked(captions.member(output, 'video-only-sources/' + name), silent)
        entry['source'].update(file=name, size=len(silent), sha256=bink_audio.digest(silent))
        source_data[original['id']] = raw
    derived_raw = captions.encoded(derived)
    derived_path = output / 'video-only-plan.json'
    write_locked(derived_path, derived_raw)
    captions.load_plan(derived_path, bink_audio.digest(derived_raw))
    args_dict = vars(args).copy()
    args_dict.update(plan=derived_path, plan_sha256=bink_audio.digest(derived_raw),
                     source_root=output/'video-only-sources', output_dir=output/'video-only-results')
    summaries = captions.run(SimpleNamespace(**args_dict))
    if args.preview:
        return summaries
    selected = [e for e in plan['entries'] if args.entry is None or e['id'] == args.entry]
    reports = []
    for entry in selected:
        name = entry['id']
        original = source_data[name]
        encoded_path = output / 'video-only-results' / (name + '.bik')
        silent = encoded_path.read_bytes()
        report_path = output / (name + '.json')
        target = output / (name + '.bik')
        if args.verify:
            report = json.loads(report_path.read_bytes(), object_pairs_hook=unique)
            final = captions.locked_file(target, report['output_sha256'])
        else:
            final = bink_audio.replace_video(original, silent)
            write_locked(target, final)
        parsed = bink_audio.inspect(final)
        original_parsed = bink_audio.inspect(original)
        if parsed['header'] != original_parsed['header']:
            raise ValueError('Final audio-caption header changed')
        audio = bink_audio.audio_fingerprint(parsed)
        if audio != bink_audio.audio_fingerprint(original_parsed):
            raise ValueError('Final original audio packet comparison failed')
        # Padding may differ between source and encoder, but every compressed
        # video packet and keyframe bit must remain those independently checked
        # by the shared caption producer.
        native_video = bink_audio.inspect(silent)['frames']
        if any(a['video'] != b['video'] or a['keyframe'] != b['keyframe']
               for a, b in zip(parsed['frames'], native_video, strict=True)):
            raise ValueError('Final remux changed encoded video packets')
        silent_report = json.loads((encoded_path.with_suffix('.json')).read_bytes())
        hashes = [bink_audio.digest(data) for data in decoded_frames(args.ffmpeg, target, parsed['header'])]
        if hashes != [r['decoded_rgb_sha256'] for r in silent_report['frames']]:
            raise ValueError('Final sound-container decoded video differs from independently replayed video')
        current = dict(schema_version=1, kind='bink-audio-caption-verification', status='PASS', id=name,
            original_member=entry['source']['member'], discs=entry['source']['discs'],
            source_sha256=bink_audio.digest(original), source_size=len(original),
            output_sha256=bink_audio.digest(final), output_size=len(final), header=parsed['header'],
            audio=audio, audio_packets_byte_identical=True, original_identity_round_trip=True,
            decoded_frames=len(hashes), decoded_video_matches_independent_replay=True,
            video_only_report=str(encoded_path.with_suffix('.json').relative_to(root).as_posix()),
            plan_sha256=args.plan_sha256, source_unchanged=True,
            hidden_background_reconstructed=True, game_rendering_verified=False,
            visual_style_acceptance=False)
        if all('frame_alpha' in caption for caption in entry['captions']):
            original_path=captions.member(source_root,entry['source']['file'])
            source_hashes=[bink_audio.digest(data) for data in decoded_frames(args.ffmpeg,original_path,original_parsed['header'])]
            # A source-locked cleanup repair may intentionally outlive visible
            # text. Only frames outside BOTH explicit operations are no-ops.
            active=set()
            for caption in entry['captions']:
                active.update(index for index,alpha in enumerate(caption['frame_alpha']) if alpha)
                active.update(record['index'] for record in
                    caption.get('erase',{}).get('frame_repairs',{}).get('records',[]))
            inactive=[index for index in range(original_parsed['header']['frames']) if index not in active]
            if any(source_hashes[index]!=silent_report['frames'][index]['expected_rgb_sha256'] for index in inactive):
                raise ValueError('An inactive caption frame changed before encoding')
            current['timed_caption_verification']=dict(inactive_frames=len(inactive),
                inactive_preencode_source_byte_identical=True,
                source_frame_rgb_hashes=source_hashes)
        if args.verify:
            if current != report:
                raise ValueError('Final audio-caption report replay mismatch')
        else:
            write_locked(report_path, captions.encoded(current))
        if captions.member(source_root, entry['source']['file']).read_bytes() != original:
            raise ValueError('Original movie changed during transport')
        reports.append(current)
        print('PASS ' + name + ': ' + str(len(hashes)) + ' frames; ' + str(audio['tracks']) +
              ' original compressed audio tracks byte-identical', flush=True)
    summary = dict(schema_version=1, kind='bink-audio-caption-bundle', status='PASS',
        plan_sha256=args.plan_sha256, entries=reports, game_rendering_verified=False)
    manifest_name = 'manifest.json' if args.entry is None else 'manifest-' + args.entry + '.json'
    write_locked(output/manifest_name, captions.encoded(summary))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--entry')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--verify', action='store_true')
    modes.add_argument('--preview', action='store_true')
    parser.add_argument('--ffmpeg', type=Path, required=True)
    parser.add_argument('--ffmpeg-sha256', required=True)
    parser.add_argument('--encoder', type=Path)
    parser.add_argument('--encoder-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if not args.verify and not args.preview and args.encoder is None:
            raise ValueError('Explicit licensed Bink encoder required')
        run(args)
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError, subprocess.SubprocessError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
