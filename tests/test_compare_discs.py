import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools.compare_discs import compare, main


def manifest(rows):
    return dict(image="synthetic.iso",image_size=4096,sha256="a"*64,entries=[dict(path=p,directory=False,offset=0,size=1,sha256=h*64) for p,h in rows])

class CompareDiscsTests(unittest.TestCase):
    def test_four_groups_and_provenance(self):
        result=compare(manifest([("a","a"),("b","b"),("c","c")]),manifest([("a","a"),("b","c"),("d","d")]))
        self.assertEqual(result["counts"],dict(identical=1,conflict=1,**{"disc1-only":1,"disc2-only":1}))
        self.assertFalse(result["merge_performed"])
        self.assertEqual(result["files"][1]["disc1"]["sha256"],"b"*64)
        self.assertEqual(result["files"][1]["disc2"]["sha256"],"c"*64)

    def test_identical_hash_different_size_not_shared(self):
        a=manifest([("a","a")]);b=copy.deepcopy(a);b["entries"][0]["size"]=2
        self.assertEqual(compare(a,b)["counts"]["conflict"],1)

    def test_reject_missing_hash(self):
        a=manifest([("a","a")]);del a["entries"][0]["sha256"]
        with self.assertRaises(ValueError):compare(a,manifest([]))

    def test_reject_bad_image_hash(self):
        a=manifest([]);a["sha256"]="unknown"
        with self.assertRaises(ValueError):compare(a,a)

    def test_extent(self):
        a=manifest([("a","a")]);a["entries"][0]["offset"]=4096
        with self.assertRaises(ValueError):compare(a,a)

    def test_duplicate(self):
        with self.assertRaises(ValueError):compare(manifest([("a","a"),("A","b")]),manifest([]))

    def test_cross_disc_case_collision(self):
        with self.assertRaises(ValueError):compare(manifest([("a","a")]),manifest([("A","a")]))

    def test_paths(self):
        for path in ["../a","a/../b","/a","a//b","a:stream","a\\b"]:
            with self.subTest(path=path),self.assertRaises(ValueError):compare(manifest([(path,"a")]),manifest([]))

    def test_deterministic(self):
        a=manifest([("b","b"),("a","a")]);b=manifest([])
        self.assertEqual(compare(a,b),compare(dict(a,entries=list(reversed(a["entries"]))),b))

    def test_output_exclusive_and_inputs_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);a=root/"a.json";b=root/"b.json";out=root/"diff.json"
            a.write_text(json.dumps(manifest([("a","a")])));b.write_text(json.dumps(manifest([])))
            originals=[a.read_bytes(),b.read_bytes()]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(a),str(b),"--output",str(out)]),0)
                before=out.read_bytes()
                self.assertEqual(main([str(a),str(b),"--output",str(out)]),2)
                self.assertEqual(main([str(a),str(b),"--output",str(a)]),2)
            self.assertEqual(before,out.read_bytes());self.assertEqual(originals,[a.read_bytes(),b.read_bytes()])
