"""Read-only, source-locked FString candidate census of effective UE3 packages.

This is a byte-structure screen, not a property parser or a visibility oracle.
Counted UTF-16LE/UTF-8 FStrings and bounded VM-token candidates are selected. The source
script intervals come from an explicit policy; no locale is built into tooling.
"""
import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from .disc_inventory import Disc, sha256_file
from .font_binding_plan import _relative
from .supplement_font import decode_logical
from .ue3_package import LzxDecoder, parse_summary, parse_tables
from .verify_resource_phase import unique


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def locked(path, expected, limit=512 * 1024 * 1024):
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Expected lowercase SHA256')
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit or digest(raw) != expected:
        raise ValueError('Input size/SHA256 mismatch: ' + str(path))
    return raw


def script_ranges(policy):
    ranges = policy.get('script_ranges')
    if not isinstance(ranges, dict) or not 1 <= len(ranges) <= 16:
        raise ValueError('Explicit script ranges required')
    for name, spans in ranges.items():
        if not isinstance(name, str) or not isinstance(spans, list) or not 1 <= len(spans) <= 16:
            raise ValueError('Invalid script ranges')
        for span in spans:
            if (not isinstance(span, list) or len(span) != 2 or
                    any(type(n) is not int for n in span) or not 0 <= span[0] <= span[1] <= 0x10ffff):
                raise ValueError('Invalid Unicode interval')
    return ranges


def overlapping_matches(pattern, data):
    """Keep overlapping starts without disabling regex literal-prefix search."""
    expression = re.compile(pattern)
    position = 0
    while True:
        match = expression.search(data, position)
        if match is None:
            return
        yield match
        position = match.start() + 1


def fstring_candidates(raw, ranges, exports=()):
    """Find bounded serialized candidates at any byte offset, including odd ones.

    The byte prefilter represents BE lengths -4096 through -1. A complete
    counted UTF-16LE value, final NUL, strict decode, absence of embedded NUL,
    and printable/control-whitelist characters are required. Ownership is
    reported only when the complete serialized extent lies in one export.
    """
    ordered = sorted((e['serial_offset'], e['serial_offset'] + e['serial_size'], i, e)
                     for i, e in enumerate(exports, 1) if e['serial_size'])
    starts = [e[0] for e in ordered]
    high_water = []
    for _, end, _, _ in ordered:
        high_water.append(max(end, high_water[-1] if high_water else 0))
    result = []
    for match in overlapping_matches(rb'\xff\xff[\xf0-\xff][\x00-\xff]', raw):
        at = match.start()
        count = -struct.unpack_from('>i', raw, at)[0]
        end = at + 4 + 2 * count
        if count < 2 or end > len(raw) or raw[end - 2:end] != b'\0\0':
            continue
        payload = raw[at + 4:end - 2]
        try:
            value = payload.decode('utf-16-le')
        except UnicodeError:
            continue
        if not value or any(not c.isprintable() and c not in '\t\n\r' for c in value):
            continue
        hits = [name for name, spans in ranges.items()
                if any(lo <= ord(c) <= hi for c in value for lo, hi in spans)]
        if not hits:
            continue
        owner = None
        slot = bisect_right(starts, at) - 1
        owners = []
        while slot >= 0 and high_water[slot] >= end:
            lo, hi, index, entry = ordered[slot]
            if end <= hi:
                owners.append(dict(export=index, path=entry['path'], class_path=entry['class_path'],
                                   relative_offset=at - lo))
            slot -= 1
        if len(owners) == 1:
            owner = owners[0]
        result.append(dict(logical_offset=at, size=end - at, length_be=-count,
                           serialized_sha256=digest(raw[at:end]), text=value,
                           encoding='utf-16-le', kind='counted-fstring',
                           script_hits=hits, owner=owner, property_type_verified=False,
                           runtime_display_observed=False))
    return result


