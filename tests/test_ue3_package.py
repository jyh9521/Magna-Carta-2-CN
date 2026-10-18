"""Synthetic fixtures only: no proprietary game resources."""
import copy
import struct
import unittest
from tools.ue3_package import FormatError, Reader, parse_summary, parse_tables, strip_lzx_frames, package_header

def fixture(endian=">"):
    pack=lambda *v:struct.pack(endian+"I"*len(v),*v)
    string=lambda s:pack(len(s)+1)+s.encode()+b"\0"
    names=["Core","Package","Class","Thing","Object"]
    name_table=b"".join(string(s)+b"\0"*8 for s in names)
    fname=lambda i:pack(i,0)
    imports=fname(0)+fname(1)+pack(0)+fname(0)+fname(0)+fname(2)+pack(0xffffffff)+fname(3)
    header_size=101+len(name_table)+len(imports)+68
    exports=pack(0xfffffffe,0,0)+fname(4)+pack(0)+b"\0"*8+pack(4,header_size,0,0,0)+b"\0"*16
    magic=b"\x9e\x2a\x83\xc1" if endian==">" else b"\xc1\x83\x2a\x9e"
    head=magic+pack((25<<16)|446,header_size)+string("None")+pack(0,len(names),101,1,101+len(name_table)+len(imports),2,101+len(name_table),0)+b"\0"*16+pack(1,1,len(names),0,3004,42,0,0)
    assert len(head)==101 and len(exports)==68
    return head+name_table+imports+exports+b"DATA"

class UE3Tests(unittest.TestCase):
    def test_big_tables_and_edges(self):
        data=fixture();t=parse_tables(data)
        self.assertEqual(t["package_dependencies"],["Core"])
        self.assertEqual(t["exports"][0]["class_path"],"Core.Thing")
        self.assertEqual(t["table_edges"],[{"source":1,"field":"class","target":-2}])
    def test_little_endian(self): self.assertEqual(parse_tables(fixture("<"))["names"][3],"Thing")
    def test_version_guard(self):
        d=bytearray(fixture());struct.pack_into(">I",d,4,447)
        with self.assertRaisesRegex(FormatError,"unsupported"):parse_summary(d)
    def test_magic(self):
        with self.assertRaises(FormatError):parse_summary(b"xxxx")
    def test_truncated_summary(self):
        for n in range(4,101):
            with self.subTest(n=n),self.assertRaises(FormatError):parse_summary(fixture()[:n])
    def test_truncated_name(self):
        with self.assertRaises(FormatError):parse_tables(fixture()[:110])
    def test_invalid_name_reference(self):
        d=bytearray(fixture());s=parse_summary(d);struct.pack_into(">I",d,s["import_offset"],999)
        with self.assertRaisesRegex(FormatError,"FName"):parse_tables(d)
    def test_bad_serial_range(self):
        d=bytearray(fixture());s=parse_summary(d);struct.pack_into(">I",d,s["export_offset"]+36,0xfffffff0)
        with self.assertRaisesRegex(FormatError,"serial range"):parse_tables(d)
    def test_cycle(self):
        d=bytearray(fixture());s=parse_summary(d);struct.pack_into(">i",d,s["import_offset"]+16,-1)
        with self.assertRaisesRegex(FormatError,"cyclic"):parse_tables(d)
    def test_object_reference(self):
        d=bytearray(fixture());s=parse_summary(d);struct.pack_into(">i",d,s["export_offset"],-3)
        with self.assertRaisesRegex(FormatError,"object reference"):parse_tables(d)
    def test_invalid_count(self):
        with self.assertRaises(FormatError):Reader(b"\xff"*4).count()
    def test_fstring_unicode(self): self.assertEqual(Reader(struct.pack(">i",-2)+"字\0".encode("utf-16-be")).string(),"字")
    def test_fstring_termination(self):
        with self.assertRaisesRegex(FormatError,"unterminated"):Reader(b"\0\0\0\x02xx").string()
    def test_fstring_utf8_guard(self):
        with self.assertRaisesRegex(FormatError,"encoding"):Reader(b"\0\0\0\x02\xff\0").string()
    def test_frames(self): self.assertEqual(strip_lzx_frames(b"\0\x03abc\xff\0\x02\0\x02de\0\0"),b"abcde")
    def test_frame_truncated(self):
        with self.assertRaises(FormatError):strip_lzx_frames(b"\0\x03a")
    def test_frame_bad_terminal(self):
        with self.assertRaises(FormatError):strip_lzx_frames(b"\0\0x")
    def test_frame_bad_size(self):
        with self.assertRaises(FormatError):strip_lzx_frames(b"\xff\0\0\0\x01x")
    def test_uncompressed_header(self):
        d=fixture();self.assertEqual(package_header(d,parse_summary(d),None),d)
    def test_compressed_without_decoder(self):
        s=copy.deepcopy(parse_summary(fixture()));s["compression_flags"]=4
        with self.assertRaisesRegex(FormatError,"not configured"):package_header(fixture(),s,None)
    def test_compressed_profile_guard(self):
        s=copy.deepcopy(parse_summary(fixture()));s["compression_flags"]=2
        with self.assertRaises(FormatError):package_header(fixture(),s,None)
    def test_overlap_tables(self):
        d=fixture();s=parse_summary(d);s["header_size"]=s["export_offset"]
        with self.assertRaises(FormatError):parse_tables(d,s)



