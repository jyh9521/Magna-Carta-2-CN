"""Self-authored PPC admission harness; no game executable/assets are needed."""
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.coalesced import EmbeddedFile, SerializedString, serialize
from tools.replay_ini_registration import (MAX_UNITS, main, replay_document,
                                           run_controls, select_document, sha256,
                                           validate_profile)


def d(op, rt, ra, imm):
    return op << 26 | rt << 21 | ra << 16 | (imm & 65535)


def x(rt, ra, rb, xo):
    return 31 << 26 | rt << 21 | ra << 16 | rb << 11 | xo << 1


def cmpi(ra, value, field=6):
    return 10 << 26 | field << 23 | ra << 16 | value


def mr(target, source):
    return x(source, target, source, 444)


def rotate(ra, rs, sh, mb, me):
    return 21 << 26 | rs << 21 | ra << 16 | sh << 11 | mb << 6 | me << 1


class Assembler:
    def __init__(self, start):
        self.start = start
        self.words = []
        self.labels = {}
        self.patches = []

    def label(self, name):
        self.labels[name] = self.start + len(self.words)*4

    def emit(self, *words):
        self.words.extend(words)

    def branch(self, name, condition=None):
        self.patches.append((len(self.words), name, condition))
        self.emit(0)

    def finish(self):
        for index, name, condition in self.patches:
            delta = self.labels[name] - (self.start + index*4)
            self.words[index] = (18 << 26 | (delta & 0x3fffffc)) if condition is None else (
                16 << 26 | condition[0] << 21 | condition[1] << 16 | (delta & 0xfffc))
        return b''.join(struct.pack('>I', word) for word in self.words)


