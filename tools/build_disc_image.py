"""Append-only, reversible XDVDFS test images from a hash-locked locale packet.

Original image bytes are retained. Only file-entry sector/size pairs change;
replacement payloads are sector-aligned beyond the original EOF. Disc TOC
position fields follow the new layout; its zero-size self entry is preserved.
No executable, media identity, directory tree or filename is rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct

from .disc_inventory import Disc, SECTOR, sha256_file
from .verify_resource_phase import hash_value, inspect, unique
from .update_resource_sizes import LINE, normalize_path

KIND = 'append-only-xdvdfs-test-image'
BLOCK = 8 * 1024 * 1024
TOC_LIMIT = 4 * 1024 * 1024


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


def toc_rows(raw):
    """Parse exact numeric spans without normalizing the serialized text."""
    if not isinstance(raw, bytes) or not raw or len(raw) > TOC_LIMIT:
        raise ValueError('TOC exceeds size bound or is empty')
    raw.decode('ascii')
    rows = []
    folded = set()
    offset = 0
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        body = line[:-2] if line.endswith(b'\r\n') else line[:-1] if line.endswith(b'\n') else line
        match = LINE.fullmatch(body)
        if match is None or b'\r' in body:
            raise ValueError(f'malformed TOC line {line_number}')
        path = normalize_path(match[4].decode('ascii'))
        if path.casefold() in folded:
            raise ValueError('duplicate or case-ambiguous TOC path: '+path)
        folded.add(path.casefold())
        if any(int(match[i]) > 0xffffffff for i in (1, 3)):
            raise ValueError('TOC size/sector exceeds uint32')
        rows.append(dict(path=path, size=int(match[1]), sector=int(match[3]),
                         offset=offset, line=line_number, match=match))
        offset += len(line)
    return rows


def inspect_toc(raw, entries, toc_path, label='image'):
    """Check the actual TOC against independently read directory entries."""
    if toc_path not in entries or entries[toc_path].get('directory', False):
        raise ValueError(label+' TOC directory entry missing')
    rows = toc_rows(raw)
    if toc_path not in {r['path'] for r in rows}:
        raise ValueError(label+' TOC self entry missing')
    checked = 0
    for row in rows:
        entry = entries.get(row['path'])
        if entry is None or entry.get('directory', False):
            continue
        expected_size = 0 if row['path'] == toc_path else entry['size']
        if row['size'] != expected_size:
            raise ValueError(label+' TOC size mismatch: '+row['path'])
        if row['sector'] != entry['sector']:
            raise ValueError(label+' TOC sector mismatch: '+row['path'])
        checked += 1
    return dict(rows_checked=checked, unmapped_rows=len(rows)-checked)


def relocate_toc(raw, expected_entries, target_entries, toc_path, label='candidate'):
    """Rewrite only guarded size/sector spans, with a byte-exact inverse proof.

    Builders use candidate sizes and original sectors as expected_entries.
    Repair callers may supply independently hash-locked old TOC positions;
    silently adopting mismatched fields from the input is never supported.
    """
    inspected = inspect_toc(raw, expected_entries, toc_path, label)
    edits = []
    for row in toc_rows(raw):
        old = expected_entries.get(row['path'])
        if old is None or old.get('directory', False):
            continue
        target = target_entries.get(row['path'])
        if target is None or target.get('directory', False):
            raise ValueError('TOC target entry missing: '+row['path'])
        for field, group in (('size', 1), ('sector', 3)):
            value = 0 if field == 'size' and row['path'] == toc_path else target[field]
            if type(value) is not int or not 0 <= value <= 0xffffffff:
                raise ValueError('TOC target size/sector exceeds uint32')
            if value == row[field]:
                continue
            start, end = row['match'].span(group)
            edits.append(dict(path=row['path'], line=row['line'], field=field,
                source_byte_offset=row['offset']+start,
                before_hex=raw[row['offset']+start:row['offset']+end].hex(),
                after_hex=str(value).encode('ascii').hex()))
    output = bytearray()
    cursor = 0
    for edit in sorted(edits, key=lambda e:e['source_byte_offset']):
        before, after = bytes.fromhex(edit['before_hex']), bytes.fromhex(edit['after_hex'])
        start = edit['source_byte_offset']
        if start < cursor or raw[start:start+len(before)] != before:
            raise ValueError('TOC rewrite expected-byte mismatch')
        output.extend(raw[cursor:start]); edit['output_byte_offset'] = len(output)
        output.extend(after); cursor = start+len(before)
    output.extend(raw[cursor:])
    output = bytes(output)
    inverse = bytearray(); cursor = 0
    for edit in sorted(edits, key=lambda e:e['output_byte_offset']):
        before, after = bytes.fromhex(edit['before_hex']), bytes.fromhex(edit['after_hex'])
        start = edit['output_byte_offset']
        if output[start:start+len(after)] != after:
            raise ValueError('TOC inverse expected-byte mismatch')
        inverse.extend(output[cursor:start]); inverse.extend(before); cursor=start+len(after)
    inverse.extend(output[cursor:])
    if inverse != raw:
        raise ValueError('TOC inverse bytes differ')
    inspect_toc(output, target_entries, toc_path, 'relocated')
    return output, dict(path=toc_path, candidate_sha256=hashlib.sha256(raw).hexdigest(),
        output_sha256=hashlib.sha256(output).hexdigest(), edits=edits,
        inverse_byte_identical=True, **inspected)


def inputs(image, image_sha256, packet, packet_sha256, disc_number, legacy_layout=False):
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
    candidates = {}
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
        candidates[row['path']] = row
    toc_paths = [p for p, row in entries.items()
                 if not row['directory'] and p.rsplit('/', 1)[-1].casefold() == 'xbox360toc.txt']
    if len(toc_paths) > 1:
        raise ValueError('multiple disc TOCs require an explicit layout profile')
    expected = {p:dict(row) for p,row in entries.items()}
    for path,row in candidates.items():
        expected[path]['size'] = row['candidate_size']
    toc_inputs = {}
    for path in toc_paths:
        old = entries[path]
        if old['size'] > TOC_LIMIT:
            raise ValueError('original TOC exceeds size bound')
        original = disc.read(old['offset'], old['size'])
        inspect_toc(original, entries, path, 'original')
        row = candidates.get(path)
        if row is not None and row['candidate_size'] > TOC_LIMIT:
            raise ValueError('candidate TOC exceeds size bound')
        raw = (packet/'candidate'/path).read_bytes() if row else original
        if row and (len(raw) != row['candidate_size'] or
                    hashlib.sha256(raw).hexdigest() != row['candidate_sha256']):
            raise ValueError('candidate TOC changed during layout')
        if {r['path'] for r in toc_rows(original)} != {r['path'] for r in toc_rows(raw)}:
            raise ValueError('TOC path set mismatch')
        inspect_toc(raw, expected, path, 'candidate')
        toc_inputs[path] = raw
    changes = []
    cursor = disc.size
    overrides = {}

    def append_change(path, size, digest):
        nonlocal cursor
        old = entries[path]
        sector = (cursor-disc.base)//SECTOR
        if not 0 <= sector <= 0xffffffff:
            raise ValueError('candidate sector exceeds XDVDFS field')
        field = offsets[path]+4
        before = struct.pack('<II', old['sector'], old['size'])
        if disc.read(field, 8) != before:
            raise ValueError('directory expected-byte mismatch')
        changes.append(dict(path=path, field_offset=field, before_hex=before.hex(),
                            after_hex=struct.pack('<II', sector, size).hex(), sector=sector,
                            offset=cursor, size=size, sha256=digest))
        cursor += ((size+SECTOR-1)//SECTOR)*SECTOR
        return changes[-1]

    for path,row in candidates.items():
        if path in toc_inputs and not legacy_layout:
            continue
        if row['candidate_sha256'] != row['original_sha256'] or row['candidate_size'] != entries[path]['size']:
            append_change(path,row['candidate_size'],row['candidate_sha256'])
    if not legacy_layout:
        target = {p:dict(row) for p,row in expected.items()}
        for row in changes:
            target[row['path']].update(sector=row['sector'],size=row['size'])
        for path,raw in toc_inputs.items():
            if not changes and raw == disc.read(entries[path]['offset'],entries[path]['size']):
                continue
            # Reserve the final TOC start before serializing its own sector.
            # No trailing allocation depends on its decimal field lengths.
            proposed = {p:dict(row) for p,row in target.items()}
            proposed[path]['sector'] = (cursor-disc.base)//SECTOR
            payload,proof = relocate_toc(raw, expected, proposed, path)
            if changes or payload != disc.read(entries[path]['offset'],entries[path]['size']):
                row = append_change(path,len(payload),hashlib.sha256(payload).hexdigest())
                target[path].update(sector=row['sector'],size=row['size'])
                overrides[path] = dict(payload=payload,proof=proof)
    return disc, manifest, inventory, changes, cursor, overrides


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
    legacy = report is not None and report.get('schema_version') == 1
    source, manifest, old_entries, changes, output_size, overrides = inputs(
        image, image_sha256, packet, packet_sha256, disc_number, legacy_layout=legacy)
    if report is not None and (report.get('kind') != KIND or report.get('schema_version') not in (1,2)
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
    actual_entries = {r['path']:r for r in new_entries}
    rows = []
    toc_rows_checked = 0
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
            if old['path'].rsplit('/', 1)[-1].casefold() == 'xbox360toc.txt':
                # This checks the on-disc table against the on-disc directory,
                # independently of the planner and manifest success flags.
                if new['size'] > TOC_LIMIT:
                    raise ValueError('image TOC exceeds size bound')
                audit = inspect_toc(after.read(new['offset'],new['size']),actual_entries,old['path'])
                toc_rows_checked += audit['rows_checked']
            rows.append(dict(path=old['path'], sha256=actual, size=new['size'], localized=bool(replacement)))
    output_hash = sha256_file(output)
    if report is not None and (report['changes'] != changes or report['output']['sha256'] != output_hash
                               or report['output']['size'] != output_size):
        raise ValueError('published image report mismatch')
    if report is not None and not legacy and report.get('toc_relocations') != [
            value['proof'] for value in overrides.values()]:
        raise ValueError('published TOC relocation report mismatch')
    if sha256_file(source.path) != image_sha256:
        raise ValueError('original image changed during verification')
    if hashlib.sha256((Path(packet)/'manifest.json').read_bytes()).hexdigest() != packet_sha256:
        raise ValueError('packet manifest changed during verification')
    return dict(status='PASS', disc=disc_number, files=len(rows), directories=len(new_entries)-len(rows),
                localized_files=len(changes), unchanged_files=len(rows)-len(changes),
                all_file_hashes_match=True, original_prefix_inverse_sha256=image_sha256,
                output_sha256=output_hash, output_size=output_size, file_inventory=rows,
                toc_rows_checked=toc_rows_checked,
                game_started=False, game_rendering_verified=False)


def build(image, image_sha256, packet, packet_sha256, disc_number, output, report_path):
    output = new_path(output, [image, Path(packet)/'manifest.json', report_path])
    report_path = new_path(report_path, [image, output, Path(packet)/'manifest.json'])
    source, manifest, inventory, changes, output_size, overrides = inputs(
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
            digest = hashlib.sha256()
            replacement = overrides.get(row['path'])
            stream = (io.BytesIO(replacement['payload']) if replacement else
                      (Path(packet)/'candidate'/row['path']).open('rb'))
            with stream:
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
    report = dict(schema_version=2, kind=KIND, disc=disc_number,
                  source=dict(path=str(source.path), size=source.size, sha256=image_sha256,
                              partition_base=source.base),
                  packet=dict(path=str(Path(packet).resolve()), manifest_sha256=packet_sha256),
                  output=dict(path=str(output), size=output_size, sha256=proof['output_sha256']),
                  changed_fields=['directory_entry.sector','directory_entry.size']+sorted({
                      'toc_entry.'+edit['field'] for value in overrides.values()
                      for edit in value['proof']['edits']}), changes=changes,
                  toc_relocations=[value['proof'] for value in overrides.values()],
                  verification=proof, game_started=False, game_rendering_verified=False)
    with report_path.open('xb') as stream:
        stream.write(encoded(report))
    if report_path.read_bytes() != encoded(report):
        raise ValueError('report reopening mismatch')
    return report


def restore(modified, report_path, report_sha256, output):
    report = load_locked(report_path, report_sha256)
    if report.get('kind') != KIND or report.get('schema_version') not in (1,2):
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
