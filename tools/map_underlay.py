"""Reconstruct a small occluded map strip from explicitly reviewed clean rows.

This is an estimate of hidden art, not recovery of the original unseen pixels.
Coordinates and source identity belong to the locale profile. No text pixels or
previous repair image are sampled inside the occluded strip.
"""
import math
from PIL import Image
from .lettering_layers import box


def retained_art(background, rectangles):
    if not isinstance(rectangles, list) or len(rectangles) > 8:
        raise ValueError('art retention rectangle bound')
    result = Image.new('RGBA', background.size)
    for rect in rectangles:
        bounds = box(rect, background.size)
        result.paste(background.crop(bounds), tuple(rect[:2]))
    return result


def scanline_art(original, rect, spec):
    if (set(spec) != {'kind', 'top', 'bottom', 'preserve_rects'}
            or spec['kind'] != 'scanline-map-art-v1'
            or not isinstance(spec['preserve_rects'], list)
            or len(spec['preserve_rects']) > 8):
        raise ValueError('scanline art fields')
    x, y, w, h = rect
    box(rect, original.size)
    for row in (spec['top'], spec['bottom']):
        if (not isinstance(row, list) or len(row) != 3
                or any(type(v) is not int for v in row)
                or not 0 <= row[0] < original.height
                or not 0 <= row[1] < row[2] <= w):
            raise ValueError('clean donor row bounds')
    ty, tl, tr = spec['top']; by, bl, br = spec['bottom']
    if not ty <= y < y+h-1 <= by or by <= ty or by-ty > 128:
        raise ValueError('donors must bracket the occluded strip')

    def sample(yy, left, right, t):
        at = left + t*(right-left)-.5
        a = max(left, min(right-1, math.floor(at)))
        b = max(left, min(right-1, math.floor(at)+1))
        k = at-math.floor(at)
        p, q = original.getpixel((x+a, yy)), original.getpixel((x+b, yy))
        pp = [p[c]*p[3]/255 for c in range(3)]+[p[3]]
        qq = [q[c]*q[3]/255 for c in range(3)]+[q[3]]
        return [u*(1-k)+v*k for u,v in zip(pp,qq,strict=True)]

    out = Image.new('RGBA', (w,h))
    for yy in range(h):
        f = (y+yy-ty)/(by-ty)
        left, right = tl*(1-f)+bl*f, tr*(1-f)+br*f
        for xx in range(w):
            if not left <= xx+.5 < right:
                continue
            t = (xx+.5-left)/(right-left)
            a, b = sample(ty,tl,tr,t), sample(by,bl,br,t)
            p = [u*(1-f)+v*f for u,v in zip(a,b,strict=True)]
            alpha = round(p[3])
            if alpha:
                out.putpixel((xx,yy), tuple(min(255,round(v*255/p[3])) for v in p[:3])+(alpha,))
    for r in spec['preserve_rects']:
        b = box(r, out.size)
        out.paste(original.crop((x+b[0],y+b[1],x+b[2],y+b[3])), tuple(r[:2]))
    return out
