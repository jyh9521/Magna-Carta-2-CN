import copy
import json
from pathlib import Path
import unittest

from tools.lettering_layers import font_ink, effects
from test_texture_render_windows import owned_font


class MapTitleColourTests(unittest.TestCase):
    def layer(self):
        root=Path(__file__).resolve().parents[1]
        plan=json.loads((root/'locales/zh-Hans/texture-overlays/map-lettering-v19.json').read_bytes())
        return next(l for r in plan['resources']for t in r['textures']for s in t['islands']
                    for l in s['layers']if l['id']=='normal_map_terrain_map_view_oldfox_02')

    def test_reported_map_title_lower_ink_stays_red_not_neutral(self):
        layer=self.layer();label=copy.deepcopy(layer['label']);label['text']='AB'
        ink=font_ink(owned_font(),label);x,y,w,h=label['appearance']['ink_box']
        pixels=[ink.getpixel((xx,yy))for yy in range(y+round(h*.75),y+h)
                for xx in range(ink.width)if ink.getpixel((xx,yy))[3]>=200]
        self.assertTrue(pixels)
        self.assertTrue(all(r>=2*g and r>=3*b for r,g,b,a in pixels),
                        'reported lower glyph band must remain orange-red / deep red, not white or grey')

    def test_colour_does_not_change_glyph_or_effect_alpha(self):
        layer=self.layer();a=copy.deepcopy(layer['label']);a['text']='AB';b=copy.deepcopy(a)
        b['appearance']['gradient']=[[0,[255,255,255,255]],[1000,[255,255,255,255]]]
        font=owned_font();ia,ib=font_ink(font,a),font_ink(font,b)
        self.assertEqual(ia.getchannel('A').tobytes(),ib.getchannel('A').tobytes())
        _,pa=effects(ia,layer['effects']);_,pb=effects(ib,layer['effects'])
        for key in ('outline','shadow'):
            self.assertEqual(pa[key].tobytes(),pb[key].tobytes())
