import copy
import tempfile
from pathlib import Path
import unittest

from tools import reface_font as ref
from tools.build_font_supplement import context
from tools.supplement_font import parse_atlas_payload, atlas_tiles
from tools.ue3_fonts import parse_font_payload
from tools.ue3_textures import untile_dxt5, decode_dxt5
from tools.texture_overlay import rgba_crop
from test_render_font_comparison import font_fixture
from test_supplement_font import package_fixture


class FontRefaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.font=Path(self.temp.name)/'face.ttf';font_fixture(self.font)
        self.hash=ref.sha(self.font.read_bytes())
        self.spec=dict(font_size=15,metric_height=24,wide_advance=20,
                       texture_index=0,stroke_em=.006,shadow=True,codepoints=[65])

    def test_native_bc3_roundtrip_matches_selected_outline(self):
        before=package_fixture()
        after,proof=ref.reface(before,ref.sha(before),'General',self.font,self.hash,self.spec)
        ctx=context(after,None);e=next(e for e in ctx['tables']['exports'] if e['path']=='General')
        font=parse_font_payload(after[e['serial_offset']:e['serial_offset']+e['serial_size']],ctx['tables']['names'])
        metric=font['characters'][0];ae=ctx['tables']['exports'][font['textures'][0]-1]
        at=ae['serial_offset'];payload=after[at:at+ae['serial_size']]
        t=parse_atlas_payload(payload,ctx['tables']['names'],at)
        pixels=decode_dxt5(untile_dxt5(atlas_tiles(payload,t,None),t['width'],t['height']),t['width'],t['height'])
        row=proof['glyphs'][0]
        actual=rgba_crop(pixels,t['width'],[metric['StartU'],metric['StartV'],row['width'],row['height']])
        self.assertEqual(ref.sha(actual),row['rgba_sha256'])
        self.assertNotEqual(before,after);self.assertEqual(len(before),len(after))
        self.assertTrue(proof['unselected_exports_preserved'])

    def test_input_and_face_guards(self):
        for data_hash,font_hash in [('0'*64,self.hash),(ref.sha(package_fixture()),'0'*64)]:
            with self.assertRaisesRegex(ValueError,'SHA256'):
                ref.reface(package_fixture(),data_hash,'General',self.font,font_hash,self.spec)

    def test_missing_source_and_selection_rejected(self):
        s=copy.deepcopy(self.spec);s['codepoints']=[66]
        with self.assertRaisesRegex(ValueError,'selection'):
            ref.reface(package_fixture(),ref.sha(package_fixture()),'General',self.font,self.hash,s)
        with self.assertRaisesRegex(ValueError,'missing source'):
            ref.raster_cells(self.font,self.hash,s,[67],{67:20})

    def test_explicit_alias_keeps_requested_codepoint(self):
        s=copy.deepcopy(self.spec);s['glyph_aliases']={'Ａ':'A'}
        cells=ref.raster_cells(self.font,self.hash,s,[0xff21],{0xff21:20})
        self.assertEqual(cells[0]['codepoint'],0xff21)
        self.assertEqual(cells[0]['source_character'],'A')

    def test_capacity_and_reserved_glyphs(self):
        c=[dict(width=8,height=8),dict(width=8,height=8)]
        preserved=[dict(StartU=0,StartV=0,USize=8,VSize=8)]
        placed=ref.place_cells(16,16,preserved,c)
        self.assertEqual((placed[0]['x'],placed[0]['y']),(8,0))
        with self.assertRaisesRegex(ValueError,'capacity'):
            ref.place_cells(4,4,[],[dict(width=8,height=8)])


if __name__=='__main__':unittest.main()