def synthetic_profile():
    base = 0x10000000
    blob = bytearray(0x1200)
    windows, labels = {}, {}

    def put(name, a):
        raw = a.finish()
        blob[a.start-base:a.start-base+len(raw)] = raw
        windows[name] = dict(start=hex(a.start), end=hex(a.start+len(raw)), sha256=sha256(raw))
        labels.update(a.labels)

    for index, name in enumerate(('loader', 'array', 'macro_replace')):
        a = Assembler(base+index*4)
        a.emit(d(24, 0, 0, 0))
        put(name, a)

    a = Assembler(base+0x100)
    a.label('swap_entry')
    a.emit(d(32, 8, 30, 4), d(14, 11, 0, 0), d(14, 10, 0, 0))
    a.label('swap_loop')
    a.emit(d(32, 9, 30, 0), x(9, 10, 9, 266), d(40, 8, 9, 0),
           rotate(7, 8, 8, 16, 23), rotate(6, 8, 24, 8, 31), x(7, 5, 6, 444),
           d(44, 5, 9, 0), d(14, 11, 11, 1), d(14, 10, 10, 2))
    a.label('swap_compare')
    a.emit(d(32, 4, 30, 4), x(24, 11, 4, 0))
    a.branch('swap_loop', (12, 24))
    a.label('swap_done')
    a.emit(0x4e800020)
    put('fstring', a)

    a = Assembler(base+0x300)
    a.label('parser_init')
    a.emit(d(14, 28, 0, 0), mr(27, 28), mr(19, 28), d(15, 21, 0, base >> 16), d(24, 21, 21, 0x1100))
    a.label('skip_newline')
    a.emit(d(40, 11, 26, 0), cmpi(11, 13))
    a.branch('skip_one', (12, 26))
    a.emit(cmpi(11, 10))
    a.branch('line_start', (4, 26))
    a.label('skip_one')
    a.emit(d(14, 26, 26, 2))
    a.branch('skip_newline')
    a.label('line_start')
    a.emit(mr(29, 26))
    a.label('scan')
    a.emit(d(40, 11, 26, 0), cmpi(11, 0))
    a.branch('split_line', (12, 26))
    a.emit(cmpi(11, 13))
    a.branch('split_line', (12, 26))
    a.emit(cmpi(11, 10))
    a.branch('split_line', (12, 26))
    a.label('scan_update')
    a.emit(d(14, 26, 26, 2))
    a.branch('scan')
    a.label('split_line')
    a.emit(d(40, 11, 26, 0), cmpi(11, 0))
    a.branch('terminate_line', (4, 26))
    a.emit(d(14, 19, 0, 1))
    a.label('terminate_line')
    a.emit(d(44, 28, 26, 0), d(14, 26, 26, 2), d(40, 11, 29, 0), cmpi(11, 91))
    a.branch('section_gate', (4, 26))
    a.emit(mr(3, 29))
    a.label('length_call')
    a.branch('length_return')
    a.label('length_return')
    a.emit(rotate(11, 3, 1, 0, 30), x(11, 11, 29, 266), d(40, 10, 11, -2), cmpi(10, 93))
    a.branch('section_gate', (4, 26))
    a.label('section_admitted')
    a.branch('line_end')
    a.label('section_gate')
    a.emit(cmpi(27, 0))
    a.branch('line_end', (12, 26))
    a.emit(d(40, 11, 29, 0), cmpi(11, 0))
    a.branch('line_end', (12, 26))
    a.emit(mr(4, 21), mr(3, 29))
    a.label('find_call')
    a.branch('find_return')
    a.label('find_return')
    a.emit(cmpi(3, 0))
    a.branch('line_end', (12, 26))
    a.label('key_admitted')
    a.branch('line_end')
    a.label('line_end')
    a.emit(cmpi(19, 0))
    a.branch('skip_newline', (12, 26))
    a.label('parser_done')
    a.emit(0x4e800020)
    put('parser', a)

    a = Assembler(base+0x700)
    a.label('length_entry')
    a.emit(mr(11, 3))
    a.label('length_loop')
    a.emit(d(40, 10, 11, 0), d(14, 11, 11, 2))
    a.label('length_compare')
    a.emit(cmpi(10, 0, 0))
    a.branch('length_loop', (4, 2))
    a.emit(x(11, 3, 11, 40), x(11, 11, 1, 824), d(14, 3, 11, -1))
    a.label('length_return_pc')
    a.emit(0x4e800020)
    put('wcslen', a)

    a = Assembler(base+0x900)
    a.label('find_entry')
    a.emit(d(40, 11, 4, 0), cmpi(11, 0, 0))
    a.label('find_empty_return')
    a.emit(0x4d820020)
    a.label('find_outer')
    a.emit(d(40, 10, 3, 0), cmpi(10, 0, 0))
    a.branch('not_found', (12, 2))
    a.label('find_reset')
    a.emit(mr(9, 3))
    a.label('find_inner')
    a.emit(d(40, 8, 4, 0))
    a.label('find_check')
    a.emit(x(0, 10, 8, 0))
    a.label('find_match_return')
    a.emit(0x4d820020)
    a.label('find_advance')
    a.emit(d(14, 3, 3, 2))
    a.branch('find_outer')
    a.label('not_found')
    a.emit(d(14, 3, 0, 0))
    a.label('find_return_pc')
    a.emit(0x4e800020)
    put('wcsstr', a)

    constants = {}
    for name, text, offset in [('equals', '=', 0x1100), ('macro', '%GAME%', 0x1120)]:
        raw = (text+'\0').encode('utf-16-be')
        blob[offset:offset+len(raw)] = raw
        constants[name] = dict(address=hex(base+offset), text=text)
    profile = dict(schema_version=1, image_base=hex(base), image_sha256=sha256(blob),
                   windows=windows, labels={k: hex(v) for k, v in labels.items()},
                   constants=constants, boundary='self-authored synthetic admission harness')
    return bytes(blob), profile


class NativeIniReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.profile = synthetic_profile()

    def replay(self, text, **kwargs):
        return replay_document(self.image, self.profile, text.encode('utf-16-le'), **kwargs)

    def test_all_nine_controls_and_explicit_positive_boundary(self):
        result = run_controls(self.image, self.profile)
        self.assertEqual(len(result), 9)
        negative = result['bad_section_tail']['result']
        self.assertTrue(negative['terminal'])
        self.assertEqual(negative['assumptions'], [])
        self.assertEqual(negative['conclusion'], 'verified-no-section-no-key-registration-route')
        positive = result['valid_section_key_witness']['result']
        self.assertEqual(positive['key_admissions'], 1)
        self.assertEqual(positive['map_insertions_executed'], 0)
        self.assertEqual(len(positive['assumptions']), 2)

    def test_bad_headers_unicode_tail_and_full_document_termination(self):
        text = '[A]\u0a0dyes=x\nKey=example\n[B]\u0a0dTail'
        result = self.replay(text)
        self.assertTrue(result['terminal'])
        self.assertEqual(result['section_admissions'], 0)
        self.assertEqual(result['key_admissions'], 0)
        self.assertEqual(len(result['lines']), 3)
        self.assertEqual(result['final_cursor_unit'], len(text)+1)
        self.assertTrue(all(x['decision'] == 'no-section-skip' for x in result['lines']))

    def test_late_valid_header_prevents_negative_classification(self):
        result = self.replay('K=x\n[A]tail\nK=y\n[Valid]\nK=z')
        self.assertFalse(result['terminal'])
        self.assertEqual(result['section_admissions'], 1)
        self.assertEqual(len(result['lines']), 4)
        self.assertEqual(result['assumptions'], [])

    def test_chunked_long_scan_and_wcslen_do_not_hide_truncation(self):
        result = self.replay('['+'A'*500+'tail\nK=x')
        self.assertTrue(result['terminal'])
        self.assertGreater(result['instruction_count'], 256)
        self.assertGreater(result['fragment_count'], 256)
        self.assertEqual(len(result['lines']), 2)

    def test_invalid_data_and_macro_fail_closed(self):
        for raw, message in [(b'x', 'even-sized'), (b'\0\0', 'embedded NUL'),
                             (b'x\0'*(MAX_UNITS+1), 'bounded replay'),
                             ('%GAME%'.encode('utf-16-le'), 'macro-bearing')]:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                replay_document(self.image, self.profile, raw)

    def test_profile_image_window_constant_and_label_guards(self):
        with self.assertRaisesRegex(ValueError, 'image SHA'):
            validate_profile(self.image[:-1]+b'x', self.profile)
        for key, edit, message in [
            ('windows', lambda p: p['windows']['parser'].update(sha256='0'*64), 'window SHA'),
            ('constants', lambda p: p['constants']['macro'].update(text='OTHER'), 'constant'),
            ('labels', lambda p: p['labels'].update(scan='0x20'), 'outside code')]:
            p = json.loads(json.dumps(self.profile))
            edit(p)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                validate_profile(self.image, p)

    def test_coalesced_bytes_source_hash_cli_output_and_input_alias(self):
        path = '..\\Sample\\Localization\\INT\\Sample.int'
        text = '[A]tail\nK=x'
        raw = text.encode('utf-16-le')
        data = serialize([EmbeddedFile(SerializedString(path, 'ascii', 0),
                                       SerializedString(text, 'utf-16-le', 0))])
        selected, offset = select_document(data, path, sha256(raw))
        self.assertEqual(selected, raw)
        self.assertEqual(data[offset+4:offset+4+len(raw)], raw)
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            select_document(data, path, '0'*64)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image, profile, source, output = (root/x for x in ('image.bin', 'profile.json', 'source.int', 'report.json'))
            image.write_bytes(self.image)
            profile.write_text(json.dumps(self.profile), encoding='utf-8')
            source.write_bytes(data)
            args = ['--image', str(image), '--profile', str(profile), '--coalesced', str(source),
                    '--coalesced-sha256', sha256(data), '--embedded-path', path,
                    '--embedded-sha256', sha256(raw), '--output', str(output), '--controls', '--expect-inactive']
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main(args), 0)
            self.assertIn('controls: PASS 9', stdout.getvalue())
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertTrue(report['source']['terminal'])
            self.assertEqual(source.read_bytes(), data)
            args[args.index(str(output))] = str(source)
            with self.assertRaisesRegex(ValueError, 'aliases'):
                main(args)
            self.assertEqual(source.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
