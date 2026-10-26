"""The real label entry point must retain source-derived multicolour lettering."""
import unittest
from pathlib import Path
from PIL import Image
from tools.texture_overlay import render_label
from tools.ue3_package import FormatError


class AppearanceTests(unittest.TestCase):
    def setUp(self):
        # Same self-authored, installed test font used by the existing fixtures.
        from test_texture_render_windows import owned_font
        self.font = owned_font()

    def label(self):
        return dict(text='ABAB', rect=[0, 0, 160, 64], font_size=32,
                    appearance=dict(kind='source-style-v1', ink_box=[8, 8, 144, 40],
                                    align='center', gradient=[[0, [255, 50, 20, 255]],
                                                             [1000, [20, 80, 255, 255]]],
                                    outline=[0, 0, 0, 255], outline_width=0,
                                    glow=[0, 0, 0, 0], glow_radius=0,
                                    shadow=[0, 0, 0, 0], shadow_offset=[0, 0],
                                    shadow_radius=0, italic=0, tracking=0,
                                    weight=0, motion=0))

    def test_gradient_reaches_real_label_entrypoint(self):
        im=Image.frombytes('RGBA',(160,64),render_label(self.font,self.label()))
        top=[p for y in range(8,20) for x in range(160) if (p:=im.getpixel((x,y)))[3]>220]
        bottom=[p for y in range(35,48) for x in range(160) if (p:=im.getpixel((x,y)))[3]>220]
        self.assertTrue(top and bottom)
        self.assertGreater(sum(p[0]-p[2] for p in top)/len(top),80)
        self.assertLess(sum(p[0]-p[2] for p in bottom)/len(bottom),-80)

    def test_unknown_fields_are_not_silently_ignored(self):
        label=self.label();label['appearance']['mystery']=1
        with self.assertRaises(FormatError):render_label(self.font,label)

    def test_italic_changes_real_raster(self):
        label=self.label();a=render_label(self.font,label)
        label['appearance']['italic']=0.24
        self.assertTrue(a!=render_label(self.font,label))

    def test_preserve_source_layer_is_empty(self):
        label=self.label();label['appearance']={'kind':'preserve-source-v1'}
        self.assertEqual(set(render_label(self.font,label)),{0})

    def test_gradient_survives_native_bc3_roundtrip(self):
        from tools.texture_layout import unit_layout,decode_texture
        from tools.texture_overlay import overlay_profile_regions
        label=self.label();label['rect']=[0,0,128,64]
        label['appearance']['ink_box']=[8,8,112,40]
        layout=unit_layout(128,64,7)
        tx=dict(layout=layout,width=128,height=64,format=7,tiles=bytes(layout['storage_bytes']))
        edit=dict(regions=['owned'],image_id='owned',channel_mode='rgba',profile=dict(kind='xbox-inline-bc-v1',format=7))
        raw,proof=overlay_profile_regions(tx,edit,{'owned':(label,render_label(self.font,label))})
        rgba=decode_texture(tx,raw)
        self.assertTrue(any(rgba[i+3]>200 and rgba[i]-rgba[i+2]>100 for i in range(0,len(rgba),4)))
        self.assertTrue(any(rgba[i+3]>200 and rgba[i+2]-rgba[i]>100 for i in range(0,len(rgba),4)))
        self.assertTrue(proof['untouched_blocks_preserved'])

    def test_source_preservation_is_explicit_and_native_exact(self):
        from test_texture_layout import profile_fixture
        from test_supplement_font import stored_decoder
        from tools.texture_overlay import patch_package,digest
        raw,e,layers=profile_fixture(7);label=layers['x'][0]
        label.update(appearance={'kind':'preserve-source-v1'},
                     restoration={'source_rgba_sha256':digest(bytes(256))},
                     _repair_mask=bytes([255])+bytes(63),_repair_pixels=bytes(256))
        e['preserve_unchanged_blocks']=True
        layers['x']=(label,bytes(256))
        out,proof=patch_package(raw,digest(raw),[e],layers,stored_decoder)
        self.assertEqual(out,raw);self.assertTrue(proof['textures'][0]['original_pixels_preserved'])
        label.pop('appearance')
        with self.assertRaisesRegex(FormatError,'no-op'):patch_package(raw,digest(raw),[e],layers,stored_decoder)


if __name__=='__main__':unittest.main()
