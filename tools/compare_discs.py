"""Compare fully hashed XDVDFS inventories. Metadata only; never merge resources."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_files(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), list):
        raise ValueError("invalid inventory")
    if type(manifest.get("image_size")) is not int or manifest["image_size"] <= 0:
        raise ValueError("invalid image size")
    if not re.fullmatch(r"[0-9a-f]{64}", manifest.get("sha256", "")):
        raise ValueError("inventory requires whole-image SHA256")
    files, seen = {}, set()
    for row in manifest["entries"]:
        if not isinstance(row, dict):
            raise ValueError("invalid record")
        name = row.get("path")
        if not isinstance(name, str) or not name or any(c in name for c in "\\:\0"):
            raise ValueError("invalid member path")
        path = PurePosixPath(name)
        if path.is_absolute() or any(x in ("", ".", "..") for x in name.split("/")):
            raise ValueError("unsafe member path")
        if name.casefold() in seen:
            raise ValueError("duplicate/case-colliding member path")
        seen.add(name.casefold())
        if type(row.get("directory")) is not bool:
            raise ValueError("missing directory flag")
        if any(type(row.get(k)) is not int or row[k] < 0 for k in ("offset", "size")) or row["offset"] + row["size"] > manifest["image_size"]:
            raise ValueError("member extent outside image")
        if row["directory"]:
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise ValueError("every file requires full SHA256; use --hash-files")
        files[name] = {k: row[k] for k in ("size", "offset", "sha256")}
    return files


def compare(left, right):
    a, b = checked_files(left), checked_files(right)
    # Case variants are not implicitly merged: they need manual resolution first.
    spellings = {}
    for name in sorted(a.keys() | b.keys()):
        if name.casefold() in spellings and spellings[name.casefold()] != name:
            raise ValueError("cross-disc case collision")
        spellings[name.casefold()] = name
    rows, counts = [], Counter()
    for name in sorted(a.keys() | b.keys()):
        l, r = a.get(name), b.get(name)
        state = "disc2-only" if l is None else "disc1-only" if r is None else "identical" if (l["size"], l["sha256"]) == (r["size"], r["sha256"]) else "conflict"
        counts[state] += 1
        rows.append(dict(path=name, status=state, disc1=l, disc2=r))
    return dict(schema_version=1, comparison="exact-path/full-SHA256-and-size", merge_performed=False,
                inputs=[{k: m[k] for k in ("image", "image_size", "sha256")} for m in (left, right)],
                counts={k: counts[k] for k in ("identical", "conflict", "disc1-only", "disc2-only")}, files=rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("disc1", type=Path); p.add_argument("disc2", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        raw = [q.read_bytes() for q in (args.disc1, args.disc2)]
        result = compare(*(json.loads(x) for x in raw))
        result["inventory_sha256"] = [digest(x) for x in raw]
        # Exclusive create: no source, output or symlink target is overwritten.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, indent=2); f.write("\n")
        print(json.dumps(dict(**result["counts"], merge_performed=False), sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("ERROR: " + str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
