"""Hash-locked optional marketplace-content bundles for isolated Xenia runs.

This copies only explicitly enumerated DLC containers, never profiles or saves.
Package parsing/rebuilding is a separate step; this module binds delivered bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat


MAX_MANIFEST_BYTES = 1024 * 1024
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("invalid content SHA256")
    return value


def check_no_links(path):
    """Inspect the lexical path before resolve(), including ancestor junctions."""
    path = Path(path).absolute()
    for part in (*reversed(path.parents), path):
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError("content path contains a link or junction")
    return path.resolve()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate content manifest key")
        result[key] = value
    return result


def _validate_manifest(manifest):
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version", "kind", "title_id", "files"
    }:
        raise ValueError("invalid content manifest fields")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported content manifest version")
    if manifest["kind"] != "xenia-content-bundle":
        raise ValueError("unsupported content bundle kind")
    title_id = manifest["title_id"]
    if not isinstance(title_id, str) or not re.fullmatch(r"[0-9A-F]{8}", title_id):
        raise ValueError("invalid content title ID")
    files = manifest["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 64:
        raise ValueError("invalid content file count")
    seen, total = set(), 0
    # Container filenames are opaque identifiers, not necessarily SHA1 digests.
    # This title's real marketplace files use 42 hex characters; retain those
    # exact names while continuing to accept conventional 40-character names.
    pattern = rf"0000000000000000/{title_id}/00000002/(?:[0-9A-F]{{40}}|[0-9A-F]{{42}})"
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            raise ValueError("invalid content file fields")
        name = entry["path"]
        if not isinstance(name, str) or not re.fullmatch(pattern, name):
            raise ValueError("invalid content file path")
        if name in seen:
            raise ValueError("duplicate content file path")
        seen.add(name)
        if type(entry["size"]) is not int or not 1 <= entry["size"] <= MAX_FILE_BYTES:
            raise ValueError("content file size outside bound")
        total += entry["size"]
        _hash(entry["sha256"])
    if total > MAX_TOTAL_BYTES:
        raise ValueError("content bundle total size outside bound")


def _inventory(root):
    root = check_no_links(root)
    if not root.is_dir():
        raise ValueError("content root must be a directory")
    files, directories, pending = set(), set(), [root]
    while pending:
        parent = pending.pop()
        for path in parent.iterdir():
            check_no_links(path)
            relative = path.relative_to(root).as_posix()
            mode = path.stat().st_mode
            if stat.S_ISDIR(mode):
                directories.add(relative)
                pending.append(path)
            elif stat.S_ISREG(mode):
                files.add(relative)
            else:
                raise ValueError("content tree contains a non-regular member")
    return files, directories


def _expected_directories(files):
    return {p.as_posix() for name in files for p in Path(name).parents if p != Path(".")}


def _verify_inventory(root, names):
    actual_files, actual_directories = _inventory(root)
    if actual_files != set(names) or actual_directories != _expected_directories(names):
        raise ValueError("content inventory mismatch")


def read_bundle(root, manifest_sha256):
    """Validate all source bytes before the launcher creates a run directory."""
    root = check_no_links(root)
    manifest_path = root / "manifest.json"
    check_no_links(manifest_path)
    if not manifest_path.is_file() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("invalid content manifest file")
    raw = manifest_path.read_bytes()
    if digest(raw) != _hash(manifest_sha256):
        raise ValueError("content manifest SHA256 mismatch")
    manifest = json.loads(raw, object_pairs_hook=_unique_object)
    _validate_manifest(manifest)
    names = ["manifest.json"] + ["files/" + entry["path"] for entry in manifest["files"]]
    _verify_inventory(root, names)
    payloads = {}
    for entry in manifest["files"]:
        path = root / "files" / entry["path"]
        check_no_links(path)
        if path.stat().st_size != entry["size"]:
            raise ValueError("content file size mismatch")
        data = path.read_bytes()
        if len(data) != entry["size"] or digest(data) != entry["sha256"]:
            raise ValueError("content file SHA256 mismatch")
        payloads[entry["path"]] = data
    _verify_inventory(root, names)
    if manifest_path.read_bytes() != raw:
        raise ValueError("content manifest changed during preflight")
    return manifest, payloads


def verify_installed(content_root, manifest):
    """Before launch, an isolated content root must contain only the bundle."""
    _validate_manifest(manifest)
    content_root = check_no_links(content_root)
    _verify_inventory(content_root, [entry["path"] for entry in manifest["files"]])
    for entry in manifest["files"]:
        path = content_root / entry["path"]
        if path.stat().st_size != entry["size"] or digest(path.read_bytes()) != entry["sha256"]:
            raise ValueError("installed content file changed")


def install_bundle(content_root, manifest, payloads):
    """Create a fresh content subtree using immutable, prevalidated payloads."""
    _validate_manifest(manifest)
    if set(payloads) != {entry["path"] for entry in manifest["files"]}:
        raise ValueError("content payload inventory mismatch")
    for entry in manifest["files"]:
        data = payloads[entry["path"]]
        if not isinstance(data, bytes) or len(data) != entry["size"] or digest(data) != entry["sha256"]:
            raise ValueError("content payload bytes mismatch")
    content_root = check_no_links(content_root)
    if content_root.exists():
        raise ValueError("content installation root must be new")
    content_root.mkdir(parents=True, exist_ok=False)
    for entry in manifest["files"]:
        path = content_root / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        check_no_links(path)
        with path.open("xb") as stream:
            stream.write(payloads[entry["path"]])
    verify_installed(content_root, manifest)
    return {str(content_root / entry["path"]): entry["sha256"] for entry in manifest["files"]}
