"""Select format/content sections in a locale-owned player-guide template."""
import re


def render_usage(template, format_name, output_name, with_dlc):
    if format_name not in ('zar', 'xex'):
        raise ValueError('unknown player guide format')
    selected = {format_name, 'dlc' if with_dlc else 'no_dlc'}
    pattern = r'\{\{#(zar|xex|dlc|no_dlc)\}\}\n(.*?)\n\{\{/\1\}\}'
    result = re.sub(pattern, lambda m: m[2] if m[1] in selected else '', template, flags=re.S)
    result = result.replace('{{OUTPUT_NAME}}', output_name)
    if '{{' in result or '}}' in result:
        raise ValueError('unresolved player guide template marker')
    return re.sub(r'\n{3,}', '\n\n', result)
