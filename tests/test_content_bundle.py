"""Synthetic content-only inventory guards; no game or emulator execution."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.content_bundle import read_bundle, install_bundle, verify_installed


REL = "0000000000000000/4E4D0811/00000002/" + "A" * 40
DATA = b"synthetic DLC payload"


def make_bundle(root):
    target = root / "files" / REL
    target.parent.mkdir(parents=True)
    target.write_bytes(DATA)
    manifest = dict(schema_version=1, kind="xenia-content-bundle", title_id="4E4D0811",
                    files=[dict(path=REL, size=len(DATA), sha256=hashlib.sha256(DATA).hexdigest())])
    return manifest, save_manifest(root, manifest)


def save_manifest(root, manifest):
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    (root / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class ContentBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bundle = self.root / "bundle"
        self.manifest, self.sha = make_bundle(self.bundle)

    def test_verified_copy_contains_no_profile_or_save(self):
        manifest, payloads = read_bundle(self.bundle, self.sha)
        out = self.root / "isolated" / "content"
        installed = install_bundle(out, manifest, payloads)
        self.assertEqual(installed, {str(out / REL): hashlib.sha256(DATA).hexdigest()})
        self.assertEqual((out / REL).read_bytes(), DATA)
        self.assertEqual((self.bundle / "files" / REL).read_bytes(), DATA)
        self.assertEqual([p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()], [REL])
        verify_installed(out, manifest)

    def test_manifest_hash_must_match(self):
        with self.assertRaisesRegex(ValueError, "manifest SHA256 mismatch"):
            read_bundle(self.bundle, "0" * 64)

    def test_original_42_character_container_identifier_is_preserved(self):
        longer=REL+'4E'
        (self.bundle/'files'/REL).rename(self.bundle/'files'/longer)
        self.manifest['files'][0]['path']=longer
        manifest,payloads=read_bundle(self.bundle,save_manifest(self.bundle,self.manifest))
        self.assertEqual(set(payloads),{longer})
        self.assertEqual(manifest['files'][0]['path'],longer)

    def test_member_size_and_digest_must_match(self):
        target = self.bundle / "files" / REL
        for data, message in ((DATA + b"!", "size mismatch"), (b"x" * len(DATA), "SHA256 mismatch")):
            with self.subTest(data=data):
                target.write_bytes(data)
                with self.assertRaisesRegex(ValueError, message):
                    read_bundle(self.bundle, self.sha)

    def test_manifest_duplicate_json_key_is_rejected(self):
        raw = b'{"schema_version":1,"schema_version":1}'
        (self.bundle / "manifest.json").write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "duplicate content manifest key"):
            read_bundle(self.bundle, hashlib.sha256(raw).hexdigest())

    def test_unknown_manifest_fields_are_rejected(self):
        self.manifest["copy_profiles"] = True
        with self.assertRaisesRegex(ValueError, "manifest fields"):
            read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))

    def test_unsafe_and_non_dlc_paths_rejected(self):
        for path in ("/absolute", "../escape", REL.replace("/", "\\"),
                     REL.replace("00000002", "00000001"),
                     REL.replace("4E4D0811", "FFFFFFFF"),
                     REL.replace("0000000000000000", "E000000000000001"),
                     REL + ":stream", REL.lower(), "./" + REL):
            with self.subTest(path=path):
                self.manifest["files"][0]["path"] = path
                with self.assertRaisesRegex(ValueError, "file path"):
                    read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))

    def test_duplicate_paths_rejected(self):
        self.manifest["files"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate content file path"):
            read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))

    def test_unknown_tree_files_and_empty_directories_rejected(self):
        for extra in (self.bundle / "unexpected.txt", self.bundle / "files" / "profile.bin"):
            extra.write_bytes(b"do not copy")
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                read_bundle(self.bundle, self.sha)
            extra.unlink()
        (self.bundle / "empty").mkdir()
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            read_bundle(self.bundle, self.sha)

    def test_missing_member_rejected(self):
        (self.bundle / "files" / REL).unlink()
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            read_bundle(self.bundle, self.sha)

    def test_empty_inventory_rejected(self):
        self.manifest["files"] = []
        with self.assertRaisesRegex(ValueError, "file count"):
            read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))

    def test_boolean_and_unbounded_sizes_rejected(self):
        for size in (True, 0, -1, 2**31):
            with self.subTest(size=size):
                self.manifest["files"][0]["size"] = size
                with self.assertRaisesRegex(ValueError, "size outside bound"):
                    read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))

    def test_invalid_hash_and_title_types_rejected(self):
        for value in (None, "x" * 64, "A" * 64, 12):
            with self.subTest(value=value):
                self.manifest["files"][0]["sha256"] = value
                with self.assertRaisesRegex(ValueError, "invalid content SHA256"):
                    read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))
        self.manifest["title_id"] = 0x4E4D0811
        with self.assertRaisesRegex(ValueError, "title ID"):
            read_bundle(self.bundle, save_manifest(self.bundle, self.manifest))

    def test_existing_destination_and_bad_payload_do_not_write(self):
        manifest, payloads = read_bundle(self.bundle, self.sha)
        out = self.root / "content"
        out.mkdir()
        (out / "save").write_bytes(b"keep")
        with self.assertRaisesRegex(ValueError, "must be new"):
            install_bundle(out, manifest, payloads)
        self.assertEqual((out / "save").read_bytes(), b"keep")
        new = self.root / "new-content"
        with self.assertRaisesRegex(ValueError, "payload bytes mismatch"):
            install_bundle(new, manifest, {REL: b"changed"})
        self.assertFalse(new.exists())

    def test_installed_mutation_and_unknown_file_rejected(self):
        manifest, payloads = read_bundle(self.bundle, self.sha)
        out = self.root / "content"
        install_bundle(out, manifest, payloads)
        (out / REL).write_bytes(b"x" * len(DATA))
        with self.assertRaisesRegex(ValueError, "installed content file changed"):
            verify_installed(out, manifest)
        (out / REL).write_bytes(DATA)
        (out / "profile").write_bytes(b"unexpected")
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            verify_installed(out, manifest)

    def test_symbolic_link_member_and_root_rejected(self):
        target = self.bundle / "files" / REL
        source = self.root / "elsewhere"
        source.write_bytes(DATA)
        target.unlink()
        try:
            target.symlink_to(source)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "link or junction"):
            read_bundle(self.bundle, self.sha)
        alias = self.root / "alias"
        alias.symlink_to(self.bundle, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "link or junction"):
            read_bundle(alias, self.sha)

    def test_mocked_link_and_junction_guards_cover_ancestors(self):
        # Runs even on Windows accounts without symlink creation privileges.
        for member in (self.bundle, self.bundle / "files", self.bundle / "files" / REL):
            for method in ("is_symlink", "is_junction"):
                with self.subTest(member=member, method=method):
                    with patch.object(Path, method, lambda p: p == member, create=True):
                        with self.assertRaisesRegex(ValueError, "link or junction"):
                            read_bundle(self.bundle, self.sha)


if __name__ == "__main__":
    unittest.main()
