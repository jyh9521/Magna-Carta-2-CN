"""Typography-only fixture tests: no native media or background restoration."""
import copy
import unittest

import numpy as np

from tools.texture_appearance import render
from tools.video_title_caption import render_title_layer
from test_texture_render_windows import owned_font


class MovieTitleTypographyTests(unittest.TestCase):
    def setUp(self):
        self.font=owned_font()
        self.appearance=dict(kind='source-style-v1',ink_box=[8,10,112,22],align='center',
            gradient=[[0,[220,141,142,255]],[1000,[255,250,224,255]]],
            outline=[8,5,5,245],outline_width=.75,glow=[0,0,0,0],glow_radius=0,
            shadow=[0,0,0,210],shadow_offset=[1,1],shadow_radius=.5,
            italic=0,tracking=3,weight=0,motion=0)

    def test_helper_reuses_existing_source_style_renderer_byte_for_byte(self):
        actual,proof=render_title_layer(self.font,'AB',(128,48),font_size=22,appearance=self.appearance)
        expected=render(self.font,dict(id='owned',text='AB',rect=[0,0,128,48],font_size=22,appearance=self.appearance))
        self.assertEqual(actual.tobytes(),expected)
        self.assertEqual(proof['render_method'],'source-style-v1')
        self.assertEqual(proof['appearance']['tracking'],3)

    def test_tracking_is_explicit_and_does_not_change_visible_glyph_height(self):
        thin=copy.deepcopy(self.appearance);thin.update(outline_width=0,shadow=[0,0,0,0],tracking=0)
        a,_=render_title_layer(self.font,'AB',(128,48),font_size=22,appearance=thin)
        thin['tracking']=8
        b,_=render_title_layer(self.font,'AB',(128,48),font_size=22,appearance=thin)
        aa=np.asarray(a.getchannel('A'))>200;bb=np.asarray(b.getchannel('A'))>200
        ay,ax=np.where(aa);by,bx=np.where(bb)
        self.assertEqual((int(ay.min()),int(ay.max())),(int(by.min()),int(by.max())))
        self.assertGreater(int(bx.max()-bx.min()),int(ax.max()-ax.min()))

    def test_font_inputs_and_locale_appearance_are_not_mutated(self):
        before=copy.deepcopy(self.appearance)
        a,p=render_title_layer(self.font,'AB',(128,48),font_size=22,appearance=self.appearance)
        b,q=render_title_layer(self.font,'AB',(128,48),font_size=22,appearance=self.appearance)
        self.assertEqual(self.appearance,before)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertEqual(p,q)

    def test_unsupported_glyphs_and_unknown_style_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            render_title_layer(self.font,'C',(128,48),font_size=22,appearance=self.appearance)
        bad={**self.appearance,'invented_effect':1}
        with self.assertRaises(ValueError):
            render_title_layer(self.font,'AB',(128,48),font_size=22,appearance=bad)

    def test_invalid_canvas_font_and_empty_layer_requests_fail(self):
        for canvas in ((0,48),(1921,48),(128,1081),(True,48),(128,48.0)):
            with self.subTest(canvas=canvas),self.assertRaises(ValueError):
                render_title_layer(self.font,'AB',canvas,font_size=22,appearance=self.appearance)
        with self.assertRaises(ValueError):
            render_title_layer(b'','AB',(128,48),font_size=22,appearance=self.appearance)
        with self.assertRaises(ValueError):
            render_title_layer(self.font,'',(128,48),font_size=22,appearance=self.appearance)


if __name__=='__main__':unittest.main()