def additional_candidates(raw, ranges, exports):
    """UTF-8 FString and UnicodeConst token candidates, without VM-boundary claims."""
    result = []
    for index, entry in enumerate(exports, 1):
        start, size = entry['serial_offset'], entry['serial_size']
        data = raw[start:start + size]
        owner = dict(export=index, path=entry['path'], class_path=entry['class_path'])
        # ASCII-only strings are not relevant to the caller's non-ASCII ranges.
        for match in overlapping_matches(rb'\x00\x00(?:\x00[\x02-\xff]|[\x01-\x0f][\x00-\xff]|\x10\x00)', data):
            at = match.start()
            count = struct.unpack_from('>I', data, at)[0]
            end = at + 4 + count
            if not 2 <= count <= 4096 or end > len(data) or data[end - 1] != 0:
                continue
            payload = data[at + 4:end - 1]
            if payload.isascii():
                continue
            try:
                text = payload.decode('utf-8')
            except UnicodeError:
                continue
            if any(not c.isprintable() and c not in '\t\n\r' for c in text):
                continue
            hits = [name for name, spans in ranges.items()
                    if any(lo <= ord(c) <= hi for c in text for lo, hi in spans)]
            if hits:
                result.append(dict(kind='counted-fstring', encoding='utf-8', logical_offset=start + at,
                                   size=end - at, length_be=count, text=text, script_hits=hits,
                                   owner={**owner, 'relative_offset': at},
                                   serialized_sha256=digest(data[at:end]), property_type_verified=False,
                                   runtime_display_observed=False))
        if entry['class_path'].rsplit('.', 1)[-1] not in ('Function', 'State'):
            continue
        for match in re.finditer(b'\x34', data):
            at = match.start()
            for encoding in ('utf-16-le', 'utf-16-be'):
                end = at + 1
                chunks = []
                while end + 2 <= len(data) and len(chunks) < 512:
                    pair = data[end:end + 2]
                    end += 2
                    if pair == b'\0\0':
                        break
                    try:
                        character = pair.decode(encoding)
                    except UnicodeError:
                        break
                    if not character.isprintable() and character not in '\t\n\r':
                        break
                    chunks.append(character)
                if not chunks or data[end - 2:end] != b'\0\0':
                    continue
                text = ''.join(chunks)
                hits = [name for name, spans in ranges.items()
                        if any(lo <= ord(c) <= hi for c in text for lo, hi in spans)]
                if hits:
                    result.append(dict(kind='vm-unicode-token-candidate', encoding=encoding,
                                       logical_offset=start + at, size=end - at, text=text,
                                       script_hits=hits, owner={**owner, 'relative_offset': at},
                                       serialized_sha256=digest(data[at:end]),
                                       instruction_boundary_verified=False, runtime_display_observed=False))
    return result


