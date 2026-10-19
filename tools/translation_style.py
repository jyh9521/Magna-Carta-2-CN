"""Opt-in, data-driven locale style checks; never rewrite translations."""
import unicodedata
import re

try:
    from .validate_catalog import TOKEN
except ImportError:
    from validate_catalog import TOKEN


def style_errors(row, rules):
    text = row.get('translation', '')
    if not text or row.get('text_kind') not in rules.get('single_clause_no_full_stop', []):
        return []
    # Check prose segments separately: game line breaks can separate stats from prose.
    # Protected syntax is not prose punctuation; preserve it in the actual record.
    segments = text.replace('\\n', '\n').splitlines()
    for segment in segments:
        visible = TOKEN.sub('', segment).strip()
        if visible.endswith(('。', '.')):
            body = visible[:-1].strip()
            prose = re.sub(r'(?<=\d)[.,](?=\d)', '', body).replace('%', '').replace('‰', '')
            if body and not any(unicodedata.category(c).startswith('P') for c in prose):
                return ['single-clause description must not end with a full stop']
    return []
