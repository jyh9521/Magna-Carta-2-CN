"""通用本地化记录检查；不假定游戏的实际文本编码或资源布局。"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

TOKEN = re.compile(r"\{[A-Za-z_0-9]+(?:![rsa])?(?::[^{}]*)?\}|%(?:\d+\$)?[-+ #0]*(?:\d+|\*)?(?:\.\d+)?[sdifuoxXeEgGc]|\$n|\\[nrt0]|\^[0-9A-Fa-f]{2}|</?[^>]+>")
FIELDS = ("id", "resource", "context", "source_locale", "source", "translation", "status", "reviewer")


def token_errors(source, target, policy=None):
    """Only explicit, count-locked layout breaks may differ; all other tokens retain order."""
    a, b = TOKEN.findall(source), TOKEN.findall(target)
    if policy is not None:
        if (not isinstance(policy, dict) or set(policy) != {'source_count','target_count'}
                or any(type(v) is not int or not 0 <= v <= 1024 for v in policy.values())
                or a.count('\\n') != policy['source_count'] or b.count('\\n') != policy['target_count']):
            return ['invalid or mismatched explicit line break policy']
        a, b = [t for t in a if t != '\\n'], [t for t in b if t != '\\n']
    errors=[]
    if Counter(a) != Counter(b): errors.append('protected token mismatch')
    if a != b: errors.append('protected token order changed (not yet verified)')
    return errors


def validate(data, style_rules=None):
    errors, seen = [], set()
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
        return ["invalid catalog envelope"]
    for n, row in enumerate(data["entries"]):
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in FIELDS):
            errors.append(f"row {n}: missing or non-string field"); continue
        if not row["id"] or row["id"] in seen:
            errors.append(f"row {n}: empty or duplicate id")
        seen.add(row["id"])
        if not row["resource"] or not row["source_locale"]:
            errors.append(f"row {n}: missing provenance")
        if row["status"] not in ("untranslated", "draft", "reviewed"):
            errors.append(f"row {n}: invalid status")
        if row["status"] == "reviewed" and (not row["reviewer"].strip() or not row["translation"].strip()):
            errors.append(f"row {n}: reviewed requires translation and reviewer")
        if row['translation']:
            errors.extend(f'row {n}: {s}' for s in token_errors(row['source'],row['translation'],row.get('line_break_policy')))
        if row["status"] == "untranslated" and row["translation"]:
            errors.append(f"row {n}: untranslated must be empty")
        if style_rules is not None:
            try:
                from .translation_style import style_errors
            except ImportError:
                from translation_style import style_errors
            errors.extend(f"row {n}: {error}" for error in style_errors(row, style_rules))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("catalog", type=Path)
    p.add_argument('--style-rules', type=Path)
    args = p.parse_args()
    try:
        rules = json.loads(args.style_rules.read_text(encoding='utf8')) if args.style_rules else None
        errors = validate(json.loads(args.catalog.read_text(encoding="utf-8")), rules)
    except (OSError, ValueError) as error:
        p.exit(2, str(error) + "\n")
    for error in errors:
        print(error)
    if errors:
        p.exit(1)
    print("PASS catalog")


if __name__ == "__main__":
    main()
