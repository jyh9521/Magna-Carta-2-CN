"""Recover a static underlay from paired screen-composited RGB video regions.

This is per-pixel weighted least squares, not blur, inpainting or a claim that
opaque source lettering reveals hidden artwork. Unknown channel information is
reported explicitly. Callers must independently establish reference alignment
and bound forward errors; a mathematically valid fit may use the wrong source.
"""
import math
from itertools import zip_longest
import numpy as np


def _pairs(reference_frames,target_frames,max_frames,max_pixels):
    if type(max_frames) is not int or not 1<=max_frames<=4096:
        raise ValueError('screen frame limit outside bound')
    if type(max_pixels) is not int or not 1<=max_pixels<=4194304:
        raise ValueError('screen pixel limit outside bound')
    missing=object();shape=None;count=0
    for reference,target in zip_longest(reference_frames,target_frames,fillvalue=missing):
        if reference is missing or target is missing:
            raise ValueError('screen source frame counts differ')
        count+=1
        if count>max_frames:raise ValueError('screen frame count exceeds bound')
        for frame in (reference,target):
            if (not isinstance(frame,np.ndarray) or frame.dtype!=np.uint8 or frame.ndim!=3
                    or frame.shape[2]!=3 or not frame.shape[0] or not frame.shape[1]
                    or frame.shape[0]*frame.shape[1]>max_pixels):
                raise ValueError('screen source must be bounded uint8 RGB')
            if shape is None:shape=frame.shape
            if frame.shape!=shape:raise ValueError('screen source geometry changed')
        yield reference.astype(np.float64)/255,target.astype(np.float64)/255
    if not count:raise ValueError('empty screen source frames')


def recover_underlay(reference_frames,target_frames,*,minimum_transmittance=.12,
                     max_frames=512,max_pixels=4194304):
    """Stream paired regions and return native RGB, confidence and unknown mask.

    With foreground F and observed target Y in [0,1], screen compositing is
    Y=F+(1-F)*B. The least-squares static estimate is
    B=sum((1-F)*(Y-F))/sum((1-F)**2). Per-channel confidence is RMS
    transmittance. A pixel is unknown if ANY channel falls below the threshold.
    Static white target pixels remain valid; only reference opacity determines
    information availability. Values returned for unknown pixels are not claims
    about original artwork and must not silently enter a reconstructed asset.
    """
    if (isinstance(minimum_transmittance,bool) or not isinstance(minimum_transmittance,(int,float))
            or not math.isfinite(minimum_transmittance) or not 0<minimum_transmittance<=1):
        raise ValueError('screen transmittance threshold outside (0,1]')
    numerator=denominator=squared=None;count=0
    for f,y in _pairs(reference_frames,target_frames,max_frames,max_pixels):
        d=1-f;z=y-f
        if numerator is None:
            numerator=np.zeros_like(f);denominator=np.zeros_like(f);squared=np.zeros_like(f)
        numerator+=d*z;denominator+=d*d;squared+=z*z;count+=1
    estimate=np.divide(numerator,denominator,out=np.zeros_like(numerator),where=denominator>0)
    estimate=np.clip(estimate,0,1)
    confidence_rgb=np.sqrt(denominator/count);confidence=confidence_rgb.min(axis=2)
    unknown=confidence<minimum_transmittance
    # Accumulated quadratic residual is algebraically the full forward replay.
    residual=np.maximum(0,squared-2*estimate*numerator+estimate*estimate*denominator)
    rms_rgb=np.sqrt(residual/count)*255
    known=~unknown
    return dict(underlay_rgb=np.rint(estimate*255).astype(np.uint8),
        native_estimate_rgb=(estimate*255).astype(np.float32),
        channel_confidence=confidence_rgb.astype(np.float32),confidence=confidence.astype(np.float32),
        unknown=unknown,forward_rms_rgb=rms_rgb.astype(np.float32),frame_count=count,
        minimum_transmittance=float(minimum_transmittance),unknown_pixels=int(unknown.sum()),
        known_pixels=int(known.sum()),
        forward_rms_known=float(np.sqrt(residual[known].sum()/(count*int(known.sum())*3))*255)
            if known.any() else None,
        model='screen-static-weighted-least-squares-v1',spatial_filter_applied=False)