class StandalonePackageTests(unittest.TestCase):
    def test_xbox_unicode_endian(self):
        self.assertEqual(Reader(struct.pack(">i", -2) + "字\0".encode("utf-16-le"), ">", "<").string(), "字")

    def test_summary_table_overlap(self):
        data = bytearray(fixture())
        struct.pack_into(">II", data, 25, 1, 53)
        struct.pack_into(">I", data, 33, 0)
        struct.pack_into(">I", data, 41, 0)
        with self.assertRaisesRegex(FormatError, "table offset"):
            parse_summary(data)

    def test_hash_guard(self):
        from tools.ue3_package import analyze_package
        for digest in ("0" * 64, "z" * 64, "123"):
            with self.subTest(digest=digest), self.assertRaises(FormatError):
                analyze_package(fixture(), digest)

    def test_metadata_report(self):
        import hashlib
        from tools.ue3_package import analyze_package
        data = fixture()
        report = analyze_package(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(report["status"], "tables-validated")
        self.assertEqual(report["class_histogram"], {"Core.Thing": 1})
        self.assertEqual(report["exports"][0]["serial_size"], 4)
        self.assertNotIn("payload", report["exports"][0])

    def test_cli_exclusive_and_input_guard(self):
        import hashlib, json, tempfile
        from pathlib import Path
        from tools.ue3_package import main
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.xxx"
            output = Path(temp) / "report.json"
            data = fixture()
            source.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            def call(dest, sha=digest):
                return main([str(source), "--sha256", sha, "--output", str(dest)])
            self.assertEqual(call(source), 1)
            self.assertEqual(call(output, "0" * 64), 1)
            self.assertFalse(output.exists())
            self.assertEqual(call(output), 0)
            original = output.read_bytes()
            self.assertEqual(json.loads(original)["status"], "tables-validated")
            self.assertEqual(call(output), 1)
            self.assertEqual(output.read_bytes(), original)
            hardlink = Path(temp) / "alias.xxx"
            hardlink.hardlink_to(source)
            self.assertEqual(call(hardlink), 1)
            self.assertEqual(source.read_bytes(), data)

    def test_truncated_compressed_decoder_output(self):
        # The adapter must return exactly the requested block output length.
        from tools.ue3_package import package_header
        summary = {"compression_flags": 4, "header_size": 8,
                   "compressed_chunks": [{"uncompressed_offset": 4, "uncompressed_size": 4,
                     "compressed_offset": 4, "compressed_size": 25}]}
        data = b"HEAD" + struct.pack(">IIIIII", 0x9e2a83c1, 4, 1, 4, 1, 4) + b"X"
        with self.assertRaisesRegex(FormatError, "decoder output"):
            package_header(data, summary, lambda data, size: b"")
