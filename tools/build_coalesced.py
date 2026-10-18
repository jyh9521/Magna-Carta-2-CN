"""Rebuild a hash-locked Coalesced copy; never deploy or overwrite input."""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

try:
    from .coalesced import MAX_BYTES, extract_entries, parse, serialize
    from .validate_catalog import TOKEN
except ImportError:
    from coalesced import MAX_BYTES, extract_entries, parse, serialize
    from validate_catalog import TOKEN


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rebuild(data, changes):
    if changes.get("schema_version") != 1:
        raise ValueError("unsupported changes schema")
    if sha256(data) != changes.get("input_sha256"):
        raise ValueError("input SHA256 mismatch")
    resource = changes.get("resource")
    if not isinstance(resource, str) or not resource:
        raise ValueError("resource identity required")
    edits = changes.get("entries")
    if not isinstance(edits, list):
        raise ValueError("entries must be a list")
    files = parse(data)
    original = extract_entries(files, resource)
    index = {r["id"]: r for r in original}
    by_document, seen = {}, set()
    for edit in edits:
        if not isinstance(edit, dict) or not all(isinstance(edit.get(k), str) for k in ("id", "source", "translation")):
            raise ValueError("invalid edit")
        identity, source, target = (edit[k] for k in ("id", "source", "translation"))
        if identity in seen or identity not in index:
            raise ValueError("duplicate or unknown edit ID")
        seen.add(identity)
        row = index[identity]
        if source != row["source"]:
            raise ValueError("expected source mismatch")
        if any(c in target for c in "\r\n\0"):
            raise ValueError("physical newline/NUL in replacement; use verified literal tokens")
        if TOKEN.findall(source) != TOKEN.findall(target):
            raise ValueError("protected token content or order changed")
        by_document.setdefault(row["embedded_path"], []).append((row, target))
    rebuilt = []
    for document in files:
        pending = by_document.get(document.path.text, [])
        if not pending:
            rebuilt.append(document)
            continue
        lines = document.content.text.splitlines(keepends=True)
        for row, target in pending:
            old = lines[row["line"] - 1]
            body = old.rstrip("\r\n")
            ending = old[len(body):]
            prefix, separator, value = body.partition("=")
            if not separator or value != row["source"]:
                raise ValueError("physical line identity mismatch")
            lines[row["line"] - 1] = prefix + "=" + target + ending
        rebuilt.append(replace(document, content=replace(document.content, text="".join(lines))))
    output = serialize(rebuilt)
    after = extract_entries(parse(output), resource)
    after_index = {r["id"]: r for r in after}
    expected = {e["id"]: e["translation"] for e in edits}
    if index.keys() != after_index.keys():
        raise ValueError("re-extraction identity changed")
    for identity, row in index.items():
        if after_index[identity]["source"] != expected.get(identity, row["source"]):
            raise ValueError("re-extraction value mismatch")
    if not edits and output != data:
        raise ValueError("unmodified rebuild is not byte-identical")
    return output


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("changes", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        if args.input.stat().st_size > MAX_BYTES:
            raise ValueError("input size limit")
        if args.output.resolve() in (args.input.resolve(), args.changes.resolve()):
            raise ValueError("output aliases input")
        original = args.input.read_bytes()
        output = rebuild(original, json.loads(args.changes.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(output)
        print(json.dumps(dict(input_sha256=sha256(original), output_sha256=sha256(output),
                              input_size=len(original), output_size=len(output),
                              reextract_equal=True, deployed=False), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("ERROR: " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
