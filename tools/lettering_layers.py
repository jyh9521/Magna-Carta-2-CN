"""Clean glyph-only lettering and finite-support effects, independent of locale.

Source ink is unmatted against black from RGB * alpha; original dark alpha is
never a shadow input. Effects depend only on this ink, not neighbouring pixels.
"""
import copy
import math

from PIL import Image, ImageChops, ImageFilter

from .texture_overlay import render_label


def box(rect, size):
    if (not isinstance(rect, list) or len(rect) != 4
            or any(type(n) is not int for n in rect) or min(rect[:2]) < 0
            or min(rect[2:]) < 1 or rect[0]+rect[2] > size[0] or rect[1]+rect[3] > size[1]):
        raise ValueError('rectangle outside image')
    x, y, w, h = rect
    return x, y, x+w, y+h


def source_ink(source, core, floor=16):
    """Retain native glyph sampling and premultiplied colour, discard old matte.

    Per-row peak ink estimates its unmatted colour. Black (including arbitrary
    opaque black inside the core) contributes no glyph coverage. This does not
    copy a halo, interpolate glyph positions, typeset, or change text size.
    """
    x0, y0, x1, y1 = box(core, source.size)
    if source.mode != 'RGBA' or type(floor) is not int or not 0 <= floor <= 32:
        raise ValueError('RGBA and bounded ink floor required')
    out = Image.new('RGBA', source.size)
    seed = Image.new('L', source.size)
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = source.getpixel((x, y))
            if p[3] >= 32 and max(p[:3]) >= 48:
                seed.putpixel((x, y), 255)
    # Only the one-sample antialias fringe of real coloured ink is eligible.
    # Weak RGB565 palette bleed in empty character spacing is not a glyph.
    eligible = seed.filter(ImageFilter.MaxFilter(3))
    for y in range(y0, y1):
        row = [source.getpixel((x, y)) for x in range(x0, x1)]
        peak = max((max(p[:3]) for p in row if p[3]), default=0)
        if peak <= floor:
            continue
        for x, p in zip(range(x0, x1), row, strict=True):
            bright = max(p[:3])
            if bright <= floor or not p[3] or not eligible.getpixel((x, y)):
                continue
            coverage = bright / peak
            alpha = round(p[3] * coverage)
            if alpha >= 4:
                out.putpixel((x, y), (*[min(255, round(c/coverage)) for c in p[:3]], alpha))
    if not out.getbbox():
        raise ValueError('empty source ink')
    return out


def font_ink(font, label):
    """Use the existing source-style geometry, without any baked effects."""
    label = copy.deepcopy(label)
    if 'appearance' in label:
        a = label['appearance']
        # Keep outline_width: it is also the renderer's historical layout margin.
        for key in ('outline', 'shadow', 'glow'):
            a[key] = [0, 0, 0, 0]
        a['shadow_radius'] = a['glow_radius'] = a['motion'] = 0
    else:
        for key in ('stroke_fill', 'shadow_fill'):
            label['style'][key] = [0, 0, 0, 0]
    ink = Image.frombytes('RGBA', tuple(label['rect'][2:]), render_label(font, label))
    ink.putalpha(ink.getchannel('A').point(lambda a: a if a >= 4 else 0))
    return ink


def effects(ink, spec):
    """Finite-support outline and drop shadow from glyph coverage alone.

    Bilinear supersampling avoids ringing in the outline. The shadow uses the
    glyph, not a rectangle or dilated outline. A radial support bound cuts only
    the already faint Gaussian tail, never a straight rectangular shadow edge.
    """
    required = {'outline_width', 'outline_alpha', 'shadow_radius', 'shadow_alpha',
                'shadow_offset', 'support_radius'}
    if set(spec) != required:
        raise ValueError('explicit effect fields required')
    for k, limit in [('outline_width', 2), ('shadow_radius', 2),
                     ('outline_alpha', 255), ('shadow_alpha', 255)]:
        v = spec[k]
        if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= limit:
            raise ValueError('effect bound: '+k)
    reach = spec['support_radius']
    shift = spec['shadow_offset']
    if (type(reach) is not int or not 1 <= reach <= 5 or not isinstance(shift, list)
            or len(shift) != 2 or any(type(v) is not int or abs(v) > 2 for v in shift)):
        raise ValueError('effect support/offset bound')
    mask = ink.getchannel('A')
    support = mask.point(lambda a: 255 if a else 0).filter(ImageFilter.MaxFilter(2*reach+1))
    high = mask.resize((ink.width*4, ink.height*4), Image.Resampling.BILINEAR)
    radius = round(spec['outline_width']*4)
    outline = high.filter(ImageFilter.MaxFilter(radius*2+1)).resize(ink.size, Image.Resampling.BILINEAR)
    shadow = Image.new('L', ink.size)
    shadow.paste(mask, tuple(shift))
    shadow = shadow.filter(ImageFilter.GaussianBlur(spec['shadow_radius']))
    layers = {}
    for name, m, alpha in [('outline', outline, spec['outline_alpha']),
                            ('shadow', shadow, spec['shadow_alpha'])]:
        m = ImageChops.multiply(m, support).point(lambda a: round(a*alpha/255))
        m = m.point(lambda a: a if a >= 3 else 0)
        layer = Image.new('RGBA', ink.size)
        layer.putalpha(m)
        layers[name] = layer
    result = Image.alpha_composite(layers['shadow'], layers['outline'])
    result = Image.alpha_composite(result, ink)
    return result, dict(ink=ink, **layers)
