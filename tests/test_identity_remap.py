"""Synthetic 256-glyph source; explicit conversion is not runtime acceptance."""
import struct
import unittest
from unittest.mock import patch
from test_supplement_font import NAMES,word,fname,prop,package_fixture,stored_decoder
from tools import supplement_font as s
from tools.ue3_fonts import parse_font_payload
from tools.ue3_package import parse_tables


def payload(tag=False,count=256,metric_height=16):
    metric=dict(StartU=0,StartV=0,USize=4,VSize=metric_height,TextureIndex=0)
    tags=prop('Characters','ArrayProperty',word(count)+s.tagged_glyph(NAMES,metric)*count)+prop('Textures','ArrayProperty',word(1,2))
    if tag:tags+=prop('IsRemapped','IntProperty',word(0))
    native=word(count)+struct.pack('>iiiiB',0,0,4,metric_height,0)*count+word(1,2,0,0,0)
    return word(0)+tags+fname('None')+native


class IdentityRemapTests(unittest.TestCase):
    def test_missing_tag_introduced_and_all_identity_pairs_checked(self):
        out=s.identity_remap_payload(payload(),NAMES);f=parse_font_payload(out,NAMES)
        self.assertTrue(f['is_remapped']);self.assertEqual([(r['codepoint'],r['glyph_index']) for r in f['remap']],list(zip(range(256),range(256))))

    def test_existing_zero_tag_is_changed_without_duplicate(self):
        f=parse_font_payload(s.identity_remap_payload(payload(True),NAMES),NAMES)
        self.assertEqual(sum(p['name']=='IsRemapped' for p in f['properties']),1)

    def test_every_original_native_glyph_byte_and_texture_preserved(self):
        raw=payload();before=parse_font_payload(raw,NAMES);out=s.identity_remap_payload(raw,NAMES);after=parse_font_payload(out,NAMES)
        self.assertEqual(raw[before['native_offset']:before['remap_offset']],out[after['native_offset']:after['remap_offset']])

    def test_every_truncation_rejected(self):
        raw=payload()
        for end in range(0,len(raw),173):
            with self.assertRaises(ValueError):s.identity_remap_payload(raw[:end],NAMES)

    def test_non256_counts_rejected(self):
        for count in [1,255,257]:
            with self.assertRaisesRegex(ValueError,'exactly 256'):s.identity_remap_payload(payload(count=count),NAMES)

    def test_already_remapped_rejected(self):
        with self.assertRaisesRegex(ValueError,'non-remapped'):s.identity_remap_payload(s.identity_remap_payload(payload(),NAMES),NAMES)

    def test_default_append_still_rejects_unmapped(self):
        with self.assertRaisesRegex(ValueError,'existing explicit remap'):s.append_font_payload(payload(),NAMES,[])

    def test_explicit_append_adds_after_256_identity_records(self):
        a=dict(codepoint=0x4e2d,StartU=8,StartV=8,USize=16,VSize=16,TextureIndex=0)
        f=parse_font_payload(s.append_font_payload(payload(),NAMES,[a],'identity-256'),NAMES)
        self.assertEqual((len(f['characters']),len(f['remap'])),(257,257));self.assertEqual(f['remap'][-1]['glyph_index'],256)

    def test_addition_cannot_redefine_existing_identity_codepoint(self):
        a=dict(codepoint=65,StartU=8,StartV=8,USize=16,VSize=16,TextureIndex=0)
        with self.assertRaisesRegex(ValueError,'already mapped'):s.append_font_payload(payload(),NAMES,[a],'identity-256')

    def test_conversion_names_must_exist_uniquely(self):
        missing=list(NAMES);missing[missing.index('IsRemapped')]='unused'
        for names in [NAMES+['IsRemapped'],missing]:
            with self.assertRaisesRegex(ValueError,'unique existing'):s.identity_remap_payload(payload(),names)

    def test_unknown_conversion_rejected(self):
        with self.assertRaisesRegex(ValueError,'unsupported explicit'):s.append_font_payload(payload(),NAMES,[],'guess')

    def test_plan_conversion_is_opt_in_and_exact(self):
        p=dict(schema_version=1,in_game_verified=False,font_size=15,glyphs=[dict(character='中',texture_index=0,x=8,y=8,width=16,height=16)])
        for value in [True,None,'identity-255']:
            with self.assertRaisesRegex(ValueError,'remap_conversion'):s.validate_plan(dict(p,remap_conversion=value))
        self.assertEqual(s.validate_plan(dict(p,remap_conversion='identity-256')),p['glyphs'])

    def test_package_preserves_unaffected_exports_and_records(self):
        with patch('test_supplement_font.font_payload',side_effect=lambda metric_height=24:payload(metric_height=metric_height)):
            raw=package_fixture(font_height=16)
        p=dict(schema_version=1,in_game_verified=False,font_size=15,metric_height=16,remap_conversion='identity-256',
            glyphs=[dict(character='中',texture_index=0,x=8,y=8,width=16,height=16)])
        out,r=s.supplement_package(raw,s.sha256(raw),'General',p,{0x4e2d:bytes([255])*256},stored_decoder)
        self.assertTrue(r['original_glyphs_and_remap_preserved']);self.assertEqual(r['unaffected_exports_byte_identical'],1)
        self.assertFalse(r['remap_conversion']['runtime_equivalence_verified']);self.assertEqual(r['supplemented_glyph_count'],257)

    def test_exact_local_font_class_supported_not_arbitrary_class(self):
        for valid in [True,False]:
            with patch('test_supplement_font.font_payload',side_effect=lambda metric_height=24:payload(metric_height=metric_height)):
                raw=bytearray(package_fixture(font_height=16))
            tables=parse_tables(raw);font=tables['exports'][0];definition=tables['exports'][2]
            struct.pack_into('>I',raw,font['table_offset'],3)
            if valid:struct.pack_into('>I',raw,definition['table_offset']+12,NAMES.index('Font'))
            p=dict(schema_version=1,in_game_verified=False,font_size=15,metric_height=16,remap_conversion='identity-256',
                glyphs=[dict(character='中',texture_index=0,x=8,y=8,width=16,height=16)])
            if valid:
                _,r=s.supplement_package(bytes(raw),s.sha256(raw),'General',p,{0x4e2d:bytes([255])*256},stored_decoder)
                self.assertEqual(r['supplemented_glyph_count'],257)
            else:
                with self.assertRaisesRegex(ValueError,'exactly one Engine.Font'):s.supplement_package(bytes(raw),s.sha256(raw),'General',p,{0x4e2d:bytes([255])*256},stored_decoder)


if __name__=='__main__':unittest.main()
