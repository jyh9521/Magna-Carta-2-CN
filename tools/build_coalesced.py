"""Rebuild a hash-locked Coalesced copy; never deploy or overwrite input."""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

try:
    from .coalesced import MAX_BYTES, extract_entries, parse, serialize
    from .validate_catalog import TOKEN, token_errors
    from .font_binding_plan import parse_json_object
except ImportError:
    from coalesced import MAX_BYTES, extract_entries, parse, serialize
    from validate_catalog import TOKEN, token_errors
    from font_binding_plan import parse_json_object


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def resolve_prefix(source, edit, row):
    """Replace an explicitly bounded Unicode prefix; preserve the exact suffix."""
    allowed = {'id','source_sha256','source_prefix_codepoints','replacement','preserve_utf16_units','selector'}
    if set(edit)-allowed or not {'source_prefix_codepoints','replacement','preserve_utf16_units'} <= set(edit):
        raise ValueError('invalid prefix edit fields')
    count, replacement = edit['source_prefix_codepoints'], edit['replacement']
    if type(count) is not int or not 0 <= count <= len(source) or not isinstance(replacement,str):
        raise ValueError('prefix codepoint range/replacement invalid')
    if type(edit['preserve_utf16_units']) is not bool:
        raise ValueError('prefix UTF16 preservation flag must be boolean')
    if any(m.start() < count < m.end() for m in TOKEN.finditer(source)):
        raise ValueError('prefix boundary splits a protected token')
    original_units = len(source[:count].encode('utf-16-le'))//2
    replacement_units = len(replacement.encode('utf-16-le'))//2
    if edit['preserve_utf16_units'] and original_units != replacement_units:
        raise ValueError('prefix UTF16 length changed')
    selector = {key:row[key] for key in ('embedded_path','section','key','occurrence')}
    if 'selector' in edit:
        supplied = edit['selector']
        if (not isinstance(supplied,dict) or set(supplied) != set(selector)
                or any(not isinstance(supplied[k],str) for k in ('embedded_path','section','key'))
                or type(supplied['occurrence']) is not int or supplied != selector):
            raise ValueError('prefix entry selector mismatch')
    target = replacement + source[count:]
    if TOKEN.findall(source) != TOKEN.findall(target):
        raise ValueError('protected token content or order changed')
    return target, dict(source_prefix_codepoints=count,source_prefix_utf16_units=original_units,
                       replacement_utf16_units=replacement_units,preserved_suffix_sha256=sha256(source[count:].encode('utf8')),
                       source_selector=selector)


def resolve_changes(data, changes):
    """Resolve optional source hashes without publishing original text in locale data."""
    if (not isinstance(changes, dict) or type(changes.get("schema_version")) is not int
            or changes.get("schema_version") != 1):
        raise ValueError("unsupported changes schema")
    mode = changes.get('source_mode', 'literal')
    if mode == 'literal':
        if isinstance(changes.get('entries'),list) and any(isinstance(e,dict) and any(k in e for k in
                ('source_prefix_codepoints','replacement','preserve_utf16_units','selector')) for e in changes['entries']):
            raise ValueError('prefix fields require explicit prefix source mode')
        return changes
    if mode not in ('sha256-utf8','sha256-utf8-prefix'):
        raise ValueError('unsupported source verification mode')
    if sha256(data) != changes.get('input_sha256'):
        raise ValueError('input SHA256 mismatch')
    resource = changes.get('resource')
    if not isinstance(resource, str) or not resource or not isinstance(changes.get('entries'), list):
        raise ValueError('invalid source-hash changes envelope')
    rows = {r['id']:r for r in extract_entries(parse(data), resource)}
    edits, seen = [], set()
    for edit in changes['entries']:
        if (not isinstance(edit, dict) or 'source' in edit
                or not isinstance(edit.get('id'), str)
                or not isinstance(edit.get('source_sha256'), str)
                or not re.fullmatch('[0-9a-f]{64}', edit['source_sha256'])):
            raise ValueError('invalid source-hash edit')
        if mode == 'sha256-utf8' and (not isinstance(edit.get('translation'),str)
                or any(k in edit for k in ('source_prefix_codepoints','replacement','preserve_utf16_units','selector'))):
            raise ValueError('invalid or mixed full-value source-hash edit')
        identity = edit['id']
        if identity in seen or identity not in rows:
            raise ValueError('duplicate or unknown edit ID')
        seen.add(identity)
        source = rows[identity]['source']
        if sha256(source.encode('utf-8')) != edit['source_sha256']:
            raise ValueError('expected source UTF-8 SHA256 mismatch')
        if mode == 'sha256-utf8-prefix':
            target, metadata = resolve_prefix(source, edit, rows[identity])
            edits.append(dict(id=identity,source=source,translation=target,prefix_scope=metadata))
        else:
            row=dict(id=identity, source=source, translation=edit['translation'])
            if 'line_break_policy' in edit: row['line_break_policy']=edit['line_break_policy']
            edits.append(row)
    resolved = dict(changes, entries=edits)
    resolved.pop('source_mode')
    return resolved


def rebuild(data, changes):
    changes = resolve_changes(data, changes)
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
        if token_errors(source,target,edit.get('line_break_policy')):
            raise ValueError("protected token content or order changed; check explicit line break policy")
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
    args = p.parse_args(argv); created = False; output = None
    try:
        if args.input.stat().st_size > MAX_BYTES or args.changes.stat().st_size > MAX_BYTES:
            raise ValueError("input size limit")
        if args.output.exists() or args.output.is_symlink() or args.output.resolve() in (args.input.resolve(), args.changes.resolve()):
            raise ValueError("output must be new and distinct from inputs")
        original = args.input.read_bytes()
        raw_plan = args.changes.read_bytes()
        output = rebuild(original, parse_json_object(raw_plan))
        if args.input.read_bytes() != original or args.changes.read_bytes() != raw_plan:
            raise ValueError('text source/plan changed before publication')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            created = True
            stream.write(output)
        if args.output.is_symlink() or args.output.read_bytes() != output:
            raise ValueError('text output byte reopening mismatch')
        if args.input.read_bytes() != original or args.changes.read_bytes() != raw_plan:
            raise ValueError('text source/plan changed after publication')
        print(json.dumps(dict(input_sha256=sha256(original), output_sha256=sha256(output),
                              input_size=len(original), output_size=len(output),
                              reextract_equal=True, deployed=False), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        if created:
            try:
                if not args.output.is_symlink() and args.output.read_bytes() == output:
                    args.output.unlink()
            except OSError:
                pass
        print("ERROR: " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
