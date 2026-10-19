import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import export_subtitle_catalogs as module
from tools.export_subtitle_catalogs import catalog
from tools.subtitle_text import digest


class SubtitleCatalogTests(unittest.TestCase):
    def setUp(self):
        self.data=b'\xff\xfe'+('1\r\n<SYNC Start=10><P Class=KRCC>source<br>text'
            '<SYNC Start=20><P Class=KRCC>&nbsp;\r\n').encode('utf-16-le')
        self.plan=dict(schema_version=1, kind='timed-subtitle-text', resource='Movies/a.txt',
            input_sha256=digest(self.data), entries=[dict(start=10,end=20,
                source_sha256=digest(b'source<br>text'),translation='字幕<br>文本')])

    def test_retains_source_timing_and_existing_draft(self):
        result=catalog(self.data,'Movies/a.txt',[self.plan])
        row=result['entries'][0]
        self.assertEqual((row['start'],row['end'],row['source'],row['translation'],row['status']),
            (10,20,'source<br>text','字幕<br>文本','draft'))
        self.assertEqual(row['reviewer'],'')

    def test_untranslated_never_copies_source(self):
        row=catalog(self.data,'Movies/a.txt',[])['entries'][0]
        self.assertEqual((row['translation'],row['status']),('','untranslated'))

    def test_no_cross_resource_merge(self):
        with self.assertRaisesRegex(ValueError,'resource/hash'):
            catalog(self.data,'Movies/other.txt',[self.plan])
        self.assertNotEqual(catalog(self.data,'Movies/a.txt',[])['entries'][0]['id'],
                            catalog(self.data,'Movies/b.txt',[])['entries'][0]['id'])

    def test_bad_markup_rejected(self):
        plan=copy.deepcopy(self.plan);plan['entries'][0]['translation']='字幕文本'
        with self.assertRaisesRegex(ValueError,'markup'):
            catalog(self.data,'Movies/a.txt',[plan])

    def test_overlapping_plans_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlapping'):
            catalog(self.data,'Movies/a.txt',[self.plan,self.plan])

    def test_timing_and_stale_source_rejected(self):
        for key,value in [('end',21),('source_sha256','0'*64)]:
            with self.subTest(key=key):
                plan=copy.deepcopy(self.plan);plan['entries'][0][key]=value
                with self.assertRaisesRegex(ValueError,'source/timing'):
                    catalog(self.data,'Movies/a.txt',[plan])

    def run_export(self, mutation=None):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'disc.iso').write_bytes(self.data)
            profile=dict(schema_version=1,plans=[],sources=[dict(disc=1,path='disc.iso',
                size=len(self.data),sha256=digest(self.data),members=[dict(
                    resource='MC2Game/Movies/a.txt',size=len(self.data),sha256=digest(self.data))])])
            if mutation:
                mutation(profile)
            class FixtureDisc:
                def __init__(inner,path): pass
                def inventory(inner):
                    return [dict(path='MC2Game/Movies/a.txt',directory=False,size=len(self.data),offset=0)]
                def read(inner,offset,size): return self.data
            with patch.object(module,'Disc',FixtureDisc):
                try:
                    result=module.export(root,profile,root/'out')
                except ValueError:
                    self.assertFalse((root/'out').exists())
                    raise
            self.assertEqual(json.loads((root/'out/manifest.json').read_bytes()),result)
            return result

    def test_export_checks_image_and_manifest(self):
        report=self.run_export()
        self.assertEqual((report['catalogs'],report['cues'],report['translated']),(1,1,0))

    def test_image_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,'image size/SHA256'):
            self.run_export(lambda p:p['sources'][0].update(sha256='0'*64))

    def test_missing_movie_member_rejected(self):
        with self.assertRaisesRegex(ValueError,'not closed'):
            self.run_export(lambda p:p['sources'][0].update(members=[]))

    def test_member_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'subtitle SHA256'):
            self.run_export(lambda p:p['sources'][0]['members'][0].update(sha256='0'*64))


if __name__=='__main__':
    unittest.main()
