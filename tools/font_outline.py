"""Bounded fractional outline emboldening shared by previews and font builds."""
import math
from PIL import Image, ImageDraw


def embolden_glyph(font, cell, record, alpha, metric_height, stroke_em):
    """Fractional FreeType outline stroke, not a designer's weight master.

    Render the font outline again, never blur or expand an antialiased bitmap.
    Keep the original baseline/advance and all original alpha. Growth is bounded
    to the existing visible metric rectangle, with excluded samples reported.
    """
    if (isinstance(stroke_em, bool) or not isinstance(stroke_em, (int, float))
            or not math.isfinite(stroke_em) or not 0 <= stroke_em <= 0.02):
        raise ValueError('Invalid bounded outline stroke')
    if not stroke_em or record['raster_bbox'] is None:
        return alpha, dict(added_alpha=0, boundary_samples=0)
    width, height = cell['width'], cell['height']
    mask, offset = font.getmask2(cell['character'], mode='L', anchor='ls')
    ink = mask.getbbox()
    if ink is None:
        raise ValueError('Unexpected empty outline during emboldening')
    anchor_x = record['raster_bbox'][0] - offset[0] - ink[0]
    pad = 3
    canvas = Image.new('L', (width+2*pad, height+2*pad))
    ImageDraw.Draw(canvas).text((anchor_x+pad, record['cell_baseline']+pad),
                               cell['character'], font=font, anchor='ls', fill=255,
                               stroke_width=font.size*stroke_em, stroke_fill=255)
    pixels = canvas.tobytes()
    result = bytearray(alpha)
    added = boundary = 0
    for y in range(-pad, height+pad):
        for x in range(-pad, width+pad):
            source = alpha[y*width+x] if 0 <= x < width and 0 <= y < height else 0
            delta = max(0, pixels[(y+pad)*(width+2*pad)+x+pad]-source)
            if 0 <= x < cell['metric_width'] and 0 <= y < metric_height:
                result[y*width+x] += delta
                added += delta
            elif delta:
                boundary += 1
    return bytes(result), dict(added_alpha=added, boundary_samples=boundary)
