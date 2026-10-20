"""Guarded first-size-field updates for an isolated Xbox360TOC.txt prototype.

This does not update ISO sectors, unknown TOC fields, or any game resources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

LINE = re.compile(rb"([0-9]+) ([0-9]+) ([0-9]+) (.+) ([0-9]+)")
UINT32_MAX = (1 << 32) - 1


def normalize_path(value):
    """Only normalize separators and one TOC-relative leading ../ component."""
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("path must be nonempty ASCII")
    value = value.replace("\\", "/")
    if value.startswith("../"):
        value = value[3:]
    if (any(part in ("", ".", "..") for part in value.split("/"))
            or any(ord(c) < 32 or ord(c) == 127 or c == ":" for c in value)):
        raise ValueError("invalid resource path")
    return value


def validate_size(value, label):
    if type(value) is not int or not 0 < value <= UINT32_MAX:
        raise ValueError(f"{label} must be an integer in 1..{UINT32_MAX}")
    return value


def update_sizes(source, expected_sha256, changes):
    """Return bytes with only explicitly requested first numeric spans replaced."""
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected SHA-256 must contain 64 hexadecimal digits")
    if hashlib.sha256(source).hexdigest() != expected_sha256.lower():
        raise ValueError("source TOC SHA-256 mismatch")
    source.decode("ascii")
    if not isinstance(changes, list) or not changes:
        raise ValueError("changes must be a nonempty JSON array")
    requested = {}
    folded = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"path", "expected_size", "new_size"}:
            raise ValueError("each change requires exactly path, expected_size, new_size")
        path = normalize_path(change["path"])
        if path.casefold() in folded:
            raise ValueError("duplicate or case-ambiguous change target")
        folded.add(path.casefold())
        old = validate_size(change["expected_size"], "expected_size")
        new = validate_size(change["new_size"], "new_size")
        if old == new:
            raise ValueError("each requested size must actually change")
        requested[path] = (old, new)

    lines = source.splitlines(keepends=True)
    entries, folded = {}, set()
    for index, line in enumerate(lines):
        if line.endswith(b"\r\n"):
            body, ending = line[:-2], b"\r\n"
        elif line.endswith(b"\n"):
            body, ending = line[:-1], b"\n"
        else:
            body, ending = line, b""
        match = LINE.fullmatch(body)
        if match is None or b"\r" in body:
            raise ValueError(f"malformed TOC line {index + 1}")
        path = normalize_path(match[4].decode("ascii"))
        if path.casefold() in folded:
            raise ValueError("duplicate or case-ambiguous TOC path: " + path)
        folded.add(path.casefold())
        entries[path] = (index, match, ending)

    for path, (old, new) in requested.items():
        if path not in entries:
            raise ValueError("exact normalized target not found: " + path)
        index, match, ending = entries[path]
        current = int(match[1])
        if current == 0:
            raise ValueError("zero-size special entry cannot be updated")
        if current != old:
            raise ValueError("expected source size mismatch: " + path)
        lines[index] = str(new).encode("ascii") + match[0][match.end(1):] + ending
    return b"".join(lines)


def update_sizes_reversible(source, expected_sha256, changes):
    """Compute one combined table from its original, then prove the exact inverse."""
    if not isinstance(changes, list):
        raise ValueError('TOC changes must be a list')
    if (not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-fA-F]{64}',expected_sha256)
            or hashlib.sha256(source).hexdigest() != expected_sha256.lower()):
        raise ValueError('source TOC SHA256 mismatch')
    source.decode('ascii')
    output = update_sizes(source, expected_sha256, changes) if changes else source
    reverse = [dict(path=c['path'],expected_size=c['new_size'],new_size=c['expected_size']) for c in changes]
    if (update_sizes(output,hashlib.sha256(output).hexdigest(),reverse) if reverse else output) != source:
        raise ValueError('combined TOC inverse mismatch')
    return output, dict(changed_resources=len(changes),source_sha256=hashlib.sha256(source).hexdigest(),
                        candidate_sha256=hashlib.sha256(output).hexdigest(),inverse_byte_identical=True)


def write_updated(source_path, expected_sha256, changes, output_path):
    source_path, output_path = Path(source_path), Path(output_path)
    if source_path.resolve() == output_path.resolve():
        raise ValueError("output must differ from input")
    # Includes preexisting hardlinks and symlinks, not only matching path strings.
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError("output already exists")
    result = update_sizes(source_path.read_bytes(), expected_sha256, changes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as output:
        output.write(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_toc", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--changes", type=Path, required=True, help="JSON array file")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        changes = json.loads(args.changes.read_text(encoding="utf-8"))
        # Prevent using the change specification itself as an output destination.
        if args.output.resolve() == args.changes.resolve():
            raise ValueError("output must differ from changes JSON")
        result = write_updated(args.input_toc, args.sha256, changes, args.output)
        print(f"updated={len(changes)} bytes={len(result)} sha256={hashlib.sha256(result).hexdigest()}")
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
