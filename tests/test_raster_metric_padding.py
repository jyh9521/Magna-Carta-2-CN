"""A block-aligned atlas cell may be taller than its visible glyph metric."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock,patch
from tools.supplement_font import rasterize_plan,sha256


@unittest.skipUnless(importlib.util.find_spec('PIL') and importlib.util.find_spec('fontTools'),'optional raster dependencies')
class RasterPaddingTests(unittest.TestCase):
    def run_plan(self,bbox):
        plan=dict(schema_version=1,font_size=27,metric_height=29,in_game_verified=False,
            glyphs=[dict(character='中',texture_index=3,x=0,y=0,width=32,height=32)])
        font=MagicMock();font.getbbox.return_value=bbox
        image=MagicMock();image.tobytes.return_value=bytes([255])*1024
        image.getbbox.return_value=(0,0,27,29)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'font';p.write_bytes(b'fixture')
            with patch('fontTools.ttLib.TTFont') as tt,patch('PIL.ImageFont.truetype',return_value=font),patch('PIL.Image.new',return_value=image),patch('PIL.ImageDraw.Draw'):
                tt.return_value.__enter__.return_value.getBestCmap.return_value={ord('中'):'glyph'}
                return rasterize_plan(p,sha256(b'fixture'),plan)

    def test_cell_padding_does_not_force_baseline_below_metric(self):
        _,reports=self.run_plan((0,-24,27,4))
        self.assertEqual(reports[0]['cell_baseline'],25)

    def test_true_union_overflow_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'union exceeds'):self.run_plan((0,-26,27,4))


if __name__=='__main__':unittest.main()
