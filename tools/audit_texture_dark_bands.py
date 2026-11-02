"""Check native RGB-only write boundaries and the reported title's dark row."""
import argparse
import json
from pathlib import Path

from .build_font_supplement import context
from .repair_texture_labels import locked, confined
from .repair_texture_dark_bands import validate, load_labels
from .reface_font import sha
from .texture_overlay import select_texture_export, rgba_crop
from .texture_layout import read_texture, decode_texture, rect_units
from .texture_dark_bands import core_mask, dark_rows


def rgb_samples(pixels, mask, width, spec):
    """Explicit native pixels/rows, so a multi-row plateau cannot evade QA."""
    if len(pixels) != len(mask)*4 or width <= 0 or len(mask) % width:
        raise ValueError('RGB sample dimensions')
    height = len(mask)//width
    if spec.get('kind') == 'core-row-red-min':
        if set(spec) != {'kind','rows','minimum'} or not spec['rows']:
            raise ValueError('core row sample shape')
        values = []
        for y in spec['rows']:
            if type(y) is not int or not 0 <= y < height:raise ValueError('sample row bounds')
            row = [pixels[i*4] for i in range(y*width,(y+1)*width) if mask[i] >= 250 and pixels[i*4+3] >= 240]
            values.append(min(row) if row else None)
        passed = all(v is not None and v >= spec['minimum'] for v in values)
    elif spec.get('kind') == 'outline-rgb-max':
        if set(spec) != {'kind','points','maximum','minimum_alpha'} or not spec['points']:
            raise ValueError('outline sample shape')
        values = []
        for x,y in spec['points']:
            if type(x) is not int or type(y) is not int or not 0 <= x < width or not 0 <= y < height:
                raise ValueError('sample point bounds')
            at=(y*width+x)*4;values.append(list(pixels[at:at+4]))
        passed = all(max(v[:3]) <= spec['maximum'] and v[3] >= spec['minimum_alpha'] for v in values)
    else:raise ValueError('unknown RGB sample kind')
    return dict(passed=passed, samples=values, criteria=spec)


def audit(profile, project, baseline, candidate, expected, title_label, rgb_checks=None):
    project, baseline, candidate = map(lambda p: Path(p).resolve(), (project, baseline, candidate))
    requests = validate(profile); labels = load_labels(profile, project)
    expected = {r['path']: r for r in expected['resources']}
    checks = []; title_results = []; sample_results = []; font = locked(project, labels[title_label]['font'])
    mask = core_mask(font, labels[title_label]); texture_count = 0
    rgb_checks = rgb_checks or {}
    if not set(rgb_checks) <= requests.keys():raise ValueError('RGB samples require a declared label')
    for row in profile['resources']:
        relative = row['path']; original = locked(baseline, dict(path=relative, sha256=row['sha256']))
        actual = confined(candidate, relative).read_bytes(); restored = bytearray(actual)
        c = context(original, None)
        if len(actual) != len(original):
            raise ValueError('RGB-only revision changed package size')
        for spec in row['textures']:
            e = select_texture_export(c['tables'], spec['object']); off = e['serial_offset']
            t = read_texture(original[off:off+e['serial_size']], c['tables']['names'], off,
                             dict(kind='xbox-inline-bc-v1', format=7), None)
            if t['flags'] or sha(t['tiles']) != spec['tiled_sha256']:
                raise ValueError('baseline native storage identity mismatch')
            at = off+t['payload_offset']; tiles = actual[at:at+len(t['tiles'])]
            for lid in spec['labels']:
                for block in rect_units(t['layout'], labels[lid]['rect']):
                    # Restore RGB only: alpha, all metadata and every other byte
                    # must already equal baseline in the final full-file check.
                    restored[at+block+8:at+block+16] = original[at+block+8:at+block+16]
            if title_label in spec['labels']:
                pixels = rgba_crop(decode_texture(t, tiles), t['width'], labels[title_label]['rect'])
                rows = dark_rows(pixels, mask, labels[title_label]['rect'][2])
                title_results.append(dict(resource=relative, object=spec['object'], dark_rows=rows))
            for lid in spec['labels']:
                if lid not in rgb_checks:continue
                label=labels[lid];f=locked(project,label['font']);m=core_mask(f,label)
                pixels=rgba_crop(decode_texture(t,tiles),t['width'],label['rect'])
                sample_results.append(dict(resource=relative,object=spec['object'],id=lid,
                    **rgb_samples(pixels,m,label['rect'][2],rgb_checks[lid])))
            texture_count += 1
        checks.append(dict(resource=relative, expected_candidate=sha(actual)==expected[relative]['sha256'],
                           only_authorized_rgb_changed=bytes(restored)==original,
                           sha256=sha(actual), baseline_sha256=row['sha256']))
    failures = sum(not r['expected_candidate'] or not r['only_authorized_rgb_changed'] for r in checks)
    failures += sum(bool(r['dark_rows']) for r in title_results)
    failures += sum(not r['passed'] for r in sample_results)
    if not title_results:
        raise ValueError('reported title was not examined')
    return dict(passed=failures==0, failures=failures, resources=len(checks), textures=texture_count,
                labels=len(requests), checks=checks, reported_title=title_results,
                rgb_samples=sample_results,
                native_alpha_identical=all(r['only_authorized_rgb_changed'] for r in checks),
                geometry_and_all_other_bytes_identical=all(r['only_authorized_rgb_changed'] for r in checks),
                game_started=False, game_rendering_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('profile','baseline','candidate','expected','report'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--title-label',required=True)
    p.add_argument('--rgb-checks',type=Path)
    a=p.parse_args()
    result=audit(json.loads(a.profile.read_bytes()),a.project_root,a.baseline,a.candidate,
                 json.loads(a.expected.read_bytes()),a.title_label,
                 json.loads(a.rgb_checks.read_bytes()) if a.rgb_checks else None)
    with a.report.open('x',encoding='utf8') as out:
        json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
    print(f'RESOURCES={result["resources"]} TEXTURES={result["textures"]} '
          f'FAILURES={result["failures"]} ALPHA_AND_GEOMETRY={"UNCHANGED" if result["native_alpha_identical"] else "FAIL"} '
          f'RESULT={"PASS" if result["passed"] else "FAIL"}')
    return int(not result['passed'])


if __name__=='__main__':
    raise SystemExit(main())
