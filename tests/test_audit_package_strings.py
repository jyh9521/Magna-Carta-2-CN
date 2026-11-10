"""Self-authored synthetic package and text fixtures only."""
import copy
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

from tools.audit_package_strings import additional_candidates, census, digest, fstring_candidates, script_ranges
from tools.ue3_package import parse_summary
from test_ue3_package import fixture


RANGES = {'sample': [[0xac00, 0xd7a3]]}


def wide(text):
    payload = (text + '\0').encode('utf-16-le')
    return struct.pack('>i', -len(payload) // 2) + payload


class PackageStringScreenTests(unittest.TestCase):
    def test_odd_overlapping_fstring_start_and_exact_owner(self):
        value = wide('가나다')
        data = b'\xff' + value + b'END'
        owner = dict(serial_offset=1, serial_size=len(value), path='Demo', class_path='Example')
        rows = fstring_candidates(data, RANGES, [owner])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['text'], '가나다')
        self.assertEqual(rows[0]['logical_offset'], 1)
        self.assertEqual(rows[0]['owner']['export'], 1)
        self.assertFalse(rows[0]['property_type_verified'])
        self.assertFalse(rows[0]['runtime_display_observed'])
        owner['serial_size'] -= 1
        self.assertIsNone(fstring_candidates(data, RANGES, [owner])[0]['owner'])
        owner['serial_size'] += 1
        self.assertIsNone(fstring_candidates(data, RANGES, [owner, dict(owner)])[0]['owner'])

    def test_bad_count_termination_controls_and_surrogate_fail(self):
        for data in (wide('가')[:-1], wide('가')[:-2] + b'xx', wide('가\0나'),
                     wide('가\x01'), struct.pack('>i', -3) + b'\x00\xd8\x00\xac\0\0'):
            self.assertEqual(fstring_candidates(data, RANGES), [])
        self.assertEqual(fstring_candidates(wide('example'), RANGES), [])

    def test_utf8_and_vm_candidates_keep_encoding_and_uncertainty(self):
        text = '가나'
        payload = text.encode() + b'\0'
        utf8 = struct.pack('>i', len(payload)) + payload
        data = utf8 + b'\x34' + (text + '\0').encode('utf-16-be')
        owner = dict(serial_offset=0, serial_size=len(data), path='Demo', class_path='Core.Function')
        rows = additional_candidates(data, RANGES, [owner])
        self.assertTrue(any(r['text'] == text and r['encoding'] == 'utf-8' for r in rows))
        vm = next(r for r in rows if r['kind'] == 'vm-unicode-token-candidate' and r['text'] == text)
        self.assertFalse(vm['instruction_boundary_verified'])
        # This API intentionally scans UTF-8/VM within exports only. The census
        # report must retain this explicit coverage limit instead of implying
        # that package-header names were screened in the same way.
        self.assertEqual(additional_candidates(data, RANGES, []), [])

    def setup_inputs(self, root, second=None):
        first = fixture()
        second = first if second is None else second
        recipe = dict(discs=[])
        inventories = {}
        actual = {}
        for number, raw in enumerate((first, second), 1):
            path = root / f'disc{number}.bin'
            path.write_bytes(raw)
            row = dict(path='Cooked/example.xxx', offset=0, size=len(raw), sha256=digest(raw), directory=False)
            actual[str(path)] = copy.deepcopy(row)
            inventories[number] = dict(image_size=len(raw), sha256=digest(raw), entries=[row])
            recipe['discs'].append(dict(iso=str(path), sha256=digest(raw), resources=[]))
        def factory(path):
            return SimpleNamespace(inventory=lambda: [actual[str(path)]],
                                   read=lambda at, size: path.read_bytes()[at:at + size])
        return recipe, inventories, factory

    def test_full_membership_and_hash_only_deduplication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            recipe, inventories, factory = self.setup_inputs(root)
            result = census(recipe, inventories, root, None, RANGES, disc_factory=factory)
            self.assertEqual(result['summary']['package_memberships'], 2)
            self.assertEqual(result['summary']['unique_packages'], 1)
            self.assertEqual(result['summary']['screened_unique'], 1)
            self.assertFalse(result['complete_language_coverage_claimed'])
            self.assertEqual(result['game_resources_written'], 0)
            self.assertIn('UTF-8 FStrings outside export serial ranges (including package name tables)',
                          result['coverage_exclusions'])

    def test_unsupported_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            recipe, inventories, factory = self.setup_inputs(root, b'NOT A PACKAGE')
            result = census(recipe, inventories, root, None, RANGES, disc_factory=factory)
            self.assertEqual(result['summary']['unique_packages'], 2)
            self.assertEqual(result['summary']['unknown_unique'], 1)
            self.assertEqual(result['unique_packages'][1]['status'], 'unknown')

    def test_current_override_is_scanned_and_hash_locked_separately(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            recipe, inventories, factory = self.setup_inputs(root)
            original = fixture()
            payload = wide('가나')
            changed = bytearray(original[:-4] + payload)
            summary = parse_summary(original, len(original))
            struct.pack_into('>I', changed, summary['export_offset'] + 32, len(payload))
            current = root / 'current.xxx'
            current.write_bytes(changed)
            recipe['discs'][0]['resources'] = [dict(path='Cooked/example.xxx', file=str(current),
                                                   sha256=digest(changed))]
            result = census(recipe, inventories, root, None, RANGES, disc_factory=factory)
            self.assertEqual(result['summary']['unique_packages'], 2)
            self.assertEqual(result['summary']['candidate_fields'], 1)
            self.assertEqual(result['unique_packages'][0]['candidates'][0]['text'], '가나')
            self.assertEqual(current.read_bytes(), changed)
            current.write_bytes(original)
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                census(recipe, inventories, root, None, RANGES, disc_factory=factory)

    def test_actual_resource_hash_and_directory_guard(self):
        for variant in ('resource', 'directory', 'image'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                recipe, inventories, factory = self.setup_inputs(root)
                if variant == 'resource':
                    inventories[1]['entries'][0]['sha256'] = '0' * 64
                if variant == 'directory':
                    inventories[1]['entries'][0]['offset'] = 1
                if variant == 'image':
                    recipe['discs'][0]['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    census(recipe, inventories, root, None, RANGES, disc_factory=factory)

    def test_policy_requires_bounded_valid_ranges(self):
        self.assertEqual(script_ranges(dict(script_ranges=RANGES)), RANGES)
        for value in (None, {}, {'x': [[1, 0]]}, {'x': [[False, 2]]}):
            with self.assertRaises(ValueError):
                script_ranges(dict(script_ranges=value))
