"""Pinned, read-only series terminology references; never rewrite translations."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dumps(data):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_lock(lock):
    if lock.get("schema") != 1 or not isinstance(lock.get("references"), list):
        raise ValueError("invalid reference lock")
    ids = set()
    for ref in lock["references"]:
        if not re.fullmatch(r"[a-z0-9-]+", ref["id"]) or ref["id"] in ids:
            raise ValueError("invalid/duplicate reference id")
        ids.add(ref["id"])
        if not re.fullmatch(r"[0-9a-f]{40}", ref["commit"]):
            raise ValueError("reference requires full commit")
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", ref["repository"]):
            raise ValueError("invalid GitHub repository")
        for item in ref["files"]:
            p = PurePosixPath(item["path"])
            if p.is_absolute() or ".." in p.parts or "\\" in item["path"] or ":" in item["path"]:
                raise ValueError("invalid reference path")
            if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                raise ValueError("invalid reference hash")
    return lock


def cached_bytes(cache, ref, item):
    data = (Path(cache) / ref["id"] / item["path"]).read_bytes()
    if digest(data) != item["sha256"]:
        raise ValueError(f"reference hash mismatch: {ref['id']}/{item['path']}")
    return data


def fetch(lock, cache):
    checked_lock(lock)
    count = 0
    for ref in lock["references"]:
        for item in ref["files"]:
            dest = Path(cache) / ref["id"] / item["path"]
            if dest.exists():
                cached_bytes(cache, ref, item)
            else:
                url = f"https://raw.githubusercontent.com/{ref['repository']}/{ref['commit']}/{item['path']}"
                with urllib.request.urlopen(url, timeout=60) as response:
                    data = response.read()
                if digest(data) != item["sha256"]:
                    raise ValueError(f"download hash mismatch: {url}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            count += 1
    return {"verified_files": count, "references": len(lock["references"])}


def markdown_rows(text):
    """Only the five-column source glossary table, not later gender tables."""
    active = False
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            active = line.strip() == "## 术语表"
        if not active or not line.startswith("|"):
            continue
        cells = [s.strip().replace(r"\|", "|") for s in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) != 5 or cells[0] == "Korean / 源文" or all(re.fullmatch(r"[-: ]+", c) for c in cells):
            continue
        source, target, category, state, context = cells
        rows.append({"source": source, "target": target, "category": category,
                     "translation_state": state, "relation": "unverified", "context": context,
                     "source_id": f"GLOSSARY.md:{number}", "path": "GLOSSARY.md", "line": number})
    return rows


def reference_terms(lock, cache):
    checked_lock(lock)
    result = []
    for ref in lock["references"]:
        files = {item["path"]: cached_bytes(cache, ref, item) for item in ref["files"]}
        if ref["format"] == "structured-terms-v1":
            data = json.loads(files[ref["canonical_path"]])
            rows = [{"source": t["source"], "target": t["target"], "category": t["category"],
                     "translation_state": t["translation_state"], "relation": t["relation"],
                     "context": t["meaning"], "source_id": t["id"], "path": ref["canonical_path"],
                     "resource_ids": t["resource_ids"], "upstream_status": t["status"],
                     "english_reference": t.get("english_reference"),
                     "reference_candidates": t.get("reference_candidates", [])} for t in data["terms"]]
        elif ref["format"] == "markdown-five-column":
            rows = markdown_rows(files[ref["canonical_path"]].decode("utf-8-sig"))
        else:
            raise ValueError("unknown reference format")
        for row in rows:
            row.update(reference=ref["id"], repository=ref["repository"], commit=ref["commit"])
            result.append(row)
    return result


def lookup(rows, phrase, variants=()):
    """No normalization, substring, fuzzy match or concept inference."""
    spellings = {phrase, *variants}
    return [row for row in rows if row["source"] in spellings or row.get("english_reference") in spellings]


def audit(rows):
    by_source = defaultdict(list)
    stats = defaultdict(Counter)
    for row in rows:
        by_source[row["source"]].append(row)
        stats[row["reference"]][row["translation_state"]] += 1
    conflicts = []
    shared = []
    internal = []
    for source, group in sorted(by_source.items()):
        targets = {row["target"] for row in group}
        refs = {row["reference"] for row in group}
        if len(refs) > 1:
            shared.append(source)
        if len(targets) > 1:
            issue = {"source": source, "concept_relation": "pending-human-review", "candidates": group}
            (conflicts if len(refs) > 1 else internal).append(issue)
    return {"counts": {k: dict(v) for k, v in sorted(stats.items())},
            "total": len(rows), "shared_exact_phrases": len(shared),
            "cross_reference_conflicts": conflicts, "within_reference_conflicts": internal,
            "inherited_terms": 0}


def validate_terms(data, rows=(), translations=()):
    errors = []
    if data.get("schema") != 1 or not data.get("locale") or not isinstance(data.get("terms"), list):
        return ["invalid project terms schema"]
    ids, groups = {}, defaultdict(list)
    for term in data["terms"]:
        tid = term.get("id", "<missing>")
        required = ["id", "source", "target", "category", "resource", "source_string_id", "review_status", "relation", "basis", "form", "series_references"]
        for key in required:
            if key not in term or term[key] in (None, ""):
                errors.append(f"{tid}: missing {key}")
        if tid in ids:
            errors.append(f"{tid}: duplicate id")
        ids[tid] = term
        if term.get("review_status") not in {"candidate", "reviewed", "in-game-verified"}:
            errors.append(f"{tid}: invalid review status")
        if term.get("relation") not in {"unverified", "same-concept", "different-concept"}:
            errors.append(f"{tid}: invalid concept relation")
        if term.get("form") not in {"full-name", "short-name", "title", "alias", "term"}:
            errors.append(f"{tid}: invalid name form")
        groups[term.get("source", "")].append(term)
        refs = term.get("series_references", [])
        if term.get("relation") == "same-concept" and not refs:
            errors.append(f"{tid}: same-concept requires reference")
        for ref in refs:
            matches = [r for r in rows if all(r.get(k) == ref.get(k) for k in ["reference", "commit", "source_id", "source", "target"])]
            if not matches:
                errors.append(f"{tid}: reference identity/translation not found in pinned sources")
            if ref.get("source") != term.get("source") and not term.get("variant_basis"):
                errors.append(f"{tid}: spelling variant requires evidence")
            if term.get("relation") == "same-concept" and term.get("target") != ref.get("target") and not term.get("override_reason"):
                errors.append(f"{tid}: confirmed series term changed without override reason")
    for source, group in groups.items():
        if len({t.get("target") for t in group}) > 1 and any(not t.get("disambiguation") for t in group):
            errors.append(f"{source}: multiple targets require per-concept disambiguation")
    for tr in translations:
        for tid in tr.get("term_ids", []):
            term = ids.get(tid)
            if not term:
                errors.append(f"{tr.get('id')}: unknown term {tid}")
            elif term.get("review_status") == "candidate":
                errors.append(f"{tr.get('id')}: unreviewed candidate {tid}")
            if term and tid in tr.get("term_forms", {}) and tr["term_forms"][tid] != term.get("form"):
                errors.append(f"{tr.get('id')}: name form mismatch for {tid}")
    # Candidate phrase presence is a review signal, not a global replacement rule.
    for term in data["terms"]:
        if term.get("review_status") == "candidate" and term.get("target"):
            for tr in translations:
                if term["target"] in tr.get("target", ""):
                    errors.append(f"{tr.get('id')}: candidate wording present: {term['id']}")
    return sorted(set(errors))


def compare(old, new):
    """Report additions/removals/metadata changes; never update a lock or target."""
    def index(rows):
        return {(r["reference"], r["source_id"]): r for r in rows}
    a, b = index(old), index(new)
    return {"added": [b[k] for k in sorted(b.keys()-a.keys())],
            "removed": [a[k] for k in sorted(a.keys()-b.keys())],
            "changed": [{"before": a[k], "after": b[k]} for k in sorted(a.keys() & b.keys())
                        if {x: y for x, y in a[k].items() if x != "commit"} != {x: y for x, y in b[k].items() if x != "commit"}]}


def glossary(data):
    lines = ["# 《真名法典2》简体中文术语表", "", "本表由 `locales/zh-Hans/terms.json` 生成。系列参考不是本作确认词条。", "",
             "| ID | 原词 | 中文 | 分类 | 称呼形式 | 审核 | 跨作品关系 | 资源 / 字符串 ID |", "|---|---|---|---|---|---|---|---|"]
    for t in data["terms"]:
        values = [t["id"], t["source"], t["target"], t["category"], t["form"], t["review_status"], t["relation"], t["resource"]+" / "+t["source_string_id"]]
        lines.append("| " + " | ".join(str(v).replace("|", r"\|").replace("\n", "<br>") for v in values) + " |")
    lines += ["", f"本作词条：{len(data['terms'])}；已继承：{sum(t.get('relation') == 'same-concept' for t in data['terms'])}。", "", "固定来源、统计、冲突与审核流程见 [系列术语参考](docs/SERIES_TERMS.md)。", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=ROOT / "references/series.lock.json")
    parser.add_argument("--cache", type=Path, default=ROOT / "build/series-references")
    parser.add_argument("--terms", type=Path, default=ROOT / "locales/zh-Hans/terms.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch")
    sub.add_parser("audit")
    query = sub.add_parser("lookup")
    query.add_argument("phrase")
    query.add_argument("--variant", action="append", default=[])
    check = sub.add_parser("check")
    check.add_argument("--with-references", action="store_true")
    check.add_argument("--translations", type=Path)
    render = sub.add_parser("render")
    render.add_argument("--output", type=Path, default=ROOT / "GLOSSARY.md")
    render.add_argument("--check", action="store_true")
    diff = sub.add_parser("compare")
    diff.add_argument("--other-lock", type=Path, required=True)
    diff.add_argument("--other-cache", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        lock = checked_lock(load(args.lock))
        if args.command == "fetch":
            output = fetch(lock, args.cache)
        elif args.command == "render":
            content = glossary(load(args.terms))
            if args.check:
                if args.output.read_text(encoding="utf-8") != content:
                    raise ValueError("generated glossary out of date")
            else:
                args.output.write_text(content, encoding="utf-8", newline="\n")
            output = {"glossary": "current"}
        elif args.command == "check":
            rows = reference_terms(lock, args.cache) if args.with_references else []
            terms = load(args.terms)
            if not args.with_references and any(t.get("series_references") for t in terms["terms"]):
                raise ValueError("referenced project terms require --with-references")
            errors = validate_terms(terms, rows, load(args.translations)["translations"] if args.translations else [])
            output = {"terms": len(terms["terms"]), "errors": errors}
            print(dumps(output), end="")
            return int(bool(errors))
        else:
            rows = reference_terms(lock, args.cache)
            if args.command == "audit":
                output = audit(rows)
            elif args.command == "lookup":
                output = {"phrase": args.phrase, "match": "exact-explicit-variants-only", "candidates": lookup(rows, args.phrase, args.variant), "automatic_inheritance": False}
            else:
                output = compare(rows, reference_terms(checked_lock(load(args.other_lock)), args.other_cache))
        print(dumps(output), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
