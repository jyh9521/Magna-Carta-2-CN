"""Metric-driven, explicit line layout with caller-supplied locale rules.

The engine tokenizer is not emulated. The output supplies hard breaks before
automatic wrapping is needed; unsupported dynamic fields fail explicitly.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import re

from .validate_catalog import TOKEN, token_errors


@dataclass(frozen=True)
class Atom:
    text: str
    width: float
    first: str = ''
    last: str = ''


def atoms(text, widths, rules, icon_widths=None):
    """Do not split markup, short bracket groups, numbers or Latin words."""
    if any(c in text for c in '\r\n\0'):
        raise ValueError('physical control in line-layout input')
    icon_widths = icon_widths or {}
    result = []
    i = 0
    while i < len(text):
        if text[i] == '<':
            m = TOKEN.match(text, i)
            if not m:
                raise ValueError('unsupported markup')
            token = m[0]
            if token.startswith('<Styles:') and token != '<Styles:/>':
                style = token[len('<Styles:'):-1]
                if style not in icon_widths:
                    raise ValueError('unbound style: '+style)
                close = text.find('<Styles:/>', m.end())
                if close < 0:
                    raise ValueError('unclosed style')
                content = text[m.end():close]
                table = icon_widths[style]
                if not content or TOKEN.search(content) or any(ord(c) not in table for c in content):
                    raise ValueError('invalid icon style content')
                # Keep start/content/end as one indivisible atom: a hard break
                # inside the style would alter the next line's font binding.
                end = close+len('<Styles:/>')
                result.append(Atom(text[i:end], sum(table[ord(c)] for c in content), content[0], content[-1]))
                i = end
                continue
            else:
                raise ValueError('unresolved dynamic markup: '+token)
        m = TOKEN.match(text, i)
        if m:
            raise ValueError('unresolved control/placeholder: '+m[0])
        if text[i] == '\\':
            raise ValueError('unresolved literal separator')
        table = widths
        if text[i] in rules['atomic_pairs']:
            closing = rules['atomic_pairs'][text[i]]
            end = text.find(closing, i+1)
            if end < 0:
                raise ValueError('unbalanced atomic bracket')
            end += 1
            if any(c in text[i+1:end-1] for c in rules['atomic_pairs']):
                raise ValueError('nested atomic bracket')
        else:
            m = re.match(r'[A-Za-z0-9]+(?:[.\-/][A-Za-z0-9]+)*', text[i:])
            end = i+len(m[0]) if m else i+1
        piece = text[i:end]
        if any(ord(c) not in table for c in piece):
            raise ValueError('missing exact glyph in text atom')
        result.append(Atom(piece, sum(table[ord(c)] for c in piece), piece[0], piece[-1]))
        i = end
    return result


def visible_edge(items, reverse=False):
    for atom in reversed(items) if reverse else items:
        c = atom.last if reverse else atom.first
        if c and not c.isspace():
            return c
    return ''


def legal_boundary(items, at, rules):
    before = visible_edge(items[:at], True)
    after = visible_edge(items[at:])
    if (before and before in rules['no_line_end']) or (after and after in rules['no_line_start']):
        return False
    # A single ellipsis/dash sequence is kept intact by the same rule.
    if before and after and before == after and before in rules['repeat_pairs']:
        return False
    return True


def wrap_paragraph(text, widths, limit, rules, icon_widths=None):
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError('positive finite line width required')
    items = atoms(text, widths, rules, icon_widths)
    if any(a.width > limit for a in items):
        raise ValueError('atomic run wider than the declared consumer')
    # Greedy full lines, preferring the last natural punctuation boundary when
    # it uses at least the caller's minimum fraction of the available width.
    lines = []
    start = 0
    while start < len(items):
        width = 0
        choices = []
        for end in range(start+1, len(items)+1):
            width += items[end-1].width
            if width > limit:
                break
            if end == len(items) or legal_boundary(items, end, rules):
                choices.append((end, width))
        if not choices:
            raise ValueError('no legal line break within consumer width')
        end, width = choices[-1]
        if end < len(items):
            natural = [(e, w) for e, w in choices
                       if w >= limit*rules['natural_break_min_fraction']
                       and visible_edge(items[start:e], True) in rules['preferred_break_after']]
            if natural:
                end, width = natural[-1]
        lines.append(''.join(a.text for a in items[start:end]))
        start = end
    return lines or ['']


def reflow(text, widths, limit, rules, break_token='\\n', icon_widths=None, merge_soft_breaks=False):
    if break_token not in ('\\n', '<br>'):
        raise ValueError('unsupported explicit break representation')
    original = text
    if merge_soft_breaks:
        # Explicit opt-in for reviewed prose fields: preserve empty paragraph
        # boundaries, only coalesce isolated soft line breaks within paragraphs.
        escaped = re.escape(break_token)
        text = re.sub(r'(?<!'+escaped+')'+escaped+r'(?!'+escaped+')', '', text)
    paragraphs = text.split(break_token)
    # A closing mark stranded by an old explicit break belongs to the previous
    # paragraph. Merge only that boundary; ordinary/empty functional breaks stay.
    index = 1
    while index < len(paragraphs):
        first = paragraphs[index].lstrip()[:1]
        last = paragraphs[index-1].rstrip()[-1:]
        if first and last and (first in rules['no_line_start'] or last in rules['no_line_end']):
            paragraphs[index-1] += paragraphs.pop(index)
        else:
            index += 1
    result = break_token.join(line for p in paragraphs
                             for line in wrap_paragraph(p, widths, limit, rules, icon_widths))
    if result.replace(break_token, '') != original.replace(break_token, ''):
        raise ValueError('layout changed visible content')
    if break_token == '\\n':
        errors = token_errors(original, result, dict(source_count=original.count('\\n'),
                                                target_count=result.count('\\n')))
        if errors:
            raise ValueError('layout changed protected tokens')
    else:
        if TOKEN.findall(original.replace('<br>', '')) != TOKEN.findall(result.replace('<br>', '')):
            raise ValueError('layout changed non-break subtitle markup')
    return result


def audit(text, widths, limit, rules, break_token='\\n', icon_widths=None, max_lines=None):
    lines = text.split(break_token)
    rows = []
    for i, line in enumerate(lines):
        items = atoms(line, widths, rules, icon_widths)
        first = visible_edge(items)
        last = visible_edge(items, True)
        width = sum(a.width for a in items)
        # Leading ellipses in original utterances have linguistic meaning;
        # generated line starts are checked separately through reflow.
        paragraph_leading_pause = first in rules['repeat_pairs'] and (not i or not lines[i-1].strip())
        bad_start = bool(i and first and first in rules['no_line_start'] and not paragraph_leading_pause)
        bad_end = bool(i+1 < len(lines) and last and last in rules['no_line_end'])
        rows.append(dict(width=width, limit=limit, bad_start=bad_start,
                         bad_end=bad_end, passed=width <= limit and not bad_start and not bad_end))
    height_ok = max_lines is None or len(lines) <= max_lines
    return dict(lines=rows, line_count=len(lines), height_ok=height_ok,
                passed=all(r['passed'] for r in rows) and height_ok)
