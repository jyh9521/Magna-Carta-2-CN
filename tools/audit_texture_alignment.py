"""Audit native bilingual title anchors and explicit empty atlas gaps.

Coordinates, thresholds and physical aliases belong to the locale contract.
This measures decoded resources, not a running game's final compositor.
"""
import argparse
import json
from pathlib import Path

from PIL import Image

from .font_binding_plan import confined_path
from .patch_tagged_fields import digest
from .replace_texture_regions import selected
from .texture_layout import decode_texture


def foreground_span(image, rect, min_alpha, min_rgb):
    if (not isinstance(rect, list) or len(rect) != 4
            or any(type(n) is not int for n in rect)
            or any(type(n) is not int or not 0 <= n <= 255 for n in (min_alpha, min_rgb))):
        raise ValueError('explicit integer rectangle and byte thresholds required')
    x, y, w, h = rect
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > image.width or y+h > image.height:
        raise ValueError('measurement rectangle outside image')
    xs = [x+px for py in range(h) for px in range(w)
          if (lambda p: p[3] >= min_alpha and max(p[:3]) >= min_rgb)(image.getpixel((x+px, y+py)))]
    if not xs:
        raise ValueError('empty title foreground')
    return [min(xs), max(xs)+1]


def anchor(span, alignment):
    if alignment not in ('left', 'center', 'right'):
        raise ValueError('explicit supported alignment required')
    return {'left': span[0], 'right': span[1], 'center': sum(span)/2}[alignment]


def audit(root, fallback, contract):
    if contract.get('schema_version') != 1 or contract.get('kind') != 'native-texture-alignment-audit':
        raise ValueError('unsupported alignment audit')
    root, fallback = Path(root).resolve(), Path(fallback).resolve()
    blobs, images = {}, {}

    def image(ref):
        r = ref['resource']
        if r not in blobs:
            p = confined_path(root, r)
            if not p.is_file():
                p = confined_path(fallback, r)
            blobs[r] = p.read_bytes()
        key = r, ref['object']
        if key not in images:
            t = selected(blobs[r], ref['object'], None)[3]
            images[key] = Image.frombytes('RGBA', (t['width'], t['height']), decode_texture(t))
        return images[key]

    def span(parts, thresholds):
        spans = [foreground_span(image(ref), ref['rect'], **thresholds) for ref in parts]
        return [min(s[0] for s in spans), max(s[1] for s in spans)]

    failures, groups, gaps, protected = [], [], [], []
    for row in contract['groups']:
        upper = span(row['upper'], row['upper_thresholds'])
        lower = span(row['lower'], row['lower_thresholds'])
        error = anchor(upper, row['alignment']) - anchor(lower, row['alignment'])
        ok = abs(error) <= row['tolerance']
        if not ok:
            failures.append('alignment:' + row['id'])
        groups.append(dict(id=row['id'], alignment=row['alignment'], upper=upper, lower=lower,
                           error=error, passed=ok))
    for row in contract['gaps']:
        x, y, w, h = row['rect']
        count = sum(p[3] > 0 and max(p[:3]) <= row['rgb_ceiling']
                    for p in image(row).crop((x, y, x+w, y+h)).get_flattened_data())
        if count:
            failures.append('gap:' + row['resource'] + ':' + row['object'])
        gaps.append(dict(resource=row['resource'], object=row['object'], residue_pixels=count))
    for row in contract['protected']:
        x, y, w, h = row['rect']
        actual = digest(image(row).crop((x, y, x+w, y+h)).tobytes())
        ok = actual == row['rgba_sha256']
        if not ok:
            failures.append('protected:' + row['id'])
        protected.append(dict(id=row['id'], passed=ok))
    return dict(schema_version=1, passed=not failures, failures=failures, groups=groups,
                gaps=gaps, protected=protected, game_started=False, game_rendering_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'fallback', 'contract', 'report'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    result = audit(a.root, a.fallback, json.loads(a.contract.read_bytes()))
    a.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    residue = sum(r['residue_pixels'] for r in result['gaps'])
    print(f'GROUPS={len(result["groups"])} ALIGNED={sum(r["passed"] for r in result["groups"])} '
          f'MENU_RESIDUE_PIXELS={residue} FAILURES={len(result["failures"])} '
          f'RESULT={"PASS" if result["passed"] else "FAIL"}')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
