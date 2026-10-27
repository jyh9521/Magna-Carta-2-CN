"""Hash-locked, append-only runtime-resource repair of an existing test image.

Preparation never changes the image. Application reuses the existing test copy;
only directory sector/size fields and appended resource extents change. Original
payloads remain available for an exact streaming inverse. No game is launched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

from . import build_disc_image as iso
from .disc_inventory import Disc, SECTOR, sha256_file
from .runtime_package import normalize_package
from .ue3_package import LzxDecoder
from .verify_resource_phase import relative, confined, hash_value, unique

KIND = 'incremental-runtime-image-repair'
PLAN_LIMIT = 16 * 1024 * 1024


def load_plan(path, expected):
    """Detailed native-export proofs need more room than a packet manifest."""
    path = Path(path)
    if path.stat().st_size > PLAN_LIMIT:
        raise ValueError('repair plan exceeds size bound')
    raw = path.read_bytes()
    if len(raw) > PLAN_LIMIT or hashlib.sha256(raw).hexdigest() != hash_value(expected):
        raise ValueError('repair plan SHA256 or size mismatch')
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite repair JSON')))


def identity(path, expected):
    path = Path(path)
    if (path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1
            or path.stat().st_size != expected['size']
            or sha256_file(path) != expected['sha256']):
        raise ValueError('image identity mismatch')


def write_payloads(stream, root, changes, old_size, digest=None):
    cursor = old_size
    for row in sorted(changes, key=lambda r: r['offset']):
        pad = row['offset']-cursor
        if not 0 <= pad < SECTOR:
            raise ValueError('invalid append alignment')
        if stream is not None:
            stream.write(bytes(pad))
        if digest is not None:
            digest.update(bytes(pad))
        path = confined(root, row['file'])
        with path.open('rb') as source:
            iso.transfer(source, stream, row['size'], digest)
            if source.read(1):
                raise ValueError('staged payload grew')
        cursor = row['offset']+row['size']
        pad = (-cursor) % SECTOR
        if stream is not None:
            stream.write(bytes(pad))
        if digest is not None:
            digest.update(bytes(pad))
        cursor += pad
    return cursor


def projected_hash(image, size, changes, root):
    """Compute expected full output without allocating another image."""
    h = hashlib.sha256()
    with Path(image).open('rb') as f:
        cursor = 0
        for row in sorted(changes, key=lambda r: r['field_offset']):
            pos = row['field_offset']
            if pos < cursor or pos+8 > size:
                raise ValueError('overlapping/out-of-range directory fields')
            iso.transfer(f, None, pos-cursor, h)
            if f.read(8) != bytes.fromhex(row['before_hex']):
                raise ValueError('directory expected bytes mismatch')
            h.update(bytes.fromhex(row['after_hex']))
            cursor = pos+8
        iso.transfer(f, None, size-cursor, h)
    write_payloads(None, root, changes, size, h)
    return h.hexdigest()


def prepare(image, previous_report, previous_report_sha256, output_dir, decoder):
    image = Path(image).resolve()
    previous_report = Path(previous_report).resolve()
    previous = iso.load_locked(previous_report, previous_report_sha256)
    if (previous.get('kind') != iso.KIND or previous.get('schema_version') not in (1, 2)
            or previous.get('disc') not in (1, 2)):
        raise ValueError('unsupported predecessor image report')
    if image == Path(previous['source']['path']).resolve():
        raise ValueError('repair target must not be the original image')
    identity(image, previous['output'])
    disc = Disc(image); inventory = disc.inventory()
    if disc.base != previous['source']['partition_base']:
        raise ValueError('partition identity mismatch')
    entries = {r['path']: r for r in inventory}
    offsets = iso.entry_offsets(disc, inventory)
    previous_changes = previous['changes']
    if len({r['path'] for r in previous_changes}) != len(previous_changes):
        raise ValueError('duplicate predecessor change')
    for row in previous_changes:
        entry = entries[row['path']]
        if (row['field_offset'] != offsets[row['path']]+4
                or disc.read(row['field_offset'], 8).hex() != row['after_hex']
                or entry['size'] != row['size']
                or disc.resource_hash(entry) != row['sha256']):
            raise ValueError('predecessor resource identity mismatch')
    root = Path(output_dir).absolute()
    if root.exists() or root.is_symlink() or root.parent.resolve() != root.parent:
        raise ValueError('repair output directory must be new and canonical')
    tocs = [r for r in inventory if not r['directory'] and Path(r['path']).name.casefold() == 'xbox360toc.txt']
    if len(tocs) != 1:
        raise ValueError('expected one explicit Xbox360TOC profile')
    root.mkdir()
    changes = []; proofs = []; cursor = (disc.size+SECTOR-1)//SECTOR*SECTOR
    targets = {k: dict(v) for k, v in entries.items()}

    def stage(name, payload, proof):
        nonlocal cursor
        if name.lower().endswith('.xex'):
            raise ValueError('executable edits are excluded')
        path = root/'resources'/relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f: f.write(payload)
        h = hashlib.sha256(payload).hexdigest()
        if sha256_file(path) != h:
            raise ValueError('staged resource reopening mismatch')
        sector = (cursor-disc.base)//SECTOR
        if cursor < disc.base or (cursor-disc.base) % SECTOR or sector > 0xffffffff or len(payload) > 0xffffffff:
            raise ValueError('append extent exceeds XDVDFS profile')
        field = offsets[name]+4
        changes.append(dict(path=name, file=path.relative_to(root).as_posix(),
            field_offset=field, before_hex=disc.read(field, 8).hex(),
            after_hex=struct.pack('<II', sector, len(payload)).hex(),
            offset=cursor, sector=sector, size=len(payload), sha256=h))
        targets[name].update(sector=sector, offset=cursor, size=len(payload))
        proofs.append(dict(proof, path=name))
        cursor += (len(payload)+SECTOR-1)//SECTOR*SECTOR

    for row in sorted(previous_changes, key=lambda r: r['path'].casefold()):
        if not row['path'].lower().endswith('.xxx'): continue
        entry = entries[row['path']]
        before = disc.read(entry['offset'], entry['size'])
        after, proof = normalize_package(before, row['sha256'], decoder)
        if after != before: stage(row['path'], after, proof)
    toc = tocs[0]; name = toc['path']
    raw = disc.read(toc['offset'], toc['size'])
    expected = {k: dict(v) for k, v in entries.items()}
    if previous['schema_version'] == 1:
        # Legacy packets updated sizes but retained original disc sectors.
        for row in previous_changes:
            expected[row['path']]['sector'] = struct.unpack('<II', bytes.fromhex(row['before_hex']))[0]
    targets[name]['sector'] = (cursor-disc.base)//SECTOR
    rewritten, toc_proof = iso.relocate_toc(raw, expected, targets, name)
    stage(name, rewritten, dict(kind='toc-size-and-sector-update', **toc_proof))
    file_inventory = []
    for e in inventory:
        if not e['directory']:
            file_inventory.append(dict(path=e['path'], size=e['size'], sha256=disc.resource_hash(e)))
    plan = dict(schema_version=1, kind=KIND, disc=previous['disc'],
        previous_report=dict(path=str(previous_report), sha256=previous_report_sha256),
        input=dict(path=str(image), size=disc.size, sha256=previous['output']['sha256']),
        output=dict(size=cursor, sha256=projected_hash(image, disc.size, changes, root)),
        partition_base=disc.base, changes=changes, file_inventory=file_inventory,
        resource_proofs=proofs, game_started=False, game_rendering_verified=False)
    identity(image, plan['input'])
    (root/'plan.json').write_bytes(iso.encoded(plan))
    if load_plan(root/'plan.json', sha256_file(root/'plan.json')) != plan:
        raise ValueError('plan reopening mismatch')
    return plan


def read_plan(plan_path, expected_sha256, check_payloads=False):
    path = Path(plan_path).resolve(); root = path.parent
    p = load_plan(path, expected_sha256)
    if p.get('kind') != KIND or p.get('schema_version') != 1 or p['output']['size'] <= p['input']['size']:
        raise ValueError('invalid repair plan')
    cursor = (p['input']['size']+SECTOR-1)//SECTOR*SECTOR
    names = set(); fields = []
    for r in p['changes']:
        name = relative(r['path']); source = confined(root, r['file'])
        if name.casefold() in names or name.casefold().endswith('.xex'):
            raise ValueError('duplicate/executable repair entry')
        names.add(name.casefold()); fields.append(r['field_offset'])
        if (r['offset'] != cursor or r['sector']*SECTOR+p['partition_base'] != cursor
                or r['after_hex'] != struct.pack('<II', r['sector'], r['size']).hex()
                or len(bytes.fromhex(r['before_hex'])) != 8):
            raise ValueError('invalid planned extent')
        cursor += (r['size']+SECTOR-1)//SECTOR*SECTOR
        if check_payloads and (source.is_symlink() or source.resolve() != root/relative(r['file'])
                or source.stat().st_size != r['size'] or sha256_file(source) != r['sha256']):
            raise ValueError('staged resource identity mismatch')
    ordered = sorted(fields)
    if (not fields or cursor != p['output']['size'] or ordered[0] < 0
            or ordered[-1]+8 > p['input']['size'] or any(b < a+8 for a,b in zip(ordered,ordered[1:]))):
        raise ValueError('invalid directory field set')
    return p, root


def preflight(image, plan_path, plan_sha256):
    p, root = read_plan(plan_path, plan_sha256, True)
    if Path(image).resolve() != Path(p['input']['path']).resolve():
        raise ValueError('preflight requires the prepared image')
    identity(image, p['input'])
    if projected_hash(image, p['input']['size'], p['changes'], root) != p['output']['sha256']:
        raise ValueError('projected output hash mismatch')
    return dict(status='PREPARED', changed_resources=len(p['changes']),
        plan_sha256=plan_sha256, output=p['output'], game_started=False)


def apply(image, plan_path, plan_sha256):
    p, root = read_plan(plan_path, plan_sha256, True)
    image = Path(image).resolve()
    if image != Path(p['input']['path']).resolve():
        raise ValueError('apply requires the explicitly prepared test image')
    identity(image, p['input'])
    with image.open('r+b') as f:
        for row in p['changes']:
            f.seek(row['field_offset'])
            if f.read(8).hex() != row['before_hex']:
                raise ValueError('pre-apply directory mismatch')
        try:
            f.seek(p['input']['size'])
            write_payloads(f, root, p['changes'], p['input']['size'])
            f.flush(); os.fsync(f.fileno())
            for row in p['changes']:
                f.seek(row['field_offset']); f.write(bytes.fromhex(row['after_hex']))
            f.flush(); os.fsync(f.fileno())
            identity(image, p['output'])
        except BaseException:
            for row in p['changes']:
                f.seek(row['field_offset']); f.write(bytes.fromhex(row['before_hex']))
            f.truncate(p['input']['size']); f.flush(); os.fsync(f.fileno())
            identity(image, p['input'])
            raise
    return dict(status='APPLIED', resources=len(p['changes']), sha256=p['output']['sha256'], game_started=False)


def verify(image, plan_path, plan_sha256):
    p, _ = read_plan(plan_path, plan_sha256)
    identity(image, p['output'])
    d = Disc(image); inventory = d.inventory(); entries = {r['path']:r for r in inventory}
    expected = {r['path']:r for r in p['file_inventory']}
    expected.update({r['path']:r for r in p['changes']})
    if set(expected) != {r['path'] for r in inventory if not r['directory']}:
        raise ValueError('file inventory changed')
    for name,r in expected.items():
        e = entries[name]
        if e['size'] != r['size'] or d.resource_hash(e) != r['sha256']:
            raise ValueError('output resource mismatch: '+name)
    for r in p['changes']:
        if d.read(r['field_offset'], 8).hex() != r['after_hex']:
            raise ValueError('output directory mismatch')
    toc_results = []
    for e in inventory:
        if Path(e['path']).name.casefold() == 'xbox360toc.txt':
            toc_results.append(iso.inspect_toc(d.read(e['offset'], e['size']), entries, e['path']))
    restored = iso.original_prefix(image, p['input']['size'], p['changes'])
    if restored != p['input']['sha256']:
        raise ValueError('inverse prefix hash mismatch')
    return dict(status='PASS', disc=p['disc'], files=len(expected), changed_resources=len(p['changes']),
        sha256=p['output']['sha256'], all_file_hashes_match=True, toc=toc_results,
        restored_input_sha256=restored, game_started=False, game_rendering_verified=False)


def restore(image, plan_path, plan_sha256, output):
    p, _ = read_plan(plan_path, plan_sha256)
    output = iso.new_path(output, [image, plan_path, p['input']['path']])
    identity(image, p['output'])
    if iso.original_prefix(image, p['input']['size'], p['changes']) != p['input']['sha256']:
        raise ValueError('inverse preflight mismatch')
    with output.open('xb') as f:
        got = iso.original_prefix(image, p['input']['size'], p['changes'], f)
    if got != p['input']['sha256'] or sha256_file(output) != got:
        raise ValueError('restored output mismatch')
    return dict(status='RESTORED', sha256=got, size=output.stat().st_size, restored_state='pre-repair test image')


def recover(image, plan_path, plan_sha256):
    """Recover a verified interrupted transaction, never an unknown image tail."""
    p, root = read_plan(plan_path, plan_sha256, True)
    image = Path(image).resolve()
    if image != Path(p['input']['path']).resolve() or not image.is_file() or image.stat().st_nlink != 1:
        raise ValueError('recovery requires the explicitly prepared image')
    size = image.stat().st_size
    if not p['input']['size'] <= size <= p['output']['size']:
        raise ValueError('interrupted image size outside transaction')
    observed = []
    with image.open('rb') as f:
        for r in p['changes']:
            f.seek(r['field_offset']); current = f.read(8)
            before, after = bytes.fromhex(r['before_hex']), bytes.fromhex(r['after_hex'])
            if any(c not in (a,b) for c,a,b in zip(current,before,after)):
                raise ValueError('recovery directory conflict')
            observed.append(dict(r, after_hex=current.hex()))
        f.seek(p['input']['size'])
        cursor = p['input']['size']
        for r in sorted(p['changes'], key=lambda r:r['offset']):
            if cursor >= size: break
            pad = r['offset']-cursor
            take = min(pad,size-cursor)
            if f.read(take) != bytes(take): raise ValueError('recovery padding conflict')
            cursor += take
            if cursor >= size: break
            with confined(root,r['file']).open('rb') as src:
                remaining = min(r['size'],size-cursor)
                while remaining:
                    take = min(iso.BLOCK,remaining)
                    if f.read(take) != src.read(take): raise ValueError('recovery payload conflict')
                    cursor += take; remaining -= take
            if cursor >= size: break
            pad = (-cursor)%SECTOR; take=min(pad,size-cursor)
            if f.read(take) != bytes(take): raise ValueError('recovery padding conflict')
            cursor += take
        if cursor != size: raise ValueError('recovery unexpected tail')
    if iso.original_prefix(image,p['input']['size'],observed) != p['input']['sha256']:
        raise ValueError('recovery original prefix conflict')
    with image.open('r+b') as f:
        for r in observed:
            f.seek(r['field_offset'])
            if f.read(8).hex() != r['after_hex']: raise ValueError('recovery concurrent field change')
        for r in observed:
            f.seek(r['field_offset']); f.write(bytes.fromhex(r['before_hex']))
        f.truncate(p['input']['size']); f.flush(); os.fsync(f.fileno())
    identity(image,p['input'])
    return dict(status='RECOVERED', sha256=p['input']['sha256'], restored_state='pre-repair test image')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--previous-report', type=Path, required=True)
    p.add_argument('--previous-report-sha256', required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--lzx-library', type=Path, required=True)
    for command in ('apply','verify','restore','recover','preflight'):
        p = sub.add_parser(command)
        p.add_argument('--image', type=Path, required=True)
        p.add_argument('--plan', type=Path, required=True)
        p.add_argument('--plan-sha256', required=True)
        if command == 'restore': p.add_argument('--output', type=Path, required=True)
    a = parser.parse_args(argv)
    try:
        if a.action == 'prepare':
            p = prepare(a.image, a.previous_report, a.previous_report_sha256, a.output_dir, LzxDecoder(a.lzx_library))
            result = dict(status='PREPARED', changed_resources=len(p['changes']),
                plan_sha256=sha256_file(a.output_dir/'plan.json'), output=p['output'], game_started=False)
        elif a.action == 'restore': result = restore(a.image, a.plan, a.plan_sha256, a.output)
        else: result = globals()[a.action](a.image, a.plan, a.plan_sha256)
        print(json.dumps(result, sort_keys=True)); return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print('ERROR: '+str(e)); return 2


if __name__ == '__main__': raise SystemExit(main())