def screen_forward_error(reference_frames,target_frames,underlay_rgb,known_mask=None,*,
                         max_frames=512,max_pixels=4194304):
    """Independent streaming replay; percentile is a conservative integer bound."""
    if (not isinstance(underlay_rgb,np.ndarray) or underlay_rgb.dtype!=np.uint8
            or underlay_rgb.ndim!=3 or underlay_rgb.shape[2]!=3):
        raise ValueError('screen underlay must be uint8 RGB')
    if known_mask is None:known_mask=np.ones(underlay_rgb.shape[:2],dtype=bool)
    if (not isinstance(known_mask,np.ndarray) or known_mask.dtype!=np.bool_
            or known_mask.shape!=underlay_rgb.shape[:2] or not known_mask.any()):
        raise ValueError('screen known mask must match underlay and select pixels')
    base=underlay_rgb.astype(np.float64)/255;total=square=0.;samples=frames=0
    histogram=np.zeros(256,np.int64);per_frame=[]
    for f,y in _pairs(reference_frames,target_frames,max_frames,max_pixels):
        if f.shape!=base.shape:raise ValueError('screen underlay geometry mismatch')
        error=(np.abs(f+(1-f)*base-y)*255)[known_mask]
        total+=float(error.sum());square+=float((error*error).sum());samples+=error.size;frames+=1
        histogram+=np.bincount(np.minimum(255,np.ceil(error)).astype(np.uint8).ravel(),minlength=256)
        per_frame.append(float(error.mean()))
    p99=int(np.searchsorted(np.cumsum(histogram),math.ceil(samples*.99)))
    return dict(frames=frames,known_pixels=int(known_mask.sum()),
        mean_absolute_error=total/samples,rms_error=math.sqrt(square/samples),
        p99_absolute_error_upper_bound=p99,per_frame_mean_absolute_error=per_frame,
        game_started=False)


def extract_stationary_matte(reference_frames,support_mask,*,max_frames=512,max_pixels=4194304):
    """Infer stationary screen matte from temporal minimum in explicit support.

    This is exact only if the reference consists of a stationary screen layer
    and every supported channel also has an unobscured zero-emission frame.
    Otherwise the minimum background haze is included. It never establishes
    the artwork hidden under opaque source pixels and never smooths neighbors.
    """
    if (not isinstance(support_mask,np.ndarray) or support_mask.dtype!=np.bool_
            or support_mask.ndim!=2 or not support_mask.any()):
        raise ValueError('stationary matte support must be a nonempty boolean mask')
    minimum=None;count=0
    # Pair each frame with itself without tee/caching either video stream.
    for frame in reference_frames:
        # Reuse the strict RGB/size checks, while retaining only the minimum.
        next(_pairs([frame],[frame],max_frames,max_pixels))
        if frame.shape[:2]!=support_mask.shape:
            raise ValueError('stationary matte support geometry mismatch')
        count+=1
        if count>max_frames:raise ValueError('stationary matte frame count exceeds bound')
        minimum=frame.copy() if minimum is None else np.minimum(minimum,frame)
    if minimum is None:raise ValueError('empty stationary matte reference')
    minimum[~support_mask]=0
    return dict(matte_rgb=minimum,frame_count=count,support_pixels=int(support_mask.sum()),
        minimum_haze_may_be_included=True,spatial_filter_applied=False,
        method='bounded-temporal-minimum-screen-matte-v1')


def inverse_screen(frame,matte,*,minimum_transmittance=.12,max_pixels=4194304):
    """Remove stationary screen matte per pixel; opaque cores remain unknown.

    Unknown RGB values are placeholders, not repaired art. The original target
    frame's moving smoke/lighting survives outside opaque cores. Zero matte
    pixels are byte-identical to the supplied frame after the round trip.
    """
    if (isinstance(minimum_transmittance,bool) or not isinstance(minimum_transmittance,(int,float))
            or not math.isfinite(minimum_transmittance) or not 0<minimum_transmittance<=1):
        raise ValueError('screen transmittance threshold outside (0,1]')
    m,y=next(_pairs([matte],[frame],1,max_pixels));d=1-m
    clean=np.divide(y-m,d,out=np.zeros_like(y),where=d>0)
    rgb=np.rint(np.clip(clean,0,1)*255).astype(np.uint8)
    confidence=d.min(axis=2);unknown=confidence<minimum_transmittance;known=~unknown
    replay=np.rint((m+d*(rgb.astype(np.float64)/255))*255).astype(np.uint8)
    error=np.abs(replay.astype(np.int16)-frame.astype(np.int16))
    below=(clean<0).any(axis=2)
    invalid=(matte.astype(np.int16)>frame.astype(np.int16)+4).any(axis=2)
    return dict(clean_rgb=rgb,channel_confidence=d.astype(np.float32),
        confidence=confidence.astype(np.float32),unknown=unknown,
        invalid_model=invalid,below_matte=below,
        unknown_pixels=int(unknown.sum()),known_pixels=int(known.sum()),
        below_matte_pixels=int(below.sum()),invalid_model_pixels=int(invalid.sum()),
        maximum_rescreen_error_known=int(error[known].max()) if known.any() else None,
        mean_rescreen_error_known=float(error[known].mean()) if known.any() else None,
        spatial_filter_applied=False)


