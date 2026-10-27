"""Incremental image transaction tests use only self-authored fixtures."""
from pathlib import Path
import tempfile
import unittest

from test_build_disc_image import Fixture, legacy_image
import test_decompress_package as decompression_fixture
from test_supplement_font import stored_decoder
from tools import repair_disc_image as repair
from tools import build_disc_image as iso
from tools.disc_inventory import Disc, sha256_file
from tools.ue3_package import parse_summary


class RepairImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.f = Fixture(self.root, payload=decompression_fixture.DecompressCopyTests().fixture(), toc=True)
        self.old = legacy_image(self.f)
        self.before = self.f.output.read_bytes()

    def tearDown(self):
        self.tmp.cleanup()

    def prepare(self):
        return repair.prepare(self.f.output, self.f.report,
                              sha256_file(self.f.report), self.root/'repair', stored_decoder)

    def test_append_verify_restore_another_copy_preserves_input(self):
        plan = self.prepare()
        plan_path = self.root/'repair/plan.json'
        lock = sha256_file(plan_path)
        self.assertEqual(self.f.output.read_bytes(), self.before)
        repair.apply(self.f.output, plan_path, lock)
        result = repair.verify(self.f.output, plan_path, lock)
        self.assertTrue(result['all_file_hashes_match'])
        self.assertEqual(result['restored_input_sha256'], self.old['output']['sha256'])
        d = Disc(self.f.output)
        entries = {r['path']: r for r in d.inventory()}
        e = entries[self.f.name]
        self.assertEqual(parse_summary(d.read(e['offset'], e['size']))['compression_flags'], 0)
        output = self.root/'restored.iso'
        repair.restore(self.f.output, plan_path, lock, output)
        self.assertEqual(output.read_bytes(), self.before)
        self.assertEqual(sha256_file(self.f.image), self.f.hash)
        self.assertEqual(sha256_file(self.f.output), plan['output']['sha256'])

    def test_changed_image_rejected_before_prepare_writes(self):
        with self.f.output.open('r+b') as f:
            f.write(b'x')
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.prepare()
        self.assertFalse((self.root/'repair').exists())

    def test_wrong_report_hash_rejected(self):
        with self.assertRaises(ValueError):
            repair.prepare(self.f.output, self.f.report, '0'*64, self.root/'repair', stored_decoder)
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_tampered_staged_resource_rejects_apply_without_writes(self):
        p = self.prepare(); row = p['changes'][0]
        (self.root/'repair'/row['file']).write_bytes(b'wrong')
        with self.assertRaises(ValueError):
            repair.apply(self.f.output, self.root/'repair/plan.json', sha256_file(self.root/'repair/plan.json'))
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_second_apply_rejected(self):
        self.prepare(); p = self.root/'repair/plan.json'; h = sha256_file(p)
        repair.apply(self.f.output, p, h)
        fixed = self.f.output.read_bytes()
        with self.assertRaises(ValueError): repair.apply(self.f.output, p, h)
        self.assertEqual(self.f.output.read_bytes(), fixed)

    def test_restore_rejects_existing_or_input_output(self):
        self.prepare(); p = self.root/'repair/plan.json'; h = sha256_file(p)
        repair.apply(self.f.output, p, h)
        for dst in (self.f.output, self.f.image):
            with self.assertRaises(ValueError): repair.restore(self.f.output, p, h, dst)
        self.assertEqual(sha256_file(self.f.image), self.f.hash)

    def test_plan_path_escape_rejected(self):
        p = self.prepare(); p['changes'][0]['file'] = '../outside'
        path = self.root/'repair/plan.json'; path.write_bytes(iso.encoded(p))
        with self.assertRaises(ValueError): repair.apply(self.f.output, path, sha256_file(path))
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_unrelated_bytes_tamper_detected_after_apply(self):
        self.prepare(); p = self.root/'repair/plan.json'; h = sha256_file(p)
        repair.apply(self.f.output, p, h)
        with self.f.output.open('r+b') as f: f.write(b'wrong')
        with self.assertRaises(ValueError): repair.verify(self.f.output, p, h)

    def test_failure_during_append_restores_exact_input(self):
        from unittest.mock import patch
        self.prepare(); p = self.root/'repair/plan.json'; h = sha256_file(p)
        with patch('tools.repair_disc_image.write_payloads', side_effect=OSError('injected write failure')):
            with self.assertRaisesRegex(OSError, 'injected'):
                repair.apply(self.f.output, p, h)
        self.assertEqual(self.f.output.read_bytes(), self.before)

    def test_recover_partial_append_and_half_written_field(self):
        plan = self.prepare(); p=self.root/'repair/plan.json'; h=sha256_file(p)
        row=plan['changes'][0]
        with self.f.output.open('r+b') as f:
            f.seek(plan['input']['size'])
            f.write((self.root/'repair'/row['file']).read_bytes()[:71])
            f.seek(row['field_offset']); f.write(bytes.fromhex(row['after_hex'])[:5])
        self.assertEqual(repair.recover(self.f.output,p,h)['status'],'RECOVERED')
        self.assertEqual(self.f.output.read_bytes(),self.before)

    def test_recover_rejects_foreign_tail_without_writing(self):
        self.prepare(); p=self.root/'repair/plan.json'; h=sha256_file(p)
        with self.f.output.open('ab') as f: f.write(b'foreign data')
        before=self.f.output.read_bytes()
        with self.assertRaisesRegex(ValueError,'payload conflict'): repair.recover(self.f.output,p,h)
        self.assertEqual(self.f.output.read_bytes(),before)

    def test_recover_rejects_unrelated_prefix_change_without_writing(self):
        self.prepare(); p=self.root/'repair/plan.json'; h=sha256_file(p)
        with self.f.output.open('r+b') as f: f.write(b'foreign')
        before=self.f.output.read_bytes()
        with self.assertRaisesRegex(ValueError,'prefix conflict'): repair.recover(self.f.output,p,h)
        self.assertEqual(self.f.output.read_bytes(),before)

    def test_recover_complete_output_then_reapply(self):
        self.prepare(); p=self.root/'repair/plan.json'; h=sha256_file(p)
        repair.apply(self.f.output,p,h)
        repair.recover(self.f.output,p,h)
        self.assertEqual(self.f.output.read_bytes(),self.before)
        repair.apply(self.f.output,p,h)
        self.assertEqual(repair.verify(self.f.output,p,h)['status'],'PASS')

    def test_preflight_rejects_wrong_projection_without_image_writes(self):
        plan=self.prepare(); p=self.root/'repair/plan.json'
        plan['output']['sha256']='0'*64; p.write_bytes(iso.encoded(plan))
        with self.assertRaisesRegex(ValueError,'projected output'):
            repair.preflight(self.f.output,p,sha256_file(p))
        self.assertEqual(self.f.output.read_bytes(),self.before)

    def test_detailed_plan_over_packet_limit_remains_bounded(self):
        from unittest.mock import patch
        plan=self.prepare(); p=self.root/'repair/plan.json'
        plan['audit_note']='x'*(4*1024*1024)
        p.write_bytes(iso.encoded(plan)); h=sha256_file(p)
        self.assertEqual(repair.preflight(self.f.output,p,h)['status'],'PREPARED')
        with patch('tools.repair_disc_image.PLAN_LIMIT',1024):
            with self.assertRaisesRegex(ValueError,'size bound'): repair.read_plan(p,h)


if __name__ == '__main__': unittest.main()
