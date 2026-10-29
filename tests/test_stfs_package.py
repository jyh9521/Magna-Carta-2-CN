import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.stfs_package import (StfsPackage, BLOCK, END, MAX_BLOCKS, data_offset,
                                table_offset, root_offset, sha256, main)


BASE = 0xB000


def put(data, offset, size, value, endian='big'):
    data[offset:offset + size] = value.to_bytes(size, endian)


def offsets(count):
    """Independent sequential physical placement, not reader formulas."""
    physical = BASE
    data = []
    groups = []
    root = None
    for logical in range(count):
        if logical == 170:
            root = physical
            physical += BLOCK
        if logical % 170 == 0:
            groups.append(physical)
            physical += BLOCK
        data.append(physical)
        physical += BLOCK
    return data, groups, groups[0] if root is None else root, physical


def seal(data, total):
    locations, groups, root, _ = offsets(total)
    for n, loc in enumerate(locations):
        h = groups[n // 170] + n % 170 * 24
        data[h:h + 20] = hashlib.sha1(data[loc:loc + BLOCK]).digest()
    if total > 170:
        for n, loc in enumerate(groups):
            data[root + n * 24:root + n * 24 + 20] = hashlib.sha1(data[loc:loc + BLOCK]).digest()
        put(data, root + 4080, 4, total)
    data[0x381:0x395] = hashlib.sha1(data[root:root + BLOCK]).digest()
    data[0x32C:0x340] = hashlib.sha1(data[0x344:BASE]).digest()
    return bytes(data)


def fixture(members=None, directory=False):
    if members is None:
        members = [('a.txt', b'original'), ('b.bin', b'untouched')]
    entries = len(members) + int(directory)
    tables = (entries + 63) // 64
    total = tables + sum((len(v) + BLOCK - 1) // BLOCK for _, v in members)
    locations, hashes, _, size = offsets(total)
    data = bytearray(size)
    data[:4] = b'LIVE'
    data[4:0x32C] = bytes((n % 251 for n in range(0x328)))
    put(data, 0x340, 4, 0xAD0E)
    put(data, 0x344, 4, 2)
    put(data, 0x348, 4, 2)
    put(data, 0x34C, 8, size - BASE)
    put(data, 0x360, 4, 0x12345678)
    data[0x379:0x37C] = bytes((0x24, 0, 1))
    put(data, 0x37C, 2, tables, 'little')
    put(data, 0x395, 4, total)
    records = bytearray(tables * BLOCK)
    if directory:
        records[:3] = b'dir'
        records[40] = 0x83
        put(records, 50, 2, 0xFFFF)
    cursor = tables
    chains = [list(range(tables))]
    for i, (name, value) in enumerate(members, start=int(directory)):
        record = memoryview(records)[i * 64:(i + 1) * 64]
        encoded = name.encode('utf-8')
        record[:len(encoded)] = encoded
        record[40] = len(encoded) | 64
        count = (len(value) + BLOCK - 1) // BLOCK
        put(record, 41, 3, count, 'little')
        put(record, 44, 3, count, 'little')
        put(record, 47, 3, cursor if count else END, 'little')
        put(record, 50, 2, 0 if directory else 0xFFFF)
        put(record, 52, 4, len(value))
        chain = list(range(cursor, cursor + count))
        chains.append(chain)
        for j, block in enumerate(chain):
            chunk = value[j * BLOCK:(j + 1) * BLOCK]
            data[locations[block]:locations[block] + len(chunk)] = chunk
        cursor += count
    for i in range(tables):
        data[locations[i]:locations[i] + BLOCK] = records[i * BLOCK:(i + 1) * BLOCK]
    for chain in chains:
        for i, block in enumerate(chain):
            h = hashes[block // 170] + (block % 170) * 24
            data[h + 20] = 0x80
            put(data, h + 21, 3, chain[i + 1] if i + 1 < len(chain) else END)
    return seal(data, total)


class StfsPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def test_inventory_all_hashes_and_noop_identity(self):
        data = fixture()
        package = StfsPackage(data, sha256(data))
        self.assertEqual(package.read_member('a.txt'), b'original')
        self.assertEqual(package.inventory()['title_id'], '12345678')
        self.assertEqual(package.integrity['data_hashes'], 3)
        rebuilt, report = package.rebuild({}, expected_sha256=sha256(data))
        self.assertEqual(rebuilt, data)
        self.assertTrue(report['no_op'])

    def test_metadata_only_preserves_entire_payload_and_signature(self):
        data = fixture()
        package = StfsPackage(data)
        out, report = package.rebuild({}, expected_sha256=package.sha256,
            metadata_updates={'display_name:6': '短剧包', 'description:6': '共三集', 'title_name': '游戏'})
        self.assertEqual(data[BASE:], out[BASE:])
        self.assertEqual(data[:0x32C], out[:0x32C])
        self.assertEqual(StfsPackage(out).metadata()['display_name:6'], '短剧包')
        self.assertEqual(report['member_changes'], [])

    def test_equal_size_preserves_padding_and_untouched_members(self):
        data = bytearray(fixture())
        locs, _, _, _ = offsets(3)
        data[locs[1] + 8:locs[1] + BLOCK] = b'Z' * (BLOCK - 8)
        data = seal(data, 3)
        package = StfsPackage(data)
        out, report = package.rebuild({'a.txt': b'changed!'}, expected_sha256=package.sha256)
        self.assertEqual(StfsPackage(out).read_member('a.txt'), b'changed!')
        self.assertEqual(StfsPackage(out).read_member('b.bin'), b'untouched')
        self.assertEqual(out[locs[1] + 8:locs[1] + BLOCK], b'Z' * (BLOCK - 8))
        self.assertEqual(report['unchanged_member_count'], 1)

    def test_growth_shrink_and_hash_level_transitions(self):
        data = fixture()
        package = StfsPackage(data)
        grown, report = package.rebuild({'a.txt': b'A' * (171 * BLOCK + 3)}, expected_sha256=package.sha256)
        after = StfsPackage(grown)
        self.assertEqual(after.read_member('a.txt'), b'A' * (171 * BLOCK + 3))
        self.assertEqual(after.read_member('b.bin'), b'untouched')
        self.assertEqual(after.integrity['level1_tables'], 1)
        shrunk, _ = after.rebuild({'a.txt': b'x'}, expected_sha256=after.sha256)
        self.assertEqual(StfsPackage(shrunk).integrity['level1_tables'], 0)
        self.assertEqual(StfsPackage(shrunk).read_member('a.txt'), b'x')
        self.assertEqual(report['publisher_signature'], 'original-signature-not-valid-for-modified-content')

    def test_block_layout_boundary_matches_sequential_model(self):
        for count in (1, 2, 169, 170, 171, 172, 339, 340, 341, 28900):
            expected, groups, root, size = offsets(count)
            self.assertEqual([data_offset(i, BASE) for i in range(count)], expected)
            self.assertEqual([table_offset(i, BASE) for i in range(len(groups))], groups)
            self.assertEqual(root_offset(count, BASE), root)
        for n in (-1, MAX_BLOCKS, True):
            with self.assertRaises(ValueError):
                data_offset(n, BASE)

    def test_exact_170_boundary_and_multiple_directory_blocks(self):
        data = fixture([('large', b'A' * (169 * BLOCK))])
        self.assertEqual(StfsPackage(data).total_blocks, 170)
        data = fixture([(f'f{i}', b'v') for i in range(65)])
        package = StfsPackage(data)
        self.assertEqual(package.table_count, 2)
        self.assertEqual(len(package.entries), 65)
        out, _ = package.rebuild({'f64': b'longer'}, expected_sha256=package.sha256)
        self.assertEqual(StfsPackage(out).read_member('f64'), b'longer')

    def test_directories_empty_file_and_extract_readback(self):
        package = StfsPackage(fixture([('empty', b''), ('a', b'content')], directory=True))
        package.extract(self.root / 'extract')
        self.assertEqual((self.root / 'extract/dir/a').read_bytes(), b'content')
        self.assertEqual((self.root / 'extract/dir/empty').read_bytes(), b'')
        with self.assertRaisesRegex(ValueError, 'new canonical'):
            package.extract(self.root / 'extract')
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaisesRegex(ValueError, 'new canonical'):
                package.extract(self.root / 'redirect')

    def test_input_hash_format_size_and_unsupported_format_guards(self):
        data = fixture()
        for expected in ('0' * 64, 'x', None):
            if expected is not None:
                with self.assertRaises(ValueError):
                    StfsPackage(data, expected)
        for offset, value in ((0, b'CON '), (0x37B, b'\0'), (0x348, b'\0\0\0\1'), (0x3A9, b'\0\0\0\1')):
            bad = bytearray(data)
            bad[offset:offset + len(value)] = value
            with self.assertRaises(ValueError):
                StfsPackage(bytes(bad))
        with self.assertRaises(ValueError):
            StfsPackage(data[:-1])

    def test_hash_mismatch_each_layer(self):
        data = fixture([('large', b'A' * 171 * BLOCK)])
        locs, groups, root, _ = offsets(172)
        for where, message in ((0x420, 'header'), (locs[1], 'data'), (groups[0], 'data'), (root, 'level-1')):
            bad = bytearray(data)
            bad[where] ^= 1
            with self.subTest(where=where), self.assertRaisesRegex(ValueError, message):
                StfsPackage(bytes(bad))
        bad = bytearray(data)
        bad[0x381] ^= 1
        bad[0x32C:0x340] = hashlib.sha1(bad[0x344:BASE]).digest()
        with self.assertRaisesRegex(ValueError, 'root SHA1'):
            StfsPackage(bytes(bad))

    def test_chain_cycle_out_of_range_and_ownership(self):
        original = fixture()
        for block, dest, message in ((1, 1, 'chain exceeds'), (1, 50, 'chain exceeds'), (0, 0, 'chain exceeds')):
            bad = bytearray(original)
            put(bad, BASE + block * 24 + 21, 3, dest)
            with self.assertRaisesRegex(ValueError, message):
                StfsPackage(seal(bad, 3))
        bad = bytearray(original)
        put(bad, BASE + BLOCK + 64 + 47, 3, 1, 'little')
        with self.assertRaisesRegex(ValueError, 'multiple members'):
            StfsPackage(seal(bad, 3))

    def test_directory_path_parent_duplicate_and_gap_guards(self):
        for name in ('../x', 'CON', 'a:b', 'x\\y', 'bad.', '/x'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                StfsPackage(fixture([(name, b'x')]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            StfsPackage(fixture([('A', b'x'), ('a', b'y')]))
        bad = bytearray(fixture())
        put(bad, BASE + BLOCK + 50, 2, 0)
        with self.assertRaisesRegex(ValueError, 'earlier directory'):
            StfsPackage(seal(bad, 3))
        bad = bytearray(fixture())
        bad[BASE + BLOCK] = 0
        with self.assertRaisesRegex(ValueError, 'sparse'):
            StfsPackage(seal(bad, 3))

    def test_rebuild_bad_hash_unknown_member_metadata_bound(self):
        package = StfsPackage(fixture())
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            package.rebuild({}, expected_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'existing file'):
            package.rebuild({'nope': b'x'}, expected_sha256=package.sha256)
        for updates in ({'publisher': 'x'}, {'display_name:9': 'x'}, {'display_name:0': '字' * 128}, {'title_name': 'a\0b'}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                package.rebuild({}, expected_sha256=package.sha256, metadata_updates=updates)

    def test_cli_rebuild_reopen_and_refuse_overwrite(self):
        source = self.root / 'input.live'
        data = fixture()
        source.write_bytes(data)
        replacement = self.root / 'replacement.txt'
        replacement.write_bytes(b'replaced')
        plan = dict(schema_version=1, kind='stfs-rebuild', members=[dict(path='a.txt', file=str(replacement),
                    before_sha256=sha256(b'original'), sha256=sha256(b'replaced'))], metadata={})
        plan_path = self.root / 'plan.json'
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        args = ['rebuild', str(source), '--sha256', sha256(data), '--plan', str(plan_path),
                '--output', str(self.root / 'modified.live'), '--report', str(self.root / 'report.json')]
        self.assertEqual(main(args), 0)
        self.assertEqual(StfsPackage.from_path(self.root / 'modified.live').read_member('a.txt'), b'replaced')
        self.assertEqual(source.read_bytes(), data)
        with self.assertRaises(ValueError):
            main(args)


if __name__ == '__main__':
    unittest.main()
