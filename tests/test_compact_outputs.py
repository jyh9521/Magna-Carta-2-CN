import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.compact_outputs import compact_outputs, require_disk_space


class CompactOutputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Valid fixtures must not accidentally exercise the traversal guard.
        self.root = Path(self.temp.name).resolve()
        self.a = self.root / "packet/candidate/a.bin"
        self.b = self.root / "packet/controls/b.bin"
        self.a.parent.mkdir(parents=True)
        self.b.parent.mkdir(parents=True)
        self.data = b"owned immutable output fixture" * 100
        self.a.write_bytes(self.data)
        self.b.write_bytes(self.data)
        self.manifest = self.root / "packet/manifest.json"
        self.members = {"candidate/a.bin": hashlib.sha256(self.data).hexdigest(),
                        "controls/b.bin": hashlib.sha256(self.data).hexdigest()}
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(dict(member_sha256=self.members)), encoding="utf-8")

    def run_compaction(self):
        return compact_outputs([self.manifest], self.root, self.root / "report", minimum_size=1)

    def test_bytes_and_manifest_preserved_with_isolated_rollback(self):
        before = self.manifest.read_bytes()
        self.assertFalse(os.path.samefile(self.a, self.b))
        report = self.run_compaction()
        self.assertEqual(report["linked_files"], 1)
        self.assertTrue(os.path.samefile(self.a, self.b))
        self.assertEqual(self.a.read_bytes(), self.data)
        self.assertEqual(self.b.read_bytes(), self.data)
        self.assertEqual(self.manifest.read_bytes(), before)
        # Materialize an isolated copy before any future in-place modification.
        temporary = self.b.with_suffix(".independent")
        shutil.copyfile(self.b, temporary)
        os.replace(temporary, self.b)
        self.assertFalse(os.path.samefile(self.a, self.b))
        self.assertEqual(self.b.read_bytes(), self.data)

    def test_bad_hash_fails_before_replacing_any_file(self):
        self.members["controls/b.bin"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            self.run_compaction()
        self.assertFalse(os.path.samefile(self.a, self.b))

    def test_permission_denial_preserves_target_and_continues(self):
        with patch('tools.compact_outputs.os.replace', side_effect=PermissionError('fixture locked')):
            report = self.run_compaction()
        self.assertEqual(report['skipped_permission_denied'], 1)
        self.assertEqual(report['linked_files'], 0)
        self.assertFalse(os.path.samefile(self.a, self.b))
        self.assertEqual(self.b.read_bytes(), self.data)
        self.assertEqual(list(self.root.rglob('.dedup-*')), [])

    def test_parent_traversal_rejected(self):
        self.members["../original.bin"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "Invalid manifest member"):
            self.run_compaction()

    def test_manifest_outside_allowed_root_rejected(self):
        with self.assertRaisesRegex(ValueError, "escaped allowed root"):
            compact_outputs([self.manifest], self.a.parent, self.root / "report")

    def test_saves_and_rollback_members_excluded(self):
        save = self.a.with_suffix(".sav")
        save.write_bytes(self.data)
        rollback = self.root / "packet/rollback/keep.bin"
        rollback.parent.mkdir()
        rollback.write_bytes(self.data)
        self.members.update({"candidate/a.sav": self.members["candidate/a.bin"],
                             "rollback/keep.bin": self.members["candidate/a.bin"]})
        self.save()
        self.run_compaction()
        self.assertFalse(os.path.samefile(self.a, save))
        self.assertFalse(os.path.samefile(self.a, rollback))

    def test_existing_report_directory_rejected(self):
        (self.root / "report").mkdir()
        with self.assertRaises(FileExistsError):
            self.run_compaction()

    def test_already_linked_members_do_not_reclaim_twice(self):
        self.b.unlink()
        os.link(self.a, self.b)
        self.assertEqual(self.run_compaction()["reclaimable_bytes"], 0)

    def test_space_gate_rejects_before_producer(self):
        usage = shutil.disk_usage(self.root)._replace(free=16 * 2**30 - 1)
        with patch("tools.compact_outputs.shutil.disk_usage", return_value=usage):
            with self.assertRaisesRegex(ValueError, "Insufficient build space"):
                require_disk_space(self.root)

    def test_space_gate_accepts_threshold(self):
        usage = shutil.disk_usage(self.root)._replace(free=16 * 2**30)
        with patch("tools.compact_outputs.shutil.disk_usage", return_value=usage):
            self.assertEqual(require_disk_space(self.root), 16 * 2**30)

    def alias_resolution(self):
        # Model Windows 8.3 names resolving to their long-name counterpart.
        alias = self.root.with_name(self.root.name + "-short")
        original = Path.resolve

        def resolve(path, *args, **kwargs):
            if path.is_relative_to(alias):
                path = self.root / path.relative_to(alias)
            return original(path, *args, **kwargs)

        return alias, resolve

    def test_short_and_long_path_spellings_share_one_allowed_root(self):
        alias, resolve = self.alias_resolution()
        with patch.object(Path, "resolve", resolve):
            report = compact_outputs([alias / "packet/manifest.json"], self.root,
                                     self.root / "report", minimum_size=1)
        self.assertEqual(report["linked_files"], 1)
        self.assertEqual(self.b.read_bytes(), self.data)

    def test_resolving_alias_does_not_hide_a_reparse_point(self):
        alias, resolve = self.alias_resolution()
        original = Path.is_junction

        def junction(path):
            return path == alias or original(path)

        with patch.object(Path, "resolve", resolve), patch.object(Path, "is_junction", junction):
            with self.assertRaisesRegex(ValueError, "Reparse points"):
                compact_outputs([alias / "packet/manifest.json"], self.root,
                                self.root / "report", minimum_size=1)

    def backup_pair(self):
        paths = [self.root / "packet/rollback-check/r.bin",
                 self.root / "packet/raw-rollback-check/s.bin"]
        for path in paths:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(self.data)
            self.members[path.relative_to(self.manifest.parent).as_posix()] = self.members["candidate/a.bin"]
        self.save()
        return paths

    def test_backup_pool_keeps_an_independent_copy_from_candidates(self):
        r, s = self.backup_pair()
        report = compact_outputs([self.manifest], self.root, self.root / "report",
                                 minimum_size=1, rollback_only=True)
        self.assertEqual(report["linked_files"], 1)
        self.assertTrue(os.path.samefile(r, s))
        self.assertFalse(os.path.samefile(self.a, r))
        self.assertEqual(r.read_bytes(), self.data)

    def test_backup_pool_excludes_inodes_with_unlisted_links(self):
        r, s = self.backup_pair()
        r.unlink()
        os.link(self.a, r)
        report = compact_outputs([self.manifest], self.root, self.root / "report",
                                 minimum_size=1, rollback_only=True)
        self.assertEqual(report["skipped_external_links"], 1)
        self.assertEqual(report["linked_files"], 0)
        self.assertFalse(os.path.samefile(r, s))

    def test_existing_backup_pool_can_merge_new_copies_without_external_sharing(self):
        r, s = self.backup_pair()
        compact_outputs([self.manifest], self.root, self.root / "report",
                        minimum_size=1, rollback_only=True)
        t = s.with_name("t.bin")
        t.write_bytes(self.data)
        self.members["raw-rollback-check/t.bin"] = self.members["candidate/a.bin"]
        self.save()
        report = compact_outputs([self.manifest], self.root, self.root / "report2",
                                 minimum_size=1, rollback_only=True)
        self.assertEqual(report["linked_files"], 1)
        self.assertTrue(os.path.samefile(r, t))
        self.assertFalse(os.path.samefile(self.a, t))

    def test_explicit_inventory_pool_preserves_default_exclusions(self):
        report = compact_outputs([self.manifest], self.root, self.root / "report",
                                 minimum_size=1, inventory_prefixes=["candidate", "controls"])
        self.assertEqual(report["mode"], "independent-inventory-pool")
        self.assertTrue(report["pool_independence_verified"])
        self.assertEqual(report["linked_files"], 1)
        self.assertTrue(os.path.samefile(self.a, self.b))

    def test_inventory_pool_excludes_an_unlisted_live_link(self):
        live = self.root / "live.bin"
        os.link(self.a, live)
        report = compact_outputs([self.manifest], self.root, self.root / "report",
                                 minimum_size=1, inventory_prefixes=["candidate", "controls"])
        self.assertEqual(report["skipped_external_links"], 1)
        self.assertEqual(report["linked_files"], 0)
        self.assertFalse(os.path.samefile(self.a, self.b))
        self.assertEqual(live.read_bytes(), self.data)

    def test_inventory_prefixes_cannot_select_parents_or_absolute_paths(self):
        for prefixes in ([], [".."], ["."], ["../other"], ["a/b"], ["a\\b"], ["C:"], [""],
                         "candidate", True, [None], [1]):
            with self.subTest(prefixes=prefixes), self.assertRaises(ValueError):
                compact_outputs([self.manifest], self.root, self.root / "report",
                                minimum_size=1, inventory_prefixes=prefixes)
        self.assertFalse((self.root / "report").exists())

    def test_inventory_and_rollback_modes_are_mutually_exclusive(self):
        with self.assertRaises(ValueError):
            compact_outputs([self.manifest], self.root, self.root / "report",
                            rollback_only=True, inventory_prefixes=["candidate"])

    def test_inventory_pool_keeps_protected_file_types_independent(self):
        for suffix in (".sav", ".save", ".xex", ".exe", ".dll", ".toml"):
            path = self.a.with_suffix(suffix)
            path.write_bytes(self.data)
            self.members[path.relative_to(self.manifest.parent).as_posix()] = self.members["candidate/a.bin"]
        self.save()
        compact_outputs([self.manifest], self.root, self.root / "report", minimum_size=1,
                        inventory_prefixes=["candidate", "controls"])
        for suffix in (".sav", ".save", ".xex", ".exe", ".dll", ".toml"):
            self.assertFalse(os.path.samefile(self.a, self.a.with_suffix(suffix)))


if __name__ == "__main__":
    unittest.main()