def census(recipe, inventories, root, decoder, ranges, progress=None, disc_factory=Disc):
    root = Path(root).resolve()
    if (not isinstance(recipe.get('discs'), list) or not 1 <= len(recipe['discs']) <= 8 or
            set(inventories) != set(range(1, len(recipe['discs']) + 1))):
        raise ValueError('Disc inventory contract mismatch')
    members = []
    discs = {}
    images = []
    snapshots = {}
    for number, view in enumerate(recipe['discs'], 1):
        image = Path(view['iso'])
        image = image if image.is_absolute() else root / image
        inv = inventories[number]
        disc = disc_factory(image)
        if image.stat().st_size != inv['image_size'] or inv['sha256'] != view['sha256']:
            raise ValueError('Original image identity declaration mismatch')
        if sha256_file(image) != view['sha256']:
            raise ValueError('Original image hash mismatch')
        actual = {(r['path'], r.get('offset'), r.get('size')) for r in disc.inventory() if not r['directory']}
        declared = {(r['path'], r.get('offset'), r.get('size')) for r in inv['entries'] if not r['directory']}
        if actual != declared:
            raise ValueError('Original directory/inventory mismatch')
        discs[number] = disc
        images.append((image, view['sha256']))
        updates = {r['path']: r for r in view['resources']}
        if len(updates) != len(view['resources']):
            raise ValueError('Duplicate recipe resource')
        original_names = {r['path'] for r in inv['entries'] if not r['directory']}
        if not set(updates).issubset(original_names):
            raise ValueError('Recipe resource absent from original inventory')
        for row in inv['entries']:
            if row['directory'] or not row['path'].lower().endswith('.xxx'):
                continue
            name = _relative(row['path'])
            if type(row['size']) is not int or not 0 < row['size'] <= 512 * 1024 * 1024:
                raise ValueError('Original package size bound')
            update = updates.get(name)
            member = dict(disc=number, resource=name, original_sha256=row['sha256'],
                          effective_sha256=update['sha256'] if update else row['sha256'],
                          original_offset=row['offset'], original_size=row['size'])
            if update:
                path = Path(update['file'])
                path = (path if path.is_absolute() else root / path).resolve()
                if path in snapshots and snapshots[path] != update['sha256']:
                    raise ValueError('Conflicting effective input identity')
                snapshots[path] = update['sha256']
                member['effective_file'] = str(path)
            members.append(member)
    if not members:
        raise ValueError('No package resources in declared inventories')
    cache = {}
    total_bytes = 0
    for ordinal, member in enumerate(members, 1):
        expected = member['effective_sha256']
        if 'effective_file' in member:
            raw = locked(member['effective_file'], expected)
        else:
            raw = discs[member['disc']].read(member['original_offset'], member['original_size'])
            if digest(raw) != expected:
                raise ValueError('Original package hash mismatch: ' + member['resource'])
        member['effective_size'] = len(raw)
        if expected not in cache:
            total_bytes += len(raw)
            record = dict(effective_sha256=expected, effective_size=len(raw), candidates=[])
            try:
                summary = parse_summary(raw, len(raw))
                logical_size = max([len(raw)] + [c['uncompressed_offset'] + c['uncompressed_size']
                                                for c in summary['compressed_chunks']])
                if logical_size > 512 * 1024 * 1024:
                    raise ValueError('Logical package bound')
                logical = decode_logical(raw, summary, decoder)
                record.update(logical_size=len(logical), logical_sha256=digest(logical))
                tables = parse_tables(logical, summary, len(logical))
                record.update(export_count=len(tables['exports']), status='screened',
                              candidates=fstring_candidates(logical, ranges, tables['exports']) +
                              additional_candidates(logical, ranges, tables['exports']))
            except (ValueError, OSError, UnicodeError, struct.error) as error:
                record.update(status='unknown', error=str(error))
            cache[expected] = record
        member['status'] = cache[expected]['status']
        if progress:
            progress(ordinal, len(members), member, cache[expected])
    for path, expected in snapshots.items():
        locked(path, expected)
    for image, expected in images:
        if sha256_file(image) != expected:
            raise ValueError('Original image changed during census')
    counts = Counter(r['status'] for r in cache.values())
    return dict(schema_version=1, kind='effective-package-fstring-census', members=members,
                unique_packages=list(cache.values()), script_ranges=ranges,
                summary=dict(package_memberships=len(members), unique_packages=len(cache),
                             screened_unique=counts['screened'], unknown_unique=counts['unknown'],
                             unique_input_bytes=total_bytes,
                             candidate_fields=sum(len(r['candidates']) for r in cache.values())),
                candidate_structure='BE length/UTF-16LE or UTF-8/NUL, 2..4096 units; token34 UTF16 in Function/State exports, <=512 units',
                coverage_exclusions=['UTF-8 FStrings outside export serial ranges (including package name tables)',
                                     'other encodings and arbitrary native formats', 'texture/movie glyph pixels',
                                     'values exceeding the declared length bounds', 'non-Function/State VM carriers',
                                     'DLC containers not part of disc package inventories'],
                complete_language_coverage_claimed=False, source_files_unchanged=True,
                game_resources_written=0, game_started=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('recipe', 'policy', 'lzx-library'):
        parser.add_argument('--' + name, type=Path, required=True)
        parser.add_argument('--' + name + '-sha256', required=True)
    parser.add_argument('--inventory', action='append', required=True, metavar='DISC=JSON=SHA256')
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve()
        output = args.output_dir.resolve()
        if output.exists() or output == root or not output.is_relative_to(root):
            raise ValueError('New output directory inside project required')
        snapshots = [(args.recipe, args.recipe_sha256), (args.policy, args.policy_sha256),
                     (args.lzx_library, args.lzx_library_sha256)]
        recipe = json.loads(locked(*snapshots[0], 4 * 1024 * 1024), object_pairs_hook=unique)
        policy = json.loads(locked(*snapshots[1], 4 * 1024 * 1024), object_pairs_hook=unique)
        ranges = script_ranges(policy)
        locked(*snapshots[2], 32 * 1024 * 1024)
        inventories = {}
        for ref in args.inventory:
            number, path, sha = ref.split('=', 2)
            number = int(number)
            if number in inventories:
                raise ValueError('Duplicate inventory disc')
            snapshots.append((Path(path), sha))
            inventories[number] = json.loads(locked(path, sha, 32 * 1024 * 1024), object_pairs_hook=unique)
        output.mkdir(parents=True)
        with (output / 'progress.jsonl').open('x', encoding='utf-8') as stream:
            def progress(index, total, member, record):
                row = dict(index=index, total=total, disc=member['disc'], resource=member['resource'],
                           sha256=member['effective_sha256'], status=record['status'],
                           candidate_fields=len(record['candidates']))
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                if index % 100 == 0 or index == total:
                    print(f'PACKAGES={index}/{total}', flush=True)
            result = census(recipe, inventories, root, LzxDecoder(args.lzx_library), ranges, progress)
        for path, sha in snapshots:
            locked(path, sha)
        result['input_identities'] = [dict(path=str(p.resolve()), sha256=s) for p, s in snapshots]
        raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
        target = output / 'report.json'
        with target.open('xb') as stream:
            stream.write(raw)
        if target.read_bytes() != raw:
            raise ValueError('Output readback mismatch')
        print(' '.join(k.upper() + '=' + str(v) for k, v in result['summary'].items()))
        return int(bool(result['summary']['unknown_unique']))
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
