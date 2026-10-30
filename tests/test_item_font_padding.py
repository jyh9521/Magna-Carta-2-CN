import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools.fit_font_padding import fit, sha
from tools.audit_font_optical_size import Sampler
from tools.reface_font import reface
from tools.ue3_fonts import read_properties
from tools.ue3_package import Reader
from tools.audit_item_spacing import item_name, names_from_banks, is_wide_letter, installer_item_sources
from test_render_font_comparison import font_fixture
from test_supplement_font import package_fixture


class ItemFontPaddingTests(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        face=Path(temp.name)/'face.ttf';font_fixture(face)
        raw=package_fixture();sample=Sampler(raw,'General')
        e=next(e for e in sample.ctx['tables']['exports'] if e['path']=='General')
        start=e['serial_offset'];g=sample.font['characters'][0]
        payload=raw[start:start+e['serial_size']];r=Reader(payload);r.seek(g['tagged_offset'])
        out=bytearray(raw)
        for p in read_properties(r,sample.ctx['tables']['names']):
            if p['name']=='USize':struct.pack_into('>I',out,start+p['value_offset'],32)
        struct.pack_into('>I',out,start+g['native_offset']+8,32)
        before,_=reface(bytes(out),sha(out),'General',face,sha(face.read_bytes()),
                        dict(font_size=15,metric_height=24,wide_advance=20,texture_index=0,
                             stroke_em=.006,shadow=True,codepoints=[65]))
        return before

    def test_trim_preserves_every_aa_shadow_pixel_and_entire_atlas(self):
        before=self.fixture();after,proof=fit(before,sha(before),'General',[65])
        a,b=Sampler(before,'General'),Sampler(after,'General')
        old,new=a.glyph(65),b.glyph(65)
        self.assertLess(new.width,old.width)
        self.assertEqual(new.getchannel('A').getbbox()[0],2)
        self.assertEqual(new.width-new.getchannel('A').getbbox()[2],3)
        self.assertEqual(old.crop(old.getchannel('A').getbbox()).tobytes(),
                         new.crop(new.getchannel('A').getbbox()).tobytes())
        self.assertEqual(a.mapping,b.mapping)
        self.assertEqual(a.font['characters'][0]['StartV'],b.font['characters'][0]['StartV'])
        self.assertEqual(a.font['characters'][0]['VSize'],b.font['characters'][0]['VSize'])
        for s in (a,b):s.glyph(65)
        self.assertEqual(a.atlases[0][1],b.atlases[0][1])
        self.assertTrue(proof['atlases_byte_identical'])
        again,_=fit(after,sha(after),'General',[65]);self.assertEqual(again,after)

    def test_source_selection_and_margin_guards(self):
        data=self.fixture()
        with self.assertRaisesRegex(ValueError,'SHA256'):fit(data,'0'*64,'General',[65])
        for cps in ([],[65,65],[True],[66],[-1]):
            with self.assertRaises(ValueError):fit(data,sha(data),'General',cps)
        for margin in (0,True,9):
            with self.assertRaises(ValueError):fit(data,sha(data),'General',[65],margin,3)

    def test_locale_profiles_cover_all_names_and_all_seven_font_aliases(self):
        root=Path(__file__).resolve().parents[1]
        plan=json.loads((root/'locales/zh-Hans/item-font-padding-v11.json').read_bytes())
        audit=json.loads((root/'locales/zh-Hans/item-spacing-audit-v11.json').read_bytes())
        self.assertEqual(len(plan['codepoints']),595)
        self.assertEqual(sum(b['expected_names'] for b in audit['banks']),689)
        self.assertEqual(sum(b['expected_fields'] for b in audit['banks']),1939)
        self.assertEqual(audit['dlc']['expected_names'],12)
        self.assertEqual({(s['resource'],f['object']) for s in plan['sources'] for f in s['fonts']},
                         {(f['resource'],f['object']) for f in audit['fonts']})
        self.assertEqual(len(audit['fonts']),7)
        self.assertTrue(all(ord(c) in plan['codepoints'] for c in '赤月斧白弓'))


class ItemInventoryTests(unittest.TestCase):
    def test_installer_view_reads_original_and_overlaid_packages_without_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);image=root/'source.iso';image.write_bytes(b'original')
            overlay=root/'changed.xxx';overlay.write_bytes(b'changed')
            recipe=root/'recipe.json'
            entry=dict(iso=str(image),sha256=sha(image.read_bytes()),resources=[
                dict(path='MC2Game/CookedXenon/A.xxx',file=str(overlay),sha256=sha(overlay.read_bytes()))])
            recipe.write_text(json.dumps(dict(discs=[entry,entry])))
            before={p.name for p in root.iterdir()}
            with patch('tools.audit_item_spacing.Disc') as disc:
                disc.return_value.inventory.return_value=[
                    dict(path='MC2Game/CookedXenon/A.xxx',directory=False,offset=0,size=8),
                    dict(path='MC2Game/CookedXenon/B.xxx',directory=False,offset=8,size=4),
                    dict(path='default.xex',directory=False,offset=12,size=4)]
                disc.return_value.read.return_value=b'base'
                result=list(installer_item_sources(recipe,sha(recipe.read_bytes()),2))
                self.assertEqual(result,[('MC2Game/CookedXenon/A.xxx',b'changed'),
                                         ('MC2Game/CookedXenon/B.xxx',b'base')])
                disc.return_value.read.assert_called_once_with(8,4)
                overlay.write_bytes(b'altered')
                with self.assertRaisesRegex(ValueError,'resource identity'):
                    list(installer_item_sources(recipe,sha(recipe.read_bytes()),2))
            self.assertEqual(before,{p.name for p in root.iterdir()})

    def test_installer_view_checks_recipe_and_original_identity_before_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);image=root/'source.iso';image.write_bytes(b'original')
            recipe=root/'recipe.json';entry=dict(iso=str(image),sha256='0'*64,resources=[])
            recipe.write_text(json.dumps(dict(discs=[entry,entry])))
            with patch('tools.audit_item_spacing.Disc') as disc:
                with self.assertRaisesRegex(ValueError,'recipe identity'):
                    list(installer_item_sources(recipe,'0'*64,1))
                with self.assertRaisesRegex(ValueError,'original disc identity'):
                    list(installer_item_sources(recipe,sha(recipe.read_bytes()),1))
                with self.assertRaisesRegex(ValueError,'disc selection'):
                    list(installer_item_sources(recipe,sha(recipe.read_bytes()),3))
                disc.assert_not_called()

    def fixture(self):
        names=['None','ItemName','StrProperty','RelatedQuestID','IntProperty']
        word=lambda *ns:struct.pack('>'+'I'*len(ns),*ns)
        text=b'<Strings:Items.Weapons.Name>\0'
        prop=word(1,0,2,0,len(text)+4,0)+word(len(text))+text
        numbered=word(3,3,4,0,4,0,47)
        return names,word(0),prop,numbered,word(0,0)

    def test_numbered_quest_property_cannot_hide_a_valid_name(self):
        n,p,name,tail,end=self.fixture()
        self.assertEqual(item_name(p+name+tail+end,n),'<Strings:Items.Weapons.Name>')

    def test_duplicate_name_or_truncated_record_fails(self):
        n,p,name,tail,end=self.fixture()
        with self.assertRaises(ValueError):item_name(p+name+name+end,n)
        with self.assertRaises(ValueError):item_name(p+name+tail[:-2],n)
        self.assertIsNone(item_name(p+tail+end,n))

    def test_all_occurrences_are_audited_not_deduplicated(self):
        fields=[dict(id='a',embedded_path='X/Items.int',section='Weapons',key='sword'),
                dict(id='b',embedded_path='X/Items.int',section='Weapons',key='sword'),
                dict(id='c',embedded_path='X/Items.int',section='Weapons',key='sword_D')]
        bank=dict(file='Items.int',sections=None,description_suffixes=['_d','_s'],expected_fields=3,expected_names=2)
        rows,total=names_from_banks(fields,[bank]);self.assertEqual(total,3);self.assertEqual(len(rows),2)
        changed=copy.deepcopy(bank);changed['expected_names']=1
        with self.assertRaises(ValueError):names_from_banks(fields,[changed])
        with self.assertRaises(ValueError):names_from_banks(fields,[bank,bank])

    def test_spacing_is_not_a_language_specific_translation_rewrite(self):
        self.assertTrue(is_wide_letter('月'));self.assertTrue(is_wide_letter('가'))
        self.assertFalse(is_wide_letter(' '));self.assertFalse(is_wide_letter('1'))
        self.assertFalse(is_wide_letter('，'))

    def test_font_overlay_cannot_change_face_height_or_unlocked_source(self):
        from tools.audit_dlc_localization import layout_with_font_metrics
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);base=root/'layout.json';overlay=root/'fonts.json'
            profile={'fonts':{'general':{'resource':'Font.xxx','object':'General','max_glyph_height':25,
                                          'advances_sha256':'a'*64}},'families':[]}
            base.write_text(json.dumps(profile),encoding='utf8')
            updated=copy.deepcopy(profile['fonts']);updated['general']['advances_sha256']='b'*64
            data={'kind':'font-metrics-overlay','schema_version':1,'base_layout_sha256':sha(base.read_bytes()),
                  'fonts':updated}
            overlay.write_text(json.dumps(data),encoding='utf8')
            self.assertEqual(layout_with_font_metrics(base,overlay)['fonts'],updated)
            self.assertEqual(layout_with_font_metrics(base),profile)
            data['fonts']['general']['max_glyph_height']=26
            overlay.write_text(json.dumps(data),encoding='utf8')
            with self.assertRaises(ValueError):layout_with_font_metrics(base,overlay)
            data['base_layout_sha256']='0'*64
            overlay.write_text(json.dumps(data),encoding='utf8')
            with self.assertRaises(ValueError):layout_with_font_metrics(base,overlay)


if __name__=='__main__':unittest.main()
