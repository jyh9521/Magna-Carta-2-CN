"""Read-only, locale-neutral text sampling regression against explicit contracts.

Atlas edit rectangles and runtime consumer windows are distinct coordinate
systems. Contracts retain their original serialized evidence and may also mark
deduced sampling routes. This probe checks owned glyphs/effects in those windows;
it does not execute a game or claim effective runtime state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from .texture_overlay import render_label


def sampled_bounds(label, pixels, window):
    """Return the >=128-alpha glyph bounds relative to a consumer window."""
    from PIL import Image
    if (not isinstance(window, (list, tuple)) or len(window) != 4
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in window)
            or min(window[2:]) <= 0):
        raise ValueError('invalid consumer window')
    width, height = label['rect'][2:]
    if len(pixels) != width * height * 4:
        raise ValueError('glyph pixel length mismatch')
    alpha = Image.frombytes('RGBA', (width, height), pixels).getchannel('A')
    bounds = alpha.point(lambda v: 255 if v >= 128 else 0).getbbox()
    if bounds is None:
        raise ValueError('empty glyph core')
    dx, dy = label['rect'][0] - window[0], label['rect'][1] - window[1]
    return [bounds[0]+dx, bounds[1]+dy, bounds[2]+dx, bounds[3]+dy]


def _field(label, path, plan):
    if not isinstance(path, list) or not path:
        raise ValueError('empty contract field path')
    value = dict(label)
    value.setdefault('font', plan['font'])
    for part in path:
        value = value[part]
    return value


def evaluate(plan, contracts, root):
    """Evaluate bounded declarative contracts; inputs and source plan stay intact."""
    from PIL import Image
    root = Path(root).resolve()
    if (contracts.get('schema_version') != 1
            or contracts.get('kind') != 'texture-consumer-probe-contracts'
            or contracts.get('game_rendering_verified') is not False):
        raise ValueError('unsupported texture consumer contracts')
    cases = contracts.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 4096:
        raise ValueError('consumer contract count bound')
    labels = {label['id']: label for label in plan['labels']}
    if len(labels) != len(plan['labels']):
        raise ValueError('duplicate texture labels')
    fonts, rendered, cores = {}, {}, {}

    def locked(ref):
        path = (root / ref['path']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('probe input outside project')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != ref['sha256']:
            raise ValueError('probe input hash mismatch: ' + ref['path'])
        return data

    def raster(key, core=False):
        cache = cores if core else rendered
        if key not in cache:
            label = copy.deepcopy(labels[key])
            ref = label.get('font', plan['font'])
            if ref['sha256'] not in fonts:
                fonts[ref['sha256']] = locked(ref)
            if core:
                if 'appearance' in label:
                    label['appearance'].update(
                        gradient=[[0, [255]*4], [1000, [255]*4]],
                        outline_width=0, glow=[0]*4, shadow=[0]*4, motion=0)
                else:
                    label['style'] = dict(fill=[255]*4, stroke_fill=[0]*4, shadow_fill=[0]*4)
            if 'glyph_mask' in label:
                import io
                image = Image.open(io.BytesIO(locked(label['glyph_mask'])))
                mask = image.getchannel('A') if image.mode == 'RGBA' else image.convert('L')
                label.update(_glyph_pixels=mask.tobytes(), _glyph_size=list(mask.size))
            cache[key] = render_label(fonts[ref['sha256']], label)
        return cache[key]

    def bounds(sample):
        key = sample['label']
        return sampled_bounds(labels[key], raster(key, True), sample['window'])

    results, names = [], set()
    for case in cases:
        name, mode = case['name'], case['mode']
        if name in names:
            raise ValueError('duplicate consumer contract name')
        names.add(name)
        if mode == 'glyph-bounds':
            box = bounds(case['sample'])
            center = [(box[0]+box[2])/2, (box[1]+box[3])/2]
            passed = True
            if 'center' in case:
                passed &= all(abs(a-b) <= case['tolerance'] for a, b in zip(center, case['center']))
            for field, index, relation in [('min_left',0,'min'), ('min_top',1,'min'),
                                           ('max_right',2,'max'), ('max_bottom',3,'max')]:
                if field in case:
                    passed &= box[index] >= case[field] if relation == 'min' else box[index] <= case[field]
            if 'min_height' in case:
                passed &= box[3]-box[1] >= case['min_height']
            if 'bottom' in case:
                passed &= abs(box[3]-case['bottom']) <= case['tolerance']
            measured = dict(glyph=box, center=center)
        elif mode == 'registration':
            measured = [bounds(sample) for sample in case['samples']]
            passed = bool(measured) and all(value == measured[0] for value in measured)
            if 'center_x' in case:
                passed &= abs((measured[0][0]+measured[0][2])/2-case['center_x']) <= case['tolerance']
        elif mode == 'same-field':
            measured = [_field(labels[key], case['field'], plan) for key in case['labels']]
            passed = bool(measured) and all(value == measured[0] for value in measured)
        elif mode == 'field-equals':
            measured = _field(labels[case['label']], case['field'], plan)
            passed = measured == case['value']
        elif mode == 'equal-core':
            values = [raster(key, True) for key in case['labels']]
            measured = [hashlib.sha256(value).hexdigest() for value in values]
            passed = bool(values) and all(value == values[0] for value in values)
        elif mode == 'baseline':
            measured = [bounds(sample)[3] + sample['origin_y'] for sample in case['samples']]
            passed = bool(measured) and max(measured)-min(measured) <= case['tolerance']
        elif mode == 'alpha-after':
            key = case['label']; label = labels[key]
            image = Image.frombytes('RGBA', tuple(label['rect'][2:]), raster(key))
            y = max(0, min(image.height, case['atlas_y']-label['rect'][1]))
            measured = (image.getchannel('A').crop((0,y,image.width,image.height)).getextrema()[1]
                        if y < image.height else 0)
            passed = measured <= case['max_alpha']
        elif mode == 'field-limits':
            measured, passed = [], True
            for limit in case['limits']:
                value = _field(labels[case['label']], limit['field'], plan)
                measured.append(value)
                if 'maximum' in limit:passed &= value <= limit['maximum']
                if 'minimum_rgb' in limit:passed &= min(value[:3]) >= limit['minimum_rgb']
        else:
            raise ValueError('unknown consumer contract mode: ' + mode)
        results.append(dict(check=name, passed=bool(passed), measured=measured,
                            evidence=case.get('evidence')))
    return dict(passed=all(r['passed'] for r in results), passed_checks=sum(r['passed'] for r in results),
                total_checks=len(results), checks=results, game_started=False,
                game_rendering_verified=False, font_sha256=sorted(fonts))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--contracts', required=True)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output')
    args = parser.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    contracts = json.loads(Path(args.contracts).read_text(encoding='utf-8'))
    report = evaluate(plan, contracts, args.root)
    report.update(plan=args.plan, contracts=args.contracts)
    for row in report['checks']:
        if not row['passed']:
            print('FAIL', row['check'], json.dumps(row['measured'], ensure_ascii=False))
    print(('PASS' if report['passed'] else 'FAIL') +
          f" {report['passed_checks']}/{report['total_checks']} consumer-geometry checks")
    if args.output:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
