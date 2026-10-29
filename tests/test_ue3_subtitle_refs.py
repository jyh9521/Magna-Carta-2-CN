import copy
import struct
import unittest
from unittest.mock import patch

from tools.ue3_subtitle_refs import read_fields,patch_package,sha

NAMES=['None','SubTitleWrap','ArrayProperty','Subtitles','Text','StrProperty','Time','FloatProperty','FaceFXSeqName']
def word(n):return struct.pack('>I',n)
def name(n):return word(NAMES.index(n))+word(0)
def tag(n,t,b):return name(n)+name(t)+word(len(b))+word(0)+b
def fstr(s):return word(len(s)+1)+s.encode()+b'\0'
def payload(text,face='D_1_1_01_juto',wave=False):
    sub=word(1)+tag('Text','StrProperty',fstr(text))+tag('Time','FloatProperty',struct.pack('>f',1.5))+name('None')
    inner=tag('Subtitles','ArrayProperty',sub)
    if not wave:inner=tag('SubTitleWrap','ArrayProperty',word(1)+inner+tag('FaceFXSeqName','StrProperty',fstr(face))+name('None'))
    return word(0)+inner+name('None')

def fixture(wave=False):
    a,b='<Strings:Doc.Scene.Line02>','<Strings:Doc.Scene.Line01>'
    first=payload(a);second=payload(b,wave=wave);raw=b'head'+first+second+b'opaque-media'
    donor='Wave.D_1_1_01_juto'if wave else'Scene.Copy'
    exports=[dict(path='Scene.Selected',class_path='MC2Game.MC2SeqAct_ShowCSMBSubtitle',serial_offset=4,serial_size=len(first)),
        dict(path=donor,class_path='Engine.SoundNodeWave'if wave else'MC2Game.MC2SeqAct_ShowCSMBSubtitle',serial_offset=4+len(first),serial_size=len(second))]
    ctx=dict(logical=raw,tables=dict(names=NAMES,exports=exports))
    plan=dict(source_sha256=sha(raw),entries=[dict(object='Scene.Selected',object_sha256=sha(first),wrap=0,item=0,
        face='D_1_1_01_juto',before=a,after=b,evidence_object=donor,evidence_sha256=sha(second))])
    return raw,ctx,plan

class SubtitleReferenceTests(unittest.TestCase):
    def apply(self,raw,ctx,plan):
        with patch('tools.ue3_subtitle_refs.decompress_copy',return_value=(raw,{})),patch('tools.ue3_subtitle_refs.context',return_value=ctx):
            return patch_package(raw,plan,None)
    def test_exact_typed_fields_and_duplicate_corroboration(self):
        raw,ctx,p=fixture();out,r=self.apply(raw,ctx,p)
        self.assertNotEqual(out,raw);self.assertTrue(r['logical_inverse_byte_identical'])
        self.assertEqual(out[-12:],raw[-12:]);self.assertEqual(len(out),len(raw))
    def test_wave_corroboration(self):
        raw,ctx,p=fixture(True);out,r=self.apply(raw,ctx,p)
        self.assertEqual(len(r['edits']),1)
    def test_source_and_export_hash_guard(self):
        for key in ('source_sha256','object_sha256','evidence_sha256'):
            raw,ctx,p=fixture()
            if key=='source_sha256':p[key]='0'*64
            else:p['entries'][0][key]='0'*64
            with self.subTest(key=key),self.assertRaises(ValueError):self.apply(raw,ctx,p)
    def test_unknown_or_wrong_field(self):
        for key,value in [('wrap',1),('item',True),('face','other'),('before','other'),('object','missing'),('evidence_object','Scene.Selected')]:
            raw,ctx,p=fixture();p['entries'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.apply(raw,ctx,p)
    def test_no_guessed_replacement(self):
        raw,ctx,p=fixture();p['entries'][0]['after']='<Strings:Doc.Scene.Line00>'
        with self.assertRaisesRegex(ValueError,'corroborate'):self.apply(raw,ctx,p)
    def test_duplicate_edits(self):
        raw,ctx,p=fixture();p['entries']*=2
        with self.assertRaisesRegex(ValueError,'overlapping'):self.apply(raw,ctx,p)
    def test_unparsed_subtitle_array_rejected(self):
        raw=payload('<Strings:Doc.Scene.Line01>')
        bad=bytearray(raw);struct.pack_into('>I',bad,28,2)
        with self.assertRaises(ValueError):read_fields(bytes(bad),NAMES,'MC2Game.MC2SeqAct_ShowCSMBSubtitle')

if __name__=='__main__':unittest.main()
