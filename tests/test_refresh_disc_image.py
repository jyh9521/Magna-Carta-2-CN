"""Incremental follow-up of an already normalized image, using authored fixtures."""
import copy
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_build_disc_image import Fixture, legacy_image, sha
from test_runtime_package import fixture
from test_supplement_font import stored_decoder
from tools import repair_disc_image as repair
from tools import build_disc_image as iso
from tools.disc_inventory import Disc, SECTOR, sha256_file


def add_movie_member(f):
    """Add an opaque authored BIK-named member; no movie decoder is involved."""
    name = 'MC2Game/Movies/intro.bik'
    movie = b'BIKi'+bytes(range(64))
    data = bytearray(f.image.read_bytes())
    # Link the extra Movies directory after the existing TOC directory record.
    struct.pack_into('<H', data, 37*SECTOR+32+2, 96//4)
    def record(table, offset, basename, sector, size, flags):
        start = table*SECTOR+offset
        struct.pack_into('<HHIIBB', data, start, 0, 0, sector, size, flags, len(basename))
        data[start+14:start+14+len(basename)] = basename
    record(37, 96, b'Movies', 39, SECTOR, 0x10)
    record(39, 0, b'intro.bik', 43, len(movie), 0x80)
    data[43*SECTOR:43*SECTOR+len(movie)] = movie
    line = f'{len(movie)} 0 43 ..\\MC2Game\\Movies\\intro.bik 0\r\n'.encode()
    f.original_toc += line
    struct.pack_into('<I', data, 37*SECTOR+32+8, len(f.original_toc))
    data[42*SECTOR:42*SECTOR+len(f.original_toc)] = f.original_toc
    f.image.write_bytes(data); f.hash = sha(data)
    f.manifest['source_image_sha256'] = f.hash
    f.manifest['resources'][-1].update(original_size=len(f.original_toc),
                                      original_sha256=sha(f.original_toc))
    f.replace_candidate_toc(f.candidate_toc+line)
    return name, movie


class RefreshImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.f = Fixture(self.root, payload=fixture(outer=True, bulk=True), toc=True)
        self.movie_name, self.old_movie = add_movie_member(self.f)
        legacy_image(self.f)
        repair.prepare(self.f.output, self.f.report, sha256_file(self.f.report),
                       self.root/'repair', stored_decoder)
        self.previous = self.root/'repair/plan.json'
        repair.apply(self.f.output, self.previous, sha256_file(self.previous))
        self.before = self.f.output.read_bytes()
        d = Disc(self.f.output)
        self.entry = next(e for e in d.inventory() if e['path'] == self.f.name)
        self.delta_root = self.root/'delta'
        self.delta_root.mkdir()
        payload = fixture(outer=True, bulk=True, fmt=5)
        (self.delta_root/'new.xxx').write_bytes(payload)
        self.delta = dict(schema_version=1, kind='disc-resource-refresh', disc=1,
            resources=[dict(path=self.f.name, before_sha256=d.resource_hash(self.entry),
                            file='new.xxx', size=len(payload), sha256=sha(payload))])
        self.manifest = self.delta_root/'manifest.json'
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self):
        self.manifest.write_bytes(iso.encoded(self.delta))

    def prepare(self):
        return repair.prepare_refresh(self.f.output, self.previous,
            sha256_file(self.previous), self.manifest, sha256_file(self.manifest),
            self.root/'refresh', stored_decoder)

    def test_followup_normalizes_applies_and_isolated_rollback(self):
        p = self.prepare()
        self.assertEqual(self.f.output.read_bytes(), self.before)
        plan = self.root/'refresh/plan.json'; lock = sha256_file(plan)
        self.assertEqual(len(p['changes']), 2)
        self.assertGreater(p['resource_proofs'][0]['generated_outer_chunks'], 0)
        repair.preflight(self.f.output, plan, lock)
        repair.apply(self.f.output, plan, lock)
        self.assertEqual(repair.verify(self.f.output, plan, lock)['status'], 'PASS')
        modified = self.f.output.read_bytes()
        restored = self.root/'restored-copy.iso'
        repair.restore(self.f.output, plan, lock, restored)
        self.assertEqual(restored.read_bytes(), self.before)
        self.assertEqual(self.f.output.read_bytes(), modified)
        self.assertEqual(sha256_file(self.f.image), self.f.hash)

    def test_current_image_conflict_zero_writes(self):
        with self.f.output.open('r+b') as f: f.write(b'conflict')
        before = self.f.output.read_bytes()
        with self.assertRaisesRegex(ValueError, 'identity'): self.prepare()
        self.assertEqual(self.f.output.read_bytes(), before)
        self.assertFalse((self.root/'refresh').exists())

    def test_wrong_before_hash_rejected(self):
        self.delta['resources'][0]['before_sha256'] = '0'*64
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'before'): self.prepare()
        self.assertFalse((self.root/'refresh').exists())

    def test_wrong_disc_rejected(self):
        self.delta['disc'] = 2; self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'disc'): self.prepare()
        self.assertFalse((self.root/'refresh').exists())

    def test_changed_source_rejected(self):
        (self.delta_root/'new.xxx').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'replacement'): self.prepare()
        self.assertFalse((self.root/'refresh').exists())

    def test_escape_rejected(self):
        self.delta['resources'][0]['file'] = '../outside'
        self.write_manifest()
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse((self.root/'refresh').exists())

    def test_duplicate_casefold_path_rejected(self):
        row = copy.deepcopy(self.delta['resources'][0]); row['path'] = row['path'].upper()
        self.delta['resources'].append(row); self.write_manifest()
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse((self.root/'refresh').exists())

    def test_no_directory_or_toc_or_executable_payload(self):
        for name in ('MC2Game', self.f.toc_name, 'default.xex'):
            with self.subTest(name=name):
                self.delta['resources'][0]['path'] = name; self.write_manifest()
                with self.assertRaises(ValueError): self.prepare()
                self.assertFalse((self.root/'refresh').exists())

    def test_unknown_package_rejected_without_image_writes(self):
        raw = b'not a package'
        (self.delta_root/'new.xxx').write_bytes(raw)
        self.delta['resources'][0].update(size=len(raw), sha256=sha(raw)); self.write_manifest()
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_predecessor_hash_rejected(self):
        with self.assertRaises(ValueError):
            repair.prepare_refresh(self.f.output, self.previous, '0'*64,
                self.manifest, sha256_file(self.manifest), self.root/'refresh', stored_decoder)
        self.assertFalse((self.root/'refresh').exists())

    def test_second_generation_refresh(self):
        p = self.prepare(); plan = self.root/'refresh/plan.json'
        repair.apply(self.f.output, plan, sha256_file(plan))
        first_generation = self.f.output.read_bytes()
        self.assertEqual(repair.verify(self.f.output, plan, sha256_file(plan))['status'], 'PASS')
        self.previous = plan
        self.delta['resources'][0]['before_sha256'] = p['changes'][0]['sha256']
        payload = fixture(outer=True, bulk=True, fmt=7)
        (self.delta_root/'new.xxx').write_bytes(payload)
        self.delta['resources'][0].update(size=len(payload), sha256=sha(payload)); self.write_manifest()
        p2 = repair.prepare_refresh(self.f.output, self.previous, sha256_file(self.previous),
            self.manifest, sha256_file(self.manifest), self.root/'refresh2', stored_decoder)
        self.assertEqual(p2['input']['sha256'], p['output']['sha256'])
        plan2 = self.root/'refresh2/plan.json'; lock2 = sha256_file(plan2)
        repair.preflight(self.f.output, plan2, lock2)
        repair.apply(self.f.output, plan2, lock2)
        proof = repair.verify(self.f.output, plan2, lock2)
        self.assertEqual(proof['restored_input_sha256'], sha(first_generation))
        final_generation = self.f.output.read_bytes()
        restored1 = self.root/'restored-generation1.iso'
        repair.restore(self.f.output, plan2, lock2, restored1)
        self.assertEqual(restored1.read_bytes(), first_generation)
        restored0 = self.root/'restored-generation0.iso'
        repair.restore(restored1, plan, sha256_file(plan), restored0)
        self.assertEqual(restored0.read_bytes(), self.before)
        self.assertEqual(self.f.output.read_bytes(), final_generation)
        self.assertEqual(sha256_file(self.f.image), self.f.hash)

    def movie_selection(self, payload, include_package=False):
        (self.delta_root/'new.bik').write_bytes(payload)
        row = dict(path=self.movie_name, before_sha256=sha(self.old_movie),
                   file='new.bik', size=len(payload), sha256=sha(payload))
        self.delta['resources'] = (self.delta['resources'] if include_package else [])+[row]
        self.write_manifest()

    def test_bik_replacement_is_exact_only_appends_and_updates_toc(self):
        payload = b'BIKi'+bytes(range(251))*17
        self.movie_selection(payload)
        with patch.object(repair, 'normalize_package', side_effect=AssertionError('BIK must remain opaque')):
            p = self.prepare()
        self.assertEqual([r['path'] for r in p['changes']], [self.movie_name, self.f.toc_name])
        plan = self.root/'refresh/plan.json'; lock = sha256_file(plan)
        self.assertEqual(self.f.output.read_bytes(), self.before)
        repair.apply(self.f.output, plan, lock)
        verified = repair.verify(self.f.output, plan, lock)
        self.assertEqual(verified['restored_input_sha256'], sha(self.before))
        d = Disc(self.f.output); entries = {e['path']:e for e in d.inventory()}
        e = entries[self.movie_name]
        self.assertEqual(d.read(e['offset'], e['size']), payload)
        self.assertEqual(d.resource_hash(entries['default.xex']), sha(b'xex'))
        toc = entries[self.f.toc_name]
        toc_rows = {r['path']:r for r in iso.toc_rows(d.read(toc['offset'], toc['size']))}
        self.assertEqual((toc_rows[self.movie_name]['size'], toc_rows[self.movie_name]['sector']),
                         (e['size'], e['sector']))
        self.assertEqual((toc_rows[self.f.toc_name]['size'], toc_rows[self.f.toc_name]['sector']),
                         (0, toc['sector']))
        modified = self.f.output.read_bytes()
        inverse = bytearray(modified[:len(self.before)])
        for row in p['changes']:
            pos = row['field_offset']
            self.assertEqual(modified[pos:pos+8].hex(), row['after_hex'])
            inverse[pos:pos+8] = bytes.fromhex(row['before_hex'])
        self.assertEqual(inverse, self.before)
        restored = self.root/'restored-bik-copy.iso'
        repair.restore(self.f.output, plan, lock, restored)
        self.assertEqual(restored.read_bytes(), self.before)
        self.assertEqual(self.f.output.read_bytes(), modified)
        self.assertEqual(sha256_file(self.f.image), self.f.hash)

    def test_selected_unchanged_bik_is_not_appended(self):
        self.movie_selection(self.old_movie, include_package=True)
        p = self.prepare()
        self.assertEqual([r['path'] for r in p['changes']], [self.f.name, self.f.toc_name])
        self.assertFalse((self.root/'refresh/resources'/self.movie_name).exists())

    def test_all_unchanged_selection_leaves_image_untouched(self):
        self.movie_selection(self.old_movie)
        with self.assertRaisesRegex(ValueError, 'no changed resources'): self.prepare()
        self.assertEqual(self.f.output.read_bytes(), self.before)
        self.assertFalse((self.root/'refresh/plan.json').exists())

    def test_stale_toc_rejected_even_when_predecessor_hashes_match(self):
        d = Disc(self.f.output); e = next(e for e in d.inventory() if e['path'] == self.f.toc_name)
        raw = bytearray(d.read(e['offset'], e['size']))
        row = iso.toc_rows(bytes(raw))[0]
        pos = row['offset']+row['match'].end(3)-1
        raw[pos] = ord('0') if raw[pos] != ord('0') else ord('1')
        with self.f.output.open('r+b') as stream:
            stream.seek(e['offset']); stream.write(raw)
        previous, _ = repair.read_plan(self.previous, sha256_file(self.previous))
        previous['output']['sha256'] = sha256_file(self.f.output)
        next(r for r in previous['changes'] if r['path'] == self.f.toc_name)['sha256'] = sha(raw)
        self.previous.write_bytes(iso.encoded(previous))
        before = self.f.output.read_bytes()
        with self.assertRaisesRegex(ValueError, 'TOC sector mismatch'): self.prepare()
        self.assertEqual(self.f.output.read_bytes(), before)
        self.assertFalse((self.root/'refresh').exists())

    def wrong_directory_plan(self):
        p = self.prepare(); row = p['changes'][0]
        # Keep every shape/hash guard valid but point the field at XEX payload.
        row['field_offset'] = 40*SECTOR
        row['before_hex'] = self.before[row['field_offset']:row['field_offset']+8].hex()
        p['output']['sha256'] = repair.projected_hash(self.f.output, p['input']['size'],
                                                     p['changes'], self.root/'refresh')
        plan = self.root/'refresh/plan.json'; plan.write_bytes(iso.encoded(p))
        return plan, sha256_file(plan)

    def test_preflight_rebinds_directory_field_to_resource(self):
        plan, lock = self.wrong_directory_plan()
        with self.assertRaisesRegex(ValueError, 'directory target'):
            repair.preflight(self.f.output, plan, lock)
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_apply_rebinds_directory_field_before_any_writes(self):
        plan, lock = self.wrong_directory_plan()
        with self.assertRaisesRegex(ValueError, 'directory target'):
            repair.apply(self.f.output, plan, lock)
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_partial_refresh_recover(self):
        p = self.prepare(); plan = self.root/'refresh/plan.json'; lock = sha256_file(plan)
        row = p['changes'][0]
        with self.f.output.open('r+b') as f:
            f.seek(p['input']['size']); f.write((plan.parent/row['file']).read_bytes()[:33])
            f.seek(row['field_offset']); f.write(bytes.fromhex(row['after_hex'])[:3])
        self.assertEqual(repair.recover(self.f.output, plan, lock)['status'], 'RECOVERED')
        self.assertEqual(self.f.output.read_bytes(), self.before)


if __name__ == '__main__': unittest.main()
