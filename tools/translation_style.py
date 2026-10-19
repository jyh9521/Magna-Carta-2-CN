"""Opt-in, data-driven locale style checks; never rewrite translations."""
import unicodedata
import re

try:
    from .validate_catalog import TOKEN
except ImportError:
    from validate_catalog import TOKEN


def style_errors(row, rules):
    text = row.get('translation', '')
    if not text:
        return []
    kind=row.get('text_kind')
    if rules.get('non_story_default') is True:
        if not isinstance(kind,str) or kind in ('','unclassified'):
            return ['explicit text_kind required for non-story punctuation rule']
        if kind in rules.get('story_text_kinds',[]):return []
    elif kind not in rules.get('single_clause_no_full_stop', []):return []
    # Check prose segments separately: game line breaks can separate stats from prose.
    # Protected syntax is not prose punctuation; preserve it in the actual record.
    lines=text.replace('\\n', '\n').splitlines()
    # Stats/descriptions retain their historical per-line contract. Other UI
    # paragraphs are one message: a visual break must not erase sentence stops
    # from a multi-sentence warning.
    segments = (lines if kind in rules.get('single_clause_no_full_stop',[])
                else [' '.join(lines)])
    for segment in segments:
        visible = TOKEN.sub('', segment).strip()
        if visible.endswith(('。', '.')):
            body = visible[:-1].strip()
            prose = re.sub(r'(?<=\d)[.,](?=\d)', '', body).replace('%', '').replace('‰', '')
            if body and not any(unicodedata.category(c).startswith('P') for c in prose):
                return ['single-clause description must not end with a full stop']
    return []
