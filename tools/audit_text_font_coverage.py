"""Read-only source-locked Coalesced literal/remap coverage, not runtime font selection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata

try:
    from .build_coalesced import rebuild, resolve_changes
    from .coalesced import MAX_BYTES
    from .font_binding_plan import digest, _hash
    from .inspect_font_references import _tables
    from .ue3_fonts import parse_font_payload
    from .ue3_package import FormatError, LzxDecoder, write_report
    from .validate_catalog import TOKEN
except ImportError:
    from build_coalesced import rebuild, resolve_changes
    from coalesced import MAX_BYTES
    from font_binding_plan import digest, _hash
    from inspect_font_references import _tables
    from ue3_fonts import parse_font_payload
    from ue3_package import FormatError, LzxDecoder, write_report
    from validate_catalog import TOKEN


def literal_codepoints(text):
    """Only exclude exact existing TOKEN matches; do not strip arbitrary syntax."""
    return sorted({ord(c) for c in TOKEN.sub('', text)})


def font_coverage(font, codepoints):
    """Check explicit BMP remap entries and positive visible glyph dimensions.

    No direct-index/non-remapped semantics, .notdef identity, fallback, shaping,
    texture pixel contents or atlas bounds are inferred here.
    """
    mapping = {r['codepoint']:r['glyph_index'] for r in font['remap']}
    records = []
    for cp in codepoints:
        row = dict(codepoint=cp)
        if not font['is_remapped']:
            row['status'] = 'non-remapped-font-mode-unverified'
        elif cp > 0xffff:
            row['status'] = 'outside-bmp-remap'
        elif unicodedata.category(chr(cp)).startswith('C'):
            row['status'] = 'control-or-format-literal-unverified'
        elif cp not in mapping:
            row['status'] = 'missing-remap'
        else:
            index = mapping[cp]; g = font['characters'][index]
            row.update(glyph_index=index, width=g['USize'], height=g['VSize'], texture_index=g['TextureIndex'])
            row['status'] = ('mapped' if chr(cp).isspace() or (g['USize'] > 0 and g['VSize'] > 0)
                             else 'zero-area-visible-glyph')
        records.append(row)
    return records


def load_font(source, decoder):
    _hash(source['sha256'])
    logical, tables = _tables(source['data'], source['sha256'], decoder)
    matches = [e for e in tables['exports'] if e['path'] == source['font_object']]
    if len(matches) != 1 or matches[0]['class_path'] != 'Engine.Font':
        raise FormatError('expected exactly one Engine.Font object: ' + source['font_object'])
    e = matches[0]; offset, size = e['serial_offset'], e['serial_size']
    if offset < 0 or size < 4 or offset + size > len(logical):
        raise FormatError('coverage Font payload outside logical package')
    return parse_font_payload(logical[offset:offset+size], tables['names'])


def audit(original, changes, fonts, decoder=None):
    if len(original) > MAX_BYTES:
        raise FormatError('Coalesced input size limit')
    # This verifies full source hash, stable IDs, exact original text, token
    # sequence, encoding and re-extraction of every field; no output is written.
    input_plan_sha256 = digest(json.dumps(changes,sort_keys=True,separators=(',',':')).encode())
    source_mode = changes.get('source_mode','literal') if isinstance(changes,dict) else None
    changes = resolve_changes(original, changes)
    rebuilt = rebuild(original, changes)
    if not changes['entries']:
        raise FormatError('coverage audit requires at least one edited entry')
    if not isinstance(fonts, list) or not fonts:
        raise FormatError('coverage audit requires explicitly supplied fonts')
    reverse = dict(schema_version=1, resource=changes['resource'], input_sha256=digest(rebuilt),
                   entries=[dict(id=e['id'],source=e['translation'],translation=e['source'])
                            for e in changes['entries']])
    if rebuild(rebuilt,reverse) != original:
        raise FormatError('inverse text rebuild did not reproduce original bytes')
    entries, codepoints = [], set()
    for edit in changes['entries']:
        if not edit['translation']:
            raise FormatError('unexpected empty coverage translation')
        cps = literal_codepoints(edit['translation']); codepoints.update(cps)
        entries.append(dict(id=edit['id'], translation_sha256=digest(edit['translation'].encode('utf-8')),
                            literal_codepoints=cps, protected_token_count=len(TOKEN.findall(edit['translation']))))
    codepoints = sorted(codepoints)
    labels, rows = set(), []
    for source in fonts:
        if (not isinstance(source,dict) or not isinstance(source.get('label'),str)
                or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',source['label'])
                or source['label'].casefold() in labels
                or not isinstance(source.get('data'),bytes)
                or not isinstance(source.get('font_object'),str) or not source['font_object']):
            raise FormatError('invalid or duplicate coverage font input')
        labels.add(source['label'].casefold())
        font = load_font(source,decoder)
        records = font_coverage(font,codepoints)
        failures = [r for r in records if r['status'] != 'mapped']
        failed = {r['codepoint'] for r in failures}
        rows.append(dict(label=source['label'], package_sha256=source['sha256'], font_object=source['font_object'],
                         glyph_count=len(font['characters']), explicit_remap=font['is_remapped'],
                         codepoints=records, failures=failures,
                         entries=[dict(id=e['id'],failed_codepoints=sorted(set(e['literal_codepoints']) & failed)) for e in entries],
                         covers_requested_literals=bool(codepoints) and not failures))
    return dict(schema_version=1, resource=changes['resource'], input_sha256=digest(original),
                rebuilt_sha256=digest(rebuilt), input_size=len(original), rebuilt_size=len(rebuilt),
                changes_canonical_sha256=input_plan_sha256, source_verification_mode=source_mode,
                source_identity_and_reextraction_verified=True, protected_token_sequences_preserved=True,
                inverse_rebuild_byte_identical=True,
                entries=entries, literal_codepoints=codepoints, fonts=rows,
                all_supplied_fonts_cover_literals=all(r['covers_requested_literals'] for r in rows),
                coverage_scope='literal Unicode scalars outside exact repository TOKEN matches; explicit BMP remap only',
                dynamic_expansion_coverage_verified=False, unknown_control_syntax_resolved=False,
                atlas_bounds_verified=False, glyph_pixels_verified=False, font_runtime_selection_verified=False,
                shaping_and_fallback_verified=False, game_rendering_verified=False, deployment_performed=False)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('coalesced',type=Path); p.add_argument('changes',type=Path)
    p.add_argument('--font-package',nargs=4,action='append',required=True,metavar=('LABEL','PATH','SHA256','OBJECT'))
    p.add_argument('--lzx-library',type=Path); p.add_argument('--output',type=Path,required=True)
    a = p.parse_args(argv)
    try:
        inputs = [a.coalesced,a.changes] + [Path(row[1]) for row in a.font_package]
        if a.lzx_library: inputs.append(a.lzx_library)
        if (a.output.exists() or a.output.is_symlink()
                or a.output.resolve() in [v.resolve() for v in inputs]):
            raise FormatError('coverage report must be new and distinct from inputs')
        if a.coalesced.stat().st_size > MAX_BYTES or a.changes.stat().st_size > MAX_BYTES:
            raise FormatError('coverage input size limit')
        original = a.coalesced.read_bytes(); raw_changes = a.changes.read_bytes()
        changes = json.loads(raw_changes.decode('utf-8-sig'))
        snapshots = [(a.coalesced,digest(original)),(a.changes,digest(raw_changes))]
        fonts = []
        for label,path,sha,obj in a.font_package:
            data = Path(path).read_bytes()
            fonts.append(dict(label=label,data=data,sha256=sha,font_object=obj))
            snapshots.append((Path(path),sha))
        decoder_sha256 = digest(a.lzx_library.read_bytes()) if a.lzx_library else None
        if a.lzx_library:
            snapshots.append((a.lzx_library,decoder_sha256))
        report = audit(original,changes,fonts,LzxDecoder(a.lzx_library) if a.lzx_library else None)
        for path,sha in snapshots:
            if digest(path.read_bytes()) != sha:
                raise FormatError('coverage input changed during audit')
        report.update(changes_sha256=digest(raw_changes), decoder_sha256=decoder_sha256,
                      input_hashes_rechecked=True)
        write_report(a.output,report)
        if json.loads(a.output.read_text(encoding='utf-8')) != report:
            raise FormatError('coverage report reopening mismatch')
        for path,sha in snapshots:
            if digest(path.read_bytes()) != sha:
                raise FormatError('coverage input changed during report publication')
        passed = report['all_supplied_fonts_cover_literals']
        print(json.dumps(dict(entries=len(report['entries']),fonts=len(report['fonts']),
                              literal_codepoints=len(report['literal_codepoints']),all_fonts_cover_literals=passed,
                              game_rendering_verified=False),sort_keys=True))
        return 0 if passed else 1
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('ERROR: '+str(exc)); return 2


if __name__ == '__main__': raise SystemExit(main())
