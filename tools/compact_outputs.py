"""Hash-guarded deduplication of immutable, manifest-listed build outputs.

Never use this on live data. Hardlinked outputs must be materialized before
in-place modification. Compaction does not delete resource paths or alter bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid


def require_disk_space(root: Path, minimum_bytes: int = 16 * 2**30) -> int:
    """Fail before starting a large producer when temporary space is inadequate."""
    if minimum_bytes < 0:
        raise ValueError("minimum_bytes must be nonnegative")
    free = shutil.disk_usage(root).free
    if free < minimum_bytes:
        raise ValueError(f"Insufficient build space: free={free}; required={minimum_bytes}")
    return free


def _checked(path: Path, root: Path) -> Path:
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError(f"Output escaped allowed root: {path}")
    # Resolve both sides for Windows 8.3/long-name equivalence, but retain the
    # original spelling while inspecting every component for reparse points.
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError(f"Output escaped allowed root: {path}")
    for component in (path, *path.parents):
        if component.is_symlink() or component.is_junction():
            raise ValueError(f"Reparse points are not eligible: {component}")
        if component.resolve(strict=True) == root:
            break
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"Not a regular build output: {path}")
    return resolved


class _Hashes:
    def __init__(self) -> None:
        self.cache: dict[tuple[int, int, int, int], str] = {}

    @staticmethod
    def identity(stat: os.stat_result) -> tuple[int, int, int, int]:
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns

    def __call__(self, path: Path) -> str:
        with path.open("rb") as stream:
            key = self.identity(os.fstat(stream.fileno()))
            if key not in self.cache:
                digest = hashlib.sha256()
                while block := stream.read(1024 * 1024):
                    digest.update(block)
                self.cache[key] = digest.hexdigest()
            if key != self.identity(os.fstat(stream.fileno())):
                raise ValueError(f"Output changed while hashing: {path}")
        if key != self.identity(path.stat()):
            raise ValueError(f"Output replaced while hashing: {path}")
        return self.cache[key]


def compact_outputs(manifests: list[Path], root: Path, output: Path,
                    minimum_size: int = 65536, rollback_only: bool = False) -> dict:
    """Compact immutable outputs, or a separately inventoried backup-only pool."""
    if minimum_size < 0 or not manifests or type(rollback_only) is not bool:
        raise ValueError("Supply manifests and a nonnegative minimum_size")
    root = root.absolute()
    if root.is_symlink() or root.is_junction():
        raise ValueError("Allowed root must not be a reparse point")
    root = root.resolve(strict=True)
    output.mkdir(parents=True, exist_ok=False)
    hashes = _Hashes()
    rows: dict[Path, str] = {}
    manifest_hashes: dict[Path, str] = {}
    excluded = {".sav", ".save", ".xex", ".exe", ".dll", ".toml"}
    prefixes = {"rollback-check", "raw-rollback-check"} if rollback_only else {"candidate", "controls", "raw-controls"}
    for manifest in manifests:
        manifest = _checked(manifest, root)
        manifest_hashes[manifest] = hashes(manifest)
        members = json.loads(manifest.read_bytes()).get("member_sha256")
        if not isinstance(members, dict):
            raise ValueError(f"Missing member_sha256 mapping: {manifest}")
        for relative, expected in members.items():
            member = Path(relative)
            if member.is_absolute() or ".." in member.parts or not member.parts:
                raise ValueError(f"Invalid manifest member: {relative}")
            if member.parts[0] not in prefixes:
                continue
            path = _checked(manifest.parent / member, root)
            if path.suffix.lower() in excluded or path.stat().st_size < minimum_size:
                continue
            if not isinstance(expected, str) or len(expected) != 64:
                raise ValueError(f"Invalid SHA256: {relative}")
            if path in rows and rows[path] != expected:
                raise ValueError(f"Conflicting manifest hashes: {path}")
            rows[path] = expected
    skipped_external_links = 0
    if rollback_only:
        # A separate backup-only pool must never share an inode with candidate,
        # live, or any other unlisted path. Account for every existing hardlink.
        groups: dict[tuple[int, int], list[Path]] = {}
        for path in rows:
            stat = path.stat()
            groups.setdefault((stat.st_dev, stat.st_ino), []).append(path)
        for paths in groups.values():
            if paths[0].stat().st_nlink != len(paths):
                skipped_external_links += len(paths)
                for path in paths:
                    del rows[path]
    # Verify the entire selected set before replacing even one directory entry.
    for path, expected in rows.items():
        if hashes(path) != expected:
            raise ValueError(f"Manifest SHA256 mismatch: {path}")
    before = shutil.disk_usage(root).free
    canonical: dict[tuple[int, str], Path] = {}
    operations = []
    skipped_read_only = 0
    skipped_permission_denied = 0
    link_counts: dict[tuple[int, int], int] = {}
    for path in rows:
        stat = path.stat()
        link_counts[(stat.st_dev, stat.st_ino)] = stat.st_nlink
    with (output / "operations.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        for path in sorted(rows, key=lambda p: -p.stat().st_size):
            stat = path.stat()
            # Do not remove read-only protection merely to save space. On
            # Windows a hardlink shares this attribute with its source, so
            # read-only members are not used as canonical link sources either.
            if getattr(stat, 'st_file_attributes', 0) & 1:
                skipped_read_only += 1
                continue
            expected = rows[path]
            key = stat.st_size, expected
            source = canonical.setdefault(key, path)
            if os.path.samefile(source, path):
                continue
            if hashes(source) != expected or hashes(path) != expected:
                raise ValueError(f"Output changed before compaction: {path}")
            _checked(source, root)
            _checked(path, root)
            source_stat = source.stat()
            source_inode = source_stat.st_dev, source_stat.st_ino
            target_inode = stat.st_dev, stat.st_ino
            if rollback_only and (source_stat.st_nlink != link_counts[source_inode]
                                  or stat.st_nlink != link_counts[target_inode]):
                raise ValueError("Rollback pool link inventory changed")
            temporary = path.with_name(".dedup-" + uuid.uuid4().hex)
            row = dict(source=str(source), target=str(path), sha256=expected,
                       reclaimable_bytes=stat.st_size if stat.st_nlink == 1 else 0)
            log.write(json.dumps(dict(state="before", **row)) + "\n")
            log.flush()
            os.link(source, temporary)
            try:
                if hashes(temporary) != expected or _Hashes.identity(path.stat()) != _Hashes.identity(stat):
                    raise ValueError(f"Output changed during compaction: {path}")
                try:
                    os.replace(temporary, path)
                except PermissionError:
                    # A live handle/ACL may protect an otherwise immutable
                    # target. Leave it in place; never chmod or retry it.
                    if hashes(path) != expected or _Hashes.identity(path.stat()) != _Hashes.identity(stat):
                        raise ValueError(f"Denied target changed during compaction: {path}")
                    skipped_permission_denied += 1
                    log.write(json.dumps(dict(state="skipped-permission-denied", **row)) + "\n")
                    log.flush()
                    continue
                link_counts[source_inode] += 1
                link_counts[target_inode] -= 1
            finally:
                if temporary.exists():
                    temporary.unlink()
            if hashes(path) != expected or not os.path.samefile(source, path):
                raise ValueError(f"Compaction verification failed: {path}")
            operations.append(row)
            log.write(json.dumps(dict(state="after", **row)) + "\n")
            log.flush()
    if rollback_only:
        current_counts: dict[tuple[int, int], int] = {}
        for path in rows:
            stat = path.stat()
            inode = stat.st_dev, stat.st_ino
            current_counts[inode] = current_counts.get(inode, 0) + 1
        for path in rows:
            stat = path.stat()
            if stat.st_nlink != current_counts[(stat.st_dev, stat.st_ino)]:
                raise ValueError("Rollback pool acquired an unlisted hardlink")
    for path, expected in {**rows, **manifest_hashes}.items():
        if hashes(path) != expected:
            raise ValueError(f"Post-compaction SHA256 mismatch: {path}")
    report = dict(verified_files=len(rows), verified_manifests=len(manifest_hashes),
                  mode="independent-rollback-pool" if rollback_only else "immutable-output-pool",
                  rollback_pool_independence_verified=rollback_only,
                  skipped_external_links=skipped_external_links,
                  skipped_read_only=skipped_read_only,
                  skipped_permission_denied=skipped_permission_denied,
                  linked_files=len(operations), all_hashes_unchanged=True,
                  reclaimable_bytes=sum(row["reclaimable_bytes"] for row in operations),
                  free_before=before, free_after=shutil.disk_usage(root).free)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-space-only", action="store_true")
    group.add_argument("--manifest", action="append", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--rollback-only", action="store_true",
                        help="Separate backup-only pool; never merge with candidate/control/live inodes")
    args = parser.parse_args()
    try:
        if args.check_space_only:
            print(json.dumps(dict(free_bytes=require_disk_space(args.root), minimum_bytes=16 * 2**30)))
        else:
            if args.output_dir is None:
                raise ValueError("Compaction requires a new --output-dir")
            print(json.dumps(compact_outputs(args.manifest, args.root, args.output_dir,
                                             rollback_only=args.rollback_only)))
    except (ValueError, OSError) as error:
        parser.exit(2, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
