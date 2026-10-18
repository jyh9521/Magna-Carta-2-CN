"""Synthetic namespace aliases, atlas data and prototype chains only."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_supplement_font import NAMES, font_payload, atlas_payload, stored_decoder
from test_ui_style_graph import Fixture, word
from tools.supplement_font import append_font_payload
from tools.ue3_package import parse_tables,parse_summary
from tools.ue3_ui_styles import StyleGraph
from tools.font_binding_audit import fingerprint,audit_font_candidates
from tools.inspect_ui_fonts import main


def alias_package(net_index=0, height=24, compressed_atlas=False):
    names=NAMES+['Assets'];fn=lambda name:word(names.index(name),0)
    string=lambda value:word(len(value)+1)+value.encode()+b'\0'
    nt=b''.join(string(n)+bytes(8) for n in names)
    im=fn('Core')+fn('Package')+word(0)+fn('Engine')
    im+=fn('Core')+fn('Class')+word(-1)+fn('Font')
    im+=fn('Core')+fn('Class')+word(-1)+fn('Texture2D')
    im+=fn('Core')+fn('Package')+word(0)+fn('Core')
    im+=fn('Core')+fn('Class')+word(-4)+fn('Package')
    exoff=101+len(nt)+len(im);headsize=exoff+3*68
    font=append_font_payload(font_payload(height),names,[dict(codepoint=0x4e2d,StartU=8,StartV=0,USize=4,VSize=24,TextureIndex=0)])
    font=word(net_index)+font[4:]
    atlas=atlas_payload(headsize+len(font),compressed_atlas)
    root=word(0)+fn('None')
    def export(cls,name,outer,size,offset,guid=bytes(16)):
        return word(cls,0,outer)+fn(name)+word(0)+bytes(8)+word(size,offset,0,1,0)+guid
    ex=export(-2,'General',3,len(font),headsize)+export(-3,'Atlas',1,len(atlas),headsize+len(font))
    ex+=export(-5,'Assets',0,len(root),headsize+len(font)+len(atlas),bytes.fromhex('a'*32))
    header=b'\x9e\x2a\x83\xc1'+word((25<<16)|446,headsize)+string('None')
    header+=word(0,len(names),101,3,exoff,5,101+len(nt),0)+bytes(16)+word(1,3,len(names),0,3004,42,0,0)
    return header+nt+im+ex+font+atlas+root


def context(data):
    return dict(logical=data,tables=parse_tables(data),sha256=hashlib.sha256(data).hexdigest(),package_guid=parse_summary(data)['guid'])


class BindingAuditTests(unittest.TestCase):
    def test_forced_namespace_root_guid_and_same_semantics(self):
        a,b=alias_package(1),alias_package(2)
        graph=StyleGraph(dict(one=context(a),two=context(b)))
        report=audit_font_candidates(graph,[('one',1)])
        group,=report['groups'];self.assertEqual(group['candidate_count'],2)
        self.assertTrue(group['same_known_namespace_guid']);self.assertTrue(group['all_supplied_candidates_semantically_equal'])
        self.assertEqual(group['canonical_path'],'assets.general')
        self.assertEqual(len({x['payload_sha256'] for x in group['fingerprints']}),2)
        self.assertEqual(len({x['semantic_sha256'] for x in group['fingerprints']}),1)
        self.assertFalse(group['runtime_precedence_resolved'])

    def test_raw_compressed_atlas_semantic_equivalence(self):
        graph=StyleGraph(dict(one=context(alias_package()),two=context(alias_package(compressed_atlas=True))))
        a=fingerprint(graph,('one',1),stored_decoder);b=fingerprint(graph,('two',1),stored_decoder)
        self.assertEqual(a['semantic_sha256'],b['semantic_sha256'])
        with self.assertRaisesRegex(ValueError,'decoder'):fingerprint(graph,('two',1))

    def test_different_glyph_or_atlas_detected(self):
        a=alias_package();b=alias_package(height=20)
        graph=StyleGraph(dict(one=context(a),two=context(b)))
        group,=audit_font_candidates(graph,[('one',1)])['groups']
        self.assertFalse(group['all_supplied_candidates_semantically_equal'])
        c=context(a);font=c['tables']['exports'][1];raw=bytearray(a)
        from tools.supplement_font import parse_atlas_payload
        meta=parse_atlas_payload(a[font['serial_offset']:font['serial_offset']+font['serial_size']],c['tables']['names'],font['serial_offset'])
        at=font['serial_offset']+meta['mips'][0]['bulk']['payload_offset'];raw[at]^=1
        self.assertNotEqual(fingerprint(StyleGraph(dict(one=context(a))),('one',1))['semantic_sha256'],fingerprint(StyleGraph(dict(one=context(bytes(raw)))),('one',1))['semantic_sha256'])

    def test_unknown_or_conflicting_guid_not_silently_matched(self):
        a=context(alias_package());b=copy.deepcopy(a);b['tables']['exports'][2]['guid']='b'*32
        group,=audit_font_candidates(StyleGraph(dict(one=a,two=b)),[('one',1)])['groups']
        self.assertFalse(group['same_known_namespace_guid']);self.assertEqual(group['candidate_count'],2)
        b['tables']['exports'][2]['guid']='0'*32
        group,=audit_font_candidates(StyleGraph(dict(one=a,two=b)),[('one',1)])['groups']
        self.assertFalse(group['same_known_namespace_guid'])

    def test_identity_outer_cycle_non_package_and_import_guard(self):
        for outer,kind in [(1,'Core.Package'),(-1,'Core.Package'),(0,'Engine.Font')]:
            c=context(alias_package());c['tables']['exports'][2]['outer']=outer;c['tables']['exports'][2]['class_path']=kind
            with self.assertRaises(ValueError):StyleGraph(dict(one=c)).canonical_identity(('one',1))

    def test_standalone_namespace_uses_supplied_package_identity(self):
        c=context(alias_package());c['tables']['exports'][0].update(path='General',outer=0,export_flags=0)
        c['package_guid']='c'*32
        i=StyleGraph(dict(Assets=c)).canonical_identity(('assets',1))
        self.assertEqual(i['canonical_path'],'assets.general');self.assertEqual(i['namespace_guid'],'c'*32)
        self.assertFalse(i['forced_export'])

    def test_wrong_font_atlas_and_truncation_guards(self):
        for what in ['font-class','atlas-class','atlas-bounds','font-bounds']:
            c=context(alias_package())
            if what=='font-class':c['tables']['exports'][0]['class_path']='Engine.MultiFont'
            elif what=='atlas-class':c['tables']['exports'][1]['class_path']='Engine.Font'
            elif what=='atlas-bounds':c['tables']['exports'][1]['serial_size']+=100000
            else:c['tables']['exports'][0]['serial_size']=3
            with self.subTest(what=what),self.assertRaises(ValueError):fingerprint(StyleGraph(dict(one=c)),('one',1))

    def test_archetype_null_never_implies_zero_override(self):
        p=Fixture().build();g=StyleGraph(p);r=g.archetype_audit(('sample',2))
        self.assertEqual(r['explicit_archetypes']['termination'],'null-archetype')
        self.assertFalse(r['effective_values_resolved']);self.assertTrue(r['unresolved'])
        self.assertFalse(any('DrawFont' in str(q) for q in r['explicit_archetypes']['nodes'][0]['fields']))

    def test_explicit_archetypes_incompatible_cycle_and_unresolved_import(self):
        for ref in [2,1,-99]:
            p=Fixture().build();p['sample']['tables']['exports'][1]['archetype']=ref
            r=StyleGraph(p).archetype_audit(('sample',2))
            self.assertEqual(r['explicit_archetypes']['termination'],'unresolved')

    def test_cdo_selected_by_flag_and_class_not_name(self):
        f=Fixture();p=f.build();engine=p['engine'];engine['tables']['names']=f.names
        body=word(0)+f.props();engine['logical']=body
        engine['tables']['exports'].append(dict(path='NotNamedDefault',class_path='UIComp_DrawString',
            serial_offset=0,serial_size=len(body),outer=0,archetype=0,super=0,object_flags='0000000000000200',**{'class':3}))
        r=StyleGraph(p).archetype_audit(('sample',2))
        self.assertEqual(len(r['class_default_candidates']),1)
        self.assertEqual(r['class_default_candidates'][0]['nodes'][0]['owner']['path'],'NotNamedDefault')
        self.assertEqual(r['unresolved'],[])

    def test_ambiguous_cdo_candidates_retained(self):
        f=Fixture();p=f.build();p['engine']['tables']['names']=f.names;p['engine']['logical']=word(0)+f.props()
        for name in ['First','Second']:
            p['engine']['tables']['exports'].append(dict(path=name,class_path='UIComp_DrawString',serial_offset=0,serial_size=12,
                outer=0,archetype=0,super=0,object_flags='0000000000000200',**{'class':3}))
        r=StyleGraph(p).archetype_audit(('sample',2));self.assertEqual(len(r['class_default_candidates']),2);self.assertTrue(r['unresolved'])

    def test_cli_audit_flag_requires_deep(self):
        self.assertEqual(main(['missing','--sha256','0'*64,'--audit-bindings','--output','unused']),2)


if __name__=='__main__':unittest.main()
