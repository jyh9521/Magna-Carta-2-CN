"""Trim only transparent horizontal Font cell padding, without touching atlases.

The locale supplies codepoints and margins. Both tagged/native metric copies are
updated. Every opaque/antialiased pixel, baseline, remap and other export stays
identical; this is not rasterization or a font/size replacement.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .audit_font_optical_size import Sampler
from .font_binding_plan import confined_path
from .ue3_fonts import read_properties
from .ue3_package import Reader


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fit(data, expected_sha, obj, codepoints, left=2, right=3):
    if sha(data) != expected_sha:
        raise ValueError('font package SHA256 mismatch')
    if (type(left) is not int or type(right) is not int or not 1 <= left <= 8 or not 1 <= right <= 8
            or not isinstance(codepoints, list) or not 1 <= len(codepoints) <= 4096
            or any(type(cp) is not int or not 0 <= cp <= 65535 for cp in codepoints)
            or len(set(codepoints)) != len(codepoints)):
        raise ValueError('explicit bounded padding/codepoints required')
    sample = Sampler(data, obj)
    if any(cp not in sample.mapping for cp in codepoints):
        raise ValueError('selected mapping missing')
    indexes = {sample.mapping[cp] for cp in codepoints}
    if len(indexes) != len(codepoints) or any(i in indexes for cp, i in sample.mapping.items() if cp not in codepoints):
        raise ValueError('shared glyph index needs an explicit alias policy')
    e = next(e for e in sample.ctx['tables']['exports'] if e['path'] == obj)
    start = e['serial_offset']
    payload = data[start:start + e['serial_size']]
    out = bytearray(data)
    rows = []
    for cp in sorted(codepoints):
        cell = sample.glyph(cp)
        box = cell.getchannel('A').getbbox()  # includes faint AA and shadow, not a visual threshold
        if box is None:
            raise ValueError('blank layout cells must not be trimmed')
        shift = max(0, box[0] - left)
        width = min(cell.width - shift, box[2] - shift + right)
        g = sample.font['characters'][sample.mapping[cp]]
        values = dict(StartU=g['StartU'] + shift, USize=width)
        r = Reader(payload)
        r.seek(g['tagged_offset'])
        for prop in read_properties(r, sample.ctx['tables']['names']):
            if prop['name'] in values:
                at = start + prop['value_offset']
                out[at:at+4] = struct.pack('>i', values[prop['name']])
        for offset, name in ((0, 'StartU'), (8, 'USize')):
            at = start + g['native_offset'] + offset
            out[at:at+4] = struct.pack('>i', values[name])
        rows.append(dict(codepoint=cp, before_advance=cell.width, advance=width,
                         start_u_shift=shift, alpha_bbox=box, cropped_alpha_pixels=0))
    result = bytes(out)
    actual = Sampler(result, obj)
    if actual.mapping != sample.mapping:
        raise ValueError('font remap changed')
    for row in rows:
        cp, shift = row['codepoint'], row['start_u_shift']
        old = sample.glyph(cp)
        expected = old.crop((shift, 0, shift+row['advance'], old.height))
        if actual.glyph(cp).tobytes() != expected.tobytes():
            raise ValueError('native glyph pixels changed')
    for i, g in enumerate(sample.font['characters']):
        if i not in indexes and actual.font['characters'][i] != g:
            raise ValueError('unselected glyph changed')
    # Only the Font export changes: all atlas bytes are therefore exact, not reencoded.
    if result[:start] != data[:start] or result[start+e['serial_size']:] != data[start+e['serial_size']:]:
        raise ValueError('non-font bytes changed')
    return result, dict(object=obj, glyphs=rows, changed=sum(r['advance'] != r['before_advance'] for r in rows),
                        input_sha256=sha(data), output_sha256=sha(result), atlases_byte_identical=True,
                        baselines_preserved=True, remap_preserved=True)


def build(profile, profile_sha, root, output):
    raw = Path(profile).read_bytes()
    if sha(raw) != profile_sha:
        raise ValueError('padding profile SHA256 mismatch')
    plan = json.loads(raw)
    if plan.get('schema_version') != 1 or plan.get('kind') != 'native-font-padding-plan':
        raise ValueError('unsupported padding profile')
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError('new disjoint output required')
    # Validate and build everything in memory before opening outputs.
    results = []
    for source in plan['sources']:
        path = confined_path(root, source['resource'])
        before = path.read_bytes()
        if sha(before) != source['sha256']:
            raise ValueError('source package identity mismatch')
        after = before
        proofs = []
        for selection in source['fonts']:
            after, proof = fit(after, sha(after), selection['object'], plan['codepoints'],
                               plan['left_padding'], plan['right_padding'])
            proofs.append(proof)
        results.append((source['resource'], before, after, proofs))
    manifest = dict(schema_version=1, kind='native-font-padding-build', profile_sha256=profile_sha,
                    game_started=False, resources=[])
    for resource, before, after, proofs in results:
        for phase, data in [('baseline', before), ('candidate', after)]:
            path = confined_path(output, phase+'/'+resource)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if path.read_bytes() != data:
                raise ValueError('output readback mismatch')
        manifest['resources'].append(dict(path=resource, before_sha256=sha(before), sha256=sha(after),
                                          size=len(after), fonts=proofs))
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(raw)
    if (output/'manifest.json').read_bytes() != raw:
        raise ValueError('manifest readback mismatch')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('profile', 'source-root', 'output'):
        parser.add_argument('--'+key, required=True, type=Path)
    parser.add_argument('--profile-sha256', required=True)
    a = parser.parse_args()
    report = build(a.profile, a.profile_sha256, a.source_root, a.output)
    print(json.dumps(dict(resources=len(report['resources']), fonts=sum(len(r['fonts']) for r in report['resources']),
                          changed_glyphs=sum(f['changed'] for r in report['resources'] for f in r['fonts']),
                          atlases_byte_identical=True, passed=True)))


if __name__ == '__main__':
    main()
