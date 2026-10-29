import hashlib
import struct
import unittest

from tools.xdbf_strings import Xdbf, read_xstr, write_xstr, rebuild


def fixture():
    rows=[(1,'원본 {0}'),(2,'another'),(3,'')]
    text=b''.join(struct.pack('>HH',i,len(s.encode()))+s.encode() for i,s in rows)
    xstr=struct.pack('>4sIIH',b'XSTR',1,len(text)+10,len(rows))+text
    payloads=[(1,0x58414348,b'unchanged achievement flags/scores'),(3,7,xstr),(2,42,b'original image')]
    header=struct.pack('>4s5I',b'XDBF',0x10000,3,3,2,1);entries=b'';data=b''
    for sec,i,p in payloads:
        entries+=struct.pack('>HQII',sec,i,len(data),len(p));data+=p
    return header+entries+struct.pack('>II',len(data),0)+bytes(8)+data


def plan(data=None):
    data=fixture() if data is None else data
    return dict(schema_version=1,kind='xdbf-string-localization',input_sha256=hashlib.sha256(data).hexdigest(),
                entries=[dict(language=7,id=1,source_sha256=hashlib.sha256('원본 {0}'.encode()).hexdigest(),translation='译文 {0}')])


class XdbfTests(unittest.TestCase):
    def test_roundtrip(self):
        d=fixture();db=Xdbf(d);self.assertEqual(db.replace_entries({}),d)
        self.assertEqual(len(db.strings()[7]),3)
    def test_rebuild_and_exact_inverse(self):
        d=fixture();out,r=rebuild(d,plan());self.assertNotEqual(out,d)
        self.assertEqual(rebuild(out,r['inverse_plan'])[0],d)
        self.assertEqual(r['preserved_entry_payloads'],2)
        self.assertEqual(Xdbf(out).strings()[7][0]['text'],'译文 {0}')
    def test_length_growth(self):
        p=plan();p['entries'][0]['translation']='很长的译文'*30+' {0}'
        out,r=rebuild(fixture(),p);self.assertGreater(len(out),len(fixture()))
        self.assertEqual(rebuild(out,r['inverse_plan'])[0],fixture())
    def test_wrong_source(self):
        p=plan();p['entries'][0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source string'):rebuild(fixture(),p)
    def test_wrong_input(self):
        p=plan();p['input_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'identity'):rebuild(fixture(),p)
    def test_duplicate_id(self):
        p=plan();p['entries']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):rebuild(fixture(),p)
    def test_unknown_id(self):
        p=plan();p['entries'][0]['id']=77
        with self.assertRaisesRegex(ValueError,'unknown'):rebuild(fixture(),p)
    def test_protected_tokens(self):
        p=plan();p['entries'][0]['translation']='丢失参数'
        with self.assertRaisesRegex(ValueError,'protected'):rebuild(fixture(),p)
    def test_overflow(self):
        p=plan();p['entries'][0]['translation']='汉'*22000+'{0}'
        with self.assertRaisesRegex(ValueError,'overflow'):rebuild(fixture(),p)
    def test_duplicate_entry(self):
        d=bytearray(fixture());d[42:52]=d[24:34]
        with self.assertRaisesRegex(ValueError,'duplicate'):Xdbf(bytes(d))
    def test_out_of_range(self):
        d=bytearray(fixture());struct.pack_into('>I',d,34,0xffffffff)
        with self.assertRaisesRegex(ValueError,'range'):Xdbf(bytes(d))
    def test_tail(self):
        d=fixture()+b'X'
        with self.assertRaisesRegex(ValueError,'free record'):Xdbf(d)
    def test_invalid_free_record(self):
        d=bytearray(fixture());d[24+3*18+7]=1
        with self.assertRaisesRegex(ValueError,'free record'):Xdbf(bytes(d))
    def test_xstr_size_conventions(self):
        db=Xdbf(fixture());p=next(e['payload'] for e in db.entries if e['section']==3)
        q=bytearray(p);struct.pack_into('>I',q,8,len(q));q=bytes(q)
        self.assertEqual(write_xstr(q,{}),q);self.assertEqual(read_xstr(p),read_xstr(q))
    def test_invalid_utf8(self):
        db=Xdbf(fixture());p=bytearray(next(e['payload']for e in db.entries if e['section']==3));p[18]=0xff
        with self.assertRaises(UnicodeError):read_xstr(bytes(p))
    def test_empty_source_remains_empty(self):
        p=plan();p['entries'][0].update(id=3,source_sha256=hashlib.sha256(b'').hexdigest(),translation='added')
        with self.assertRaisesRegex(ValueError,'blank'):rebuild(fixture(),p)
    def test_strict_schema(self):
        for value in (True, 1.0):
            p=plan();p['schema_version']=value
            with self.assertRaisesRegex(ValueError,'schema'):rebuild(fixture(),p)
        p=plan();p['unknown']=True
        with self.assertRaisesRegex(ValueError,'schema'):rebuild(fixture(),p)


if __name__=='__main__':unittest.main()
