import unittest
from PIL import Image
from tools.texture_overlay import render_label
from tools.texture_appearance import validate
from test_texture_render_windows import owned_font


class EffectClipTests(unittest.TestCase):
    def fixture(self):
        a=dict(kind='source-style-v1',ink_box=[4,4,24,16],align='left',
            gradient=[[0,[255]*4],[1000,[255]*4]],outline=[0,0,0,255],outline_width=1,
            glow=[0,0,0,0],glow_radius=0,shadow=[0,0,0,255],shadow_offset=[1,4],
            shadow_radius=1,italic=0,tracking=0,weight=0,motion=0)
        return dict(id='owned',text='A',rect=[0,0,32,32],font_size=18,appearance=a)

    def test_clip_only_effects_and_keeps_glyphs(self):
        label=self.fixture();before=Image.frombytes('RGBA',(32,32),render_label(owned_font(),label))
        self.assertGreater(before.getchannel('A').crop((0,22,32,32)).getextrema()[1],0)
        label['appearance']['effect_clip']=[0,0,32,22]
        after=Image.frombytes('RGBA',(32,32),render_label(owned_font(),label))
        self.assertEqual(after.crop((0,0,32,22)).tobytes(),before.crop((0,0,32,22)).tobytes())
        self.assertEqual(after.getchannel('A').crop((0,22,32,32)).getextrema()[1],0)

    def test_glyph_crop_fails_instead_of_hiding_missing_text(self):
        label=self.fixture();label['appearance']['effect_clip']=[0,0,32,8]
        with self.assertRaisesRegex(ValueError,'crop glyph ink'):render_label(owned_font(),label)

    def test_invalid_windows_fail_closed(self):
        for clip in ([0,0,33,32],[0,0,32,0],[-1,0,32,32],[0,0,32.,32],[0,0,32]):
            a=self.fixture()['appearance'];a['effect_clip']=clip
            with self.assertRaises(ValueError):validate(a,32,32)
