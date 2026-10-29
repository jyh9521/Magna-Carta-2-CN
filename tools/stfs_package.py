"""Strict read-only-format STFS container reader and hash-guarded rebuilder.

Supported: LIVE/PIRS, STFS v0, single backing hash tables, densely allocated
level-0/level-1 containers (at most 28,900 logical 4 KiB blocks). Resilient CON,
SVOD, free/orphan blocks, level-2 trees and non-canonical directories fail closed.
The implementation preserves the original license and RSA-signature bytes. It
recomputes content SHA-1 integrity, not the publisher's cryptographic signature.

Format cross-check: xenia-project/xenia, commit
95a5c3ee250f80c3b9d139658649d9ffb6db3eec, src/xenia/vfs/devices/stfs_xbox.h
and stfs_container_device.cc (BSD; Ben Vanik and Xenia contributors). The Python
parser and rebuilding/validation policy are independent implementations.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

BLOCK = 4096
FANOUT = 170
MAX_BLOCKS = FANOUT * FANOUT
END = 0xFFFFFF
MAX_CONTAINER_BYTES = 128 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _sha1(data):
    return hashlib.sha1(data).digest()


def _int(data, start, length, endian='big'):
    if start < 0 or length < 0 or start + length > len(data):
        raise ValueError('STFS integer outside input')
    return int.from_bytes(data[start:start + length], endian)


def _set(data, start, length, value, endian='big'):
    data[start:start + length] = value.to_bytes(length, endian)


def _identity(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('expected SHA256 must be a lowercase 64-digit digest')
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate STFS plan JSON key')
        result[key] = value
    return result


def _name(value):
    if (not value or value in {'.', '..'} or value[-1] in ' .'
            or any(ord(c) < 32 or c in '/\\:*?"<>|\x7f' for c in value)
            or value.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL'}
            or re.fullmatch(r'(COM|LPT)[0-9]', value.split('.')[0].upper())):
        raise ValueError('unsafe STFS path component')
    return value


def data_offset(block, base):
    """Map a supported logical data block to its physical file offset."""
    if type(block) is not int or not 0 <= block < MAX_BLOCKS:
        raise ValueError('STFS logical block outside supported range')
    tables = 1 + block // FANOUT + int(block >= FANOUT)
    return base + (block + tables) * BLOCK


def table_offset(group, base):
    if type(group) is not int or not 0 <= group < FANOUT:
        raise ValueError('STFS level-0 group outside supported range')
    return base + (0 if group == 0 else group * (FANOUT + 1) + 1) * BLOCK


def root_offset(total, base):
    return base if total <= FANOUT else base + (FANOUT + 1) * BLOCK


@dataclass(frozen=True)
class Entry:
    index: int
    path: str
    directory: bool
    size: int
    start_block: int
    blocks: tuple[int, ...]
    record: bytes


class StfsPackage:
    """Parse and independently validate every data, table and header digest."""

    def __init__(self, data, expected_sha256=None):
        if not isinstance(data, bytes):
            raise TypeError('STFS input must be immutable bytes')
        if not 0xB000 <= len(data) <= MAX_CONTAINER_BYTES:
            raise ValueError('STFS container size outside supported bounds')
        self.data = data
        self.sha256 = sha256(data)
        if expected_sha256 is not None and self.sha256 != _identity(expected_sha256):
            raise ValueError('STFS input SHA256 mismatch')
        if data[:4] not in (b'LIVE', b'PIRS'):
            raise ValueError('unsupported STFS magic; expected LIVE or PIRS')
        self.header_size = _int(data, 0x340, 4)
        self.base = (self.header_size + BLOCK - 1) // BLOCK * BLOCK
        if not 0x971A <= self.header_size <= 0xB000 or self.base != 0xB000:
            raise ValueError('unsupported STFS header layout')
        if _int(data, 0x348, 4) != 2 or _int(data, 0x3A9, 4) != 0:
            raise ValueError('unsupported STFS metadata version or volume type')
        if data[0x379:0x37C] != bytes((0x24, 0, 1)):
            raise ValueError('unsupported STFS volume descriptor or hash flags')
        self.table_count = _int(data, 0x37C, 2, 'little')
        self.table_start = _int(data, 0x37E, 3, 'little')
        self.total_blocks = _int(data, 0x395, 4)
        if not 1 <= self.total_blocks <= MAX_BLOCKS:
            raise ValueError('unsupported STFS block count')
        if _int(data, 0x399, 4) != 0:
            raise ValueError('free STFS blocks are not supported')
        if not 1 <= self.table_count <= 64 or self.table_count > self.total_blocks:
            raise ValueError('STFS file table count outside supported bounds')
        expected_size = data_offset(self.total_blocks - 1, self.base) + BLOCK
        if len(data) != expected_size or _int(data, 0x34C, 8) != len(data) - self.base:
            raise ValueError('STFS content size or final block mismatch')
        self.integrity = self._verify_hashes()
        self.table_blocks = self._chain(self.table_start, self.table_count)
        self.entries = self._read_entries()
        self.by_path = {e.path: e for e in self.entries}

    @classmethod
    def from_path(cls, path, expected_sha256=None):
        path = Path(path)
        if not path.is_file() or path.stat().st_size > MAX_CONTAINER_BYTES:
            raise ValueError('STFS input path or size')
        return cls(path.read_bytes(), expected_sha256)

    def _entry_offset(self, block):
        if type(block) is not int or not 0 <= block < self.total_blocks:
            raise ValueError('STFS block pointer outside allocation')
        return table_offset(block // FANOUT, self.base) + (block % FANOUT) * 24

    def _verify_hashes(self):
        data = self.data
        if data[0x32C:0x340] != _sha1(data[0x344:self.base]):
            raise ValueError('STFS header SHA1 mismatch')
        for n in range(self.total_blocks):
            h = self._entry_offset(n)
            offset = data_offset(n, self.base)
            if data[h:h + 20] != _sha1(data[offset:offset + BLOCK]):
                raise ValueError(f'STFS data SHA1 mismatch: block {n}')
            if data[h + 20] != 0x80:
                raise ValueError(f'STFS data allocation flags unsupported: block {n}')
        groups = (self.total_blocks + FANOUT - 1) // FANOUT
        for g in range(groups):
            off = table_offset(g, self.base)
            used = min(FANOUT, self.total_blocks - g * FANOUT)
            if any(data[off + used * 24:off + BLOCK]):
                raise ValueError('nonzero unused STFS level-0 table bytes')
        root = root_offset(self.total_blocks, self.base)
        if groups > 1:
            for g in range(groups):
                off = table_offset(g, self.base)
                h = root + 24 * g
                if data[h:h + 20] != _sha1(data[off:off + BLOCK]):
                    raise ValueError(f'STFS level-1 SHA1 mismatch: group {g}')
                if any(data[h + 20:h + 24]):
                    raise ValueError('unsupported STFS level-1 flags')
            if (any(data[root + groups * 24:root + 4080])
                    or _int(data, root + 4080, 4) != self.total_blocks
                    or any(data[root + 4084:root + BLOCK])):
                raise ValueError('STFS root table count or padding mismatch')
        if data[0x381:0x395] != _sha1(data[root:root + BLOCK]):
            raise ValueError('STFS root SHA1 mismatch')
        return dict(data_hashes=self.total_blocks, level0_tables=groups,
                    level1_tables=int(groups > 1), root_hash=True, header_hash=True,
                    publisher_signature='preserved-not-verified')

    def _chain(self, start, count):
        seen = set()
        result = []
        n = start
        for _ in range(count):
            if n == END or n in seen:
                raise ValueError('STFS chain terminated early or contains cycle')
            h = self._entry_offset(n)
            seen.add(n)
            result.append(n)
            n = _int(self.data, h + 21, 3)
        if n != END:
            raise ValueError('STFS chain exceeds declared allocation')
        return tuple(result)

    def _read_entries(self):
        raw = b''.join(self.data[data_offset(n, self.base):data_offset(n, self.base) + BLOCK]
                       for n in self.table_blocks)
        entries = []
        paths = set()
        owned = set(self.table_blocks)
        for i in range(len(raw) // 64):
            record = raw[i * 64:(i + 1) * 64]
            if not record[0]:
                if any(raw[i * 64:]):
                    raise ValueError('sparse or nonzero trailing STFS directory records')
                break
            flags = record[40]
            namelen = flags & 63
            if not 1 <= namelen <= 40 or any(record[namelen:40]):
                raise ValueError('STFS filename length or padding')
            name = _name(record[:namelen].decode('utf-8', errors='strict'))
            parent = _int(record, 50, 2)
            if parent == 0xFFFF:
                path = name
            else:
                if parent >= len(entries) or not entries[parent].directory:
                    raise ValueError('STFS parent must be an earlier directory')
                path = entries[parent].path + '/' + name
            if path.casefold() in paths:
                raise ValueError('duplicate case-insensitive STFS path')
            paths.add(path.casefold())
            valid = _int(record, 41, 3, 'little')
            allocated = _int(record, 44, 3, 'little')
            start = _int(record, 47, 3, 'little')
            size = _int(record, 52, 4)
            directory = bool(flags & 128)
            if directory:
                if size or valid or allocated or start not in (0, END):
                    raise ValueError('STFS directory has data allocation')
                blocks = ()
            else:
                count = (size + BLOCK - 1) // BLOCK
                if valid != count or allocated != count:
                    raise ValueError('STFS member length/allocation mismatch')
                if not count:
                    if start not in (0, END):
                        raise ValueError('STFS empty member start pointer')
                    blocks = ()
                else:
                    blocks = self._chain(start, count)
                    if flags & 64 and blocks != tuple(range(start, start + count)):
                        raise ValueError('STFS contiguous flag contradicts chain')
                if owned.intersection(blocks):
                    raise ValueError('STFS data block belongs to multiple members')
                owned.update(blocks)
            entries.append(Entry(i, path, directory, size, start, blocks, record))
        if not entries or (len(entries) + 63) // 64 != self.table_count:
            raise ValueError('empty or overallocated STFS directory')
        if owned != set(range(self.total_blocks)):
            raise ValueError('orphan STFS logical blocks')
        return entries

    def read_member(self, path):
        entry = self.by_path[path]
        if entry.directory:
            raise ValueError('requested STFS member is a directory')
        return b''.join(self.data[data_offset(n, self.base):data_offset(n, self.base) + BLOCK]
                        for n in entry.blocks)[:entry.size]

    def metadata(self):
        result = {}
        for kind, start in (('display_name', 0x411), ('description', 0xD11)):
            for i in range(9):
                raw = self.data[start + 256 * i:start + 256 * (i + 1)]
                result[f'{kind}:{i}'] = raw.decode('utf-16-be').split('\0')[0]
        for kind, start in (('publisher', 0x1611), ('title_name', 0x1691)):
            result[kind] = self.data[start:start + 128].decode('utf-16-be').split('\0')[0]
        return result

    def inventory(self):
        return dict(schema_version=1, kind='stfs-inventory', sha256=self.sha256,
                    size=len(self.data), magic=self.data[:4].decode(),
                    title_id=f'{_int(self.data, 0x360, 4):08X}',
                    content_type=f'{_int(self.data, 0x344, 4):08X}',
                    header_size=self.header_size, data_start=self.base,
                    total_blocks=self.total_blocks, integrity=self.integrity,
                    metadata=self.metadata(), entries=[dict(index=e.index, path=e.path,
                        directory=e.directory, size=e.size, start_block=e.start_block,
                        block_count=len(e.blocks), sha256=None if e.directory else sha256(self.read_member(e.path)))
                        for e in self.entries])

    def extract(self, output):
        output = _new_output_directory(output)
        output.mkdir(parents=True)
        for e in self.entries:
            path = output.joinpath(*e.path.split('/'))
            if e.directory:
                path.mkdir()
            else:
                with path.open('xb') as f:
                    f.write(self.read_member(e.path))
                if path.read_bytes() != self.read_member(e.path):
                    raise ValueError('STFS extraction readback mismatch')
        return self.inventory()

    def rebuild(self, replacements, *, expected_sha256, metadata_updates=None):
        """Return rebuilt immutable bytes; preserve unrelated members and header.

        Replacements use exact existing case-sensitive member paths. Metadata
        updates allow only explicit display-name/description slots 0..8 or the
        title-name slot. Publisher, IDs, license descriptors, thumbnail art and
        RSA signature bytes are immutable. A fresh parse verifies every digest.
        """
        if self.sha256 != _identity(expected_sha256):
            raise ValueError('STFS rebuild input SHA256 mismatch')
        if (not isinstance(replacements, dict)
                or metadata_updates is not None and not isinstance(metadata_updates, dict)):
            raise ValueError('STFS edits must be mappings')
        metadata_updates = metadata_updates or {}
        for path, value in replacements.items():
            if path not in self.by_path or self.by_path[path].directory:
                raise ValueError('STFS replacement is not an existing file')
            if not isinstance(value, bytes) or len(value) > MAX_CONTAINER_BYTES:
                raise ValueError('STFS replacement must be bounded immutable bytes')
        changed = {p: v for p, v in replacements.items() if v != self.read_member(p)}
        if not changed and not metadata_updates:
            return self.data, dict(before_sha256=self.sha256, sha256=self.sha256,
                                   member_changes=[], metadata_changes=[], no_op=True)
        members = {e.path: replacements.get(e.path, self.read_member(e.path))
                   for e in self.entries if not e.directory}
        counts = {p: (len(v) + BLOCK - 1) // BLOCK for p, v in members.items()}
        total = self.table_count + sum(counts.values())
        if not 1 <= total <= MAX_BLOCKS:
            raise ValueError('rebuilt STFS block count outside supported range')
        same_lengths = all(len(value) == self.by_path[path].size for path, value in changed.items())
        if same_lengths:
            # Metadata and equal-size edits retain directory records, original
            # block order and all padding outside the actual replacement bytes.
            out = bytearray(self.data)
            for path, value in changed.items():
                for j, n in enumerate(self.by_path[path].blocks):
                    chunk = value[j * BLOCK:(j + 1) * BLOCK]
                    pos = data_offset(n, self.base)
                    out[pos:pos + len(chunk)] = chunk
        else:
            out = bytearray(data_offset(total - 1, self.base) + BLOCK)
            out[:self.base] = self.data[:self.base]
            directory = bytearray(self.table_count * BLOCK)
            chains = [tuple(range(self.table_count))]
            cursor = self.table_count
            for e in self.entries:
                record = bytearray(e.record)
                if not e.directory:
                    count = counts[e.path]
                    _set(record, 41, 3, count, 'little')
                    _set(record, 44, 3, count, 'little')
                    _set(record, 47, 3, cursor if count else END, 'little')
                    _set(record, 52, 4, len(members[e.path]))
                    # Preserve original contiguous flag; the new chain satisfies it.
                    chain = tuple(range(cursor, cursor + count))
                    chains.append(chain)
                    for j, n in enumerate(chain):
                        chunk = members[e.path][j * BLOCK:(j + 1) * BLOCK]
                        pos = data_offset(n, self.base)
                        out[pos:pos + len(chunk)] = chunk
                    cursor += count
                directory[e.index * 64:(e.index + 1) * 64] = record
            for j in range(self.table_count):
                pos = data_offset(j, self.base)
                out[pos:pos + BLOCK] = directory[j * BLOCK:(j + 1) * BLOCK]
            for chain in chains:
                for j, n in enumerate(chain):
                    h = table_offset(n // FANOUT, self.base) + (n % FANOUT) * 24
                    out[h + 20] = 0x80
                    _set(out, h + 21, 3, chain[j + 1] if j + 1 < len(chain) else END)
            _set(out, 0x37E, 3, 0, 'little')
        for n in range(total):
            pos = data_offset(n, self.base)
            h = table_offset(n // FANOUT, self.base) + (n % FANOUT) * 24
            out[h:h + 20] = _sha1(out[pos:pos + BLOCK])
        groups = (total + FANOUT - 1) // FANOUT
        root = root_offset(total, self.base)
        if groups > 1:
            for g in range(groups):
                pos = table_offset(g, self.base)
                out[root + 24 * g:root + 24 * g + 20] = _sha1(out[pos:pos + BLOCK])
            _set(out, root + 4080, 4, total)
        _set(out, 0x395, 4, total)
        _set(out, 0x34C, 8, len(out) - self.base)
        out[0x381:0x395] = _sha1(out[root:root + BLOCK])
        metadata_changes = []
        current = self.metadata()
        for key, text in metadata_updates.items():
            if key == 'title_name':
                offset, size = 0x1691, 128
            else:
                match = re.fullmatch(r'(display_name|description):([0-8])', key) if isinstance(key, str) else None
                if not match:
                    raise ValueError('unsupported STFS metadata update key')
                offset = (0x411 if match[1] == 'display_name' else 0xD11) + 256 * int(match[2])
                size = 256
            if not isinstance(text, str) or '\0' in text:
                raise ValueError('STFS metadata update must be NUL-free text')
            encoded = text.encode('utf-16-be') + b'\0\0'
            if len(encoded) > size:
                raise ValueError('STFS metadata update exceeds fixed field')
            out[offset:offset + size] = encoded.ljust(size, b'\0')
            metadata_changes.append(dict(field=key, before=current[key], after=text))
        out[0x32C:0x340] = _sha1(out[0x344:self.base])
        result = bytes(out)
        parsed = StfsPackage(result)
        if [(e.path, e.directory) for e in parsed.entries] != [(e.path, e.directory) for e in self.entries]:
            raise ValueError('STFS rebuilt directory identity changed')
        for path, value in members.items():
            if parsed.read_member(path) != value:
                raise ValueError('STFS member rebuild readback mismatch')
        if result[:0x32C] != self.data[:0x32C]:
            raise ValueError('STFS license/signature preservation failure')
        report = dict(before_sha256=self.sha256, sha256=parsed.sha256,
                      before_size=len(self.data), size=len(result), integrity=parsed.integrity,
                      member_changes=[dict(path=p, before_size=len(self.read_member(p)), size=len(v),
                          before_sha256=sha256(self.read_member(p)), sha256=sha256(v)) for p, v in changed.items()],
                      metadata_changes=metadata_changes,
                      unchanged_member_count=len(members) - len(changed),
                      signature_bytes_preserved=True,
                      publisher_signature='original-signature-not-valid-for-modified-content')
        return result, report


def _new_output_directory(path):
    path = Path(path).absolute()
    if (path.exists() or path.is_symlink() or getattr(path, 'is_junction', lambda: False)()
            or path.resolve() != path):
        raise ValueError('output must be a new canonical directory')
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for action in ('inspect', 'extract', 'rebuild'):
        p = sub.add_parser(action)
        p.add_argument('input', type=Path)
        p.add_argument('--sha256', required=True)
        p.add_argument('--report', type=Path, required=True)
        if action != 'inspect':
            p.add_argument('--output', type=Path, required=True)
        if action == 'rebuild':
            p.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args(argv)
    package = StfsPackage.from_path(args.input, args.sha256)
    report_path = args.report.absolute()
    if (report_path.exists() or report_path.is_symlink()
            or getattr(report_path, 'is_junction', lambda: False)()
            or report_path.resolve() != report_path):
        raise ValueError('report output must be a new canonical file')
    if args.command == 'inspect':
        report = package.inventory()
    elif args.command == 'extract':
        report = package.extract(args.output)
    else:
        plan = json.loads(args.plan.read_text(encoding='utf-8'), object_pairs_hook=_unique)
        if (not isinstance(plan, dict)
                or set(plan) != {'schema_version', 'kind', 'members', 'metadata'}
                or type(plan['schema_version']) is not int or plan['schema_version'] != 1
                or plan['kind'] != 'stfs-rebuild'
                or not isinstance(plan['members'], list) or len(plan['members']) > 4096
                or not isinstance(plan['metadata'], dict)):
            raise ValueError('STFS rebuild plan schema')
        replacements = {}
        for row in plan['members']:
            if set(row) != {'path', 'file', 'before_sha256', 'sha256'} or row['path'] in replacements:
                raise ValueError('STFS replacement schema or duplicate member')
            if sha256(package.read_member(row['path'])) != _identity(row['before_sha256']):
                raise ValueError('STFS original member SHA256 mismatch')
            replacement = Path(row['file'])
            if not replacement.is_file() or replacement.stat().st_size > MAX_CONTAINER_BYTES:
                raise ValueError('STFS replacement path or size')
            value = replacement.read_bytes()
            if sha256(value) != _identity(row['sha256']):
                raise ValueError('STFS replacement SHA256 mismatch')
            replacements[row['path']] = value
        output = args.output.absolute()
        if (output.exists() or output.is_symlink()
                or getattr(output, 'is_junction', lambda: False)()
                or output.resolve() != output or output == report_path):
            raise ValueError('STFS output must be a new canonical file')
        result, report = package.rebuild(replacements, expected_sha256=args.sha256, metadata_updates=plan['metadata'])
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as f:
            f.write(result)
        if output.read_bytes() != result:
            raise ValueError('STFS output readback mismatch')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(dict(command=args.command, sha256=report.get('sha256'),
                         entries=len(package.entries), status='PASS'), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
