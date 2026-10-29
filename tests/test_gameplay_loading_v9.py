"""Both left and right indicator layouts must retain their original destination."""
import copy,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class LoadingPlanContractTests(unittest.TestCase):
    def test_caption_art_styles_and_destination_translation_are_retained(self):
        old=json.loads((ROOT/'locales/zh-Hans/loading-captions-v7.json').read_bytes())
        new=json.loads((ROOT/'locales/zh-Hans/loading-captions-v9.json').read_bytes())
        self.assertEqual(old['fonts'],new['fonts']);self.assertEqual(old['rasterizer_versions'],new['rasterizer_versions'])
        self.assertEqual(len(old['entries']),15);self.assertEqual(len(new['entries']),15)
        for a,b in zip(old['entries'],new['entries']):
            with self.subTest(movie=a['id']):
                self.assertEqual(a['source'],b['source'])
                for c,d in zip(a['captions'],b['captions']):
                    if c['role']!='indicator':self.assertEqual(c,d);continue
                    self.assertEqual(c['style'],d['style']);self.assertEqual(c['text'],d['text'])
                    self.assertEqual(d['erase']['rect'][:2],[c['erase']['rect'][0]+2,c['erase']['rect'][1]-3])
                    self.assertEqual(d['erase']['rect'][2:],[192,40])
                    self.assertEqual(d['erase']['reference']['sampling'],'all-frames-union')
                    self.assertEqual(d['erase']['radius'],8)
                    old_offset=[x-y for x,y in zip(c['erase']['rect'][:2],c['erase']['reference']['rect'][:2])]
                    new_offset=[x-y for x,y in zip(d['erase']['rect'][:2],d['erase']['reference']['rect'][:2])]
                    self.assertEqual(old_offset,new_offset)
