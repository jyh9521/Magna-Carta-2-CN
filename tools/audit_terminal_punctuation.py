"""Audit complete localized messages using explicit locale sentence rules.

Visual line breaks do not end logical sentences. Numeric stat lines, names,
dialogue and runtime fragments have separate, source-reviewed classifications.
This tool reports; publication still uses the hash-guarded Coalesced rebuilder.
"""
import argparse
import json
from pathlib import Path
import re

from .coalesced import parse, extract_entries
from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .validate_catalog import TOKEN


def needs_stop(text, rules):
    visible = TOKEN.sub('', text).strip().strip('"').strip()
    visible = re.sub(rules.get('annotation_pattern', r'(?!)'), '', visible).strip()
    if not visible:
        return False
    # Quoted punctuation remains a valid ending. A trailing reference bracket
    # alone does not turn an unfinished sentence into a finished one.
    end = visible.rstrip(rules['closing_characters']).rstrip()
    if not end or end[-1] in rules['endings']:
        return False
    body = re.sub(r'(?<=\d)[.,](?=\d)', '', visible)
    return bool(re.search(rules['internal_pattern'], body[:-1]))


def corrected(text, kind, rules):
    if kind not in rules['sentence_kinds']:
        return text
    # Keep whitespace, markup, literal breaks and numeric stat rows byte-exact.
    separate_choices = kind in rules.get('choice_kinds', []) and len(re.findall(rules['choice_marker_pattern'], text)) > 1
    chunks = re.split(r'(\\n|\n)' if separate_choices else r'(\\n\\n|\n\n)', text)
    for i in range(0, len(chunks), 2):
        chunk = chunks[i]
        lines = re.split(r'(\\n|\n)', chunk)
        j = len(lines)
        if kind in rules['stat_line_kinds']:
            while j and (not lines[j-1].strip() or re.fullmatch(rules['stat_line_pattern'], TOKEN.sub('', lines[j-1]).strip())):
                j = max(0, j-2)
        body = ''.join(lines[:j])
        if needs_stop(body, rules):
            trimmed = body.rstrip()
            body = trimmed + rules['full_stop'] + body[len(trimmed):]
            chunks[i] = body + ''.join(lines[j:])
    return ''.join(chunks)


def classifications(contract, project):
    kinds = {}
    for ref in contract['classification_sources']:
        raw = confined_path(Path(project).resolve(), ref['path']).read_bytes()
        if digest(raw) != ref['sha256']:
            raise ValueError('classification source SHA256 mismatch')
        for row in json.loads(raw)['entries']:
            if row.get('text_kind'):
                kinds[row['id']] = row['text_kind']
    for row in contract['classification_overrides']:
        if row['id'] not in kinds or kinds[row['id']] != row['before']:
            raise ValueError('classification override changed')
        kinds[row['id']] = row['after']
    return kinds


def audit(data, contract, project):
    if contract.get('kind') != 'terminal-punctuation-audit-v1':
        raise ValueError('unsupported punctuation contract')
    rows = extract_entries(parse(data), contract['resource'])
    if len(rows) != contract['entry_count']:
        raise ValueError('text inventory coverage changed')
    kinds = classifications(contract, project)
    violations, counts = [], {}
    for row in rows:
        kind = kinds.get(row['id'], 'unlocalized')
        counts[kind] = counts.get(kind, 0) + 1
        proposed = corrected(row['source'], kind, contract['rules'])
        if proposed != row['source']:
            violations.append(dict(id=row['id'], text_kind=kind,
                source_sha256=digest(row['source'].encode()), translation=proposed))
    return dict(schema_version=1, rows=len(rows), classifications=counts,
                violations=violations, passed=not violations, game_started=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('input', 'contract', 'report'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--project', type=Path, default=Path('.'))
    a = p.parse_args()
    result = audit(a.input.read_bytes(), json.loads(a.contract.read_bytes()), a.project)
    raw = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode()
    a.report.write_bytes(raw)
    if a.report.read_bytes() != raw:
        raise ValueError('report readback mismatch')
    print(f"ROWS={result['rows']} MISSING_TERMINATORS={len(result['violations'])} "
          f"RESULT={'PASS' if result['passed'] else 'FAIL'}")
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
