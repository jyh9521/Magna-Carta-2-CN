"""Read-only XDVDFS inventory and explicit selected extraction (Python stdlib)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

SECTOR = 2048
MAGIC = b"MICROSOFT*XBOX*MEDIA"
BASES = (0, 0xFD90000, 0x2080000, 0x18300000)


class FormatError(ValueError):
    """Malformed or unsupported disc image."""


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class Disc:
    def __init__(self, path, base=None):
        self.path = Path(path)
        self.size = self.path.stat().st_size
        candidates = BASES if base is None else (base,)
        matches = []
        for offset in candidates:
            if offset >= 0 and offset + 0x10800 <= self.size:
                header = self.read(offset + 0x10000, SECTOR)
                if header[:20] == MAGIC and header[-20:] == MAGIC:
                    matches.append((offset, header))
        if len(matches) != 1:
            raise FormatError("expected exactly one XDVDFS descriptor; specify --base")
        self.base, header = matches[0]
        self.root_sector, self.root_size = struct.unpack_from("<II", header, 20)
        self.timestamp_raw = header[28:36].hex()

    def read(self, offset, size):
        if offset < 0 or size < 0 or offset + size > self.size:
            raise FormatError("extent outside image")
        with self.path.open("rb") as stream:
            stream.seek(offset)
            data = stream.read(size)
        if len(data) != size:
            raise FormatError("short image read")
        return data

    def inventory(self):
        records = []
        directories = set()
        paths = set()
        pending = [("", self.root_sector, self.root_size)]
        while pending:
            parent, sector, length = pending.pop()
            if length == 0:
                continue
            key = (sector, length)
            if key in directories:
                raise FormatError("repeated or cyclic directory extent")
            directories.add(key)
            if length > 64 * 1024 * 1024:
                raise FormatError("directory exceeds 64 MiB safety limit")
            table = self.read(self.base + sector * SECTOR, length)
            nodes, seen, spans = [0], set(), []
            while nodes:
                offset = nodes.pop()
                if offset in seen:
                    raise FormatError("repeated or cyclic tree pointer")
                seen.add(offset)
                if offset + 14 > length:
                    raise FormatError("truncated directory record")
                left, right, start, size, flags, name_len = struct.unpack_from("<HHIIBB", table, offset)
                end = offset + 14 + name_len
                if not name_len or end > length:
                    raise FormatError("invalid filename length")
                if any(offset < b and end > a for a, b in spans):
                    raise FormatError("overlapping directory records")
                spans.append((offset, end))
                name = table[offset + 14:end].decode("ascii", errors="strict")
                reserved = name.split(".")[0].upper()
                if (name in (".", "..") or name.endswith((".", " "))
                        or any(c in name for c in '/\\:\x00<>"|?*')
                        or any(ord(c) < 32 for c in name)
                        or reserved in {"CON", "PRN", "AUX", "NUL"}
                        or reserved in {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}):
                    raise FormatError("unsafe filename")
                path = parent + name
                if path.casefold() in paths:
                    raise FormatError("duplicate case-insensitive path")
                paths.add(path.casefold())
                absolute = self.base + start * SECTOR
                if absolute + size > self.size:
                    raise FormatError("file extent outside image")
                is_dir = bool(flags & 0x10)
                records.append(dict(path=path, directory=is_dir, sector=start,
                                    offset=absolute, size=size, attributes=flags))
                if len(records) > 1_000_000:
                    raise FormatError("entry count exceeds safety limit")
                if is_dir:
                    pending.append((path + "/", start, size))
                nodes.extend(x * 4 for x in (right, left) if x)
        return sorted(records, key=lambda r: r["path"].casefold())

    def resource_hash(self, record):
        h = hashlib.sha256()
        with self.path.open("rb") as stream:
            stream.seek(record["offset"])
            remaining = record["size"]
            while remaining:
                block = stream.read(min(8 * 1024 * 1024, remaining))
                if not block:
                    raise FormatError("short resource read")
                h.update(block)
                remaining -= len(block)
        return h.hexdigest()

    def extract(self, record, destination):
        """Caller chooses an exact source path; output never overwrites existing files."""
        if record["directory"]:
            raise FormatError("select a file, not a directory")
        root = Path(destination).resolve()
        target = root.joinpath(*record["path"].split("/")).resolve()
        if not target.is_relative_to(root) or target == self.path.resolve():
            raise FormatError("extraction path escapes output root")
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("rb") as source, target.open("xb") as out:
            source.seek(record["offset"])
            remaining = record["size"]
            while remaining:
                block = source.read(min(1024 * 1024, remaining))
                if not block:
                    raise FormatError("short resource read")
                out.write(block)
                remaining -= len(block)
        return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--base", type=lambda x: int(x, 0))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hash-image", action="store_true")
    parser.add_argument("--hash-files", action="store_true")
    parser.add_argument("--extract", action="append", default=[], help="exact inventory path; repeatable")
    parser.add_argument("--extract-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.extract and args.extract_dir is None:
            raise FormatError("--extract requires --extract-dir")
        if args.output.resolve() == args.image.resolve() or (args.output.exists() and args.output.samefile(args.image)):
            raise FormatError("inventory output must differ from image")
        disc = Disc(args.image, args.base)
        records = disc.inventory()
        if args.hash_files:
            for record in records:
                if not record["directory"]:
                    record["sha256"] = disc.resource_hash(record)
        selected = []
        for path in args.extract:
            matches = [r for r in records if r["path"] == path and not r["directory"]]
            if len(matches) != 1:
                raise FormatError("selected file not found: " + path)
            selected.append(matches[0])
        result = dict(image=args.image.name, image_size=disc.size, partition_base=disc.base,
                      root_sector=disc.root_sector, root_size=disc.root_size,
                      timestamp_raw=disc.timestamp_raw, entries=records)
        if args.hash_image:
            result["sha256"] = sha256_file(args.image)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2, ensure_ascii=False)
            output.write("\n")
        for record in selected:
            print(disc.extract(record, args.extract_dir))
        print(f"files={sum(not r['directory'] for r in records)} directories={sum(r['directory'] for r in records)} base=0x{disc.base:x}")
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
