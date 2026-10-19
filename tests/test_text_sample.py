"""Synthetic layout-sample allocation, capacity and atlas-growth regressions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from tools import supplement_font as s
from tools.prepare_text_sample import allocate
from tools.ue3_package import parse_tables
from test_supplement_font import package_fixture, plan, stored_decoder, NAMES


class TextSampleTests(unittest.TestCase):
    def test_allocator_is_deterministic_disjoint_and_block_aligned(self):
        font = dict(characters=[dict(StartU=0,StartV=0,USize=5,VSize=5,TextureIndex=0)])
        template = dict(texture_index=0,width=8,height=8)
        a = allocate(font,dict(width=32,height=32),'ABC',template)
        self.assertEqual(a,allocate(font,dict(width=32,height=32),'ABC',template))
        self.assertEqual((a[0]['x'],a[0]['y']),(8,0))
        self.assertTrue(all(g['x']%4==g['y']%4==0 for g in a))
        s.validate_placements(font,dict(width=32,height=32),a)

    def test_allocator_capacity_is_explicit(self):
        with self.assertRaisesRegex(ValueError,'insufficient'):
            allocate(dict(characters=[]),dict(width=8,height=8),'AB',dict(texture_index=0,width=8,height=8))

    def test_glyph_count_remains_bounded(self):
        p=plan();p['glyphs']=[dict(p['glyphs'][0],character=chr(0x4e00+i)) for i in range(128)]
        self.assertEqual(len(s.validate_plan(p)),128)
        p['glyphs'].append(dict(p['glyphs'][0],character=chr(0x5000)))
        with self.assertRaisesRegex(ValueError,'1..128'):
            s.validate_plan(p)

    def build(self,p,raw=True,compressed=False):
        original=package_fixture(texture_compressed=compressed)
        return s.supplement_package(original,hashlib.sha256(original).hexdigest(),'General',p,
            {ord(g['character']):bytes([255])*g['width']*g['height'] for g in p['glyphs']},stored_decoder,raw_atlas=raw)

    def test_growth_and_more_than_sixteen_glyphs_preserve_original_pixels(self):
        for compressed in (False,True):
            with self.subTest(compressed=compressed):
                p=plan();p['atlas_height']=256
                p['glyphs']=[dict(p['glyphs'][0],character=chr(0x4e00+i),x=(i%5)*24,y=128+(i//5)*24) for i in range(17)]
                out,r=self.build(p,compressed=compressed)
                self.assertEqual(r['supplemented_glyph_count'],18)
                self.assertTrue(r['atlas_growth']['original_decoded_rows_identical'])
                self.assertTrue(r['original_glyph_rect_pixels_identical'])
                self.assertTrue(r['all_pixels_outside_selected_cells_identical'])
                self.assertTrue(r['original_glyphs_and_remap_preserved'])
                table=parse_tables(out);e=table['exports'][1]
                tex=s.parse_atlas_payload(out[e['serial_offset']:e['serial_offset']+e['serial_size']],NAMES,e['serial_offset'])
                self.assertEqual((tex['width'],tex['height']),(128,256))
                self.assertEqual(tex['mips'][0]['bulk']['element_count'],128*256)

    def test_growth_rejects_shrink_non_power_and_implicit_raw(self):
        for h in (128,192,False,4096):
            p=plan();p['atlas_height']=h
            with self.subTest(height=h),self.assertRaises(ValueError):self.build(p)
        p=plan();p['atlas_height']=256
        with self.assertRaisesRegex(ValueError,'explicit raw_atlas'):self.build(p,False)

    def test_sample_preserves_three_breaks_and_has_unbroken_long_sentence(self):
        root=Path(__file__).resolve().parents[1]
        sample=json.loads((root/'locales/zh-Hans/text-probe-layout.json').read_bytes())
        text=sample['entries'][0]['translation'];parts=text.split('\\n')
        self.assertEqual(len(parts),4)
        self.assertGreater(len(parts[-1]),35)
        self.assertNotIn(' ',parts[-1]);self.assertNotIn('\n',text)
        self.assertTrue(parts[-1].endswith('到这里。'))
        for char in '，。！？（）“”：':self.assertIn(char,text)

    @unittest.skipUnless(importlib.util.find_spec('PIL') and importlib.util.find_spec('fontTools'),'optional raster dependencies')
    def test_shared_baseline_uses_available_last_row_without_clipping(self):
        # Real font not required: mocked cmap/font exercise the union condition.
        from unittest.mock import patch,MagicMock
        import tempfile
        p=plan();p['font_size']=15;p['metric_height']=16
        p['glyphs']=[dict(p['glyphs'][0],width=16,height=16)]
        font=MagicMock();font.getbbox.return_value=(0,-13,15,3)
        image=MagicMock();image.tobytes.return_value=bytes([255])*256;image.getbbox.return_value=(0,0,15,16)
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'font';file.write_bytes(b'fixture')
            with patch('fontTools.ttLib.TTFont') as tt,patch('PIL.ImageFont.truetype',return_value=font),patch('PIL.Image.new',return_value=image),patch('PIL.ImageDraw.Draw'):
                tt.return_value.__enter__.return_value.getBestCmap.return_value={0x4e2d:'sample'}
                _,report=s.rasterize_plan(file,hashlib.sha256(b'fixture').hexdigest(),p)
                self.assertEqual(report[0]['cell_baseline'],13)
                font.getbbox.return_value=(0,-14,15,3)
                with self.assertRaisesRegex(ValueError,'union exceeds'):
                    s.rasterize_plan(file,hashlib.sha256(b'fixture').hexdigest(),p)


if __name__=='__main__':unittest.main()
