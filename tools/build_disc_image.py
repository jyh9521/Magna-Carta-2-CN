"""Append-only, reversible XDVDFS test images from a hash-locked locale packet.

Original image bytes are retained. Only file-entry sector/size pairs change;
replacement payloads are sector-aligned beyond the original EOF. No executable,
media identity, authentication data, directory tree or filename is rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

from .disc_inventory import Disc, SECTOR, sha256_file
from .verify_resource_phase import hash_value, inspect, unique

KIND = 'append-only-xdvdfs-test-image'
BLOCK = 8 * 1024 * 1024


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)+'\n').encode()


def load_locked(path, expected):
    if Path(path).stat().st_size > 4*1024*1024:
        raise ValueError('report/manifest exceeds size bound')
    raw = Path(path).read_bytes()
    if len(raw) > 4*1024*1024 or hashlib.sha256(raw).hexdigest() != hash_value(expected):
        raise ValueError('report/manifest SHA256 or size mismatch')
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON')))


def new_path(path, inputs):
    path = Path(path).absolute()
    if path.is_symlink() or path.exists() or path.resolve() in {Path(p).resolve() for p in inputs}:
        raise ValueError('output must be new and distinct from inputs')
    if not path.parent.is_dir() or path.parent.resolve() != path.parent:
        raise ValueError('output parent must be an existing canonical directory')
    return path


def entry_offsets(disc, inventory):
    """Locate fields only after the existing strict reader validates the tree."""
    by_path = {r['path']: r for r in inventory}
    tables = [('', disc.root_sector, disc.root_size)]
    tables += [(r['path']+'/', r['sector'], r['size']) for r in inventory if r['directory']]
    offsets = {}
    extents = [(disc.base+0x10000, disc.base+0x10800)]
    for parent, sector, length in tables:
        if not length:
            continue
        start = disc.base+sector*SECTOR
        extents.append((start, start+length))
        data = disc.read(start, length)
        pending = [0]
        while pending:
            offset = pending.pop()
            left, right, first, size, flags, n = struct.unpack_from('<HHIIBB', data, offset)
            name = parent+data[offset+14:offset+14+n].decode('ascii')
            row = by_path[name]
            if name in offsets or (first, size, flags) != (row['sector'], row['size'], row['attributes']):
                raise ValueError('directory location disagrees with validated inventory')
            offsets[name] = start+offset
            pending.extend(v*4 for v in (right, left) if v)
    if set(offsets) != set(by_path):
        raise ValueError('directory entry set mismatch')
    for row in inventory:
        if not row['directory'] and row['size'] and any(
                row['offset'] < b and a < row['offset']+row['size'] for a,b in extents):
            raise ValueError('file overlaps directory or volume metadata')
    return offsets


def inputs(image, image_sha256, packet, packet_sha256, disc_number):
    image, packet = Path(image).resolve(), Path(packet).resolve()
    if type(disc_number) is not int or disc_number not in (1,2):
        raise ValueError('explicit disc 1 or 2 required')
    if sha256_file(image) != hash_value(image_sha256):
        raise ValueError('original image SHA256 mismatch')
    disc = Disc(image)
    if disc.size % SECTOR or disc.base % SECTOR:
        raise ValueError('unaligned source image')
    manifest = load_locked(packet/'manifest.json', packet_sha256)
    if (manifest.get('kind') != 'offline-disc-locale-raw-comparison'
            or manifest.get('disc') != disc_number
            or manifest.get('source_image_sha256') != image_sha256):
        raise ValueError('packet/source disc identity mismatch')
    result, _ = inspect(packet, packet_sha256, packet/'candidate', 'candidate')
    if not result['all_resources_match']:
        raise ValueError('candidate packet verification failed')
    inventory = disc.inventory()
    entries = {r['path']: r for r in inventory}
    offsets = entry_offsets(disc, inventory)
    changes = []
    cursor = disc.size
    for row in sorted(manifest['resources'], key=lambda r: r['path'].casefold()):
        if row['path'].lower().endswith('.xex'):
            raise ValueError('executable replacement is not part of a resource test image')
        old = entries.get(row['path'])
        if old is None or old['directory'] or old['size'] != row['original_size']:
            raise ValueError('original resource path/size mismatch')
        if disc.resource_hash(old) != row['original_sha256']:
            raise ValueError('original resource hash mismatch')
        size = row['candidate_size']
        if type(size) is not int or not 0 <= size <= 0xffffffff:
            raise ValueError('candidate size exceeds XDVDFS field')
        if row['candidate_sha256'] == row['original_sha256'] and size == old['size']:
            continue
        sector = (cursor-disc.base)//SECTOR
        if not 0 <= sector <= 0xffffffff:
            raise ValueError('candidate sector exceeds XDVDFS field')
        field = offsets[row['path']]+4
        before = struct.pack('<II', old['sector'], old['size'])
        if disc.read(field, 8) != before:
            raise ValueError('directory expected-byte mismatch')
        changes.append(dict(path=row['path'], field_offset=field, before_hex=before.hex(),
                            after_hex=struct.pack('<II', sector, size).hex(), sector=sector,
                            offset=cursor, size=size, sha256=row['candidate_sha256']))
        cursor += ((size+SECTOR-1)//SECTOR)*SECTOR
    return disc, manifest, inventory, changes, cursor


def transfer(source, destination, size, digest=None):
    while size:
        block = source.read(min(BLOCK, size))
        if not block:
            raise ValueError('short image/resource read')
        if destination is not None:
            destination.write(block)
        if digest is not None:
            digest.update(block)
        size -= len(block)


def original_prefix(image, size, changes, destination=None):
    """Replay inverse field edits while streaming, without modifying the input."""
    digest = hashlib.sha256()
    with Path(image).open('rb') as source:
        cursor = 0
        for row in sorted(changes, key=lambda r: r['field_offset']):
            offset = row['field_offset']
            before, after = bytes.fromhex(row['before_hex']), bytes.fromhex(row['after_hex'])
            if (type(offset) is not int or offset < cursor or offset+8 > size
                    or len(before) != 8 or len(after) != 8):
                raise ValueError('invalid or overlapping inverse field')
            transfer(source, destination, offset-cursor, digest)
            if source.read(8) != after:
                raise ValueError('inverse expected-byte mismatch')
            digest.update(before)
            if destination is not None:
                destination.write(before)
            cursor = offset+8
        transfer(source, destination, size-cursor, digest)
    return digest.hexdigest()


def verify(image, image_sha256, packet, packet_sha256, disc_number, output, report=None):
    source, manifest, old_entries, changes, output_size = inputs(
        image, image_sha256, packet, packet_sha256, disc_number)
    if report is not None and (report.get('kind') != KIND or report.get('schema_version') != 1
            or report.get('disc') != disc_number or report['source']['sha256'] != image_sha256
            or report['source']['size'] != source.size
            or report['packet']['manifest_sha256'] != packet_sha256):
        raise ValueError('published image provenance mismatch')
    output = Path(output).resolve()
    if output == source.path.resolve() or output.stat().st_size != output_size:
        raise ValueError('candidate image path/size mismatch')
    after = Disc(output)
    if (after.base, after.root_sector, after.root_size, after.timestamp_raw) != (
            source.base, source.root_sector, source.root_size, source.timestamp_raw):
        raise ValueError('volume metadata changed')
    if original_prefix(output, source.size, changes) != image_sha256:
        raise ValueError('original prefix changed outside declared directory fields')
    new_entries = after.inventory()
    if len(new_entries) != len(old_entries):
        raise ValueError('candidate entry count mismatch')
    replacements = {r['path']:r for r in changes}
    rows = []
    for old, new in zip(old_entries, new_entries):
        expected = dict(old)
        replacement = replacements.get(old['path'])
        if replacement:
            for key in ('sector','offset','size'):
                expected[key] = replacement[key]
        if new != expected:
            raise ValueError('candidate directory entry mismatch: '+old['path'])
        if not old['directory']:
            wanted = replacement['sha256'] if replacement else source.resource_hash(old)
            actual = after.resource_hash(new)
            if actual != wanted:
                raise ValueError('candidate file hash mismatch: '+old['path'])
            rows.append(dict(path=old['path'], sha256=actual, size=new['size'], localized=bool(replacement)))
    output_hash = sha256_file(output)
    if report is not None and (report['changes'] != changes or report['output']['sha256'] != output_hash
                               or report['output']['size'] != output_size):
        raise ValueError('published image report mismatch')
    if sha256_file(source.path) != image_sha256:
        raise ValueError('original image changed during verification')
    if hashlib.sha256((Path(packet)/'manifest.json').read_bytes()).hexdigest() != packet_sha256:
        raise ValueError('packet manifest changed during verification')
    return dict(status='PASS', disc=disc_number, files=len(rows), directories=len(new_entries)-len(rows),
                localized_files=len(changes), unchanged_files=len(rows)-len(changes),
                all_file_hashes_match=True, original_prefix_inverse_sha256=image_sha256,
                output_sha256=output_hash, output_size=output_size, file_inventory=rows,
                game_started=False, game_rendering_verified=False)


def build(image, image_sha256, packet, packet_sha256, disc_number, output, report_path):
    output = new_path(output, [image, Path(packet)/'manifest.json', report_path])
    report_path = new_path(report_path, [image, output, Path(packet)/'manifest.json'])
    source, manifest, inventory, changes, output_size = inputs(
        image, image_sha256, packet, packet_sha256, disc_number)
    source_state = source.path.stat()
    with source.path.open('rb') as original, output.open('x+b') as target:
        digest = hashlib.sha256()
        transfer(original, target, source.size, digest)
        if digest.hexdigest() != image_sha256:
            raise ValueError('source changed during image copy')
        for row in changes:
            if target.tell() != row['offset']:
                raise ValueError('append cursor mismatch')
            resource = Path(packet)/'candidate'/row['path']
            digest = hashlib.sha256()
            with resource.open('rb') as stream:
                transfer(stream, target, row['size'], digest)
                if stream.read(1) or digest.hexdigest() != row['sha256']:
                    raise ValueError('candidate resource changed while appending')
            target.write(bytes((-row['size']) % SECTOR))
        if target.tell() != output_size:
            raise ValueError('output allocation mismatch')
        for row in changes:
            target.seek(row['field_offset'])
            if target.read(8).hex() != row['before_hex']:
                raise ValueError('candidate directory expected-byte mismatch')
            target.seek(row['field_offset'])
            target.write(bytes.fromhex(row['after_hex']))
        target.flush()
        os.fsync(target.fileno())
    now = source.path.stat()
    if (source_state.st_size,source_state.st_mtime_ns) != (now.st_size,now.st_mtime_ns):
        raise ValueError('source image changed during publication')
    proof = verify(image, image_sha256, packet, packet_sha256, disc_number, output)
    report = dict(schema_version=1, kind=KIND, disc=disc_number,
                  source=dict(path=str(source.path), size=source.size, sha256=image_sha256,
                              partition_base=source.base),
                  packet=dict(path=str(Path(packet).resolve()), manifest_sha256=packet_sha256),
                  output=dict(path=str(output), size=output_size, sha256=proof['output_sha256']),
                  changed_fields=['directory_entry.sector','directory_entry.size'], changes=changes,
                  verification=proof, game_started=False, game_rendering_verified=False)
    with report_path.open('xb') as stream:
        stream.write(encoded(report))
    if report_path.read_bytes() != encoded(report):
        raise ValueError('report reopening mismatch')
    return report


def restore(modified, report_path, report_sha256, output):
    report = load_locked(report_path, report_sha256)
    if report.get('kind') != KIND or report.get('schema_version') != 1:
        raise ValueError('unsupported image rollback report')
    output = new_path(output, [modified, report_path, report['source']['path']])
    modified = Path(modified).resolve()
    if (modified.stat().st_size != report['output']['size'] or
            sha256_file(modified) != hash_value(report['output']['sha256'])):
        raise ValueError('modified image identity mismatch')
    source = report['source']
    if type(source['size']) is not int or not 0 < source['size'] <= report['output']['size']:
        raise ValueError('invalid original image size')
    with output.open('xb') as target:
        actual = original_prefix(modified, source['size'], report['changes'], target)
        target.flush()
        os.fsync(target.fileno())
    if actual != hash_value(source['sha256']) or sha256_file(output) != source['sha256']:
        raise ValueError('restored image hash mismatch')
    if sha256_file(modified) != report['output']['sha256']:
        raise ValueError('modified image changed during rollback')
    return dict(status='PASS', disc=report['disc'], restored_sha256=actual,
                restored_size=output.stat().st_size, modified_image_unchanged=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    for operation in ('build','verify'):
        p = sub.add_parser(operation)
        p.add_argument('--image', type=Path, required=True)
        p.add_argument('--image-sha256', required=True)
        p.add_argument('--packet', type=Path, required=True)
        p.add_argument('--packet-sha256', required=True)
        p.add_argument('--disc', type=int, choices=(1,2), required=True)
        p.add_argument('--output', type=Path, required=True)
        p.add_argument('--report', type=Path, required=True)
        if operation == 'verify':
            p.add_argument('--report-sha256', required=True)
    p = sub.add_parser('restore')
    p.add_argument('--modified', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--report-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = parser.parse_args(argv)
    try:
        if a.operation == 'restore':
            result = restore(a.modified,a.report,a.report_sha256,a.output)
        else:
            args = (a.image,a.image_sha256,a.packet,a.packet_sha256,a.disc,a.output)
            if a.operation == 'build':
                r = build(*args,a.report)
                result = {k:v for k,v in r['verification'].items() if k!='file_inventory'}
            else:
                report = load_locked(a.report,a.report_sha256)
                result = verify(*args,report=report)
                result = {k:v for k,v in result.items() if k!='file_inventory'}
        print(json.dumps(result,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('ERROR: '+str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
