"""Source-frame-indexed caption compositing; all timing and wording are data."""
from __future__ import annotations

import hashlib
import copy


def render_title_layer(font_bytes, text, canvas, *, font_size, appearance):
    """Reuse the native-ink/tracking renderer without touching any background.

    Font, measured ink rectangle, colour/effect values and wording are explicit
    caller data. Legacy video-caption plans continue to use their old renderer.
    """
    from PIL import Image
    from .texture_appearance import render
    if (not isinstance(canvas,(tuple,list)) or len(canvas)!=2
            or any(type(value) is not int for value in canvas)
            or not 1<=canvas[0]<=1920 or not 1<=canvas[1]<=1080
            or not isinstance(font_bytes,bytes) or not 0<len(font_bytes)<=40*1024*1024):
        raise ValueError('Title layer font/canvas bound')
    label=dict(id='explicit-video-title-layer',text=text,rect=[0,0,*canvas],
               font_size=font_size,appearance=copy.deepcopy(appearance))
    rgba=render(font_bytes,label)
    image=Image.frombytes('RGBA',tuple(canvas),rgba)
    if image.getbbox() is None:
        raise ValueError('Title layer has no visible glyphs')
    proof=dict(render_method='source-style-v1',canvas=list(canvas),font_size=font_size,
               font_sha256=hashlib.sha256(font_bytes).hexdigest(),
               rgba_sha256=hashlib.sha256(rgba).hexdigest(),
               alpha_bbox=list(image.getbbox()),appearance=copy.deepcopy(appearance))
    return image,proof


def reference_window(erase, frame_count):
    window = erase.get('reference_window', [0, frame_count])
    if (type(frame_count) is not int or not 1 <= frame_count <= 6144
            or not isinstance(window, list) or len(window) != 2
            or any(type(value) is not int for value in window)
            or not 0 <= window[0] < window[1] <= frame_count):
        raise ValueError('Temporal source reference window bound')
    return window


def active_frame_indices(frame_alpha, expected_frames):
    """Validate a complete explicit opacity curve before opening repair assets."""
    if (type(expected_frames) is not int or not 1 <= expected_frames <= 6144
            or not isinstance(frame_alpha, list) or len(frame_alpha) != expected_frames
            or any(type(value) is not int or not 0 <= value <= 255 for value in frame_alpha)
            or not any(frame_alpha)):
        raise ValueError('Timed caption requires explicit bounded frame opacity values')
    return [index for index, alpha in enumerate(frame_alpha) if alpha]


def frame_exposure_values(frame_exposure, expected_frames):
    """Validate optional foreground-RGB exposure independently of opacity.

    Exposure is an explicit byte curve, not a fade of the composed background.
    ``None`` preserves the legacy layer RGB and its existing proof contract.
    """
    if (type(expected_frames) is not int or not 1 <= expected_frames <= 6144
            or (frame_exposure is not None
                and (not isinstance(frame_exposure, list) or len(frame_exposure) != expected_frames
                     or any(type(value) is not int or not 0 <= value <= 255
                            for value in frame_exposure)))):
        raise ValueError('Timed caption requires bounded frame exposure values')
    return None if frame_exposure is None else tuple(frame_exposure)


class VideoTitleCaption:
    def __init__(self, rect, mask, layer, frame_alpha, expected_frames, *, repairs=None,
                 frame_exposure=None):
        import numpy as np
        from PIL import Image
        active = active_frame_indices(frame_alpha, expected_frames)
        exposure = frame_exposure_values(frame_exposure, expected_frames)
        if (not isinstance(rect, list) or len(rect) != 4 or any(type(v) is not int for v in rect)
                or min(rect[:2]) < 0 or min(rect[2:]) <= 0
                or not isinstance(mask, np.ndarray) or mask.dtype != np.dtype('bool')
                or mask.shape != (rect[3], rect[2]) or not mask.any()
                or not isinstance(layer, Image.Image) or layer.mode != 'RGBA'
                or rect[0]+rect[2] > layer.width or rect[1]+rect[3] > layer.height):
            raise ValueError('Timed caption mask/layer geometry mismatch')
        if repairs is not None:
            from .video_frame_repairs import VideoFrameRepairs
            if (not isinstance(repairs, VideoFrameRepairs) or repairs.rect != tuple(rect)
                    or repairs.canvas != layer.size or repairs.frame_count != expected_frames
                    or not set(active).issubset(repairs.active_frames)
                    or not np.array_equal(repairs.mask, mask)):
                raise ValueError('Timed caption frame repairs must match geometry, mask and cover active text frames')
        self.rect = list(rect)
        self.mask = mask.copy()
        self.layer = layer.copy()
        self.layers = [self.layer]
        self.paint_bounds = self.layer.getbbox()
        if self.paint_bounds is None:
            raise ValueError('Timed caption layer has no visible glyphs')
        self.paint_layer = self.layer.crop(self.paint_bounds)
        self.frame_alpha = tuple(frame_alpha)
        self.frame_exposure = exposure
        self.repairs = repairs
        self._scaled = {}

    def apply(self, frame, frame_index):
        from PIL import Image
        if (type(frame_index) is not int or not 0 <= frame_index < len(self.frame_alpha)
                or not isinstance(frame, Image.Image) or frame.size != self.layer.size):
            raise ValueError('Timed caption frame index/canvas mismatch')
        alpha = self.frame_alpha[frame_index]
        if self.repairs is not None:
            repaired = self.repairs.apply(frame, frame_index)
        elif alpha:
            # Retained only for reproducible legacy research plans. Supplied
            # repairs always fail closed, never falling back to reconstruction.
            from .video_caption import restore_masked
            repaired, _ = restore_masked(frame, self.rect, self.mask)
        else:
            repaired = frame.copy()
        if not alpha:
            return repaired
        exposure = 255 if self.frame_exposure is None else self.frame_exposure[frame_index]
        key = (alpha, exposure)
        if key not in self._scaled:
            layer = self.paint_layer.copy()
            if exposure != 255:
                rgb_lookup = [round(value * exposure / 255) for value in range(256)]
                layer = layer.point(rgb_lookup * 3 + list(range(256)))
            layer.putalpha(layer.getchannel('A').point(lambda value: round(value*alpha/255)))
            self._scaled[key] = layer
        result = repaired.convert('RGBA')
        result.alpha_composite(self._scaled[key], self.paint_bounds[:2])
        return result.convert('RGB')

    def proof(self):
        text_active = [i for i, alpha in enumerate(self.frame_alpha) if alpha]
        active = list(self.repairs.active_frames) if self.repairs is not None else text_active
        evidence = dict(frame_opacity_sha256=hashlib.sha256(bytes(self.frame_alpha)).hexdigest(),
                    active_frames=len(active), first_active_frame=active[0],
                    last_active_frame_exclusive=active[-1]+1,
                    inactive_frames_preencode_byte_identical=True,
                    hidden_glyph_background_reconstructed=True,
                    background_method='sparse-frame-rgba-v1' if self.repairs is not None else 'legacy-harmonic-rgb-v1')
        if self.frame_exposure is not None:
            evidence['frame_exposure_sha256'] = hashlib.sha256(bytes(self.frame_exposure)).hexdigest()
        if self.repairs is not None:
            evidence['frame_repairs'] = self.repairs.proof()
            if active != text_active:
                evidence.update(text_active_frames=len(text_active),
                                first_text_active_frame=text_active[0],
                                last_text_active_frame_exclusive=text_active[-1]+1,
                                background_only_frames=len(active)-len(text_active))
        return evidence