def nearest_known_indices(unknown,*,max_radius=32,max_pixels=4194304):
    """Return (2,H,W) nearest-known index map, with deterministic bounded search.

    The map does not interpolate or replace texture. Callers may sample only a
    temporal lighting ratio using these indices. Known pixels map to themselves.
    Equal distances prefer lower row offset, then lower column offset.
    """
    if type(max_pixels) is not int or not 1<=max_pixels<=4194304:
        raise ValueError('nearest-known pixel limit outside bound')
    if (not isinstance(unknown,np.ndarray) or unknown.dtype!=np.bool_ or unknown.ndim!=2
            or not unknown.size or unknown.size>max_pixels or unknown.all()):
        raise ValueError('nearest-known mask must be bounded and contain known pixels')
    if type(max_radius) is not int or not 1<=max_radius<=128:
        raise ValueError('nearest-known radius outside [1,128]')
    indices=np.indices(unknown.shape,dtype=np.int32)
    rows,cols=np.where(unknown);pending=np.ones(len(rows),bool)
    offsets=sorted((dy*dy+dx*dx,dy,dx)
        for dy in range(-max_radius,max_radius+1) for dx in range(-max_radius,max_radius+1)
        if 0<dy*dy+dx*dx<=max_radius*max_radius)
    height,width=unknown.shape
    for _,dy,dx in offsets:
        active=np.flatnonzero(pending)
        if not active.size:break
        y=rows[active]+dy;x=cols[active]+dx
        inside=(y>=0)&(y<height)&(x>=0)&(x<width)
        active=active[inside];y=y[inside];x=x[inside]
        valid=~unknown[y,x];active=active[valid]
        indices[0,rows[active],cols[active]]=y[valid]
        indices[1,rows[active],cols[active]]=x[valid]
        pending[active]=False
    if pending.any():raise ValueError('nearest known pixel exceeds bounded radius')
    return indices


def extract_glyph_matte(reference_frames,support_mask,*,max_frames=512,max_pixels=4194304):
    """Infer glyph-only matte without stripping the native minimum FX haze.

    Input must be a black-background foreground reference, not target artwork.
    Provide known native FX context around the ink support, e.g. a 320x100
    reference crop containing a padded 192x40 source-ink mask. Only the reference
    temporal-minimum FX is spatially reconstructed beneath the ink, using the
    existing deterministic masked front-average/Laplace solver. Then
    T=(Fmin-Emin)/(1-Emin), with T=0 outside source support. The hidden native FX
    is an estimate, not an exact clean source; target artwork is never filtered.
    """
    if (not isinstance(support_mask,np.ndarray) or support_mask.dtype!=np.bool_
            or support_mask.ndim!=2 or not support_mask.any()
            or support_mask[0].any() or support_mask[-1].any()
            or support_mask[:,0].any() or support_mask[:,-1].any()):
        raise ValueError('glyph matte requires a known native FX perimeter around ink support')
    from PIL import Image
    from tools.video_caption import restore_masked
    proof=extract_stationary_matte(reference_frames,np.ones_like(support_mask),
        max_frames=max_frames,max_pixels=max_pixels)
    minimum=proof['matte_rgb'];height,width=support_mask.shape
    background,restoration=restore_masked(Image.fromarray(minimum),[0,0,width,height],support_mask)
    background_rgb=np.asarray(background).copy();f=minimum.astype(np.float64)/255
    e=background_rgb.astype(np.float64)/255;d=1-e
    matte=np.divide(f-e,d,out=np.zeros_like(f),where=d>0)
    matte=np.rint(np.clip(matte,0,1)*255).astype(np.uint8);matte[~support_mask]=0
    return dict(matte_rgb=matte,background_estimate_rgb=background_rgb,
        reference_minimum_rgb=minimum,frame_count=proof['frame_count'],
        support_pixels=int(support_mask.sum()),matte_nonzero_pixels=int((matte.max(2)>0).sum()),
        reference_fx_reconstructed=True,target_art_spatial_filter_applied=False,
        original_fx_exact=False,restoration=restoration,
        method='reference-fx-subtracted-glyph-screen-matte-v1')
