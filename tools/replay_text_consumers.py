"""Bounded source-locked text-consumer replay using real UI fields/glyph metrics.

Not a renderer: dynamic UI state, the complete native tokenizer and final pixel
shader execution are intentionally not inferred from these controlled cases.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .build_font_supplement import context
from .coalesced import extract_entries, parse
from .supplement_font import parse_atlas_payload, atlas_tiles
from .ue3_fonts import parse_font_payload, read_properties
from .ue3_package import Reader
from .ue3_textures import untile_dxt5, decode_dxt5


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def property_value(payload, names, prefix, path):
    reader = Reader(payload)
    reader.seek(prefix)
    properties = read_properties(reader, names)
    for position, (name, index) in enumerate(path):
        selected = [p for p in properties if p['name'] == name and p['array_index'] == index]
        if len(selected) != 1:
            raise ValueError('consumer field missing or ambiguous')
        prop = selected[0]
        if position + 1 < len(path):
            if prop['type'] != 'StructProperty':
                raise ValueError('consumer field is not nested tagged structure')
            properties = read_properties(Reader(prop['raw']), names)
    if prop['type'] == 'FloatProperty' and len(prop['raw']) == 4:
        return struct.unpack('>f', prop['raw'])[0]
    if prop['type'] == 'StrProperty':
        return Reader(prop['raw']).string()
    if prop['type'] == 'ByteProperty' and len(prop['raw']) == 1:
        return prop['raw'][0]
    raise ValueError('unsupported consumer scalar')


def advances(font, text):
    mapping = {r['codepoint']:r['glyph_index'] for r in font['remap']}
    values = []
    for char in text:
        index = mapping.get(ord(char)) if font['is_remapped'] else ord(char)
        if index is None or not 0 <= index < len(font['characters']):
            raise ValueError('consumer text lacks an exact glyph')
        values.append(font['characters'][index]['USize'])
    return values


def line_case(text, font, limit, line_count=None, gap=0):
    if '\n' in text or '\r' in text:
        raise ValueError('physical newlines are not engine literal breaks')
    lines = text.split('\\n')
    widths = [sum(advances(font, line)) - max(0, len(line) - 1) * gap for line in lines]
    intact = all(line.count('[') == line.count(']') for line in lines)
    return dict(lines=lines, widths=widths, limit=limit, brackets_intact=intact,
                passed=max(widths, default=0) <= limit and intact
                and (line_count is None or len(lines) == line_count))


def shadow_counts(ctx, font, text):
    mapping = {r['codepoint']:r['glyph_index'] for r in font['remap']}
    atlases = {}
    counts = []
    for cp in sorted(set(map(ord, text))):
        metric = font['characters'][mapping[cp]]
        ti = metric['TextureIndex']
        if ti not in atlases:
            e = ctx['tables']['exports'][font['textures'][ti] - 1]
            raw = ctx['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']]
            texture = parse_atlas_payload(raw, ctx['tables']['names'], e['serial_offset'])
            w, h = texture['width'], texture['height']
            atlases[ti] = w, decode_dxt5(untile_dxt5(atlas_tiles(raw, texture, None), w, h), w, h)
        w, pixels = atlases[ti]
        dark = white = 0
        for y in range(metric['VSize']):
            for x in range(metric['USize']):
                at = ((metric['StartV'] + y) * w + metric['StartU'] + x) * 4
                rgba = pixels[at:at + 4]
                if rgba[3]:
                    dark += max(rgba[:3]) == 0
                    white += min(rgba[:3]) == 255
        counts.append(dict(codepoint=cp, black_shadow_pixels=dark, white_foreground_pixels=white))
    return counts


def audit(root, ui_package, native, profile):
    if profile.get('schema_version') != 1 or profile.get('kind') != 'bounded-text-consumer-replay':
        raise ValueError('consumer replay schema mismatch')
    if digest(ui_package) != profile['ui_sha256'] or digest(native) != profile['native_sha256']:
        raise ValueError('UI/native source SHA256 mismatch')
    for window in profile['native_windows']:
        at = window['address'] - profile['native_base']
        if at < 0 or at + window['size'] > len(native) or digest(native[at:at + window['size']]) != window['sha256']:
            raise ValueError('native consumer window mismatch')
    ui_context = context(ui_package, None)
    ui_logical, tables = ui_context['logical'], ui_context['tables']
    exports = {e['path']:e for e in tables['exports']}
    fields = {}
    for spec in profile['ui_fields']:
        e = exports[spec['object']]
        payload = ui_logical[e['serial_offset']:e['serial_offset'] + e['serial_size']]
        if digest(payload) != spec['payload_sha256']:
            raise ValueError('UI consumer payload mismatch')
        value = property_value(payload, tables['names'], spec['prefix'], spec['field'])
        if value != spec['expected']:
            raise ValueError('UI consumer field mismatch')
        fields[spec['id']] = value
    fonts, contexts = {}, {}
    for key, spec in profile['fonts'].items():
        path = (root / spec['resource']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('font resource escapes input root')
        if spec['resource'] not in contexts:
            contexts[spec['resource']] = context(path.read_bytes(), None)
        ctx = contexts[spec['resource']]
        es = [e for e in ctx['tables']['exports'] if e['path'] == spec['object']]
        if len(es) != 1:
            raise ValueError('consumer Font export mismatch')
        e = es[0]
        fonts[key] = parse_font_payload(ctx['logical'][e['serial_offset']:e['serial_offset'] + e['serial_size']], ctx['tables']['names'])
    resource = profile['text_resource']
    raw = (root / resource).read_bytes()
    strings = {r['id']:r['source'] for r in extract_entries(parse(raw), resource)}
    cases = []
    for spec in profile['cases']:
        text = strings[spec['entry_id']]
        if spec['kind'] == 'menu-slots':
            icon = sum(advances(fonts[spec['icon_font']], spec['icon_text']))
            width = icon + sum(advances(fonts[spec['font']], text))
            limit = fields[spec['right_field']] - fields.get(spec.get('left_field'), 0)
            row = dict(width=width, limit=limit, clearance=limit - width, passed=width <= limit)
        elif spec['kind'] == 'explicit-lines':
            limit = fields[spec['limit_field']] if 'limit_field' in spec else spec['limit']
            row = line_case(text, fonts[spec['font']], limit, spec['line_count'], spec.get('gap', 0))
        else:
            raise ValueError('unknown text consumer case')
        cases.append(dict(id=spec['id'], entry_id=spec['entry_id'], **row))
    for spec in profile['shadows']:
        counts = shadow_counts(contexts[profile['fonts'][spec['font']]['resource']], fonts[spec['font']], spec['text'])
        cases.append(dict(id=spec['id'], glyphs=counts,
                          passed=all(r['black_shadow_pixels'] and r['white_foreground_pixels'] for r in counts)))
    return dict(cases=cases, failures=sum(not r['passed'] for r in cases),
                ui_fields=fields, native_windows_verified=len(profile['native_windows']),
                text_sha256=digest(raw), game_started=False, game_rendering_verified=False,
                boundary='static serialized layout plus exact glyph metrics; not complete UI/tokenizer/shader execution')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('resource-root', 'ui-package', 'native-image', 'profile', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.output.exists():
            raise ValueError('replay output must be new')
        result = audit(a.resource_root, a.ui_package.read_bytes(), a.native_image.read_bytes(), json.loads(a.profile.read_bytes()))
        raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('xb') as stream:
            stream.write(raw)
        if a.output.read_bytes() != raw:
            raise ValueError('replay output reopening mismatch')
        print(json.dumps(dict(cases=len(result['cases']), failures=result['failures'], game_started=False), sort_keys=True))
        return int(result['failures'] > 0)
    except (ValueError, OSError, KeyError) as exc:
        print('ERROR: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
