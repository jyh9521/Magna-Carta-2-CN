"""Authored byte-widen loop, not a redistributed game-code fixture."""
import copy
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.replay_narrow_fstring import MAX_BYTES, digest, main, replay, validate_profile
from test_ppc_fragment import BASE, d, x, compare, conditional, image


def fixture():
    code=image(d(32,9,30,4),d(14,11,0,0),compare(11,6,9,0),conditional(40,4,25),
               d(14,10,0,0),x(9,11,29,87),d(14,11,11,1),d(32,8,30,0),
               x(9,10,8,407),d(14,10,10,2),d(32,7,30,4),
               (31<<26)|(6<<23)|(11<<16)|(7<<11),conditional(-28,12,24),d(14,3,0,0))
    profile=dict(schema_version=1,kind='positive-fstring-byte-widen-profile',profile_id='authored',
                 image_base=hex(BASE),image_sha256=digest(code),
                 window=dict(start=hex(BASE),end=hex(BASE+len(code)),sha256=digest(code)),
                 labels={k:hex(BASE+n)for k,n in dict(entry=0,loop=20,compare=40,done=52).items()})
    return code,profile


class ByteWidenTests(unittest.TestCase):
    def test_every_byte_is_unsigned_and_terminal_is_consumed(self):
        image,profile=fixture();payload=bytes(range(1,256));r=replay(image,profile,payload)
        self.assertEqual(r['stores'],256);self.assertTrue(r['terminal'])
        self.assertEqual(r['decoded_utf8_sha256'],digest(''.join(map(chr,payload)).encode()))
        self.assertEqual(r['non_ascii'][0],dict(offset=127,byte=128,codepoint='U+0080'))
        self.assertEqual(r['non_ascii'][-1]['codepoint'],'U+00FF')
        self.assertFalse(r['allocation_and_archive_read_executed'])
        self.assertFalse(r['ini_registration_executed']);self.assertFalse(r['game_rendering_verified'])
        self.assertEqual(replay(image,profile,b'')['stores'],1)

    def test_byte_count_not_instruction_fragment_limit(self):
        image,profile=fixture();r=replay(image,profile,b'x'*4097+b'\xa9')
        self.assertEqual(r['stores'],4099);self.assertGreater(r['fragment_count'],256)

    def test_payload_limits_and_embedded_terminator(self):
        image,profile=fixture()
        for payload in (b'a\0b',b'a'*(MAX_BYTES+1),'text',bytearray(b'a')):
            with self.subTest(payload_type=type(payload)),self.assertRaises(ValueError):replay(image,profile,payload)

    def test_code_profile_labels_and_hashes_are_bound(self):
        image,profile=fixture()
        for mutate in (lambda p:p.update(schema_version=True),lambda p:p.update(image_sha256='0'*64),
                       lambda p:p['window'].update(sha256='0'*64),
                       lambda p:p['labels'].update(loop=p['labels']['entry']),
                       lambda p:p['labels'].update(compare='0x00000004')):
            p=copy.deepcopy(profile);mutate(p)
            with self.assertRaises(ValueError):validate_profile(image,p)
        with self.assertRaises(ValueError):replay(image[:-4]+b'\0'*4,profile,b'a')

    def test_cli_reopens_output_and_rejects_source_drift_or_overwrite(self):
        image,profile=fixture()
        with tempfile.TemporaryDirectory() as temp,redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            root=Path(temp);p=root/'profile.json';p.write_bytes(json.dumps(profile).encode())
            i=root/'image';i.write_bytes(image);b=root/'payload';b.write_bytes(b'own\xa9')
            out=root/'report.json'
            args=['--image',str(i),'--profile',str(p),'--profile-sha256',digest(p.read_bytes()),
                  '--payload',str(b),'--payload-sha256',digest(b.read_bytes()),'--output',str(out)]
            self.assertEqual(main(args),0);self.assertEqual(json.loads(out.read_bytes())['stores'],5)
            raw=out.read_bytes();self.assertEqual(main(args),2);self.assertEqual(out.read_bytes(),raw)
            out.unlink();b.write_bytes(b'other');self.assertEqual(main(args),2)
            self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
