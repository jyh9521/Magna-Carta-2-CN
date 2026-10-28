"""Small, hash-guarded texture-plan deltas and transparent glyph restoration.

The mask operation removes source pixels with known alpha support; it never
inpaints or resamples surrounding artwork. Native BC writing remains in the
existing texture_overlay pipeline. Locale wording and source identities live
in declarative data, not in this module.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_hash(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':')).encode('utf-8'))


def merge_delta(plan, delta):
    """Merge only explicitly guarded labels and additional texture bindings."""
    if (delta.get('schema_version') != 1
            or delta.get('kind') != 'texture-region-repair-delta'
            or delta.get('game_rendering_verified') is not False):
        raise ValueError('unsupported texture repair delta')
    if (plan.get('kind') != 'texture-text-overlay-plan'
            or plan.get('schema_version') != 1):
        raise ValueError('unsupported base texture plan')
    out = copy.deepcopy(plan)
    labels = {row['id']: row for row in out['labels']}
    sources = {row['path']: row for row in out['sources']}
    if len(labels) != len(out['labels']) or len(sources) != len(out['sources']):
        raise ValueError('duplicate base labels or sources')
    seen = set()
    for change in delta['labels']:
        label = copy.deepcopy(change['label']); key = label['id']
        if key in seen:
            raise ValueError('duplicate delta label')
        seen.add(key)
        expected = change['expected_label_sha256']
        before = labels.get(key)
        if ((expected is None and before is not None)
                or (expected is not None and (before is None or object_hash(before) != expected))):
            raise ValueError('label precondition mismatch: ' + key)
        if before is None:
            out['labels'].append(label)
        else:
            out['labels'][out['labels'].index(before)] = label
        labels[key] = label
    seen = set()
    for change in delta['source_additions']:
        header = copy.deepcopy(change['source']); key = header['path']
        if key in seen or 'textures' in header:
            raise ValueError('duplicate delta source or nested textures')
        seen.add(key)
        before = sources.get(key); expected = change['expected_header_sha256']
        current_header = None if before is None else {k:v for k,v in before.items() if k != 'textures'}
        if ((expected is None and before is not None)
                or (expected is not None and (before is None or object_hash(current_header) != expected))
                or (before is not None and header != current_header)):
            raise ValueError('source precondition mismatch: ' + key)
        if before is None:
            before = dict(header, textures=[])
            out['sources'].append(before); sources[key] = before
        objects = {edit['object'] for edit in before['textures']}
        for edit in change['textures']:
            if edit['object'] in objects:
                raise ValueError('duplicate delta texture object')
            objects.add(edit['object'])
            ids = [edit['label']] if 'label' in edit else edit['regions']
            if any(key not in labels for key in ids):
                raise ValueError('delta texture label is missing')
            before['textures'].append(copy.deepcopy(edit))
    return out


def alpha_support_mask(rgba, width, height, seed=None):
    """Select all visible source alpha or one 4-connected alpha component.

    A seed is local to the locked crop. This permits text and adjacent artwork
    to occupy one rectangle without deleting the artwork. Alpha-zero RGB is
    not owned or rewritten. No antialias threshold discards faint glyph edges.
    """
    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= 8192 or not 1 <= height <= 8192
            or not isinstance(rgba, bytes) or len(rgba) != width * height * 4):
        raise ValueError('invalid alpha-mask image')
    support = {i for i, value in enumerate(rgba[3::4]) if value}
    if seed is not None:
        if (not isinstance(seed, list) or len(seed) != 2
                or any(type(v) is not int for v in seed)
                or not 0 <= seed[0] < width or not 0 <= seed[1] < height):
            raise ValueError('invalid alpha-mask seed')
        first = seed[1] * width + seed[0]
        if first not in support:
            raise ValueError('alpha-mask seed is transparent')
        selected = {first}; todo = [first]
        while todo:
            i = todo.pop(); x, y = i % width, i // width
            neighbours = []
            if x: neighbours.append(i - 1)
            if x + 1 < width: neighbours.append(i + 1)
            if y: neighbours.append(i - width)
            if y + 1 < height: neighbours.append(i + width)
            for j in neighbours:
                if j in support and j not in selected:
                    selected.add(j); todo.append(j)
        support = selected
    if not support:
        raise ValueError('empty alpha-mask support')
    return bytes(255 if i in support else 0 for i in range(width * height))


def protect_mask_rects(mask, width, height, rectangles):
    """Exclude explicitly protected neighbouring artwork from an alpha mask."""
    if len(mask) != width*height or set(mask)-{0,255}:
        raise ValueError('invalid protection mask')
    if not isinstance(rectangles,list) or len(rectangles)>16:
        raise ValueError('mask protection rectangle bound')
    result=bytearray(mask)
    for rect in rectangles:
        if (not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect)
                or min(rect[:2])<0 or min(rect[2:])<1
                or rect[0]+rect[2]>width or rect[1]+rect[3]>height):
            raise ValueError('mask protection rectangle outside crop')
        x,y,w,h=rect
        for row in range(y,y+h):
            result[row*width+x:row*width+x+w]=bytes(w)
    return bytes(result)


def locked_bytes(root, ref):
    path = (Path(root).resolve() / ref['path']).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('texture input outside project')
    data = path.read_bytes()
    if digest(data) != ref['sha256']:
        raise ValueError('texture input SHA256 mismatch: ' + ref['path'])
    return data


def source_alpha_preservation(original, modified, width, rect, mask):
    """Count changes to visible source art outside a traced caption mask."""
    if len(original) != len(modified) or len(original) % (width * 4):
        raise ValueError('source preservation image length mismatch')
    x, y, w, h = rect
    if len(mask) != w * h or set(mask) - {0, 255}:
        raise ValueError('source preservation mask mismatch')
    count = changed = 0
    for index, alpha in enumerate(original[3::4]):
        if not alpha:
            continue
        px, py = index % width, index // width
        if x <= px < x+w and y <= py < y+h and mask[(py-y)*w+px-x]:
            continue
        count += 1
        changed += original[index*4:index*4+4] != modified[index*4:index*4+4]
    return dict(visible_source_pixels=count, changed_source_pixels=changed)


def resolve_layers(root, plan, ids):
    """Resolve only requested layers with the production font/PNG hash locks."""
    import io
    import importlib.metadata
    from PIL import Image
    from .texture_overlay import render_label
    for key, expected in plan['rasterizer_versions'].items():
        if importlib.metadata.version(key) != expected:
            raise ValueError('rasterizer version mismatch')
    selected = set(ids); result = {}
    for row in plan['labels']:
        if row['id'] not in selected:
            continue
        label = copy.deepcopy(row)
        if any(k.startswith(('_repair_', '_glyph_')) for k in label):
            raise ValueError('private fields in texture plan')
        if 'restoration' in label:
            for key, mode, field in [('patch','RGBA','_repair_pixels'), ('mask','L','_repair_mask')]:
                im = Image.open(io.BytesIO(locked_bytes(root, label['restoration'][key])))
                if im.mode != mode or list(im.size) != label['rect'][2:]:
                    raise ValueError('restoration image geometry/mode mismatch')
                label[field] = im.tobytes()
        if 'glyph_mask' in label:
            im = Image.open(io.BytesIO(locked_bytes(root, label['glyph_mask'])))
            im = im.getchannel('A') if im.mode == 'RGBA' else im.convert('L')
            label.update(_glyph_pixels=im.tobytes(), _glyph_size=list(im.size))
        font = locked_bytes(root, label.get('font', plan['font']))
        result[row['id']] = (label, render_label(font, label))
    if set(result) != selected:
        raise ValueError('requested texture layers are missing')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--delta', required=True, type=Path)
    parser.add_argument('--delta-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output plan must be new')
    plan = args.plan.read_bytes(); delta = args.delta.read_bytes()
    if digest(plan) != args.plan_sha256 or digest(delta) != args.delta_sha256:
        raise ValueError('merge input SHA256 mismatch')
    out = merge_delta(json.loads(plan), json.loads(delta))
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS texture delta merged; labels=%d sources=%d sha256=%s' %
          (len(out['labels']), len(out['sources']), digest(args.output.read_bytes())))


if __name__ == '__main__':
    main()
