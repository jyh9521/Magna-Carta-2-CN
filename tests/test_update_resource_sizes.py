"""Synthetic-only tests for conservative TOC size-span updates."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from update_resource_sizes import update_sizes, write_updated


SOURCE = (b"10 9 123 ..\\MC2Game\\CookedXenon\\font.xxx 8\r\n"
          b"20 0 456 ../MC2Game/CookedXenon/font_ui.xxx 7\n"
          b"0 0 789 ..\\MC2Game\\Xbox360TOC.txt 0")
HASH = hashlib.sha256(SOURCE).hexdigest()


def change(path="MC2Game/CookedXenon/font.xxx", old=10, new=30):
    return dict(path=path, expected_size=old, new_size=new)


class SizeUpdaterTests(unittest.TestCase):
    def test_only_first_span_and_line_endings_change(self):
        result = update_sizes(SOURCE, HASH, [change()])
        self.assertEqual(result, b"30" + SOURCE[2:])

    def test_multiple_targets_normalized_slashes_and_prefix(self):
        result = update_sizes(SOURCE, HASH, [change("..\\MC2Game\\CookedXenon\\font.xxx"),
                              change("MC2Game/CookedXenon/font_ui.xxx", 20, 99)])
        self.assertEqual(result, SOURCE.replace(b"10 9", b"30 9").replace(b"20 0", b"99 0"))

    def test_hash_mismatch_and_invalid_hash(self):
        for digest in ("0" * 64, "x" * 64, "abc", None):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                update_sizes(SOURCE, digest, [change()])

    def test_expected_size_mismatch(self):
        with self.assertRaisesRegex(ValueError, "source size mismatch"):
            update_sizes(SOURCE, HASH, [change(old=11)])

    def test_absent_and_case_mismatched_targets(self):
        for path in ("missing", "mc2game/CookedXenon/font.xxx"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                update_sizes(SOURCE, HASH, [change(path)])

    def test_duplicate_change_targets(self):
        for path in ("../MC2Game/CookedXenon/font.xxx", "MC2GAME/CookedXenon/font.xxx"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                update_sizes(SOURCE, HASH, [change(), change(path)])

    def test_duplicate_and_case_ambiguous_toc(self):
        for extra in (SOURCE.splitlines()[0], SOURCE.splitlines()[0].replace(b"MC2Game", b"MC2GAME")):
            data = SOURCE + b"\n" + extra
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "ambiguous TOC"):
                update_sizes(data, hashlib.sha256(data).hexdigest(), [change()])

    def test_malformed_source(self):
        for data in (b"bad\n", SOURCE.replace(b"10 9", b"10  9"), SOURCE + b"\r", SOURCE+b"\n\xff"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                update_sizes(data, hashlib.sha256(data).hexdigest(), [change()])

    def test_size_bounds_types_and_no_op(self):
        for value in (0, -1, True, 1.5, "30", 2**32, None, 10):
            with self.subTest(value=value), self.assertRaises(ValueError):
                update_sizes(SOURCE, HASH, [change(new=value)])
        with self.assertRaises(ValueError):
            update_sizes(SOURCE, HASH, [change(old=True)])

    def test_zero_self_entry_is_preserved_and_rejected(self):
        result = update_sizes(SOURCE, HASH, [change()])
        self.assertEqual(result.splitlines()[-1], SOURCE.splitlines()[-1])
        with self.assertRaises(ValueError):
            update_sizes(SOURCE, HASH, [change("MC2Game/Xbox360TOC.txt", 1, 30)])

    def test_invalid_changes_and_paths(self):
        for changes in ([], {}, [dict(path="x", expected_size=1)], [change("../../x")],
                        [change("/x")], [change("C:/x")], [change("MC2Game//x")],
                        [change("./x")], [change("x\x00")]):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                update_sizes(SOURCE, HASH, changes)

    def test_output_alias_existing_and_hardlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.txt"; source.write_bytes(SOURCE)
            for output in (source, Path(tmp) / "sub" / ".." / "source.txt"):
                with self.assertRaises(ValueError):
                    write_updated(source, HASH, [change()], output)
            target = Path(tmp) / "hardlink.txt"
            os.link(source, target)
            with self.assertRaises(FileExistsError):
                write_updated(source, HASH, [change()], target)
            output = Path(tmp) / "output.txt"
            result = write_updated(source, HASH, [change()], output)
            self.assertEqual(output.read_bytes(), result)
            with self.assertRaises(FileExistsError):
                write_updated(source, HASH, [change()], output)
            self.assertEqual(source.read_bytes(), SOURCE)


if __name__ == "__main__":
    unittest.main()
