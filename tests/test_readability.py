import json, unittest, importlib.util, hashlib, tempfile
from pathlib import Path
from tools.translation_style import style_errors
from tools.supplement_font import rasterize_plan

ROOT=Path(__file__).resolve().parents[1]

class ReadabilityTests(unittest.TestCase):
    def test_readability_plan_keeps_story_and_removes_only_four_ui_stops(self):
        load=lambda p:json.loads((ROOT/p).read_bytes())
        old=load('locales/zh-Hans/display-fix.json');new=load('locales/zh-Hans/readability-fix.json')
        kinds={e['id']:e['text_kind'] for e in load('locales/zh-Hans/readability-fix.review.json')['entries']}
        self.assertEqual(len(new['entries']),262)
        changed=[];rules=load('locales/zh-Hans/style-rules.json')
        for a,b in zip(old['entries'],new['entries']):
            self.assertEqual(a['id'],b['id'])
            self.assertFalse(style_errors(dict(b,text_kind=kinds[b['id']]),rules))
            if a!=b:
                self.assertEqual(b['translation'],a['translation'][:-1]);self.assertEqual(kinds[b['id']],'system_message');changed.append(b)
        self.assertEqual(len(changed),4)
        self.assertIn('正在检查下载内容',[e['translation'] for e in changed])
        route=load('locales/zh-Hans/readability-fonts/route.json')
        for ref in [route['text_plan'],*route['font_plans'],*route['additional_text_plans']]:
            self.assertEqual(hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest(),ref['sha256'])
        for ref in route['font_plans']:
            f=load(ref['path']);g=load(f['supplement']['path'])
            self.assertEqual(g['ink_padding'],dict(left=2,right=3))
            self.assertEqual(g['wide_letter_advance'],g['font_size']+5)
            import unicodedata
            for glyph in g['glyphs']:
                c=glyph['character']
                if unicodedata.category(c).startswith('L') and unicodedata.east_asian_width(c) in ('W','F'):
                    self.assertGreaterEqual(glyph['metric_width'],g['wide_letter_advance'])

    def test_current_rule_covers_system_not_just_item_descriptions(self):
        rules=json.loads((ROOT/'locales/zh-Hans/style-rules.json').read_bytes())
        for kind in ['system_message','menu','tutorial','effect_description','name']:
            self.assertTrue(style_errors(dict(translation='正在检查下载内容。',text_kind=kind),rules),kind)
        for kind in ['dialogue','narrative','story_subtitle']:
            self.assertFalse(style_errors(dict(translation='正在检查下载内容。',text_kind=kind),rules),kind)
        for text in ['第一句。\\n第二句。','第一句，第二句。','真的要继续吗？']:
            self.assertFalse(style_errors(dict(translation=text,text_kind='system_message'),rules))

    @unittest.skipUnless(importlib.util.find_spec('PIL') and importlib.util.find_spec('fontTools'),'optional raster libraries')
    def test_explicit_padding_is_respected_not_silently_clamped_to_one(self):
        from unittest.mock import patch, MagicMock
        import io
        from PIL import Image
        p=dict(schema_version=1,in_game_verified=False,font_size=15,metric_height=16,
               ink_padding=dict(left=2,right=3),glyphs=[dict(character='A',texture_index=0,x=8,y=8,width=20,height=16,metric_width=10)])
        # A real alpha mask with a controlled five-pixel stroke width.
        font=MagicMock();font.getbbox.return_value=(0,-8,5,0)
        def draw_text(image,position,*args,**kwargs):
            x,y=position
            for yy in range(y-8,y):
                for xx in range(x,x+5):image.putpixel((xx,yy),255)
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'font';f.write_bytes(b'fixture')
            with patch('fontTools.ttLib.TTFont') as tt,patch('PIL.ImageFont.truetype',return_value=font),patch('PIL.ImageDraw.ImageDraw.text',autospec=True) as draw:
                tt.return_value.__enter__.return_value.getBestCmap.return_value={65:'A'}
                draw.side_effect=lambda self,pos,*a,**kw:draw_text(self._image,pos)
                alphas,reports=rasterize_plan(f,hashlib.sha256(b'fixture').hexdigest(),p)
            bbox=reports[0]['raster_bbox']
            self.assertEqual(bbox[0],2)
            self.assertEqual(p['glyphs'][0]['metric_width']-bbox[2],3)

if __name__=='__main__':unittest.main()
