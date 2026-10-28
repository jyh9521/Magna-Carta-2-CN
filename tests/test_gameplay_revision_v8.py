"""Current user-approved text/face boundary, distinct from historical drafts."""
import json
from pathlib import Path
import unittest
from tools.audit_resource_terms import strings

ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_bytes())


class GameplayRevisionTests(unittest.TestCase):
    def test_term_overlay_and_pickup_phrases(self):
        entries=load('locales/zh-Hans/gameplay-text-v8.json')['entries']
        self.assertEqual(len(entries),52)
        self.assertEqual(len({e['id'] for e in entries}),52)
        terms=[e for e in entries if '真名法典' in e['translation']]
        self.assertEqual(len(terms),46)
        self.assertEqual(sum(e['translation'].count('真名法典') for e in terms),48)
        self.assertFalse(any('玛格纳卡尔塔' in e['translation'] for e in entries))
        grammar=[e['translation'] for e in entries if e not in terms]
        self.assertCountEqual(grammar,['','','已获得','已获得','已获得','已习得'])
        for noun in ('100SID','治愈种子','木剑'):
            self.assertTrue((noun+''+' '+'已获得').endswith(' 已获得'))

    def test_subtitle_and_font_scope(self):
        sub=load('locales/zh-Hans/subtitles/terminology-v8-csm09-40.txt.json')
        self.assertEqual(len(sub['entries']),3)
        self.assertTrue(all('真名法典' in e['translation'] for e in sub['entries']))
        face=load('locales/zh-Hans/dynamic-font-zhuque-500.json')
        self.assertTrue(face['font']['path'].endswith('ZhuqueFangsong-Regular.ttf'))
        self.assertEqual(sum(len(s['fonts']) for s in face['sources']),7)
        self.assertEqual({r['font_size'] for r in face['roles']},{15,22,27})
        self.assertTrue(all(r['stroke_em']==.006 for r in face['roles']))
        revision=load('locales/zh-Hans/gameplay-revision-v8.json')
        self.assertEqual(revision['texture_rects'],[[176,100,104,36],[696,64,12,12]])
        self.assertEqual(len(revision['texture_targets']),2)

    def test_text_reader_does_not_silently_ignore_unknown_bytes(self):
        self.assertEqual(strings('已获得'.encode(),'x.txt'),['已获得'])
        self.assertEqual(strings(b'\xff\xfe'+'真名法典'.encode('utf-16-le'),'x.int'),['真名法典'])
        with self.assertRaises(UnicodeDecodeError):strings(b'\xffbroken','x.int')


if __name__=='__main__':unittest.main()
